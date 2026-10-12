"""Extract auditable agriculture rows from the three downloaded economic PDFs.

This is an extraction/quality-control step, NOT a training-data merger. The
MoSPI publications use different constant-price bases and the RBI table uses
a different national-accounts measure. Never concatenate their values into a
single model target without a documented harmonisation decision.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data" / "raw" / "economic"
DEFAULT_OUTPUT = ROOT / "data" / "interim" / "economic"
import sys

sys.path.insert(0, str(ROOT / "backend"))
from app.services.ingestion.states import INDIAN_STATES

PROJECT_STATES = INDIAN_STATES
YEAR_RE = re.compile(r"\b((?:19|20)\d{2})-((?:19|20)\d{2}|\d{2})\b")
VALUE_RE = re.compile(r"\d[\d,]*|[-–—]")
FIELDS = (
    "state", "financial_year", "start_year", "agriculture_lakh",
    "agriculture_crore", "source", "price_base", "measure", "sector",
    "source_file", "pdf_page", "quality_flags",
)
ISSUE_FIELDS = ("severity", "code", "state", "financial_year", "source_file", "pdf_page", "detail")


def issue(severity: str, code: str, detail: str, *, state: str = "",
          financial_year: str = "", source_file: str = "", pdf_page: int | str = "") -> dict:
    return dict(severity=severity, code=code, state=state,
                financial_year=financial_year, source_file=source_file,
                pdf_page=pdf_page, detail=detail)


def find_years(text: str) -> list[str]:
    """Find the table header with the most financial-year columns."""
    lines = text.splitlines()
    matches = max((list(YEAR_RE.finditer(line)) for line in lines), key=len, default=[])
    years = []
    for match in matches:
        start, end = int(match.group(1)), int(match.group(2))
        if end < 100:
            end = (start // 100) * 100 + end
            if end < start:
                end += 100
        if end != start + 1:
            raise ValueError(f"Invalid financial-year header: {match.group(0)}")
        years.append(f"{start}-{end % 100:02d}")
    if len(years) < 3 or len(years) != len(set(years)):
        raise ValueError("Could not identify an unambiguous financial-year header")
    return years


def parse_value(token: str) -> int | None:
    token = token.strip()
    if token in {"-", "–", "—", "NA", "N/A", ".."}:
        return None
    if not re.fullmatch(r"\d[\d,]*", token):
        raise ValueError(f"Unrecognised numeric cell: {token!r}")
    return int(token.replace(",", ""))


def mospi_agriculture_cells(text: str, years: list[str]) -> list[str]:
    """Select only row 1 Agriculture, not Ag & Allied or total GSDP."""
    for line in text.splitlines():
        english_left = re.match(r"^\s*1\s+Agriculture\s+(.+)$", line)
        # In four pages the last value and the right-hand row number touch in
        # extracted text (e.g. "43001761 Agriculture" = 4300176 + row 1).
        english_right = re.search(r"1\s+Agriculture\s*$", line)
        if english_left:
            cells = VALUE_RE.findall(english_left.group(1))
        elif english_right:
            cells = VALUE_RE.findall(line[:english_right.start()])
            if cells and cells[0] == "1":
                cells = cells[1:]
        else:
            continue
        if len(cells) != len(years):
            raise ValueError(f"Agriculture row has {len(cells)} cells, expected {len(years)}")
        return cells
    raise ValueError("Row 1 Agriculture not found")


def rbi_agriculture_cells(text: str, state: str, years: list[str]) -> list[str]:
    for line in text.splitlines():
        match = re.match(rf"^\s*{re.escape(state)}\s+(.+)$", line, re.IGNORECASE)
        if match:
            cells = VALUE_RE.findall(match.group(1))
            if len(cells) != len(years):
                raise ValueError(f"{state} has {len(cells)} cells, expected {len(years)}")
            return cells
    raise ValueError(f"State row not found: {state}")


def make_rows(state: str, years: list[str], cells: list[str], source: str,
              price_base: str, measure: str, source_file: str, pdf_page: int) -> list[dict]:
    rows = []
    for financial_year, token in zip(years, cells, strict=True):
        value = parse_value(token)
        rows.append(dict(
            state=state, financial_year=financial_year,
            start_year=int(financial_year[:4]), agriculture_lakh=value,
            agriculture_crore=round(value / 100, 2) if value is not None else None,
            source=source, price_base=price_base, measure=measure,
            sector="Agriculture (excluding separate forestry and fishing rows)",
            source_file=source_file, pdf_page=pdf_page, quality_flags="",
        ))
    return rows


def compact(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.casefold())


def source_label(path: Path) -> str:
    """Use portable project-relative provenance when the PDF is in this repo."""
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path.resolve())


def extract_mospi_state_pdfs(folder: Path, states: tuple[str, ...]) -> tuple[list[dict], list[dict]]:
    import pdfplumber

    rows, issues = [], []
    files = {compact(p.stem.removeprefix("GSDP_")): p for p in folder.glob("GSDP_*.pdf")}
    # The older publication's file is GSDP_Andhra.pdf, not GSDP_AndhraPradesh.pdf.
    if "andhra" in files:
        files["andhrapradesh"] = files["andhra"]
    if "arunachal" in files:
        files["arunachalpradesh"] = files["arunachal"]
    for source_name, current_name in (("chattisgarh", "chhattisgarh"),
                                      ("orissa", "odisha"),
                                      ("uttrakhand", "uttarakhand")):
        if source_name in files:
            files[current_name] = files[source_name]
    for state in states:
        path = files.get(compact(state))
        if path is None:
            severity = "warning" if state == "Telangana" else "error"
            detail = ("State did not exist separately in this historical series"
                      if state == "Telangana" else "No matching 1999-2000 state PDF")
            issues.append(issue(severity, "missing_state_pdf", detail, state=state))
            continue
        with pdfplumber.open(path) as pdf:
            selected = [(n, page) for n, page in enumerate(pdf.pages, 1)
                        if "AT 1999-2000 PRICES" in (page.extract_text() or "").upper()]
            if len(selected) != 1:
                issues.append(issue("error", "constant_page_count",
                                    f"Expected one 1999-2000-price page, found {len(selected)}",
                                    state=state, source_file=source_label(path)))
            for page_no, page in selected:
                try:
                    text = page.extract_text(layout=True) or ""
                    years = find_years(text)
                    cells = mospi_agriculture_cells(text, years)
                    rows.extend(make_rows(state, years, cells, "mospi_1999_2000", "1999-2000",
                                          "GSDP at factor cost, Agriculture row", source_label(path), page_no))
                except ValueError as exc:
                    issues.append(issue("error", "extraction_failed", str(exc), state=state,
                                        source_file=source_label(path), pdf_page=page_no))
    return rows, issues


def extract_mospi_all_states(path: Path, states: tuple[str, ...]) -> tuple[list[dict], list[dict]]:
    import pdfplumber

    rows, issues = [], []
    found = Counter()
    with pdfplumber.open(path) as pdf:
        for page_no, page in enumerate(pdf.pages, 1):
            plain = (page.extract_text() or "").upper()
            if "AT 2004-05 PRICES" not in plain:
                continue  # Skip the adjacent current-price page.
            text = page.extract_text(layout=True) or ""
            header_lines = {line.strip().upper() for line in text.splitlines()[:20]}
            historical_names = {"Chhattisgarh": "CHATTISGARH", "Odisha": "ORISSA",
                                "Uttarakhand": "UTTARANCHAL"}
            candidates = [state for state in states
                          if state.upper() in header_lines or historical_names.get(state) in header_lines]
            if not candidates:
                continue  # Page does not match the current state catalogue.
            if len(candidates) != 1:
                issues.append(issue("error", "ambiguous_state_header", repr(candidates),
                                    source_file=source_label(path), pdf_page=page_no))
                continue
            state = candidates[0]
            found[state] += 1
            try:
                years = find_years(text)
                cells = mospi_agriculture_cells(text, years)
                rows.extend(make_rows(state, years, cells, "mospi_2004_05", "2004-05",
                                      "GSDP at factor cost, Agriculture row", source_label(path), page_no))
            except ValueError as exc:
                issues.append(issue("error", "extraction_failed", str(exc), state=state,
                                    source_file=source_label(path), pdf_page=page_no))
    for state in states:
        if found[state] != 1:
            severity = "warning" if state == "Telangana" and found[state] == 0 else "error"
            issues.append(issue(severity, "constant_page_count",
                                f"Expected one 2004-05-price page, found {found[state]}",
                                state=state, source_file=source_label(path)))
    return rows, issues


def extract_rbi(path: Path, states: tuple[str, ...]) -> tuple[list[dict], list[dict]]:
    import pdfplumber

    rows, issues = [], []
    with pdfplumber.open(path) as pdf:
        if len(pdf.pages) != 2:
            issues.append(issue("warning", "unexpected_page_count",
                                f"Expected the two-page RBI Table 30, found {len(pdf.pages)}",
                                source_file=source_label(path)))
        all_text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        if "TABLE 30" not in all_text.upper() or "BASE: 2011-12" not in all_text.upper():
            issues.append(issue("error", "wrong_rbi_table",
                                "PDF does not identify Table 30 and base 2011-12",
                                source_file=source_label(path)))
            return rows, issues
        if "DATA PERTAIN TO CROPS" not in all_text.upper():
            issues.append(issue("warning", "missing_scope_note",
                                "Could not verify RBI's crops-only footnote",
                                source_file=source_label(path)))
        for page_no, page in enumerate(pdf.pages, 1):
            text = page.extract_text(layout=True) or ""
            try:
                years = find_years(text)
            except ValueError as exc:
                issues.append(issue("error", "extraction_failed", str(exc),
                                    source_file=source_label(path), pdf_page=page_no))
                continue
            for state in states:
                try:
                    cells = rbi_agriculture_cells(text, state, years)
                    rows.extend(make_rows(state, years, cells, "rbi_2011_12", "2011-12",
                                          "GSVA, Agriculture (RBI note: crops)", source_label(path), page_no))
                except ValueError as exc:
                    issues.append(issue("error", "extraction_failed", str(exc), state=state,
                                        source_file=source_label(path), pdf_page=page_no))
    return rows, issues


def audit(rows: list[dict], issues: list[dict]) -> None:
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    seen = set()
    for row in rows:
        key = (row["source"], row["state"], row["financial_year"])
        if key in seen:
            row["quality_flags"] = "duplicate_source_state_year"
            issues.append(issue("error", "duplicate_source_state_year", "Repeated extraction key",
                                state=row["state"], financial_year=row["financial_year"],
                                source_file=row["source_file"], pdf_page=row["pdf_page"]))
        seen.add(key)
        groups[(row["source"], row["state"])].append(row)
        if row["agriculture_lakh"] is None:
            row["quality_flags"] += ";missing_official_value" if row["quality_flags"] else "missing_official_value"
            issues.append(issue("warning", "missing_official_value", "Source table contains a dash; not imputed",
                                state=row["state"], financial_year=row["financial_year"],
                                source_file=row["source_file"], pdf_page=row["pdf_page"]))
        elif row["agriculture_lakh"] <= 0:
            row["quality_flags"] += ";nonpositive_value" if row["quality_flags"] else "nonpositive_value"
            issues.append(issue("warning", "nonpositive_value", "Review source PDF; value not changed",
                                state=row["state"], financial_year=row["financial_year"],
                                source_file=row["source_file"], pdf_page=row["pdf_page"]))
    for group in groups.values():
        group.sort(key=lambda r: r["start_year"])
        for previous, current in zip(group, group[1:]):
            a, b = previous["agriculture_lakh"], current["agriculture_lakh"]
            if a and b is not None and current["start_year"] == previous["start_year"] + 1:
                change = (b - a) / a
                if abs(change) > 0.5:
                    current["quality_flags"] += ";large_yoy_change" if current["quality_flags"] else "large_yoy_change"
                    issues.append(issue("review", "large_yoy_change",
                                        f"{change:+.1%} from prior financial year; not altered",
                                        state=current["state"], financial_year=current["financial_year"],
                                        source_file=current["source_file"], pdf_page=current["pdf_page"]))


def write_csv(path: Path, fields: tuple[str, ...], rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--overwrite", action="store_true", help="Replace this script's earlier generated outputs")
    args = parser.parse_args()
    folder = args.input_dir
    old_folder = folder / "mospi_1999_2000"
    middle_pdf = folder / "mospi_2004_05.pdf"
    rbi_pdf = folder / "rbi_2011_12.pdf"
    for expected in (old_folder, middle_pdf, rbi_pdf):
        if not expected.exists():
            parser.error(f"Required source not found: {expected}")
    targets = [args.output_dir / name for name in
               ("extracted_agriculture.csv", "complete_cases_by_source.csv",
                "extraction_issues.csv", "extraction_summary.json")]
    existing = [str(path) for path in targets if path.exists()]
    if existing and not args.overwrite:
        parser.error("Generated output already exists. Pass --overwrite to replace it: " + ", ".join(existing))

    try:
        import pdfplumber  # noqa: F401
    except ImportError:
        parser.error("pdfplumber is missing. Install: python -m pip install -r scripts/requirements-economic.txt")

    rows, issues = [], []
    for extracted, found_issues in (
        extract_mospi_state_pdfs(old_folder, PROJECT_STATES),
        extract_mospi_all_states(middle_pdf, PROJECT_STATES),
        extract_rbi(rbi_pdf, PROJECT_STATES),
    ):
        rows.extend(extracted)
        issues.extend(found_issues)
    audit(rows, issues)
    rows.sort(key=lambda r: (r["source"], r["state"], r["start_year"]))
    issues.sort(key=lambda r: (r["severity"], r["code"], r["state"], r["financial_year"]))
    complete = [r for r in rows if r["agriculture_lakh"] is not None and r["agriculture_lakh"] > 0]
    coverage = {}
    for source in ("mospi_1999_2000", "mospi_2004_05", "rbi_2011_12"):
        coverage[source] = {}
        for state in PROJECT_STATES:
            group = [r for r in rows if r["source"] == source and r["state"] == state]
            coverage[source][state] = {
                "rows": len(group),
                "first": min((r["financial_year"] for r in group), default=None),
                "last": max((r["financial_year"] for r in group), default=None),
            }
    summary = {
        "rows": len(rows), "rows_by_source": dict(Counter(r["source"] for r in rows)),
        "complete_case_rows": len(complete),
        "missing_values": sum(r["agriculture_lakh"] is None for r in rows),
        "issues_by_code": dict(Counter(item["code"] for item in issues)),
        "coverage": coverage,
        "ready_for_training": False,
        "why_not_training_ready": [
            "The three sources have different constant-price bases and accounting measures.",
            "Financial-year targets have not been aligned to climate periods.",
            "All extraction warnings and source-page values require review.",
        ],
        "policy": "No missing-value imputation, clipping, outlier removal, or model fitting is performed.",
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(targets[0], FIELDS, rows)
    write_csv(targets[1], FIELDS, complete)
    write_csv(targets[2], ISSUE_FIELDS, issues)
    targets[3].write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"Saved extracted rows and review report in {args.output_dir}")
    return 0 if not any(item["severity"] == "error" for item in issues) else 1


if __name__ == "__main__":
    raise SystemExit(main())

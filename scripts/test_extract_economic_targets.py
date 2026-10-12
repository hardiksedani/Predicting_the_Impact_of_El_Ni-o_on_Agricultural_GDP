"""Small parser tests; no user PDFs or external packages required."""

import unittest

from extract_economic_targets import (
    PROJECT_STATES, audit, find_years, make_rows, mospi_agriculture_cells,
    parse_value, rbi_agriculture_cells,
)


class EconomicExtractionTests(unittest.TestCase):
    def test_all_28_states_are_included(self):
        self.assertEqual(len(PROJECT_STATES), 28)
        self.assertIn("Arunachal Pradesh", PROJECT_STATES)

    def test_four_digit_end_year_in_mospi_header(self):
        text = "Sector 2010-11 2011-2012 2012-13\n1 Agriculture 100 200 300"
        self.assertEqual(find_years(text), ["2010-11", "2011-12", "2012-13"])

    def test_old_mospi_selects_agriculture_not_allied(self):
        text = "Sector 2001-02 2002-03 2003-04\n1 Agriculture 100 200 300\nAgr and Allied 150 250 350"
        years = find_years(text)
        self.assertEqual(mospi_agriculture_cells(text, years), ["100", "200", "300"])

    def test_bilingual_mospi_glued_row_number(self):
        text = "Sector 2004-05 2005-06 2006-07\n1 कृषष 100 200 3001 Agriculture"
        years = find_years(text)
        self.assertEqual(mospi_agriculture_cells(text, years), ["100", "200", "300"])

    def test_rbi_dash_is_missing_not_zero(self):
        text = "State 2022-23 2023-24 2024-25\nGujarat 1,03,36,581 - -"
        years = find_years(text)
        cells = rbi_agriculture_cells(text, "Gujarat", years)
        self.assertEqual([parse_value(x) for x in cells], [10336581, None, None])

    def test_audit_flags_but_keeps_large_real_change(self):
        rows = make_rows("Rajasthan", ["2002-03", "2003-04"], ["100", "200"],
                         "test", "1999-2000", "GSDP Agriculture", "sample.pdf", 2)
        problems = []
        audit(rows, problems)
        self.assertEqual(rows[1]["agriculture_lakh"], 200)
        self.assertIn("large_yoy_change", rows[1]["quality_flags"])


if __name__ == "__main__":
    unittest.main()

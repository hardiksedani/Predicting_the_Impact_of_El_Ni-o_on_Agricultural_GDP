"""Two-tier Search and Knowledge Assistant Engine.

Separates:
- System A: ML Prediction & Scenario Engine
- System B: Trusted Climate / El Niño Knowledge Base

Performs query intent classification:
- Type 1: General factual El Niño question (retrieves verified knowledge with citations)
- Type 2: Historical project-data query (queries panel database)
- Type 3: Model prediction question (calls ML prediction engine)
- Type 4: Scenario question (calls scenario engine)
- Type 5: Mixed question (synthesizes model results + verified context)
"""

import re
from typing import Any, Optional

from app.constants import DISCLAIMER
from app.models.schemas import (
    SearchCitation,
    SearchRequest,
    SearchResponse,
)
from app.services.db_storage import get_db
from app.services.ml import (
    fetch_climate_dataframe,
    get_model_metrics,
    predict_gdp,
)
from app.services.scenario_service import PRESET_CONFIGS, run_scenario_simulation
from app.models.schemas import ScenarioRequest

# Trusted Knowledge Base for El Niño & Indian Agriculture
KNOWLEDGE_DOCS = [
    {
        "id": "enso_definition",
        "keywords": ["what is el nino", "enso", "definition", "oceanic nino index", "oni", "meaning", "explain el nino"],
        "source": "NOAA Climate Prediction Center",
        "title": "Understanding El Niño-Southern Oscillation (ENSO) and the Oceanic Niño Index (ONI)",
        "url": "https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/ensostuff/ensoyears.shtml",
        "content": (
            "El Niño is the warm phase of the El Niño-Southern Oscillation (ENSO), characterized by anomalous "
            "sea surface warming in the central and eastern tropical Pacific Ocean (Niño 3.4 region). NOAA monitors "
            "ENSO using the Oceanic Niño Index (ONI), defined as the 3-month running mean of ERSST.v5 sea surface "
            "temperature anomalies in the Niño 3.4 region (5°N–5°S, 120°–170°W). An ONI threshold of +0.5°C or higher "
            "for at least five consecutive overlapping three-month seasons signifies an El Niño episode."
        ),
    },
    {
        "id": "monsoon_impact",
        "keywords": ["monsoon", "rainfall", "impact on india", "indian monsoon", "drought", "agriculture"],
        "source": "India Meteorological Department (IMD) & Ministry of Earth Sciences",
        "title": "Historical Association Between El Niño Episodes and Southwest Monsoon Deficits in India",
        "url": "https://mausam.imd.gov.in/",
        "content": (
            "Historical meteorological records indicate that approximately 60% of major Indian drought years have "
            "coincided with El Niño episodes. During strong El Niño events (such as 2002, 2009, 2014, 2015), the "
            "Walker Circulation shifts eastward, suppressing convective rainfall activity across the Indian subcontinent "
            "during the crucial June-to-September Southwest Monsoon season, which supplies over 70% of India's annual precipitation."
        ),
    },
    {
        "id": "economic_impact",
        "keywords": ["gdp", "gva", "economic", "agriculture gdp", "crop", "kharif", "loss", "farm income"],
        "source": "Reserve Bank of India (RBI) & MoSPI",
        "title": "Macroeconomic Impact of Monsoon Variability on Agricultural Gross Value Added (GSVA)",
        "url": "https://rbi.org.in/",
        "content": (
            "Agriculture and allied sectors contribute approximately 16–18% of India's overall GVA and employ over 45% "
            "of the national workforce. Severe monsoon deficits during El Niño years disproportionately impact Kharif "
            "crop sowing (especially rice, pulses, and oilseeds), leading to reduced Agricultural GSVA growth rates, "
            "rural wage contractions, and potential food price inflationary pressures."
        ),
    },
    {
        "id": "mitigation_irrigation",
        "keywords": ["irrigation", "policy", "mitigation", "resilience", "drought management"],
        "source": "Directorate of Economics and Statistics (DES), Ministry of Agriculture",
        "title": "Agricultural Drought Management and Irrigation Buffer Mechanisms",
        "url": "https://agricoop.nic.in/",
        "content": (
            "States with high canal and groundwater irrigation coverage (such as Punjab and Haryana) exhibit greater "
            "resilience against El Niño-induced rainfall shocks compared to rainfed agro-climatic zones (such as Vidarbha "
            "and Marathwada in Maharashtra, or dry zones in Rajasthan and Karnataka). Expanding micro-irrigation and "
            "crop diversification are central to state drought mitigation strategies."
        ),
    },
]


def classify_query_intent(query: str) -> str:
    q = query.lower()

    # Check for scenario
    if any(k in q for k in ["scenario", "what happens if", "under strong", "under moderate", "simulate", "if rainfall drops"]):
        return "scenario"

    # Check for prediction
    if any(k in q for k in ["predict", "prediction", "forecast", "will gdp decline", "estimated impact", "future"]):
        return "prediction"

    # Check for historical data
    if any(k in q for k in ["highest", "lowest", "in 201", "in 202", "historical", "trend", "past gdp", "which state"]):
        return "historical"

    # Check for factual ENSO / climate questions
    if any(k in q for k in ["what is", "how does", "explain", "who", "definition", "why does", "meaning of"]):
        return "factual"

    return "mixed"


def _answer_factual(query: str) -> tuple[str, list[SearchCitation]]:
    q = query.lower()
    matched_docs = []
    for doc in KNOWLEDGE_DOCS:
        score = sum(1 for kw in doc["keywords"] if kw in q)
        if score > 0:
            matched_docs.append((score, doc))

    matched_docs.sort(key=lambda x: x[0], reverse=True)
    selected = [d[1] for d in matched_docs[:2]] if matched_docs else [KNOWLEDGE_DOCS[0], KNOWLEDGE_DOCS[1]]

    citations = [
        SearchCitation(
            source=doc["source"],
            title=doc["title"],
            url=doc.get("url"),
            snippet=doc["content"][:200] + "...",
        )
        for doc in selected
    ]

    answer_parts = [f"**Knowledge Retrieval Result:**\n\n{selected[0]['content']}"]
    if len(selected) > 1:
        answer_parts.append(f"\n\n**Additional Climate Context:**\n{selected[1]['content']}")

    return "".join(answer_parts), citations


def _answer_historical(query: str) -> tuple[str, Optional[dict[str, Any]], list[SearchCitation]]:
    df = fetch_climate_dataframe()
    if df.empty:
        return "No historical records are currently available in the database. Please run the pipeline first.", None, []

    q = query.lower()
    citations = [
        SearchCitation(
            source="PBL Panel Database (Open-Meteo climate, NOAA ONI, unverified GDP sample)",
            title="Cleaned state-wise climate and illustrative agricultural target panel",
            url=None,
            snippet=f"Covering {df['state'].nunique()} states from {int(df['year'].min())} to {int(df['year'].max())}.",
        )
    ]

    # Check if a specific state is mentioned
    state_match = None
    for s in df["state"].unique():
        if s.lower() in q:
            state_match = s
            break

    if state_match:
        sdf = df[df["state"] == state_match].sort_values("year")
        avg_gdp = float(sdf["agricultural_gdp_cr"].mean())
        latest = sdf.iloc[-1]
        earliest = sdf.iloc[0]

        answer = (
            f"**Historical Records for {state_match}:**\n\n"
            f"• **Historical Average Agricultural GVA/GDP:** ₹{avg_gdp:,.1f} Crore\n"
            f"• **Earliest Year ({int(earliest['year'])}):** ₹{float(earliest['agricultural_gdp_cr']):,.1f} Cr (Rainfall: {float(earliest['rainfall_mm']):.1f} mm, ONI: {float(earliest['oni_index']):.2f})\n"
            f"• **Most Recent Year ({int(latest['year'])}):** ₹{float(latest['agricultural_gdp_cr']):,.1f} Cr (Rainfall: {float(latest['rainfall_mm']):.1f} mm, ONI: {float(latest['oni_index']):.2f})\n"
            f"• **Total Observations:** {len(sdf)} years recorded in our panel."
        )
        return answer, {"state": state_match, "history_count": len(sdf), "avg_gdp_cr": avg_gdp}, citations

    # Overall dataset summary
    top_state = df.groupby("state")["agricultural_gdp_cr"].mean().idxmax()
    top_val = df.groupby("state")["agricultural_gdp_cr"].mean().max()
    lowest_state = df.groupby("state")["agricultural_gdp_cr"].mean().idxmin()
    lowest_val = df.groupby("state")["agricultural_gdp_cr"].mean().min()

    answer = (
        f"**Panel Dataset Overview:**\n\n"
        f"• **Total States:** {df['state'].nunique()}\n"
        f"• **Observation Period:** {int(df['year'].min())} – {int(df['year'].max())}\n"
        f"• **State with Highest Average Output:** {top_state} (₹{top_val:,.1f} Crore)\n"
        f"• **State with Lowest Average Output:** {lowest_state} (₹{lowest_val:,.1f} Crore)\n"
        f"• **Total State-Year Records:** {len(df)}"
    )
    return answer, {"total_states": int(df["state"].nunique()), "years": [int(df["year"].min()), int(df["year"].max())]}, citations


def _answer_prediction(query: str) -> tuple[str, Optional[dict[str, Any]], list[SearchCitation]]:
    df = fetch_climate_dataframe()
    if df.empty:
        return "Cannot run prediction: No dataset available. Please run the data pipeline first.", None, []

    state_match = "Maharashtra"
    for s in df["state"].unique():
        if s.lower() in query.lower():
            state_match = s
            break

    # Get recent state averages
    sdf = df[df["state"] == state_match]
    mean_rain = float(sdf["rainfall_mm"].mean()) if not sdf.empty else 700.0
    mean_temp = float(sdf["avg_temperature_c"].mean()) if not sdf.empty else 28.0

    # Assume mild El Nino scenario (ONI = +1.5) with 15% rainfall reduction
    scenario_rain = round(mean_rain * 0.85, 1)
    scenario_temp = round(mean_temp + 1.0, 1)
    oni = 1.5

    pred_res = predict_gdp(
        state=state_match,
        rainfall=scenario_rain,
        temperature=scenario_temp,
        oni_index=oni,
    )

    metrics = get_model_metrics()
    best_m = metrics.get("best_model", "xgboost") if metrics else "xgboost"
    best_pred = next((p for p in pred_res["predictions"] if p["model"] == best_m), pred_res["predictions"][0])

    answer = (
        f"### PROJECT MODEL PREDICTION RESULT\n\n"
        f"• **Target State:** {state_match}\n"
        f"• **Baseline Historical Average:** ₹{pred_res['historical_avg_gdp_cr']:,.1f} Crore\n"
        f"• **Simulated Inputs:** Rainfall = {scenario_rain} mm (-15%), Temp = {scenario_temp}°C, ONI = {oni} (Moderate El Niño)\n"
        f"• **Predicted Output ({best_m.upper()}):** ₹{best_pred['predicted_gdp_cr']:,.1f} Crore\n"
        f"• **Estimated Impact:** {best_pred['predicted_impact_pct']:+.1f}% vs. Historical Baseline\n"
        f"• **Ensemble Model Average:** ₹{pred_res.get('ensemble_gdp_cr', best_pred['predicted_gdp_cr']):,.1f} Crore"
    )

    citations = [
        SearchCitation(
            source="PBL Multi-Model Machine Learning Engine",
            title=f"Prediction using {best_m.upper()} on held-out panel validation data",
            url=None,
            snippet=f"Evaluated with time-aware splitting. MAE: {metrics['models'][best_m]['mae'] if metrics else 'N/A'}, RMSE: {metrics['models'][best_m]['rmse'] if metrics else 'N/A'}",
        )
    ]

    return answer, pred_res, citations


def _answer_scenario(query: str) -> tuple[str, Optional[dict[str, Any]], list[SearchCitation]]:
    df = fetch_climate_dataframe()
    state_match = "Maharashtra"
    for s in (df["state"].unique() if not df.empty else ["Maharashtra"]):
        if s.lower() in query.lower():
            state_match = s
            break

    sdf = df[df["state"] == state_match] if not df.empty else None
    mean_rain = float(sdf["rainfall_mm"].mean()) if sdf is not None and not sdf.empty else 750.0
    mean_temp = float(sdf["avg_temperature_c"].mean()) if sdf is not None and not sdf.empty else 28.0

    preset_name = "Moderate El Niño"
    if "strong" in query.lower():
        preset_name = "Strong El Niño"
        oni = 2.2
        rain = mean_rain * 0.70
        temp = mean_temp + 2.0
    elif "weak" in query.lower():
        preset_name = "Weak El Niño"
        oni = 0.8
        rain = mean_rain * 0.90
        temp = mean_temp + 0.5
    else:
        oni = 1.5
        rain = mean_rain * 0.80
        temp = mean_temp + 1.2

    req = ScenarioRequest(
        state=state_match,
        rainfall=round(rain, 1),
        temperature=round(temp, 1),
        oni_index=oni,
        preset_name=preset_name,
    )
    scen_res = run_scenario_simulation(req)

    answer = (
        f"### HYPOTHETICAL MODEL SCENARIO: {preset_name.upper()}\n\n"
        f"• **State:** {state_match}\n"
        f"• **Scenario Inputs:** Rainfall: {scen_res.inputs['rainfall_mm']} mm, Temp: {scen_res.inputs['avg_temperature_c']}°C, ONI: {scen_res.inputs['oni_index']}\n"
        f"• **Historical Sample Baseline:** {scen_res.historical_avg_gdp_cr:,.1f} (unverified units)\n"
        f"• **Projected Sample Output ({scen_res.best_model_result.model_name_display}):** {scen_res.best_model_result.predicted_gdp_cr:,.1f} (unverified units)\n"
        f"• **Projected Impact:** {scen_res.best_model_result.predicted_impact_pct:+.1f}% ({scen_res.best_model_result.absolute_change_cr:+,.1f} sample units)\n\n"
        f"**Interpretation:** {scen_res.interpretation}"
    )

    citations = [
        SearchCitation(
            source="PBL Scenario Engine",
            title="Hypothetical Policy Simulation Module",
            url=None,
            snippet="Generates projections based on trained multi-model regression estimators.",
        )
    ]

    return answer, scen_res.dict(), citations


def answer_search_query(req: SearchRequest) -> SearchResponse:
    query = req.query.strip()
    intent = classify_query_intent(query)
    project_data = None
    citations = []

    if intent == "factual":
        answer, citations = _answer_factual(query)
    elif intent == "historical":
        answer, project_data, citations = _answer_historical(query)
    elif intent == "prediction":
        answer, project_data, citations = _answer_prediction(query)
    elif intent == "scenario":
        answer, project_data, citations = _answer_scenario(query)
    else:  # mixed
        factual_text, f_citations = _answer_factual(query)
        pred_text, p_data, p_citations = _answer_prediction(query)
        answer = f"{pred_text}\n\n---\n\n### TRUSTED CLIMATE CONTEXT\n\n{factual_text}"
        project_data = p_data
        citations = p_citations + f_citations

    # Log to SQLite
    try:
        db = get_db()
        from app.services.db_storage import _get_sqlite_conn
        conn = _get_sqlite_conn()
        with conn:
            conn.execute(
                "INSERT INTO search_logs (query, intent, response, created_at) VALUES (?, ?, ?, datetime('now'))",
                (query, intent, answer[:500]),
            )
    except Exception:
        pass

    return SearchResponse(
        query=query,
        intent=intent,  # type: ignore
        answer=answer,
        project_data=project_data,
        citations=citations,
        disclaimer=DISCLAIMER,
    )

"""Risk scoring model for configuration integrity."""

from __future__ import annotations

import pandas as pd

CRITICALITY_WEIGHT = {"Low": 0, "Medium": 6, "High": 12, "Critical": 18}


def score_configuration_risk(report: pd.DataFrame) -> pd.DataFrame:
    scored = report.copy()
    scored["risk_score"] = (
        scored["work_instruction_gap"] * 15
        + scored["inspection_gap"] * 13
        + scored["max_part_revision_gap"] * 10
        + scored["max_supplier_revision_gap"] * 12
        + scored["obsolete_parts"] * 8
        + scored["lagging_suppliers"] * 3
        + scored["single_source_parts"] * 2
        + scored["open_quality_notes"] * 2
        + scored["criticality"].map(CRITICALITY_WEIGHT).fillna(0)
        + (scored["approval_status"].ne("Approved") * 10).astype(int)
        + (scored["last_review_days_ago"].gt(120) * 8).astype(int)
        + (scored["avg_supplier_acknowledgement_days"].gt(45) * 8).astype(int)
    )
    scored["risk_score"] = scored["risk_score"].round(0).astype(int)
    scored["risk_level"] = pd.cut(
        scored["risk_score"],
        bins=[-1, 35, 65, 95, 999],
        labels=["Low", "Medium", "High", "Critical"],
    ).astype(str)
    scored["recommended_action"] = scored.apply(recommend_action, axis=1)
    return scored.sort_values("risk_score", ascending=False)


def recommend_action(row: pd.Series) -> str:
    if row["risk_level"] == "Critical":
        return "Hold affected build until revision alignment is verified. Escalate ECN closure and supplier confirmation."
    if row["risk_level"] == "High":
        return "Prioritize document review, supplier acknowledgement, and quality note closure before next production release."
    if row["risk_level"] == "Medium":
        return "Schedule configuration review and monitor supplier/document revision status."
    return "Continue routine configuration monitoring."

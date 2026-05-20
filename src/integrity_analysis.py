"""Configuration integrity analysis utilities."""

from __future__ import annotations

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"

REVISION_ORDER = {"A": 0, "B": 1, "C": 2, "D": 3, "E": 4}


def revision_gap(actual: str, expected: str) -> int:
    """Return how many revision levels an item lags behind expected."""
    return max(0, REVISION_ORDER.get(expected, 0) - REVISION_ORDER.get(actual, 0))


def load_data(data_dir: Path = DATA_DIR) -> dict[str, pd.DataFrame]:
    return {
        "engineering": pd.read_csv(data_dir / "engineering_revisions.csv"),
        "bom": pd.read_csv(data_dir / "bom_traceability.csv"),
        "suppliers": pd.read_csv(data_dir / "supplier_revision_status.csv"),
        "work_instructions": pd.read_csv(data_dir / "work_instruction_revisions.csv"),
        "inspection": pd.read_csv(data_dir / "inspection_revision_log.csv"),
    }


def analyze_revision_drift(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    engineering = data["engineering"][["assembly_id", "assembly_name", "expected_revision", "criticality", "engineering_change_notice"]]

    wi = data["work_instructions"][["assembly_id", "work_instruction_id", "manufacturing_cell", "work_instruction_revision", "approval_status", "last_review_days_ago"]]
    insp = data["inspection"][["assembly_id", "inspection_plan_id", "inspection_revision", "acceptance_criteria_status", "open_quality_notes"]]

    bom_agg = data["bom"].assign(
        part_revision_gap=lambda df: df.apply(lambda r: revision_gap(r["part_revision"], r["expected_revision"]), axis=1)
    ).groupby("assembly_id", as_index=False).agg(
        outdated_parts=("part_revision_gap", lambda x: int((x > 0).sum())),
        max_part_revision_gap=("part_revision_gap", "max"),
        obsolete_parts=("obsolete_flag", "sum"),
        single_source_parts=("is_single_source", "sum"),
        total_parts=("part_id", "count"),
    )

    supplier_agg = data["suppliers"].assign(
        supplier_revision_gap=lambda df: df.apply(lambda r: revision_gap(r["supplier_confirmed_revision"], r["expected_revision"]), axis=1)
    ).groupby("assembly_id", as_index=False).agg(
        lagging_suppliers=("supplier_revision_gap", lambda x: int((x > 0).sum())),
        max_supplier_revision_gap=("supplier_revision_gap", "max"),
        avg_supplier_acknowledgement_days=("supplier_acknowledgement_days", "mean"),
    )

    report = engineering.merge(wi, on="assembly_id", how="left").merge(insp, on="assembly_id", how="left")
    report = report.merge(bom_agg, on="assembly_id", how="left").merge(supplier_agg, on="assembly_id", how="left")
    report["work_instruction_gap"] = report.apply(lambda r: revision_gap(r["work_instruction_revision"], r["expected_revision"]), axis=1)
    report["inspection_gap"] = report.apply(lambda r: revision_gap(r["inspection_revision"], r["expected_revision"]), axis=1)
    report["avg_supplier_acknowledgement_days"] = report["avg_supplier_acknowledgement_days"].round(1)
    return report


def build_heatmap_matrix(report: pd.DataFrame) -> pd.DataFrame:
    return report.set_index("assembly_name")[[
        "work_instruction_gap",
        "inspection_gap",
        "max_part_revision_gap",
        "max_supplier_revision_gap",
    ]].rename(columns={
        "work_instruction_gap": "Work Instruction",
        "inspection_gap": "Inspection Plan",
        "max_part_revision_gap": "BOM Parts",
        "max_supplier_revision_gap": "Supplier Confirmed Rev",
    })

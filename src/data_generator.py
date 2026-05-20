"""Synthetic data generator for Manufacturing Configuration Integrity Monitor.
"""

from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"

RNG = np.random.default_rng(42)
REVISIONS = ["A", "B", "C", "D", "E"]


def _date_series(start: str, periods: int, low_step: int = 5, high_step: int = 18) -> list[pd.Timestamp]:
    dates = [pd.Timestamp(start)]
    for _ in range(periods - 1):
        dates.append(dates[-1] + pd.Timedelta(days=int(RNG.integers(low_step, high_step))))
    return dates


def generate_engineering_revisions() -> pd.DataFrame:
    assemblies = [
        "AVN-100 Flight Computer",
        "PWR-210 Power Distribution Unit",
        "COM-330 Communications Module",
        "SNS-450 Sensor Payload",
        "CTL-500 Actuator Controller",
        "THM-620 Thermal Regulation Unit",
        "NAV-700 Guidance Assembly",
        "RAD-810 Radar Interface Board",
        "DRV-900 Motor Drive Assembly",
        "STR-115 Structural Bracket Kit",
    ]
    criticality = ["Critical", "High", "High", "Critical", "Medium", "Medium", "Critical", "High", "Medium", "Low"]
    dates = _date_series("2025-01-15", len(assemblies), 7, 21)
    rows = []
    for i, assembly in enumerate(assemblies):
        expected_rev_idx = int(RNG.choice([1, 2, 3, 4], p=[0.15, 0.30, 0.35, 0.20]))
        rows.append(
            {
                "assembly_id": f"ASM-{1000+i}",
                "assembly_name": assembly,
                "expected_revision": REVISIONS[expected_rev_idx],
                "engineering_change_notice": f"ECN-{2400+i}",
                "ecn_release_date": dates[i].date().isoformat(),
                "criticality": criticality[i],
                "change_type": RNG.choice(
                    ["Design Update", "Supplier Change", "Inspection Update", "Material Substitution", "Process Improvement"],
                    p=[0.30, 0.20, 0.20, 0.15, 0.15],
                ),
            }
        )
    return pd.DataFrame(rows)


def generate_bom_traceability(engineering: pd.DataFrame) -> pd.DataFrame:
    part_types = ["PCB", "Harness", "Fastener", "Machined Housing", "Connector", "Sensor", "Coating", "Firmware", "Bracket"]
    suppliers = ["Apex Precision", "Nova Circuits", "Vector Components", "Orion Machining", "Summit Coatings", "Helix Electronics"]
    rows = []
    for _, asm in engineering.iterrows():
        num_parts = int(RNG.integers(5, 9))
        expected_idx = REVISIONS.index(asm["expected_revision"])
        for part_num in range(num_parts):
            rev_offset = int(RNG.choice([0, -1, -2], p=[0.70, 0.23, 0.07]))
            part_rev_idx = max(0, expected_idx + rev_offset)
            obsolete = bool(RNG.choice([False, True], p=[0.86, 0.14]))
            rows.append(
                {
                    "assembly_id": asm["assembly_id"],
                    "part_id": f"P-{asm['assembly_id'].split('-')[1]}-{part_num+1:02d}",
                    "part_type": RNG.choice(part_types),
                    "part_revision": REVISIONS[part_rev_idx],
                    "expected_revision": asm["expected_revision"],
                    "supplier_name": RNG.choice(suppliers),
                    "quantity_per_assembly": int(RNG.integers(1, 12)),
                    "is_single_source": bool(RNG.choice([False, True], p=[0.72, 0.28])),
                    "obsolete_flag": obsolete,
                }
            )
    return pd.DataFrame(rows)


def generate_supplier_revision_status(bom: pd.DataFrame) -> pd.DataFrame:
    rows = []
    supplier_groups = bom.groupby(["supplier_name", "assembly_id", "part_id", "expected_revision"], as_index=False).first()
    for _, row in supplier_groups.iterrows():
        expected_idx = REVISIONS.index(row["expected_revision"])
        lag = int(RNG.choice([0, 1, 2], p=[0.62, 0.30, 0.08]))
        supplier_rev_idx = max(0, expected_idx - lag)
        ack_delay = int(RNG.integers(2, 35) + lag * RNG.integers(10, 26))
        rows.append(
            {
                "supplier_name": row["supplier_name"],
                "assembly_id": row["assembly_id"],
                "part_id": row["part_id"],
                "supplier_confirmed_revision": REVISIONS[supplier_rev_idx],
                "expected_revision": row["expected_revision"],
                "supplier_acknowledgement_days": ack_delay,
                "supplier_status": "Current" if lag == 0 else ("Lagging" if lag == 1 else "Critical Lag"),
            }
        )
    return pd.DataFrame(rows)


def generate_work_instruction_revisions(engineering: pd.DataFrame) -> pd.DataFrame:
    cells = ["Assembly Cell A", "Assembly Cell B", "Electronics Cell", "Final Integration", "Special Processes"]
    rows = []
    for _, asm in engineering.iterrows():
        expected_idx = REVISIONS.index(asm["expected_revision"])
        drift = int(RNG.choice([0, 1, 2], p=[0.67, 0.25, 0.08]))
        wi_idx = max(0, expected_idx - drift)
        last_review_days = int(RNG.integers(10, 160) + drift * 30)
        rows.append(
            {
                "work_instruction_id": f"WI-{asm['assembly_id'].split('-')[1]}",
                "assembly_id": asm["assembly_id"],
                "manufacturing_cell": RNG.choice(cells),
                "work_instruction_revision": REVISIONS[wi_idx],
                "expected_revision": asm["expected_revision"],
                "last_review_days_ago": last_review_days,
                "approval_status": RNG.choice(["Approved", "Pending Approval", "Requires Review"], p=[0.68, 0.20, 0.12]),
            }
        )
    return pd.DataFrame(rows)


def generate_inspection_revision_log(engineering: pd.DataFrame) -> pd.DataFrame:
    methods = ["Visual Inspection", "Dimensional Inspection", "Electrical Test", "Functional Test", "Torque Verification"]
    rows = []
    for _, asm in engineering.iterrows():
        expected_idx = REVISIONS.index(asm["expected_revision"])
        drift = int(RNG.choice([0, 1, 2], p=[0.72, 0.21, 0.07]))
        insp_idx = max(0, expected_idx - drift)
        rows.append(
            {
                "inspection_plan_id": f"INSP-{asm['assembly_id'].split('-')[1]}",
                "assembly_id": asm["assembly_id"],
                "inspection_method": RNG.choice(methods),
                "inspection_revision": REVISIONS[insp_idx],
                "expected_revision": asm["expected_revision"],
                "open_quality_notes": int(RNG.integers(0, 6) + drift),
                "acceptance_criteria_status": "Aligned" if drift == 0 else "Potential Drift",
            }
        )
    return pd.DataFrame(rows)


def generate_all() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    engineering = generate_engineering_revisions()
    bom = generate_bom_traceability(engineering)
    suppliers = generate_supplier_revision_status(bom)
    work_instructions = generate_work_instruction_revisions(engineering)
    inspection = generate_inspection_revision_log(engineering)

    engineering.to_csv(DATA_DIR / "engineering_revisions.csv", index=False)
    bom.to_csv(DATA_DIR / "bom_traceability.csv", index=False)
    suppliers.to_csv(DATA_DIR / "supplier_revision_status.csv", index=False)
    work_instructions.to_csv(DATA_DIR / "work_instruction_revisions.csv", index=False)
    inspection.to_csv(DATA_DIR / "inspection_revision_log.csv", index=False)


if __name__ == "__main__":
    generate_all()
    print(f"Synthetic data written to {DATA_DIR}")

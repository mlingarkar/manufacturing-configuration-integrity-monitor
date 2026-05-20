from __future__ import annotations

from pathlib import Path

from data_generator import generate_all
from integrity_analysis import analyze_revision_drift, build_heatmap_matrix, load_data
from risk_scoring import score_configuration_risk
from visualization import generate_all_visuals

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "outputs" / "reports"


def main() -> None:
    generate_all()
    data = load_data()
    report = analyze_revision_drift(data)
    scored = score_configuration_risk(report)
    heatmap = build_heatmap_matrix(scored)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    scored.to_csv(REPORTS_DIR / "configuration_risk_report.csv", index=False)
    generate_all_visuals(data, scored, heatmap)

    print("Configuration integrity analysis complete.")
    print(f"Report saved to: {REPORTS_DIR / 'configuration_risk_report.csv'}")
    print(f"Figures saved to: {ROOT / 'outputs' / 'figures'}")


if __name__ == "__main__":
    main()

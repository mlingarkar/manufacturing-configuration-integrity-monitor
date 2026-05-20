"""Streamlit dashboard for Manufacturing Configuration Integrity Monitor."""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "src"))

from data_generator import generate_all  # noqa: E402
from integrity_analysis import analyze_revision_drift, build_heatmap_matrix, load_data  # noqa: E402
from risk_scoring import score_configuration_risk  # noqa: E402

st.set_page_config(page_title="Configuration Integrity Monitor", layout="wide")


def ensure_data() -> tuple[dict[str, pd.DataFrame], pd.DataFrame, pd.DataFrame]:
    required = [
        ROOT / "data" / "engineering_revisions.csv",
        ROOT / "data" / "bom_traceability.csv",
        ROOT / "data" / "supplier_revision_status.csv",
        ROOT / "data" / "work_instruction_revisions.csv",
        ROOT / "data" / "inspection_revision_log.csv",
    ]
    if not all(path.exists() for path in required):
        generate_all()
    data = load_data(ROOT / "data")
    report = analyze_revision_drift(data)
    scored = score_configuration_risk(report)
    heatmap = build_heatmap_matrix(scored)
    return data, scored, heatmap


def risk_summary_cards(scored: pd.DataFrame) -> None:
    total = len(scored)
    unresolved = int((scored[["work_instruction_gap", "inspection_gap", "max_part_revision_gap", "max_supplier_revision_gap"]].sum(axis=1) > 0).sum())
    high_or_critical = int(scored["risk_level"].isin(["High", "Critical"]).sum())
    obsolete = int(scored["obsolete_parts"].sum())

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Assemblies Monitored", total)
    col2.metric("Assemblies with Drift", unresolved)
    col3.metric("High/Critical Risk", high_or_critical)
    col4.metric("Obsolete Parts Flagged", obsolete)


def heatmap_chart(heatmap: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(10, 6))
    im = ax.imshow(heatmap.values, aspect="auto")
    ax.set_xticks(range(len(heatmap.columns)))
    ax.set_xticklabels(heatmap.columns, rotation=30, ha="right")
    ax.set_yticks(range(len(heatmap.index)))
    ax.set_yticklabels(heatmap.index)
    ax.set_title("Revision Drift by Configuration Element")
    for i in range(heatmap.shape[0]):
        for j in range(heatmap.shape[1]):
            ax.text(j, i, int(heatmap.iloc[i, j]), ha="center", va="center")
    fig.colorbar(im, ax=ax, label="Revision Levels Behind Expected")
    fig.tight_layout()
    st.pyplot(fig)


def risk_bar_chart(scored: pd.DataFrame) -> None:
    df = scored.sort_values("risk_score", ascending=True)
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(df["assembly_name"], df["risk_score"])
    ax.set_xlabel("Risk Score")
    ax.set_ylabel("Assembly")
    ax.set_title("Configuration Risk Scores")
    fig.tight_layout()
    st.pyplot(fig)


def supplier_delay_chart(scored: pd.DataFrame) -> None:
    df = scored.sort_values("avg_supplier_acknowledgement_days", ascending=True)
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(df["assembly_name"], df["avg_supplier_acknowledgement_days"])
    ax.axvline(45, linestyle="--", linewidth=1)
    ax.set_xlabel("Average Acknowledgement Days")
    ax.set_ylabel("Assembly")
    ax.set_title("Supplier Revision Acknowledgement Delay")
    fig.tight_layout()
    st.pyplot(fig)


def traceability_network(data: dict[str, pd.DataFrame], scored: pd.DataFrame) -> None:
    top_assemblies = scored.head(5)["assembly_id"].tolist()
    assembly_names = scored.set_index("assembly_id")["assembly_name"].to_dict()
    graph = nx.Graph()
    for asm in top_assemblies:
        graph.add_node(assembly_names[asm])
        wi = data["work_instructions"].loc[data["work_instructions"]["assembly_id"] == asm, "work_instruction_id"].iloc[0]
        insp = data["inspection"].loc[data["inspection"]["assembly_id"] == asm, "inspection_plan_id"].iloc[0]
        graph.add_edge(assembly_names[asm], wi)
        graph.add_edge(assembly_names[asm], insp)
        for _, part in data["bom"][data["bom"]["assembly_id"] == asm].head(4).iterrows():
            graph.add_edge(assembly_names[asm], part["part_id"])
            graph.add_edge(part["part_id"], part["supplier_name"])

    fig, ax = plt.subplots(figsize=(12, 8))
    pos = nx.spring_layout(graph, seed=7, k=0.7)
    nx.draw_networkx_nodes(graph, pos, node_size=650, ax=ax)
    nx.draw_networkx_edges(graph, pos, alpha=0.5, ax=ax)
    nx.draw_networkx_labels(graph, pos, font_size=7, ax=ax)
    ax.set_title("Traceability Network for Highest-Risk Assemblies")
    ax.axis("off")
    fig.tight_layout()
    st.pyplot(fig)


st.title("Manufacturing Configuration Integrity Monitor")
st.caption("AI-assisted revision traceability and configuration risk monitoring for regulated manufacturing environments.")

data, scored, heatmap = ensure_data()

risk_summary_cards(scored)

st.divider()

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Overview",
    "Revision Integrity",
    "Supplier Traceability",
    "Audit Readiness",
    "Traceability Network",
])

with tab1:
    st.subheader("Configuration Risk Overview")
    left, right = st.columns([1.1, 1])
    with left:
        risk_bar_chart(scored)
    with right:
        st.dataframe(
            scored[["assembly_name", "criticality", "risk_score", "risk_level", "recommended_action"]],
            use_container_width=True,
            hide_index=True,
        )

with tab2:
    st.subheader("Revision Drift Detection")
    heatmap_chart(heatmap)
    st.dataframe(
        scored[[
            "assembly_name",
            "expected_revision",
            "work_instruction_revision",
            "inspection_revision",
            "work_instruction_gap",
            "inspection_gap",
            "max_part_revision_gap",
            "max_supplier_revision_gap",
        ]],
        use_container_width=True,
        hide_index=True,
    )

with tab3:
    st.subheader("Supplier Revision Lag")
    supplier_delay_chart(scored)
    st.dataframe(data["suppliers"], use_container_width=True, hide_index=True)

with tab4:
    st.subheader("Audit Readiness Indicators")
    audit_cols = [
        "assembly_name",
        "engineering_change_notice",
        "approval_status",
        "last_review_days_ago",
        "open_quality_notes",
        "obsolete_parts",
        "lagging_suppliers",
        "risk_level",
    ]
    st.dataframe(scored[audit_cols], use_container_width=True, hide_index=True)
    st.info(
        "Audit readiness risk is modeled using outdated work instructions, inspection drift, obsolete parts, open quality notes, supplier lag, and pending approvals."
    )

with tab5:
    st.subheader("Configuration Traceability Network")
    traceability_network(data, scored)
    st.caption("Network shows relationships among high-risk assemblies, parts, suppliers, work instructions, and inspection plans.")

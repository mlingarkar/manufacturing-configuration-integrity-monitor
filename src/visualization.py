"""Static visualization generation for project outputs."""

from __future__ import annotations

from pathlib import Path
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FIGURES_DIR = ROOT / "outputs" / "figures"


def save_revision_drift_heatmap(matrix: pd.DataFrame, output_path: Path = FIGURES_DIR / "revision_drift_heatmap.png") -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 7))
    im = ax.imshow(matrix.values, aspect="auto")
    ax.set_xticks(range(len(matrix.columns)))
    ax.set_xticklabels(matrix.columns, rotation=30, ha="right")
    ax.set_yticks(range(len(matrix.index)))
    ax.set_yticklabels(matrix.index)
    ax.set_title("Revision Drift Heatmap")
    ax.set_xlabel("Configuration Element")
    ax.set_ylabel("Assembly")
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            ax.text(j, i, int(matrix.iloc[i, j]), ha="center", va="center")
    fig.colorbar(im, ax=ax, label="Revision Levels Behind Expected")
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def save_propagation_delay_chart(scored: pd.DataFrame, output_path: Path = FIGURES_DIR / "propagation_delay_chart.png") -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df = scored.sort_values("avg_supplier_acknowledgement_days", ascending=True)
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(df["assembly_name"], df["avg_supplier_acknowledgement_days"])
    ax.axvline(45, linestyle="--", linewidth=1)
    ax.set_title("Average Supplier Revision Acknowledgement Delay")
    ax.set_xlabel("Average Acknowledgement Days")
    ax.set_ylabel("Assembly")
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def save_configuration_risk_scores(scored: pd.DataFrame, output_path: Path = FIGURES_DIR / "configuration_risk_scores.png") -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df = scored.sort_values("risk_score", ascending=True)
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(df["assembly_name"], df["risk_score"])
    ax.set_title("Configuration Risk Scores by Assembly")
    ax.set_xlabel("Risk Score")
    ax.set_ylabel("Assembly")
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def save_traceability_network(data: dict[str, pd.DataFrame], scored: pd.DataFrame, output_path: Path = FIGURES_DIR / "traceability_network.png") -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    bom = data["bom"]
    suppliers = data["suppliers"]
    work = data["work_instructions"]
    inspection = data["inspection"]

    top_assemblies = scored.head(5)["assembly_id"].tolist()
    assembly_names = scored.set_index("assembly_id")["assembly_name"].to_dict()

    graph = nx.Graph()
    for asm in top_assemblies:
        graph.add_node(assembly_names[asm], node_type="Assembly")
        wi = work.loc[work["assembly_id"] == asm, "work_instruction_id"].iloc[0]
        insp = inspection.loc[inspection["assembly_id"] == asm, "inspection_plan_id"].iloc[0]
        graph.add_edge(assembly_names[asm], wi)
        graph.add_edge(assembly_names[asm], insp)
        asm_parts = bom[bom["assembly_id"] == asm].head(4)
        for _, part in asm_parts.iterrows():
            graph.add_edge(assembly_names[asm], part["part_id"])
            graph.add_edge(part["part_id"], part["supplier_name"])

    fig, ax = plt.subplots(figsize=(12, 8))
    pos = nx.spring_layout(graph, seed=7, k=0.7)
    nx.draw_networkx_nodes(graph, pos, node_size=650, ax=ax)
    nx.draw_networkx_edges(graph, pos, alpha=0.5, ax=ax)
    nx.draw_networkx_labels(graph, pos, font_size=7, ax=ax)
    ax.set_title("Configuration Traceability Network: Top Risk Assemblies")
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(output_path, dpi=170)
    plt.close(fig)


def generate_all_visuals(data: dict[str, pd.DataFrame], scored: pd.DataFrame, heatmap_matrix: pd.DataFrame) -> None:
    save_revision_drift_heatmap(heatmap_matrix)
    save_propagation_delay_chart(scored)
    save_configuration_risk_scores(scored)
    save_traceability_network(data, scored)

# Project Overview

## Manufacturing Configuration Integrity Monitor

This project models a configuration-control monitoring system for regulated manufacturing environments, with a focus on defense and aerospace-style production operations.

The project uses synthetic data to simulate how engineering changes propagate through manufacturing systems. It identifies where revision drift occurs across engineering releases, work instructions, inspection plans, supplier acknowledgements, and bill-of-materials records.

## Problem Statement

In complex manufacturing environments, production risk does not only come from machine downtime or material shortages. It can also come from configuration misalignment. A production team may be building to one engineering revision while a supplier, inspection plan, or work instruction is still aligned to an older release.

These issues can create rework, quality escapes, audit findings, delayed builds, and schedule disruption.

## What the System Monitors

- Engineering revision releases
- Work instruction revision alignment
- Inspection plan revision alignment
- BOM part revision consistency
- Supplier revision acknowledgement status
- Obsolete part exposure
- Single-source part exposure
- Open quality notes and approval status

## Risk Scoring Logic

The project calculates a configuration risk score using several operational signals:

- Revision gap between expected and actual documents
- Supplier revision lag
- Obsolete parts
- Single-source parts
- Open quality notes
- Criticality of the assembly
- Pending or incomplete approval status
- Stale document review timelines
- Supplier acknowledgement delays

Each assembly receives a risk level: Low, Medium, High, or Critical.

## Output Files

Running `python src/main.py` creates:

- `outputs/reports/configuration_risk_report.csv`
- `outputs/figures/revision_drift_heatmap.png`
- `outputs/figures/propagation_delay_chart.png`
- `outputs/figures/configuration_risk_scores.png`
- `outputs/figures/traceability_network.png`


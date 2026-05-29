# MIMIC-IV COPD RAAS Portfolio Modernization Plan

This roadmap adapts the portfolio presentation pattern from the public-health statistics project while preserving the current MIMIC-IV analysis as an observational, hypothesis-generating clinical analytics project.

## Current Repository Inventory

- `README.md` already provides a portfolio overview, clinical framing, key findings, links to notebooks/docs, and a live Quarto report link.
- Workflow documentation exists across `docs/`, including study background, methods, results summary, discussion/limitations, validation notes, figure reproducibility notes, and short notebook summaries.
- Existing figures are tracked in `assets/` and mirrored in `docs/assets/`: Kaplan-Meier curve, Cox forest plot, RAAS subgroup forest plot, sensitivity comparison forest plot, and workflow diagram.
- Existing notebooks cover ICU cohort extraction, COPD/RAAS exposure construction, baseline covariates, exposure merging, primary Cox modeling, RAAS subgroup modeling, extended covariate modeling, secondary logistic validation, and SAS-Python validation.
- Existing outputs include `python/outputs/python_logistic_parameters.csv` and the rendered Quarto HTML report under `docs/`.
- Quarto assets already exist in `reports/`, including `_quarto.yml` and `copd_raas_survival_report.qmd`; the current Quarto configuration renders into `docs/`.

## Executive Summary

Proposed recruiter-facing summary:

This project demonstrates a reproducible real-world evidence workflow using MIMIC-IV v3.1 to study whether pre-ICU RAAS inhibitor exposure is associated with time-to-in-hospital mortality among ICU patients with COPD. The analysis uses BigQuery SQL for cohort and exposure construction, Python/Jupyter for Kaplan-Meier and Cox proportional hazards modeling, SAS for cross-platform validation, and Quarto for narrative reporting. Findings are observational and should be interpreted as hypothesis-generating associations rather than causal treatment effects.

## Dataset Snapshot

- Data source: MIMIC-IV v3.1 via PhysioNet and BigQuery.
- Cohort: Adult ICU admissions with COPD identified using ICD-9 and ICD-10 diagnosis codes.
- Exposure: Pre-ICU inpatient prescription orders for ACE inhibitors or ARBs before or at ICU admission, with combined RAAS and ACE inhibitor/ARB subclass indicators.
- Outcome: Time-to-in-hospital mortality from ICU admission to death or hospital discharge; patients discharged alive are censored at discharge.
- Sample size: Existing notebook outputs report 11,964 COPD ICU admissions for the primary survival cohort.
- Compliance: Repository contains no patient-level data and requires independent MIMIC-IV/PhysioNet, Google Cloud, BigQuery, and SAS configuration for reproduction.

## Workflow Diagram

Proposed portfolio workflow:

```text
MIMIC-IV
-> Cohort Construction
-> Exposure Definition
-> Outcome Definition
-> Baseline Analysis
-> Cox Regression
-> Sensitivity Analyses
-> SAS Validation
-> Quarto Report
-> GitHub Pages
```

Suggested visual update:

- Keep the diagram linear and recruiter-readable.
- Use short stage labels matching the README and Quarto report.
- Link stages to the corresponding notebooks or docs where possible.

## Quarto Report Structure

Recommended report sections:

- Executive summary
- Study question and clinical motivation
- Data source and cohort definition
- Exposure, outcome, and covariates
- Baseline cohort and exposure summary
- Kaplan-Meier survival results
- Cox proportional hazards results
- ACE inhibitor vs ARB subgroup analysis
- Extended covariate and sensitivity analyses
- SAS-Python validation note
- Limitations and causal interpretation guardrails
- Reproducibility and repository navigation

## GitHub Pages Deployment Plan

- Keep `reports/copd_raas_survival_report.qmd` as the report source.
- Keep `reports/_quarto.yml` configured to render into `docs/` if using the GitHub Pages `docs/` publishing source.
- Add a GitHub Actions workflow in a later implementation phase to install Quarto and Python dependencies, render the report, and publish the resulting HTML.
- Avoid committing patient-level data, credentials, BigQuery extracts, or large generated intermediates.
- Use the public-health project workflow as the reference for deployable Quarto structure and recruiter-facing navigation.

## Migration Priority

1. Add a concise README executive summary, dataset snapshot, and skills-demonstrated section modeled on the public-health project.
2. Tighten README figure captions and make each preview explicitly connect to the analytic question.
3. Refresh the workflow diagram to show the full path from MIMIC-IV to GitHub Pages using the proposed stage labels.
4. Review the Quarto report for consistent figure numbering, captions, cautious interpretation, and recruiter-friendly section flow.
5. Add or update a GitHub Actions workflow to render Quarto and deploy GitHub Pages reproducibly.
6. Separate generated outputs from curated portfolio assets more explicitly, keeping only stable preview/report assets tracked.
7. Add a lightweight validation checklist for notebook/report freshness, figure presence, and rendered HTML availability.
8. Standardize docs navigation so README, Quarto report, notebook short notes, and validation notes reinforce the same workflow narrative.

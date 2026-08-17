# UK VAT Identifier Discovery

This repository contains a proof-of-concept workflow for the **UK VAT Identifier Discovery - Data Assets Intern challenge**.

## What the PoC does

1. Samples active, non-dormant UK companies from a Companies House bulk CSV.
2. Uses a discovery log of company websites.
3. Crawls each discovered website homepage plus up to 5 relevant internal pages (`terms`, `privacy`, `legal`, `contact`, `about`).
4. Extracts VAT candidates only when an explicit VAT label is present (e.g. `VAT number`, `VAT no`).
5. Saves extracted candidates and local context for manual HMRC verification.

## Project layout

- `/src/sampling.py` - random sample generation from Companies House data.
- `/src/extraction.py` - VAT candidate extraction from discovered websites.
- `/data/` - input/output CSV files (`data/raw/` is ignored due to large source file size).

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run sampling

```bash
python src/sampling.py \
  --input data/raw/BasicCompanyDataAsOneFile-2026-08-01.csv \
  --output data/sample_companies.csv \
  --size 50 \
  --seed 42
```

## Run extraction

```bash
python src/extraction.py \
  --discovery-log data/discovery_log.csv \
  --output data/vat_candidates.csv
```

## Notes

- A “not found” result means no candidate was discovered by this process; it does **not** prove a company is not VAT registered.
- HMRC validation and company matching are expected to be done manually after candidate extraction.

#!/usr/bin/env python3
"""Step 1: List candidate tables for validation checklist."""

from __future__ import annotations

import sys

import google.auth
from google.cloud import bigquery

PROJECT_ID = "mimic-iv-portfolio"
DATASET_ID = "copd_raas"


def eprint(message: str) -> None:
    print(message, file=sys.stderr)


def main() -> int:
    eprint(f"sys.executable: {sys.executable}")

    eprint("auth default begin")
    creds, proj = google.auth.default()
    eprint(f"auth default end; project={proj}")
    eprint(f"creds class={creds.__class__.__name__}")

    client = bigquery.Client(project=PROJECT_ID)
    sql = f"""
    SELECT table_name
    FROM `{PROJECT_ID}.{DATASET_ID}.INFORMATION_SCHEMA.TABLES`
    WHERE table_type = 'BASE TABLE'
    ORDER BY table_name
    """
    eprint("listing tables...")
    rows = client.query(sql).result()
    print("Tables:")
    for row in rows:
        print(f"- {row['table_name']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

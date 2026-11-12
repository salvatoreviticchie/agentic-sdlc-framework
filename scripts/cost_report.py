#!/usr/bin/env python3
"""
cost_report.py - summarise runs/costs.csv as a markdown table.

For every change request (CR) and stage it shows the number of runs, the
tokens and the cost, then a total row per CR and a grand total.

Example:
  python3 scripts/cost_report.py            # reads runs/costs.csv
  python3 scripts/cost_report.py other.csv  # reads another file

Standard library only. The costs are Claude Code's client-side estimates at
API prices, not amounts billed on a subscription.
"""

import csv
import subprocess
import sys
from pathlib import Path

# The numbers we add up, as (CSV column, table heading).
NUMBER_COLUMNS = [
    ("input_tokens", "Input"),
    ("output_tokens", "Output"),
    ("cache_read_tokens", "Cache read"),
    ("cache_creation_tokens", "Cache write"),
]


def default_csv_path():
    """runs/costs.csv at the top of the git repository."""
    result = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                            capture_output=True, text=True)
    root = Path(result.stdout.strip()) if result.returncode == 0 else Path.cwd()
    return root / "runs" / "costs.csv"


def empty_totals():
    """A fresh set of counters, all at zero."""
    totals = {"runs": 0, "cost": 0.0, "budget_stops": 0}
    for column, _ in NUMBER_COLUMNS:
        totals[column] = 0
    return totals


def add_row(totals, row):
    """Add one CSV row to a set of counters."""
    totals["runs"] += 1
    # float(... or 0) turns the text "1.2345" into a number, and "" into 0.
    totals["cost"] += float(row.get("total_cost_usd") or 0)
    if row.get("budget_stopped") == "yes":
        totals["budget_stops"] += 1
    for column, _ in NUMBER_COLUMNS:
        totals[column] += int(row.get(column) or 0)


def table_line(cr, stage, totals, bold=False):
    """Format one markdown table row. Bold is used for the total rows."""
    cells = [cr, stage, str(totals["runs"])]
    # f"{n:,}" writes 1234567 as 1,234,567, which is easier to read.
    cells += [f"{totals[column]:,}" for column, _ in NUMBER_COLUMNS]
    cells += [f"${totals['cost']:.2f}", str(totals["budget_stops"])]
    if bold:
        cells = [f"**{c}**" if c else "" for c in cells]
    return "| " + " | ".join(cells) + " |"


def main():
    csv_path = Path(sys.argv[1]) if len(sys.argv) > 1 else default_csv_path()
    if not csv_path.exists():
        sys.exit(f"No cost log yet: {csv_path} does not exist. Run scripts/run_agent.py first.")

    # by_cr looks like {"CR-002": {"build": totals, "review": totals}}.
    # A normal dict keeps the order in which keys were first added,
    # so CRs and stages appear in the order they were run.
    by_cr = {}
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):        # each row is a dict: column -> text
            stages = by_cr.setdefault(row["cr"], {})
            totals = stages.setdefault(row["stage"], empty_totals())
            add_row(totals, row)

    headings = ["CR", "Stage", "Runs"] + [h for _, h in NUMBER_COLUMNS] + ["Cost (USD)", "Budget stops"]
    print("| " + " | ".join(headings) + " |")
    print("|" + "---|" * len(headings))

    grand = empty_totals()
    for cr, stages in by_cr.items():
        cr_total = empty_totals()
        for stage, totals in stages.items():
            print(table_line(cr, stage, totals))
            # Add this stage into the CR total and the grand total.
            for key in cr_total:
                cr_total[key] += totals[key]
                grand[key] += totals[key]
        print(table_line(f"{cr} total", "", cr_total, bold=True))
    print(table_line("All CRs", "", grand, bold=True))

    print()
    print("Costs are Claude Code's client-side estimates at API prices, "
          "not billed amounts on a subscription.")


if __name__ == "__main__":
    main()

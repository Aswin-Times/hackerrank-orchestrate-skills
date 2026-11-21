"""Refund Desk demo agent: python code/main.py [--input CSV] [--output CSV]

Reads requests, applies rules.py, validates every row against the contract,
and writes the output atomically (temp file, then rename).
"""
import argparse
import csv
import os

from rules import decide

COLUMNS = ["request_id", "decision", "policy_id", "justification"]  # SPEC: AGENTS.md section 2
DECISIONS = {"APPROVE", "DENY", "ESCALATE"}


def load(path):
    with open(path, encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            yield {"id": row["request_id"], "tier": row["customer_tier"], "days": int(row["days_since_purchase"]),
                   "amount": float(row["amount"]), "item_condition": row["item_condition"], "message": row["message"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="dataset/requests.csv")
    ap.add_argument("--output", default="output.csv")
    a = ap.parse_args()
    rows = []
    for req in load(a.input):
        decision, pid, why = decide(req)
        assert decision in DECISIONS and why, req["id"]
        rows.append([req["id"], decision, pid, why])
    tmp = a.output + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(COLUMNS)
        w.writerows(rows)
    os.replace(tmp, a.output)
    print("wrote %d rows to %s" % (len(rows), a.output))


if __name__ == "__main__":
    main()

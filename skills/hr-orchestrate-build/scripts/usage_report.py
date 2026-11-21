#!/usr/bin/env python3
"""Build evaluation/usage_report.md from a per-call usage log (JSONL).

Each line of the log is one model call, for example:
  {"run_id": "20261212T1830", "row_id": "C001", "provider": "anthropic",
   "model": "claude-sonnet-5-5", "input_tokens": 1830, "output_tokens": 212,
   "cache_read_input_tokens": 0, "cached": false, "latency_ms": 2140}

"cached": true means the call was served from the agent's local cache
(no API charge in this run, but its original token counts still describe
what it took to produce the output). Prices are never built in: pass
--price MODEL=USD_PER_M_INPUT:USD_PER_M_OUTPUT for each model, from a
current pricing page, and record the source with --price-source.
Models without a price get cost UNKNOWN.
Standard library only.
"""
import argparse
import json
import sys
from collections import OrderedDict
from datetime import date


def load(path, run_id):
    calls, bad = [], 0
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except ValueError:
                bad += 1
                continue
            if run_id and str(rec.get("run_id")) != run_id:
                continue
            calls.append(rec)
    return calls, bad


def parse_prices(items):
    prices = {}
    for it in items or []:
        try:
            model, rest = it.split("=", 1)
            inp, out = rest.split(":", 1)
            prices[model.strip()] = (float(inp), float(out))
        except ValueError:
            raise SystemExit("bad --price %r; expected MODEL=IN:OUT (USD per million tokens)" % it)
    return prices


def money(x):
    return "UNKNOWN" if x is None else "$%.4f" % x


def build(calls, prices, requests, run_id, price_source):
    per = OrderedDict()
    rows = set()
    for c in calls:
        key = (str(c.get("provider", "unknown")), str(c.get("model", "unknown")))
        m = per.setdefault(key, {"calls": 0, "api_calls": 0, "in": 0, "out": 0, "cache_read": 0,
                                 "billed_in": 0, "billed_out": 0})
        i, o = int(c.get("input_tokens") or 0), int(c.get("output_tokens") or 0)
        cr = int(c.get("cache_read_input_tokens") or 0)
        m["calls"] += 1
        m["in"] += i
        m["out"] += o
        m["cache_read"] += cr
        if not c.get("cached"):
            m["api_calls"] += 1
            m["billed_in"] += i
            m["billed_out"] += o
        if c.get("row_id") is not None:
            rows.add(str(c["row_id"]))
    n_req = requests or len(rows)

    def cost(model, tin, tout):
        if model not in prices:
            return None
        pi, po = prices[model]
        return tin / 1e6 * pi + tout / 1e6 * po

    lines = ["# Usage report", "",
             "Final run: `%s`. Generated %s from `usage.jsonl` by usage_report.py." % (run_id or "all runs", date.today().isoformat()),
             "Requests in this run: %d%s." % (n_req, "" if requests else " (distinct row ids in the log)"), ""]
    lines += ["## Per model (all calls used to produce the output)", "",
              "| Provider | Model | Calls | Input tokens | Output tokens | Total tokens | Est. cost |",
              "|---|---|---|---|---|---|---|"]
    tot = {"calls": 0, "in": 0, "out": 0, "api_calls": 0, "billed_in": 0, "billed_out": 0}
    tot_cost, tot_billed, unknown = 0.0, 0.0, False
    for (prov, model), m in per.items():
        c = cost(model, m["in"], m["out"])
        b = cost(model, m["billed_in"], m["billed_out"])
        if c is None:
            unknown = True
        else:
            tot_cost += c
            tot_billed += b
        for k in tot:
            tot[k] += m[k]
        lines.append("| %s | %s | %d | %d | %d | %d | %s |" % (prov, model, m["calls"], m["in"], m["out"],
                                                              m["in"] + m["out"], money(c)))
    total_tokens = tot["in"] + tot["out"]
    overall = None if unknown else tot_cost
    lines.append("| **All** | | **%d** | **%d** | **%d** | **%d** | **%s** |" % (
        tot["calls"], tot["in"], tot["out"], total_tokens, money(overall)))
    lines += ["", "## Per request", "",
              "| Metric | Value |", "|---|---|",
              "| Model calls per request | %s |" % ("%.2f" % (tot["calls"] / n_req) if n_req else "UNKNOWN"),
              "| Tokens per request (input + output) | %s |" % ("%.0f" % (total_tokens / n_req) if n_req else "UNKNOWN"),
              "| Input tokens per request | %s |" % ("%.0f" % (tot["in"] / n_req) if n_req else "UNKNOWN"),
              "| Output tokens per request | %s |" % ("%.0f" % (tot["out"] / n_req) if n_req else "UNKNOWN"),
              "| Est. cost per request | %s |" % (money(overall / n_req) if (overall is not None and n_req) else "UNKNOWN"),
              "", "## Billed during this run", "",
              "Calls served from the local cache cost nothing in this run.", "",
              "| Metric | Value |", "|---|---|",
              "| API calls | %d |" % tot["api_calls"],
              "| Cache hits | %d |" % (tot["calls"] - tot["api_calls"]),
              "| Billed input tokens | %d |" % tot["billed_in"],
              "| Billed output tokens | %d |" % tot["billed_out"],
              "| Billed est. cost | %s |" % money(None if unknown else tot_billed), ""]
    lines += ["## Prices used", ""]
    if prices:
        lines += ["| Model | USD per 1M input | USD per 1M output |", "|---|---|---|"]
        lines += ["| %s | %g | %g |" % (k, v[0], v[1]) for k, v in prices.items()]
    else:
        lines.append("No prices given; costs are UNKNOWN.")
    lines += ["", "Source: %s" % (price_source or "not stated (add --price-source)"), "",
              "Costs are estimates from token counts and list prices; provider-side prompt caching "
              "discounts are not applied unless stated."]
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("log", help="usage JSONL file")
    ap.add_argument("--run-id", help="only include calls from this run (the final full run)")
    ap.add_argument("--price", action="append", help="MODEL=IN:OUT in USD per million tokens (repeatable)")
    ap.add_argument("--price-source", help="where and when prices were taken from")
    ap.add_argument("--requests", type=int, help="number of requests in the run (default: distinct row ids)")
    ap.add_argument("--out", help="write Markdown here instead of stdout")
    a = ap.parse_args()
    calls, bad = load(a.log, a.run_id)
    if not calls:
        raise SystemExit("no calls found%s" % (" for run %s" % a.run_id if a.run_id else ""))
    if bad:
        print("warning: skipped %d unparseable lines" % bad, file=sys.stderr)
    md = build(calls, parse_prices(a.price), a.requests, a.run_id, a.price_source)
    if a.out:
        with open(a.out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(md)
        print("wrote %s (%d calls)" % (a.out, len(calls)))
    else:
        sys.stdout.write(md)


if __name__ == "__main__":
    main()

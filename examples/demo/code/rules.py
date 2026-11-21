"""Refund Desk decision rules (demo).

Pure functions: request fields in, (decision, policy_id, justification) out.
No model calls and no I/O, so every decision is reproducible and testable.
Policy text: problem_statement.md, "Policy" table.
"""

UNOPENED_DAYS = 30        # SPEC: P1 limit
OPENED_DAYS = 14          # SPEC: P2 limit
OPENED_AMOUNT_LIMIT = 200  # SPEC: P2 amount limit (inclusive)
GOLD_DAYS = 45            # SPEC: P3 gold exception
ESCALATION_TERMS = ("fraud", "chargeback", "lawyer", "legal")  # JUDGEMENT: P4 wording, not tuned

RULE_ORDER = ["P4", "P1", "P2", "P3"]  # SPEC: P4 is checked first


def days(req):
    return "%d day%s" % (req["days"], "" if req["days"] == 1 else "s")


def p4(req):
    text = req["message"].lower()
    hits = [t for t in ESCALATION_TERMS if t in text]
    if hits:
        return "ESCALATE", "message mentions %s" % " and ".join(hits)
    return None


def p1(req):
    if req["item_condition"] == "unopened" and req["days"] <= UNOPENED_DAYS:
        return "APPROVE", "unopened, %s since purchase (limit %d)" % (days(req), UNOPENED_DAYS)
    return None


def p2(req):
    if req["item_condition"] == "opened" and req["days"] <= OPENED_DAYS:
        if req["amount"] <= OPENED_AMOUNT_LIMIT:
            return "APPROVE", "opened, %s, amount %.2f within %d" % (days(req), req["amount"], OPENED_AMOUNT_LIMIT)
        return "ESCALATE", "opened, %s, amount %.2f above %d" % (days(req), req["amount"], OPENED_AMOUNT_LIMIT)
    return None


def p3(req):
    if req["tier"] == "gold" and req["days"] <= GOLD_DAYS:
        return "APPROVE", "gold exception, %s since purchase (gold limit %d)" % (days(req), GOLD_DAYS)
    return "DENY", "%s since purchase, outside P1/P2 limits" % days(req)


RULES = {"P1": p1, "P2": p2, "P3": p3, "P4": p4}


def decide(req):
    """Return (decision, policy_id, justification). First matching rule in RULE_ORDER wins."""
    for pid in RULE_ORDER:
        result = RULES[pid](req)
        if result:
            decision, why = result
            return decision, pid, "%s under %s: %s." % (decision, pid, why)
    return "ESCALATE", "P4", "ESCALATE under P4: no rule matched."

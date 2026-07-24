"""Margin/commission calculation rules shared by every page.

Kept dependency-free (plain dicts/DataFrames in, updated ones out) so the
same functions work identically against mock data now and real data once
file_store.py/folder_index.py replace mock_data.py in a later phase.
"""
import pandas as pd

from mock_data import COST_TYPE_DEFAULT_PCT


def _num(value, default=0):
    """Coerces missing/None/NaN to `default` - a plain `value or default`
    is NOT enough here, since a NaN is truthy in Python (`nan or 0` returns
    nan itself, not 0), and a line item with a not-yet-found cost commonly
    comes back as NaN once it's passed through a pandas DataFrame column
    that mixes real numbers with missing values on other rows."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return default
    return value


def recompute_line(row):
    """Takes a line-item dict/Series and returns it with cost/margin/commission
    recomputed from qty, selling_unit_price, cost_type, cost_pct_override (for
    PS lines) or cost_unit_price (for Standard lines), and commission_pct."""
    row = dict(row)
    qty = _num(row.get("qty"))
    sell_unit = _num(row.get("selling_unit_price"))
    selling_amount = round(qty * sell_unit, 2)

    if row.get("cost_type") == "Standard":
        cost_unit = _num(row.get("cost_unit_price"))
        cost_amount = round(qty * cost_unit, 2)
    else:
        pct = row.get("cost_pct_override")
        if pct is None or (isinstance(pct, float) and pd.isna(pct)):
            pct = COST_TYPE_DEFAULT_PCT.get(row.get("cost_type"), 0)
        cost_amount = round(selling_amount * pct / 100, 2)
        cost_unit = round(cost_amount / qty, 2) if qty else 0
        row["cost_pct_override"] = pct

    margin_amount = round(selling_amount - cost_amount, 2)
    margin_pct = round(margin_amount / selling_amount * 100, 2) if selling_amount else 0.0
    commission_pct = _num(row.get("commission_pct"))
    commission_amount = round(margin_amount * commission_pct / 100, 2)

    row.update(
        selling_amount=selling_amount,
        cost_unit_price=cost_unit,
        cost_amount=cost_amount,
        margin_amount=margin_amount,
        margin_pct=margin_pct,
        commission_amount=commission_amount,
    )
    return row


def confidence_badge(score):
    """Shared formatting for a document-link (or other) confidence score -
    used by both the Import Sales Invoice List and Import PO List pages'
    folder-scan sections, and by Auto-Match & Extract's summary."""
    if score is None or pd.isna(score):
        return "⚪ n/a"
    if score >= 0.85:
        return f"🟢 {score:.0%}"
    if score >= 0.6:
        return f"🟡 {score:.0%}"
    return f"🔴 {score:.0%}"


def invoice_rollup(line_items_df, invoice_no):
    lines = line_items_df[line_items_df["invoice_no"] == invoice_no]
    return dict(
        selling_total=round(lines["selling_amount"].sum(), 2),
        cost_total=round(lines["cost_amount"].sum(), 2),
        margin_total=round(lines["margin_amount"].sum(), 2),
        commission_total=round(lines["commission_amount"].sum(), 2),
    )


def summary_totals(invoices_df, line_items_df):
    """Overall summary strip: commission earned / paid out / pending -
    ignored invoices excluded entirely, matching the sample's convention."""
    active = invoices_df[~invoices_df["ignored"]]
    commission_by_invoice = {
        inv_no: invoice_rollup(line_items_df, inv_no)["commission_total"]
        for inv_no in active["invoice_no"]
    }
    total_commission = sum(commission_by_invoice.values())
    paid = active[active["paid_by_customer"]]
    pending = active[~active["paid_by_customer"]]
    paid_total = sum(commission_by_invoice[i] for i in paid["invoice_no"])
    pending_total = sum(commission_by_invoice[i] for i in pending["invoice_no"])
    return dict(
        total_commission=round(total_commission, 2),
        paid_total=round(paid_total, 2),
        pending_total=round(pending_total, 2),
        ignored_count=int(invoices_df["ignored"].sum()),
    )


def payout_status(inv):
    """Payout eligibility = commission_approved AND paid_by_customer AND
    NOT ignored (see plan) - this names which of the two independent gates
    a pending invoice is still waiting on, so summaries never just say
    'not paid yet' when the real blocker is 'not approved yet'."""
    if inv.get("ignored"):
        return "ignored"
    approved = bool(inv.get("commission_approved"))
    paid = bool(inv.get("paid_by_customer"))
    if approved and paid:
        return "payable"
    if approved and not paid:
        return "approved, awaiting customer payment"
    if not approved and paid:
        return "paid, awaiting commission approval"
    return "not yet approved"


def invoice_status(inv):
    """One of 'ignored', 'resolved' (confidently matched, or correctly has
    no PO because it's professional service), or 'needs_review' (anything
    else - low/no-confidence match, or unmatched with no explanation)."""
    if inv["ignored"]:
        return "ignored"
    conf = inv["match_confidence"]
    if pd.isna(conf):
        if "professional service" in (inv["po_source"] or ""):
            return "resolved"
        return "needs_review"
    return "resolved" if conf >= 0.85 else "needs_review"


def line_review_flags(row):
    """Per-line-item reasons a row needs a manual look, shown as its own
    column so it's visible without any cell-background styling (data_editor
    doesn't support that on editable cells)."""
    reasons = []
    cost_unit = row.get("cost_unit_price")
    cost_missing = cost_unit is None or pd.isna(cost_unit) or cost_unit == 0
    if row.get("cost_type") == "Standard" and cost_missing:
        reasons.append("no cost found - enter manually")
    margin = row.get("margin_amount")
    if margin is not None and not pd.isna(margin) and margin <= 0:
        reasons.append("zero/negative margin")
    return reasons

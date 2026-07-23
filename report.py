"""Builds an .xlsx shaped like the existing
`Karen - Commission - Payment on 26 Jul 26.xlsx` - one row per invoice,
grouped under PO-ref header rows, with a totals row per group and a grand
total. Ignored invoices are excluded from every total but listed in a
separate sheet for audit trail.
"""
import io

from openpyxl import Workbook
from openpyxl.styles import Font

import commission

HEADERS = ["No.", "Posting Date", "Customer", "Amount", "Cost", "GP", "Comm %", "Comm Amt", "Remarks"]
BOLD = Font(bold=True)
RED = Font(color="FFFF0000")


def _comm_pct_display(line_items_df, invoice_no):
    pcts = line_items_df.loc[line_items_df["invoice_no"] == invoice_no, "commission_pct"].unique()
    if len(pcts) == 1:
        return pcts[0]
    return "mixed"


def build_report(invoices_df, line_items_df, require_approved=True, require_paid=True,
                  salesperson=None, date_from=None, date_to=None):
    """Payout eligibility defaults to commission_approved AND paid_by_customer
    AND NOT ignored (see plan) - the two require_* flags let Finance loosen
    this deliberately (e.g. to preview approved-but-unpaid amounts) rather
    than the report silently including invoices that aren't actually payable
    yet."""
    invoices = invoices_df[~invoices_df["ignored"]].copy()
    if require_approved:
        invoices = invoices[invoices["commission_approved"]]
    if require_paid:
        invoices = invoices[invoices["paid_by_customer"]]
    if salesperson and salesperson != "All":
        invoices = invoices[invoices["salesperson"] == salesperson]
    if date_from:
        invoices = invoices[invoices["invoice_date"] >= date_from]
    if date_to:
        invoices = invoices[invoices["invoice_date"] <= date_to]

    wb = Workbook()
    ws = wb.active
    ws.title = "Commission Report"
    ws.append(["CACTOZ PTE LTD", None, "Commission Listing", None, "Invoice in RED = Payment outstanding"])
    ws.append([])

    if len(invoices):
        ws.append(["Payout by salesperson"])
        ws[ws.max_row][0].font = BOLD
        for sp, sp_group in invoices.groupby("salesperson"):
            sp_commission = sum(
                commission.invoice_rollup(line_items_df, no)["commission_total"] for no in sp_group["invoice_no"]
            )
            ws.append([sp, None, None, None, None, None, None, round(sp_commission, 2)])
        ws.append([])

    ws.append(HEADERS)
    for cell in ws[ws.max_row]:
        cell.font = BOLD

    grand_amount = grand_cost = grand_gp = grand_comm = 0.0

    for po_ref, group in invoices.groupby(invoices["po_ref"].replace("", "(No PO)")):
        ws.append([po_ref])
        ws[ws.max_row][0].font = BOLD
        group_amount = group_cost = group_gp = group_comm = 0.0
        for invoice_no, inv in group.iterrows():
            rollup = commission.invoice_rollup(line_items_df, invoice_no)
            comm_pct = _comm_pct_display(line_items_df, invoice_no)
            row = [
                invoice_no, inv["invoice_date"], inv["customer"],
                rollup["selling_total"], rollup["cost_total"], rollup["margin_total"],
                comm_pct, rollup["commission_total"], inv.get("notes", ""),
            ]
            ws.append(row)
            if not inv["paid_by_customer"]:
                for cell in ws[ws.max_row]:
                    cell.font = RED
            group_amount += rollup["selling_total"]
            group_cost += rollup["cost_total"]
            group_gp += rollup["margin_total"]
            group_comm += rollup["commission_total"]
        ws.append([None, None, "Subtotal", group_amount, group_cost, group_gp, None, group_comm])
        for cell in ws[ws.max_row]:
            cell.font = BOLD
        ws.append([])
        grand_amount += group_amount
        grand_cost += group_cost
        grand_gp += group_gp
        grand_comm += group_comm

    ws.append(["Total", None, None, grand_amount, grand_cost, grand_gp, None, grand_comm])
    for cell in ws[ws.max_row]:
        cell.font = BOLD

    ignored = invoices_df[invoices_df["ignored"]]
    if len(ignored):
        ws2 = wb.create_sheet("Ignored (excluded)")
        ws2.append(HEADERS[:3] + ["Reason"])
        for cell in ws2[1]:
            cell.font = BOLD
        for invoice_no, inv in ignored.iterrows():
            ws2.append([invoice_no, inv["invoice_date"], inv["customer"], inv["ignore_reason"]])

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()

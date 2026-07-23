"""Hardcoded mock data for the Phase 0 clickable prototype.

Numbers are lifted from real sample documents already in hand
(PO-S26070005-KY / Elush, INV-S260392 / ESAB) plus a few real historical
rows from Karen's existing commission spreadsheet, so the prototype feels
grounded rather than arbitrary. The "TechNova" invoice, and everything for
John Tan, are synthesized (clearly marked) - John exists purely to prove
the multi-salesperson isolation actually works (switching Settings to him
should show a completely different, non-overlapping set of invoices).

None of this is read from disk yet - Phase 0 is UI/UX only. Phase 1+
replaces this module with real parsing (extractor.py), real matching
(matcher.py / auto_match.py) reading from a configured folder, and the real
finance <-> salesperson file exchange (exchange.py).
"""
import pandas as pd

COST_TYPES = ["Standard", "Infra/HW PS (30% cost)", "Apps PS (70% cost)"]
COST_TYPE_DEFAULT_PCT = {
    "Standard": None,
    "Infra/HW PS (30% cost)": 30.0,
    "Apps PS (70% cost)": 70.0,
}

SALESPEOPLE = ["Karen Yeung", "John Tan"]

SALES_STATUSES = ["Not yet reviewed", "Ready for finance", "Needs correction"]


def _invoice(**kw):
    base = dict(
        po_ref="", salesperson="Karen Yeung", paid_by_customer=False,
        paid_date=None, ignored=False, ignore_reason="", po_source="",
        match_confidence=None, invoice_pdf_path="", po_pdf_path="",
        notes="", sales_status="Not yet reviewed", correction_note="",
        commission_approved=False, commission_approved_date=None,
    )
    base.update(kw)
    return base


def seed_invoices():
    return pd.DataFrame([
        # --- Karen Yeung ---
        _invoice(
            invoice_no="INV-S260043", customer="Avi-Tech Electronics Pte Ltd",
            invoice_date="2026-01-27", po_ref="PO 36002531",
            po_source="imported-list", match_confidence=0.97,
            invoice_pdf_path="Invoices/INV-S260043.pdf", po_pdf_path="",
            sales_status="Ready for finance",
            commission_approved=True, commission_approved_date="2026-02-10",
            paid_by_customer=True, paid_date="2026-02-15",
            notes="Fully done: approved and paid - shows what 'complete' looks like",
        ),
        _invoice(
            invoice_no="INV-S260392", customer="ESAB Asia/Pacific Pte Ltd",
            invoice_date="2026-07-17", po_ref="KY-SQ2512-S010",
            po_source="none (professional service)", match_confidence=None,
            invoice_pdf_path="Invoices/INV-S260392 - ESAB.pdf", po_pdf_path="",
            sales_status="Ready for finance",
            commission_approved=True, commission_approved_date="2026-07-20",
            paid_by_customer=False,
            notes="Approved but customer hasn't paid yet - the two gates are independent",
        ),
        _invoice(
            invoice_no="INV-S260410", customer="TechNova Pte Ltd (example)",
            invoice_date="2026-07-10", po_ref="PO-S26070005-KY",
            po_source="folder-match", match_confidence=0.93,
            invoice_pdf_path="Invoices/INV-S260410 - TechNova.pdf",
            po_pdf_path="Supplier POs/PO-S26070005-KY_R2 - Elush.pdf",
            sales_status="Not yet reviewed",
            notes="Synthesized example - still sitting in Karen's own queue, untouched",
        ),
        _invoice(
            invoice_no="INV-S260421", customer="Techn0va Pte. Ltd",
            invoice_date="2026-07-12", po_ref="",
            po_source="unmatched", match_confidence=0.41,
            invoice_pdf_path="Invoices/INV-S260421.pdf", po_pdf_path="",
            sales_status="Needs correction",
            correction_note="Customer name looks misspelled vs. the source doc, and the cost is still blank - please confirm both before resubmitting.",
            notes="Low-confidence example, already kicked back once by finance",
        ),
        _invoice(
            invoice_no="CR-S260009", customer="Pan Pacific International Holdings Corporation",
            invoice_date="2026-06-04", po_ref="",
            ignored=True, ignore_reason="Credit note - voided, no commission due",
            invoice_pdf_path="Invoices/CR-S260009.pdf", po_pdf_path="",
        ),
        _invoice(
            invoice_no="INV-S260159", customer="8x8 International Pte Ltd",
            invoice_date="2026-03-27", po_ref="",
            po_source="imported-list", match_confidence=0.99,
            invoice_pdf_path="Invoices/INV-S260159.pdf", po_pdf_path="",
            sales_status="Ready for finance",
            commission_approved=True, commission_approved_date="2026-04-05",
            paid_by_customer=True, paid_date="2026-04-20",
        ),
        # --- John Tan --- (synthesized, proves salesperson isolation)
        _invoice(
            invoice_no="INV-S260500", customer="Straits Marine Supplies Pte Ltd",
            invoice_date="2026-07-14", po_ref="PO-S26070080-JT",
            salesperson="John Tan",
            po_source="folder-match", match_confidence=0.88,
            invoice_pdf_path="Invoices/INV-S260500 - Straits Marine.pdf",
            po_pdf_path="Supplier POs/PO-S26070080-JT.pdf",
            sales_status="Not yet reviewed",
            notes="John's own invoice - Karen should never see this one",
        ),
        _invoice(
            invoice_no="INV-S260510", customer="Nordic Cold Chain Pte Ltd",
            invoice_date="2026-07-18", po_ref="",
            salesperson="John Tan",
            po_source="none (professional service)", match_confidence=None,
            invoice_pdf_path="Invoices/INV-S260510 - Nordic.pdf", po_pdf_path="",
            sales_status="Ready for finance",
            notes="John marked this ready - awaiting finance's first approval pass",
        ),
        _invoice(
            invoice_no="INV-S260488", customer="Straits Marine Supplies Pte Ltd",
            invoice_date="2026-06-30", po_ref="PO-S26060071-JT",
            salesperson="John Tan",
            po_source="imported-list", match_confidence=0.95,
            invoice_pdf_path="Invoices/INV-S260488 - Straits Marine.pdf",
            po_pdf_path="",
            sales_status="Ready for finance",
            commission_approved=True, commission_approved_date="2026-07-05",
            paid_by_customer=True, paid_date="2026-07-12",
        ),
    ]).set_index("invoice_no", drop=False)


def _line(invoice_no, line_no, part_no, description, qty, sell_unit, cost_type,
          cost_unit=None, cost_pct_override=None, commission_pct=10.0, remarks=""):
    selling_amount = round(qty * sell_unit, 2)
    if cost_type == "Standard":
        cost_amount = round(qty * (cost_unit or 0), 2)
    else:
        pct = cost_pct_override if cost_pct_override is not None else COST_TYPE_DEFAULT_PCT[cost_type]
        cost_amount = round(selling_amount * pct / 100, 2)
        cost_unit = round(cost_amount / qty, 2) if qty else 0
    margin_amount = round(selling_amount - cost_amount, 2)
    margin_pct = round(margin_amount / selling_amount * 100, 2) if selling_amount else 0
    commission_amount = round(margin_amount * commission_pct / 100, 2)
    return dict(
        invoice_no=invoice_no, line_no=line_no, part_no=part_no, description=description,
        qty=qty, selling_unit_price=sell_unit, selling_amount=selling_amount,
        cost_type=cost_type, cost_pct_override=cost_pct_override,
        cost_unit_price=cost_unit, cost_amount=cost_amount,
        margin_amount=margin_amount, margin_pct=margin_pct,
        commission_pct=commission_pct, commission_amount=commission_amount,
        remarks=remarks,
    )


def seed_line_items():
    rows = []
    rows.append(_line("INV-S260043", 1, "", "Avi-Tech recurring service", 1, 5440,
                       "Standard", cost_unit=5140, commission_pct=10))

    rows.append(_line("INV-S260392", 1, "", "Maintenance Services - Comprehensive Package (Q3)", 1, 1750,
                       "Apps PS (70% cost)", commission_pct=10,
                       remarks="Apps Change Request Cost 70%"))

    # TechNova / Elush example - mirrors the real PO line items, sold at a markup
    rows.append(_line("INV-S260410", 1, "MDE14ZP/A", "Apple MB Pro 14 M5 10cCPU/10cGPU/16GB/1TB SSD Space Black",
                       5, 2732.00, "Standard", cost_unit=2373.00, commission_pct=10))
    rows.append(_line("INV-S260410", 2, "SXKH2ZX/A", "Apple AppleCare+ for 14-inch MacBook Pro (M5)",
                       5, 337.00, "Standard", cost_unit=293.00, commission_pct=10))
    rows.append(_line("INV-S260410", 3, "MDHF4ZP/A", "Apple MB Air 13 M5 10cCPU/10cGPU/16GB/1TB SSD Midnight",
                       3, 2376.00, "Standard", cost_unit=2066.00, commission_pct=10))
    rows.append(_line("INV-S260410", 4, "SCW83ZX/A", "Apple AppleCare+ for 13-inch MacBook Air (M5)",
                       3, 236.00, "Standard", cost_unit=205.00, commission_pct=10))
    rows.append(_line("INV-S260410", 5, "MXK53ZA/A", "Apple Magic Mouse White",
                       3, 96.00, "Standard", cost_unit=83.00, commission_pct=10))
    rows.append(_line("INV-S260410", 6, "MXCJ3ZA/A", "Apple Magic Keyboard Numeric Keypad - US English",
                       5, 154.00, "Standard", cost_unit=134.00, commission_pct=10))

    rows.append(_line("INV-S260421", 1, "", "Onsite support retainer", 1, 980, "Standard",
                       cost_unit=None, commission_pct=10,
                       remarks="No PO matched yet - cost not found, needs manual entry"))

    rows.append(_line("CR-S260009", 1, "", "Credit note - voided", 1, 0, "Standard", cost_unit=0, commission_pct=0))

    rows.append(_line("INV-S260159", 1, "", "8x8 subscription true-up", 1, 9400, "Standard",
                       cost_unit=8547.20, commission_pct=10))

    # --- John Tan's line items ---
    rows.append(_line("INV-S260500", 1, "", "Marine radar unit + install", 1, 6200, "Standard",
                       cost_unit=4650, commission_pct=8))
    rows.append(_line("INV-S260510", 1, "", "Cold chain monitoring - quarterly service", 1, 2400,
                       "Infra/HW PS (30% cost)", commission_pct=8,
                       remarks="Infra PS 30%"))
    rows.append(_line("INV-S260488", 1, "", "Marine safety equipment resupply", 1, 3100, "Standard",
                       cost_unit=2200, commission_pct=8))

    return pd.DataFrame(rows)


def bc_import_preview():
    """Canned 'what the BC export looks like, and how columns get mapped'."""
    raw = pd.DataFrame([
        {"No.": "INV-S260043", "Posting Date": "2026-01-27", "Sell-to Customer Name": "Avi-Tech Electronics Pte Ltd", "Salesperson Code": "KY", "Amount": 5440.00},
        {"No.": "INV-S260392", "Posting Date": "2026-07-17", "Sell-to Customer Name": "ESAB Asia/Pacific Pte Ltd", "Salesperson Code": "KY", "Amount": 1750.00},
        {"No.": "INV-S260410", "Posting Date": "2026-07-10", "Sell-to Customer Name": "TechNova Pte Ltd", "Salesperson Code": "KY", "Amount": 20876.00},
        {"No.": "INV-S260421", "Posting Date": "2026-07-12", "Sell-to Customer Name": "Techn0va Pte. Ltd", "Salesperson Code": "KY", "Amount": 980.00},
        {"No.": "CR-S260009", "Posting Date": "2026-06-04", "Sell-to Customer Name": "Pan Pacific International Holdings Corporation", "Salesperson Code": "KY", "Amount": 0.00},
        {"No.": "INV-S260159", "Posting Date": "2026-03-27", "Sell-to Customer Name": "8x8 International Pte Ltd", "Salesperson Code": "KY", "Amount": 9400.00},
        {"No.": "INV-S260500", "Posting Date": "2026-07-14", "Sell-to Customer Name": "Straits Marine Supplies Pte Ltd", "Salesperson Code": "JT", "Amount": 6200.00},
        {"No.": "INV-S260510", "Posting Date": "2026-07-18", "Sell-to Customer Name": "Nordic Cold Chain Pte Ltd", "Salesperson Code": "JT", "Amount": 2400.00},
        {"No.": "INV-S260488", "Posting Date": "2026-06-30", "Sell-to Customer Name": "Straits Marine Supplies Pte Ltd", "Salesperson Code": "JT", "Amount": 3100.00},
    ])
    mapping = {
        "No.": "invoice_no",
        "Posting Date": "invoice_date",
        "Sell-to Customer Name": "customer",
        "Salesperson Code": "salesperson",
        "Amount": "amount",
    }
    return raw, mapping


def po_list_preview():
    """Canned 'imported PO list' export and its column mapping."""
    raw = pd.DataFrame([
        {"PO No": "PO 36002531", "Order Date": "2026-01-15", "Supplier": "Avi-Tech Electronics Pte Ltd", "Cost Amount": 5140.00, "Linked Invoice": "INV-S260043"},
        {"PO No": "PO-S26070005-KY", "Order Date": "2026-07-02", "Supplier": "Elush (T3) Pte Ltd", "Cost Amount": 21062.00, "Linked Invoice": "INV-S260410"},
        {"PO No": "PO 36002656-A", "Order Date": "2026-03-20", "Supplier": "8x8 International Pte Ltd", "Cost Amount": 8547.20, "Linked Invoice": "INV-S260159"},
        {"PO No": "PO-S26060071-JT", "Order Date": "2026-06-25", "Supplier": "Straits Marine Supplies Pte Ltd", "Cost Amount": 2200.00, "Linked Invoice": "INV-S260488"},
    ])
    mapping = {
        "PO No": "po_no",
        "Order Date": "po_date",
        "Supplier": "supplier",
        "Cost Amount": "amount",
        "Linked Invoice": "linked_invoice_no",
    }
    return raw, mapping

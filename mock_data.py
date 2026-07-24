"""Hardcoded mock data for the Phase 0 clickable prototype.

Numbers are lifted from real sample documents already in hand
(PO-S26070005-KY / Elush, INV-S260392 / ESAB) plus real rows/shapes from
Karen's three actual Business Central exports (Sales invoice list, PO
list, Sales commission worksheet), so the prototype feels grounded rather
than arbitrary. The "TechNova" invoice, and everything for Joen Tan, are
synthesized (clearly marked) - Joen exists purely to prove the
multi-salesperson isolation actually works (switching Settings to her
should show a completely different, non-overlapping set of invoices).

Standard-cost line items now represent real admin-keyed cost as it would
come from the Sales Commission Worksheet import (the new primary line-item
source - see the plan's "Major pivot" section) rather than PO-PDF
extraction. Professional-service (PS) line items are unchanged: PS lines
have no PO to sanity-check a keyed-in cost against, so their cost still
always comes from the Infra/HW-PS 30% / Apps-PS 70% % rule, never from a
worksheet total-cost figure.

None of this is read from disk yet - Phase 0 is UI/UX only. Phase 1+
replaces this module with real parsing (bc_import.py / po_import.py /
commission_worksheet_import.py) reading from uploaded exports, and the real
finance <-> salesperson file exchange (exchange.py).
"""
import pandas as pd

COST_TYPES = ["Standard", "Infra/HW PS (30% cost)", "Apps PS (70% cost)"]
COST_TYPE_DEFAULT_PCT = {
    "Standard": None,
    "Infra/HW PS (30% cost)": 30.0,
    "Apps PS (70% cost)": 70.0,
}

SALESPEOPLE = ["Karen Yeung", "Joen Tan"]

SALES_STATUSES = ["Not yet reviewed", "Ready for finance", "Needs correction"]

# Withholding tax: Thailand and Taiwan customers have WHT deducted from the
# invoiced amount before Cactoz actually gets paid - e.g. a THB 155.63
# invoice with 5% WHT is really only 147.85 received. Commission has to be
# calculated on that net-of-WHT figure, not the gross invoiced amount
# (confirmed with Karen - the historical spreadsheet missed this, which is
# why INV-S250442 is the example that surfaced it). Auto-detected from the
# customer name so nobody has to remember to apply it by hand, but every
# WHT-affected line still gets flagged for a manual double-check (see
# commission.line_review_flags) since the country match is just a keyword
# guess against the customer name.
WHT_RATES_BY_COUNTRY = {"Thailand": 5.0, "Taiwan": 20.0}


def wht_rate_for_customer(customer_name):
    """Best-effort country detection from the customer name alone (no
    dedicated country field in any of the 3 real BC exports) - keyword
    match against WHT_RATES_BY_COUNTRY. Returns 0.0 for anyone else."""
    name = (customer_name or "").lower()
    for country, rate in WHT_RATES_BY_COUNTRY.items():
        if country.lower() in name:
            return rate
    return 0.0

# Canned "what's in the shared SharePoint folder" listing, used by both the
# Import Sales Invoice List page (invoice-PDF scan) and the Import PO List
# page (PO-PDF scan) - these PDFs are sanity-check reference links now, not
# a cost source, but folks still want to open the source document.
ALL_FILES = [
    "Invoices/INV-S260043.pdf", "Invoices/INV-S260392 - ESAB.pdf",
    "Invoices/INV-S260410 - TechNova.pdf", "Invoices/INV-S260421.pdf",
    "Invoices/CR-S260009.pdf", "Invoices/INV-S260159.pdf",
    "Invoices/INV-S260500 - Straits Marine.pdf", "Invoices/INV-S260510 - Nordic.pdf",
    "Invoices/INV-S260488 - Straits Marine.pdf",
    "Supplier POs/PO-S26070005-KY_R2 - Elush.pdf", "Supplier POs/PO 36002531.pdf",
    "Supplier POs/PO 36002656-A.pdf", "Supplier POs/PO-S26070080-JT.pdf",
    "Quotes/QUO-S260201 - unrelated.pdf",
    "(no PO match)",
]
INVOICE_FILES = ALL_FILES[:9]
PO_FILES = ALL_FILES[9:14]


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
            correction_note="Margin on this line looks off (98% - cost seems too low for this kind of work). Please double-check the cost and recalculate before resubmitting.",
            notes="Low-confidence example, already sent back once by finance",
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
        # --- WHT examples (real historical invoices - the same
        # INV-S250442 Karen flagged as missing WHT in the old spreadsheet) ---
        _invoice(
            invoice_no="INV-S250442", customer="DONKI (Thailand) Co., Ltd.",
            invoice_date="2025-08-21", po_ref="",
            po_source="none (professional service)", match_confidence=None,
            invoice_pdf_path="Invoices/INV-S250442 - PPRM TH.pdf", po_pdf_path="",
            sales_status="Ready for finance",
            paid_by_customer=True, paid_date="2025-09-10",
            notes="Thailand customer - 5% WHT auto-applied, needs a manual double-check before approving",
        ),
        _invoice(
            invoice_no="INV-S250352", customer="Taiwan Pan Pacific Retail Management Co., Ltd",
            invoice_date="2025-07-04", po_ref="",
            po_source="none (professional service)", match_confidence=None,
            invoice_pdf_path="", po_pdf_path="",
            sales_status="Ready for finance",
            paid_by_customer=True, paid_date="2025-07-28",
            notes="Taiwan customer - 20% WHT auto-applied, needs a manual double-check before approving",
        ),
        # --- Joen Tan --- (synthesized, proves salesperson isolation;
        # sales person code "JT" matches the real commission worksheet)
        _invoice(
            invoice_no="INV-S260500", customer="Straits Marine Supplies Pte Ltd",
            invoice_date="2026-07-14", po_ref="PO-S26070080-JT",
            salesperson="Joen Tan",
            po_source="folder-match", match_confidence=0.88,
            invoice_pdf_path="Invoices/INV-S260500 - Straits Marine.pdf",
            po_pdf_path="Supplier POs/PO-S26070080-JT.pdf",
            sales_status="Not yet reviewed",
            notes="Joen's own invoice - Karen should never see this one",
        ),
        _invoice(
            invoice_no="INV-S260510", customer="Nordic Cold Chain Pte Ltd",
            invoice_date="2026-07-18", po_ref="",
            salesperson="Joen Tan",
            po_source="none (professional service)", match_confidence=None,
            invoice_pdf_path="Invoices/INV-S260510 - Nordic.pdf", po_pdf_path="",
            sales_status="Ready for finance",
            notes="Joen marked this ready - awaiting finance's first approval pass",
        ),
        _invoice(
            invoice_no="INV-S260488", customer="Straits Marine Supplies Pte Ltd",
            invoice_date="2026-06-30", po_ref="PO-S26060071-JT",
            salesperson="Joen Tan",
            po_source="imported-list", match_confidence=0.95,
            invoice_pdf_path="Invoices/INV-S260488 - Straits Marine.pdf",
            po_pdf_path="",
            sales_status="Ready for finance",
            commission_approved=True, commission_approved_date="2026-07-05",
            paid_by_customer=True, paid_date="2026-07-12",
        ),
    ]).set_index("invoice_no", drop=False)


def _line(invoice_no, line_no, part_no, description, qty, sell_unit, cost_type,
          cost_unit=None, cost_pct_override=None, commission_pct=10.0, remarks="",
          wht_pct=0.0):
    selling_amount = round(qty * sell_unit, 2)
    if cost_type == "Standard":
        cost_amount = round(qty * (cost_unit or 0), 2)
    else:
        pct = cost_pct_override if cost_pct_override is not None else COST_TYPE_DEFAULT_PCT[cost_type]
        cost_amount = round(selling_amount * pct / 100, 2)
        cost_unit = round(cost_amount / qty, 2) if qty else 0
    wht_amount = round(selling_amount * wht_pct / 100, 2)
    net_selling_amount = round(selling_amount - wht_amount, 2)
    margin_amount = round(net_selling_amount - cost_amount, 2)
    margin_pct = round(margin_amount / selling_amount * 100, 2) if selling_amount else 0
    commission_amount = round(margin_amount * commission_pct / 100, 2)
    return dict(
        invoice_no=invoice_no, line_no=line_no, part_no=part_no, description=description,
        qty=qty, selling_unit_price=sell_unit, selling_amount=selling_amount,
        cost_type=cost_type, cost_pct_override=cost_pct_override,
        cost_unit_price=cost_unit, cost_amount=cost_amount,
        wht_pct=wht_pct, wht_amount=wht_amount,
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
                       remarks="Not in this period's commission worksheet yet - cost not found, needs manual entry"))

    rows.append(_line("CR-S260009", 1, "", "Credit note - voided", 1, 0, "Standard", cost_unit=0, commission_pct=0))

    rows.append(_line("INV-S260159", 1, "", "8x8 subscription true-up", 1, 9400, "Standard",
                       cost_unit=8547.20, commission_pct=10))

    # --- WHT examples ---
    rows.append(_line("INV-S250442", 1, "", "Top Up", 1, 155.63, "Standard",
                       cost_unit=0, commission_pct=5,
                       wht_pct=wht_rate_for_customer("DONKI (Thailand) Co., Ltd."),
                       remarks="Top Up"))
    rows.append(_line("INV-S250352", 1, "", "PS Downgrade Azure Server Cost", 1, 937.5,
                       "Infra/HW PS (30% cost)", commission_pct=5,
                       wht_pct=wht_rate_for_customer("Taiwan Pan Pacific Retail Management Co., Ltd"),
                       remarks="PS Downgrade Azure Server Cost 30%"))

    # --- Joen Tan's line items ---
    rows.append(_line("INV-S260500", 1, "", "Marine radar unit + install", 1, 6200, "Standard",
                       cost_unit=4650, commission_pct=8))
    rows.append(_line("INV-S260510", 1, "", "Cold chain monitoring - quarterly service", 1, 2400,
                       "Infra/HW PS (30% cost)", commission_pct=8,
                       remarks="Infra PS 30% - no PO to check a keyed-in cost against, so the % rule always applies"))
    rows.append(_line("INV-S260488", 1, "", "Marine safety equipment resupply", 1, 3100, "Standard",
                       cost_unit=2200, commission_pct=8))

    return pd.DataFrame(rows)


def bc_import_preview():
    """Canned preview shaped like Karen's real 'Sales invoice lsit.xlsx'
    export - the source of truth for which invoices exist. No salesperson
    column here (that comes from joining the PO list's Assigned User ID);
    `Closed` is the (Karen-confirmed) signal for paid_by_customer, since
    the invoice list and commission worksheet are always pulled for the
    same period."""
    raw = pd.DataFrame([
        {"No.": "INV-S260043", "Order No.": "SO-S260012", "Document Date": "2026-01-27", "Customer No.": "SC0091", "Customer": "Avi-Tech Electronics Pte Ltd", "External Document No.": "36002531", "Currency Code": None, "Amount": 5440.00, "Amount Including GST": 5929.60, "Closed": "Yes"},
        {"No.": "INV-S260392", "Order No.": "SO-S260287", "Document Date": "2026-07-17", "Customer No.": "SC0233", "Customer": "ESAB Asia/Pacific Pte Ltd", "External Document No.": "KY-SQ2512-S010", "Currency Code": None, "Amount": 1750.00, "Amount Including GST": 1907.50, "Closed": "No"},
        {"No.": "INV-S260410", "Order No.": "SO-S260310", "Document Date": "2026-07-10", "Customer No.": "SC0301", "Customer": "TechNova Pte Ltd", "External Document No.": "PO-S26070005-KY", "Currency Code": None, "Amount": 20876.00, "Amount Including GST": 22754.84, "Closed": "No"},
        {"No.": "INV-S260421", "Order No.": "SO-S260315", "Document Date": "2026-07-12", "Customer No.": "SC0301", "Customer": "Techn0va Pte. Ltd", "External Document No.": None, "Currency Code": None, "Amount": 980.00, "Amount Including GST": 1068.20, "Closed": "No"},
        {"No.": "CR-S260009", "Order No.": None, "Document Date": "2026-06-04", "Customer No.": "SC0455", "Customer": "Pan Pacific International Holdings Corporation", "External Document No.": None, "Currency Code": None, "Amount": 0.00, "Amount Including GST": 0.00, "Closed": "Yes"},
        {"No.": "INV-S260159", "Order No.": "SO-S260098", "Document Date": "2026-03-27", "Customer No.": "SC0451", "Customer": "8x8 International Pte Ltd", "External Document No.": None, "Currency Code": None, "Amount": 9400.00, "Amount Including GST": 10246.00, "Closed": "Yes"},
        {"No.": "INV-S260500", "Order No.": "SO-S260396", "Document Date": "2026-07-14", "Customer No.": "SC0512", "Customer": "Straits Marine Supplies Pte Ltd", "External Document No.": None, "Currency Code": None, "Amount": 6200.00, "Amount Including GST": 6758.00, "Closed": "No"},
        {"No.": "INV-S260510", "Order No.": "SO-S260401", "Document Date": "2026-07-18", "Customer No.": "SC0518", "Customer": "Nordic Cold Chain Pte Ltd", "External Document No.": None, "Currency Code": None, "Amount": 2400.00, "Amount Including GST": 2616.00, "Closed": "No"},
        {"No.": "INV-S260488", "Order No.": "SO-S260380", "Document Date": "2026-06-30", "Customer No.": "SC0512", "Customer": "Straits Marine Supplies Pte Ltd", "External Document No.": None, "Currency Code": None, "Amount": 3100.00, "Amount Including GST": 3379.00, "Closed": "Yes"},
    ])
    mapping = {
        "No.": "invoice_no",
        "Order No.": "order_no",
        "Document Date": "invoice_date",
        "Customer No.": "customer_no",
        "Customer": "customer",
        "External Document No.": "external_doc_no",
        "Amount": "amount",
        "Amount Including GST": "amount_incl_gst",
        "Closed": "closed",
    }
    return raw, mapping


def po_list_preview():
    """Canned preview shaped like Karen's real 'PO list.xlsx' export - one
    row per supplier PO. `Sales Order No.` is the join key back to the
    invoice list's `Order No.`; `Assigned User ID` is where
    salesperson-per-invoice actually comes from (via that join) now that
    the invoice list itself carries no salesperson column."""
    raw = pd.DataFrame([
        {"No.": "PO-S26010031", "Your Reference": "36002531", "Buy-from Vendor No.": "SV0102", "Sales Order No.": "SO-S260012", "Buy-from Vendor Name": "Avi-Tech Supplies Pte Ltd", "Assigned User ID": "KAREN.YEO", "Document Date": "2026-01-25", "Amount": 5140.00, "Amount Including GST": 5602.60},
        {"No.": "PO-S26070005", "Your Reference": None, "Buy-from Vendor No.": "SV0376", "Sales Order No.": "SO-S260310", "Buy-from Vendor Name": "Elush Distribution Pte Ltd", "Assigned User ID": "KAREN.YEO", "Document Date": "2026-07-08", "Amount": 18956.00, "Amount Including GST": 20661.04},
        {"No.": "PO-S26030022", "Your Reference": None, "Buy-from Vendor No.": "SV0198", "Sales Order No.": "SO-S260098", "Buy-from Vendor Name": "8x8 Distribution Pte Ltd", "Assigned User ID": "KAREN.YEO", "Document Date": "2026-03-24", "Amount": 8547.20, "Amount Including GST": 9316.45},
        {"No.": "PO-S26070080", "Your Reference": None, "Buy-from Vendor No.": "SV0284", "Sales Order No.": "SO-S260396", "Buy-from Vendor Name": "Marine Tech Supplies Pte Ltd", "Assigned User ID": "JOEN.TAN", "Document Date": "2026-07-12", "Amount": 4650.00, "Amount Including GST": 5068.50},
        {"No.": "PO-S26060071", "Your Reference": None, "Buy-from Vendor No.": "SV0284", "Sales Order No.": "SO-S260380", "Buy-from Vendor Name": "Marine Tech Supplies Pte Ltd", "Assigned User ID": "JOEN.TAN", "Document Date": "2026-06-27", "Amount": 2200.00, "Amount Including GST": 2398.00},
    ])
    mapping = {
        "No.": "po_no",
        "Your Reference": "your_reference",
        "Buy-from Vendor No.": "vendor_no",
        "Sales Order No.": "sales_order_no",
        "Buy-from Vendor Name": "vendor_name",
        "Assigned User ID": "assigned_user_id",
        "Document Date": "po_date",
        "Amount": "amount",
        "Amount Including GST": "amount_incl_gst",
    }
    return raw, mapping


def commission_worksheet_preview():
    """Canned preview shaped like Karen's real 'sales commission
    worksheet.xlsx' export - the primary line-item source (see the plan's
    'Major pivot' section). For lines classified Standard, `total cost` is
    the real admin-keyed cost, trusted directly. For lines classified as
    professional service (item `no` == "PS" here), `total cost` is
    intentionally NOT trusted - there's no PO to sanity-check it against -
    so those lines still get their cost from the Infra/HW-PS 30% / Apps-PS
    70% rule once imported, same as today. The unlabeled trailing column
    (admin's own name/login who keyed the invoice in - confirmed with
    Karen) is included for reference only, never used in any logic."""
    raw = pd.DataFrame([
        {"Document number": "INV-S260043", "posting date": "2026-01-27", "sell-to customer name": "Avi-Tech Electronics Pte Ltd", "type": "Item", "no": "HW", "part number": "", "description": "Avi-Tech recurring service", "qty": 1, "unit price excl. gst": 5440.00, "amount": 5440.00, "invoice remaining amount": 0.00, "unit cost": None, "total cost": 5140.00, "gross profit": 300.00, "commission amount": 30.00, "sales person code": "KY", "sales person": "Karen Yeung", "keyed in by": "KAREN.YEO"},
        {"Document number": "INV-S260392", "posting date": "2026-07-17", "sell-to customer name": "ESAB Asia/Pacific Pte Ltd", "type": "Item", "no": "PS", "part number": "", "description": "Maintenance Services - Comprehensive Package (Q3)", "qty": 1, "unit price excl. gst": 1750.00, "amount": 1750.00, "invoice remaining amount": 1907.50, "unit cost": None, "total cost": 1225.00, "gross profit": 525.00, "commission amount": 52.50, "sales person code": "KY", "sales person": "Karen Yeung", "keyed in by": "ANN"},
        {"Document number": "INV-S260159", "posting date": "2026-03-27", "sell-to customer name": "8x8 International Pte Ltd", "type": "Item", "no": "LGR", "part number": "8X8-SUB", "description": "8x8 subscription true-up", "qty": 1, "unit price excl. gst": 9400.00, "amount": 9400.00, "invoice remaining amount": 0.00, "unit cost": None, "total cost": 8547.20, "gross profit": 852.80, "commission amount": 85.28, "sales person code": "KY", "sales person": "Karen Yeung", "keyed in by": "KAREN.YEO"},
        {"Document number": "INV-S260500", "posting date": "2026-07-14", "sell-to customer name": "Straits Marine Supplies Pte Ltd", "type": "Item", "no": "HW-ACC", "part number": "MR-RADAR-1", "description": "Marine radar unit + install", "qty": 1, "unit price excl. gst": 6200.00, "amount": 6200.00, "invoice remaining amount": 6758.00, "unit cost": None, "total cost": 4650.00, "gross profit": 1550.00, "commission amount": 124.00, "sales person code": "JT", "sales person": "Joen Tan", "keyed in by": "JOEN.TAN"},
        {"Document number": "INV-S260488", "posting date": "2026-06-30", "sell-to customer name": "Straits Marine Supplies Pte Ltd", "type": "Item", "no": "HW-ACC", "part number": "MR-SAFETY-2", "description": "Marine safety equipment resupply", "qty": 1, "unit price excl. gst": 3100.00, "amount": 3100.00, "invoice remaining amount": 0.00, "unit cost": None, "total cost": 2200.00, "gross profit": 900.00, "commission amount": 72.00, "sales person code": "JT", "sales person": "Joen Tan", "keyed in by": "JOEN.TAN"},
        {"Document number": "INV-S250442", "posting date": "2025-08-21", "sell-to customer name": "DONKI (Thailand) Co., Ltd.", "type": "Item", "no": "HW", "part number": "", "description": "Top Up", "qty": 1, "unit price excl. gst": 155.63, "amount": 155.63, "invoice remaining amount": 0.00, "unit cost": None, "total cost": 0.00, "gross profit": 155.63, "commission amount": 7.7815, "sales person code": "KY", "sales person": "Karen Yeung", "keyed in by": "KAREN.YEO"},
        {"Document number": "INV-S250352", "posting date": "2025-07-04", "sell-to customer name": "Taiwan Pan Pacific Retail Management Co., Ltd", "type": "Item", "no": "PS", "part number": "", "description": "PS Downgrade Azure Server Cost", "qty": 1, "unit price excl. gst": 937.5, "amount": 937.5, "invoice remaining amount": 0.00, "unit cost": None, "total cost": 281.25, "gross profit": 656.25, "commission amount": 32.8125, "sales person code": "KY", "sales person": "Karen Yeung", "keyed in by": "KAREN.YEO"},
    ])
    mapping = {
        "Document number": "invoice_no",
        "posting date": "posting_date",
        "sell-to customer name": "customer",
        "no": "item_code",
        "part number": "part_no",
        "description": "description",
        "qty": "qty",
        "unit price excl. gst": "unit_price",
        "amount": "amount",
        "invoice remaining amount": "invoice_remaining_amount",
        "total cost": "total_cost",
        "gross profit": "gross_profit",
        "commission amount": "commission_amount",
        "sales person code": "sales_person_code",
        "sales person": "salesperson",
        "keyed in by": "keyed_in_by",
    }
    return raw, mapping

"""Builds/reads the file that actually moves between Finance and a
salesperson - this IS the privacy boundary (see plan's "How salesperson
privacy is enforced"), not a role filter over one shared file. A
salesperson's exchange file contains only their own rows; there is nothing
else on their machine to expose.

Phase 0: operates on in-session DataFrames and produces/reads real .xlsx
bytes via Streamlit's upload/download widgets (no shared folder involved -
that's consistent with the plan, since the exchange is a deliberate
send/receive, never a background sync). Phase 1+ wires the same functions
to file_store.py so Finance's side reads/writes the master workbook on disk.
"""
import io

import pandas as pd
from openpyxl import load_workbook


def write_workbook(invoices, line_items):
    """Writes already-scoped invoices/line_items to .xlsx bytes - shared by
    Finance's initial per-salesperson export and a salesperson re-exporting
    their own (already single-person) working copy back to Finance."""
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        invoices.to_excel(writer, sheet_name="invoices", index=False)
        line_items.to_excel(writer, sheet_name="line_items", index=False)
    return buf.getvalue()


def build_export(invoices, line_items, salesperson):
    """Returns .xlsx bytes containing only `salesperson`'s invoices/line
    items - this is the file Finance sends to that salesperson manually."""
    inv_slice = invoices[invoices["salesperson"] == salesperson].copy()
    line_slice = line_items[line_items["invoice_no"].isin(inv_slice["invoice_no"])].copy()
    return write_workbook(inv_slice, line_slice)


def read_export(file_bytes):
    """Reads back a file built by build_export (or one a salesperson has
    since edited and re-exported) into (invoices_df, line_items_df)."""
    buf = io.BytesIO(file_bytes)
    invoices = pd.read_excel(buf, sheet_name="invoices")
    buf.seek(0)
    line_items = pd.read_excel(buf, sheet_name="line_items")
    if "invoice_no" in invoices.columns:
        invoices = invoices.set_index("invoice_no", drop=False)
    return invoices, line_items


def merge_salesperson_update(master_invoices, master_line_items, updated_invoices, updated_line_items):
    """Writes a salesperson's edits back into Finance's master, matched by
    invoice_no. Returns (merged_invoices, merged_line_items, warnings) -
    warnings flag any invoice that looks like it moved on in the master
    since this export (e.g. re-run through auto-match again) so Finance
    doesn't silently overwrite something newer with a stale update; this is
    a one-shot staleness check, not real-time locking, since the hand-off
    is sequential rather than concurrent."""
    warnings = []
    merged_invoices = master_invoices.copy()
    merged_line_items = master_line_items.copy()

    for invoice_no, updated_row in updated_invoices.iterrows():
        if invoice_no not in merged_invoices.index:
            warnings.append(f"{invoice_no}: not found in the master dataset - skipped.")
            continue
        current = merged_invoices.loc[invoice_no]
        if current.get("sales_status") == "Not yet reviewed" and updated_row.get("sales_status") == "Not yet reviewed":
            warnings.append(f"{invoice_no}: still marked 'Not yet reviewed' - nothing to merge.")
            continue
        for col in ["sales_status", "correction_note"]:
            if col in updated_row:
                merged_invoices.loc[invoice_no, col] = updated_row[col]

    for _, updated_line in updated_line_items.iterrows():
        mask = (
            (merged_line_items["invoice_no"] == updated_line["invoice_no"])
            & (merged_line_items["line_no"] == updated_line["line_no"])
        )
        if not mask.any():
            warnings.append(
                f"{updated_line['invoice_no']} line {updated_line['line_no']}: not found in the "
                "master - skipped (was it added after this export was sent?)."
            )
            continue
        for col in updated_line_items.columns:
            merged_line_items.loc[mask, col] = updated_line[col]

    return merged_invoices, merged_line_items, warnings

import streamlit as st

from state import ensure_state

st.set_page_config(page_title="Commission Calculator (Prototype)", layout="wide")
ensure_state()

# Sidebar is grouped into Account / Finance / Salesperson so each role's steps
# are visually separate, in the order they're actually meant to be worked
# through - not just an alphabetical/flat page list. Individual pages still
# self-gate via require_finance()/require_salesperson() (see state.py) for a
# user in the wrong role, since both groups are always shown here rather
# than being hidden based on the current role.

settings_page = st.Page("pages/settings.py", title="Settings (sign in)", icon=":material/settings:")

finance_pages = [
    st.Page("pages/finance_import_commission_worksheet.py", title="1. Import Commission Worksheet", icon=":material/upload_file:"),
    st.Page("pages/finance_import_bc_invoices.py", title="2. Import Sales Invoice List + Scan Invoice PDFs", icon=":material/upload_file:"),
    st.Page("pages/finance_import_po_list.py", title="3. Import PO List + Scan PO PDFs", icon=":material/upload_file:"),
    st.Page("pages/finance_auto_match_extract.py", title="4. Auto-Match & Extract (sanity check)", icon=":material/compare_arrows:"),
    st.Page("pages/finance_export_for_salesperson.py", title="5. Export for Salesperson", icon=":material/outbox:"),
    st.Page("pages/finance_import_salesperson_updates.py", title="6. Import Salesperson Updates", icon=":material/inbox:"),
    st.Page("pages/finance_approval.py", title="7. Finance Approval", icon=":material/fact_check:"),
    st.Page("pages/finance_export.py", title="8. Export Payout Report", icon=":material/download:"),
]

salesperson_pages = [
    st.Page("pages/salesperson_my_invoices.py", title="1. My Invoices", icon=":material/inventory:"),
    st.Page("pages/salesperson_export_updates.py", title="2. Export My Updates", icon=":material/outbox:"),
]

pg = st.navigation({
    "Account": [settings_page],
    "Finance": finance_pages,
    "Salesperson": salesperson_pages,
})
pg.run()

import streamlit as st

from state import current_role, current_salesperson, ensure_state

st.set_page_config(page_title="Commission Calculator (Prototype)", layout="wide")
ensure_state()

st.title("Commission Calculator")
st.caption(
    "Prototype - every number on these pages is mock/sample data, nothing is read from or "
    "written to disk yet. This exists to validate the finance/salesperson workflow and privacy "
    "boundary before the real PDF-parsing, folder-scanning, and file-exchange logic is built."
)

role = current_role()
if role == "Finance":
    st.info("Signed in as **Finance**. You see everyone's invoices, across the stages below.", icon="🗂️")
else:
    st.info(
        f"Signed in as **Salesperson: {current_salesperson()}**. You only ever see your own "
        "invoices - never anyone else's.",
        icon="🔒",
    )

with st.container(border=True):
    st.subheader("0. Settings")
    st.write("Set your role (Finance, or Salesperson + your name) and root folder.")
    st.page_link("pages/0_Settings.py", label="Open Settings", icon=":material/settings:")

st.markdown("#### Finance's flow")
with st.container(border=True):
    st.subheader("1-2. Import BC Invoices / PO List")
    st.write("The authoritative invoice list, plus an optional PO list to supplement folder-matched costs.")
    st.page_link("pages/1_Import_BC_Invoices.py", label="Open Import BC Invoices", icon=":material/upload_file:")
    st.page_link("pages/2_Import_PO_List.py", label="Open Import PO List", icon=":material/upload_file:")

with st.container(border=True):
    st.subheader("3. Auto-Match & Extract")
    st.write("First-pass check across everyone - this is what produces the flags salespeople act on next.")
    st.page_link("pages/3_Auto_Match_and_Extract.py", label="Open Auto-Match & Extract", icon=":material/compare_arrows:")

with st.container(border=True):
    st.subheader("4. Export for Salesperson")
    st.write("Send each salesperson a file containing only their own rows - the actual privacy boundary.")
    st.page_link("pages/4_Export_for_Salesperson.py", label="Open Export for Salesperson", icon=":material/outbox:")

st.markdown("#### Salesperson's flow")
with st.container(border=True):
    st.subheader("5. My Invoices")
    st.write("Import the file Finance sent you, fix flagged items, mark ready, export your updates back.")
    st.page_link("pages/5_My_Invoices.py", label="Open My Invoices", icon=":material/inventory:")

st.markdown("#### Back to Finance")
with st.container(border=True):
    st.subheader("6. Import Salesperson Updates")
    st.write("Merge a returned file back into the master dataset.")
    st.page_link("pages/6_Import_Salesperson_Updates.py", label="Open Import Salesperson Updates", icon=":material/inbox:")

with st.container(border=True):
    st.subheader("7. Finance Approval")
    st.write("Approve or kick back with a note; separately, mark paid-by-customer and ignore/void.")
    st.page_link("pages/7_Finance_Approval.py", label="Open Finance Approval", icon=":material/fact_check:")

with st.container(border=True):
    st.subheader("8. Export")
    st.write("Download the payout report, scoped to approved + paid, with per-salesperson subtotals.")
    st.page_link("pages/8_Export.py", label="Open Export", icon=":material/download:")

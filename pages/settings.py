import streamlit as st

import exchange
import mock_data
from state import ensure_state

st.set_page_config(page_title="Settings", layout="wide")
ensure_state()

st.title("Commission Calculator")
st.caption(
    "Prototype - every number on these pages is mock/sample data, nothing is read from or "
    "written to disk yet. This exists to validate the finance/salesperson workflow and privacy "
    "boundary before the real PDF-parsing, folder-scanning, and file-exchange logic is built. "
    "Use the sidebar to move between the **Finance** and **Salesperson** steps, grouped separately."
)

st.subheader("Settings")
st.caption(
    "Role/name here is self-declared (no real login), same as the real v1 will be. It's still "
    "what every other page uses to decide what you can see - try switching it and watch My "
    "Invoices / the Finance pages change."
)

st.subheader("Your role")
role = st.radio(
    "Who are you signed in as?",
    options=["Finance", "Salesperson"],
    index=["Finance", "Salesperson"].index(st.session_state["role"]),
    horizontal=True,
)
st.session_state["role"] = role
# Re-run the master-data isolation check immediately with the just-picked
# role, rather than waiting for the next page load - ensure_state() only
# saw the *previous* role when it ran at the top of this script pass,
# since this radio's on-screen change is what triggered this rerun in the
# first place.
ensure_state()

if role == "Salesperson":
    name = st.selectbox(
        "Your name",
        options=mock_data.SALESPEOPLE,
        index=mock_data.SALESPEOPLE.index(st.session_state["current_salesperson"]),
        help="In the real app this determines which exchange file you're working from - "
             "you'd never have anyone else's data on your machine to begin with.",
    )
    st.session_state["current_salesperson"] = name
    st.info(
        f"You'll only see **{name}'s** own invoices on My Invoices - try switching to the "
        "other salesperson above to confirm nothing carries over.",
        icon="🔒",
    )
else:
    st.info(
        "Finance sees the Import/Auto-Match/Export-for-Salesperson/Import-Updates/"
        "Finance Approval/Export pages, across every salesperson at once.",
        icon="🗂️",
    )

    st.divider()
    st.subheader("Continue where you left off")
    st.caption(
        "Nothing persists automatically yet - this app doesn't have (or need) a database, but "
        "that does mean your approvals/paid flags/edits only live in this browser session. "
        "**Download your progress before closing this session**, and load it back here next time "
        "- otherwise you start over from the BC/PO/Worksheet imports with everything back to "
        "not-yet-reviewed."
    )
    p1, p2 = st.columns(2)
    with p1:
        progress_file = st.file_uploader(
            "Load a previously saved progress file (.xlsx)", type=["xlsx"], key="progress_upload",
        )
        if progress_file:
            inv, lines = exchange.read_export(progress_file.read())
            st.session_state["invoices"] = inv
            st.session_state["line_items"] = lines
            st.success(f"Loaded {len(inv)} invoice(s) from your saved progress file.")
    with p2:
        st.download_button(
            "Download current progress (.xlsx)",
            data=exchange.write_workbook(st.session_state["invoices"], st.session_state["line_items"]),
            file_name="commission_progress.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            help="Grab this before you close the app - reload it here next time to pick up where you left off.",
        )

st.divider()
st.subheader("What this will do once real")
st.markdown(
    "- Scan for PDF invoices/POs and build a searchable index - **manually, only when Finance "
    "clicks \"Scan folder now\" on Import Sales Invoice List / Import PO List.** Never automatic, "
    "never in the background, never triggered by a salesperson opening the app (a salesperson's "
    "own folder is just for viewing their linked documents as a sanity check - salespeople don't "
    "need to upload invoice/PO PDFs themselves)\n"
    "- Resolve every invoice/PO link **relative to a salesperson's own folder root**, matching "
    "the real SharePoint permission structure IT sets up per salesperson - each import page "
    "handles this scan itself now rather than a shared folder setting here\n"
    "- Structured data (invoices/line items) does **not** sync through this folder at all - it "
    "moves as an explicit exported/imported file between Finance and each salesperson (see "
    "Export for Salesperson / Import Salesperson Updates) - that's the actual privacy boundary, "
    "not any folder setting"
)

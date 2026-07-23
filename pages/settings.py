import streamlit as st

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
root = st.text_input(
    "Your root folder (your OneDrive/SharePoint sync, or any local folder)",
    value=st.session_state["root_folder"],
    placeholder=r"C:\Users\KarenYeung\OneDrive - Cactoz\Commission App\Karen Yeung"
                if role == "Salesperson" else
                r"C:\Users\KarenYeung\OneDrive - Cactoz\Commission App",
    help="Salesperson: your own single SharePoint-permissioned folder. "
         "Finance: the parent folder with one subfolder per salesperson.",
)
st.session_state["root_folder"] = root

if root:
    st.success(f"Pointed at: `{root}` (not actually scanned in this prototype)")
else:
    st.warning("No folder set yet - the real app would refuse to scan/match until this is set.")

st.divider()
st.subheader("What this will do once real")
st.markdown(
    "- Scan this folder for PDF invoices/POs/quotes and build a searchable index - "
    "**manually, only when Finance clicks \"Scan folder now\" on Auto-Match & Extract.** "
    "Never automatic, never in the background, never triggered by a salesperson opening the "
    "app (a salesperson's own folder is just for viewing/uploading their linked documents)\n"
    "- Resolve every invoice/PO link **relative to a salesperson's own folder root** - for "
    "Finance that means `<this folder>/<salesperson name>/...`, matching the real SharePoint "
    "permission structure IT sets up per salesperson\n"
    "- Structured data (invoices/line items) does **not** sync through this folder at all - it "
    "moves as an explicit exported/imported file between Finance and each salesperson (see "
    "Export for Salesperson / Import Salesperson Updates) - that's the actual privacy boundary, "
    "not this folder setting"
)

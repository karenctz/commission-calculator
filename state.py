"""Shared session-state init - every page calls ensure_state() first so
Streamlit's per-page-file model still sees one consistent in-memory dataset
for the duration of the browser session (Phase 0 only; nothing is persisted
to disk yet)."""
import streamlit as st

import mock_data

# Streamlit's default st.metric value is ~2.5rem - reads as a page-level KPI
# even when used for a per-invoice/per-row rollup (selling/cost/GP/commission),
# where it visually overpowers everything else on the card. Shrunk here but
# kept above normal body text size (~1rem) so it still reads as emphasized.
_METRIC_CSS = """
<style>
[data-testid="stMetricValue"] { font-size: 1.35rem; }
[data-testid="stMetricLabel"] { font-size: 0.8rem; }
</style>
"""


def ensure_state():
    st.markdown(_METRIC_CSS, unsafe_allow_html=True)
    if "invoices" not in st.session_state:
        st.session_state["invoices"] = mock_data.seed_invoices()
    if "line_items" not in st.session_state:
        st.session_state["line_items"] = mock_data.seed_line_items()
    if "root_folder" not in st.session_state:
        st.session_state["root_folder"] = ""
    if "bc_imported" not in st.session_state:
        st.session_state["bc_imported"] = False
    if "po_list_imported" not in st.session_state:
        st.session_state["po_list_imported"] = False
    if "role" not in st.session_state:
        st.session_state["role"] = "Finance"
    if "current_salesperson" not in st.session_state:
        st.session_state["current_salesperson"] = mock_data.SALESPEOPLE[0]


def current_role():
    return st.session_state.get("role", "Finance")


def current_salesperson():
    return st.session_state.get("current_salesperson", mock_data.SALESPEOPLE[0])


def require_finance():
    """Call at the top of a Finance-only page, right after ensure_state().
    Stops the page (nothing else on it renders) for a Salesperson role -
    in the real app this is what stands in for "this data never reaches a
    salesperson's machine at all" until the real file-exchange replaces
    this in-session gate with an actual separate process/session per role."""
    if current_role() != "Finance":
        st.warning(
            "This page is Finance only. Switch your role in Settings to see it - "
            "you're currently signed in as a Salesperson.",
            icon="🔒",
        )
        st.stop()


def require_salesperson():
    """Call at the top of a Salesperson-only page - Finance uses the
    Export/Import/Approval pages instead of this one."""
    if current_role() != "Salesperson":
        st.warning(
            "This page is for salespeople reviewing their own invoices. "
            "Switch your role in Settings to 'Salesperson' to see it.",
            icon="🔒",
        )
        st.stop()

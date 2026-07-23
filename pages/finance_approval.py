import streamlit as st

import commission
from state import ensure_state, require_finance

st.set_page_config(page_title="Finance Approval", layout="wide")
ensure_state()
require_finance()

st.title("Finance Approval")
st.caption(
    "Cross-salesperson queue of invoices marked 'Ready for finance'. Approve (commission math "
    "confirmed correct) or kick back with a note (returns to that salesperson's own queue - "
    "Finance doesn't silently edit their numbers). Paid-by-customer and ignore/void are separate "
    "from approval - an invoice can be approved well before the customer has actually paid."
)

invoices = st.session_state["invoices"]
line_items = st.session_state["line_items"]

salespeople = sorted(invoices["salesperson"].unique().tolist())
filter_sp = st.selectbox("Salesperson", options=["All"] + salespeople)

queue = invoices[invoices["sales_status"] == "Ready for finance"]
if filter_sp != "All":
    queue = queue[queue["salesperson"] == filter_sp]

st.subheader(f"Awaiting approval ({len(queue)})")
if not len(queue):
    st.info("Nothing waiting on Finance right now.")

eligible = [no for no, inv in queue.iterrows() if not inv["commission_approved"]]
paid_eligible = [no for no, inv in queue.iterrows() if not inv["paid_by_customer"]]

if eligible or paid_eligible:
    bulk_approve_col, bulk_paid_col = st.columns(2)
    with bulk_approve_col:
        if eligible:
            st.markdown("**Approve multiple**")
            r1, r2, r3 = st.columns(3)
            with r1:
                if st.button(f"☑️ All {len(eligible)}", key="approve_select_all", help="Select all eligible"):
                    for no in eligible:
                        st.session_state[f"bulk_approve_{no}"] = True
                    st.rerun()
            with r2:
                if st.button("☐ Clear", key="approve_clear_selection"):
                    for no in eligible:
                        st.session_state[f"bulk_approve_{no}"] = False
                    st.rerun()
            selected = [no for no in eligible if st.session_state.get(f"bulk_approve_{no}", False)]
            with r3:
                if st.button(f"✅ ({len(selected)})", disabled=not selected, type="primary", key="approve_selected_btn", help="Approve selected"):
                    for no in selected:
                        invoices.loc[no, "commission_approved"] = True
                        invoices.loc[no, "commission_approved_date"] = "2026-07-23"
                        st.session_state[f"bulk_approve_{no}"] = False
                    st.session_state["invoices"] = invoices
                    st.success(f"Approved {len(selected)} invoice(s).")
                    st.rerun()
    with bulk_paid_col:
        if paid_eligible:
            st.markdown("**Mark paid by customer**")
            r1, r2, r3 = st.columns(3)
            with r1:
                if st.button(f"☑️ All {len(paid_eligible)}", key="paid_select_all", help="Select all unpaid"):
                    for no in paid_eligible:
                        st.session_state[f"bulk_paid_{no}"] = True
                    st.rerun()
            with r2:
                if st.button("☐ Clear", key="paid_clear_selection"):
                    for no in paid_eligible:
                        st.session_state[f"bulk_paid_{no}"] = False
                    st.rerun()
            paid_selected = [no for no in paid_eligible if st.session_state.get(f"bulk_paid_{no}", False)]
            with r3:
                if st.button(f"💰 ({len(paid_selected)})", disabled=not paid_selected, type="primary", key="paid_selected_btn", help="Mark selected paid"):
                    for no in paid_selected:
                        invoices.loc[no, "paid_by_customer"] = True
                        st.session_state[f"bulk_paid_{no}"] = False
                    st.session_state["invoices"] = invoices
                    st.success(f"Marked {len(paid_selected)} invoice(s) as paid by customer.")
                    st.rerun()
    st.divider()

for invoice_no, inv in queue.iterrows():
    rollup = commission.invoice_rollup(line_items, invoice_no)
    with st.container(border=True):
        approved_badge = "✅ approved" if inv["commission_approved"] else "⏳ awaiting approval"
        chk_approve_col, chk_paid_col, title_col = st.columns([0.05, 0.05, 0.90])
        with chk_approve_col:
            if not inv["commission_approved"]:
                st.checkbox(
                    f"Select {invoice_no} for bulk approval",
                    key=f"bulk_approve_{invoice_no}",
                    label_visibility="collapsed",
                    help="Select for bulk approval",
                )
        with chk_paid_col:
            if not inv["paid_by_customer"]:
                st.checkbox(
                    f"Select {invoice_no} for bulk paid",
                    key=f"bulk_paid_{invoice_no}",
                    label_visibility="collapsed",
                    help="Select for bulk mark-paid",
                )
        with title_col:
            st.markdown(f"**{invoice_no}** — {inv['customer']} — _{inv['salesperson']}_ — {approved_badge}")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Selling", f"${rollup['selling_total']:,.2f}")
        c2.metric("Cost", f"${rollup['cost_total']:,.2f}")
        c3.metric("GP", f"${rollup['margin_total']:,.2f}")
        c4.metric("Commission", f"${rollup['commission_total']:,.2f}")

        with st.expander("Line items"):
            st.dataframe(
                line_items[line_items["invoice_no"] == invoice_no].drop(columns=["invoice_no"]),
                use_container_width=True, hide_index=True,
            )

        a1, a2 = st.columns([1, 2])
        with a1:
            if not inv["commission_approved"]:
                if st.button("✅ Approve", key=f"approve_{invoice_no}"):
                    invoices.loc[invoice_no, "commission_approved"] = True
                    invoices.loc[invoice_no, "commission_approved_date"] = "2026-07-23"
                    st.session_state["invoices"] = invoices
                    st.rerun()
        with a2:
            note = st.text_input("Kick back with a note", key=f"note_{invoice_no}", placeholder="What needs fixing?")
            if st.button("🔁 Kick back", key=f"kickback_{invoice_no}", disabled=not note):
                invoices.loc[invoice_no, "sales_status"] = "Needs correction"
                invoices.loc[invoice_no, "correction_note"] = note
                invoices.loc[invoice_no, "commission_approved"] = False
                invoices.loc[invoice_no, "commission_approved_date"] = None
                st.session_state["invoices"] = invoices
                st.success(f"Kicked back to {inv['salesperson']}'s queue with your note.")
                st.rerun()

        p1, p2 = st.columns(2)
        with p1:
            paid = st.checkbox("Paid by customer", value=bool(inv["paid_by_customer"]), key=f"paid_{invoice_no}")
        with p2:
            ignored = st.checkbox("Ignore (e.g. voided)", value=bool(inv["ignored"]), key=f"ignore_{invoice_no}")
        if paid != inv["paid_by_customer"] or ignored != inv["ignored"]:
            invoices.loc[invoice_no, "paid_by_customer"] = paid
            invoices.loc[invoice_no, "ignored"] = ignored
            st.session_state["invoices"] = invoices
            st.rerun()

st.divider()
st.subheader("Summary, by salesperson")
totals = commission.summary_totals(invoices, line_items)
m1, m2, m3 = st.columns(3)
m1.metric("Total commission (active)", f"${totals['total_commission']:,.2f}")
m2.metric("Fully payable now", f"${totals['paid_total']:,.2f}")
m3.metric("Pending (approval or payment)", f"${totals['pending_total']:,.2f}")

for sp in salespeople:
    sp_invoices = invoices[invoices["salesperson"] == sp]
    with st.expander(f"{sp} — {len(sp_invoices)} invoice(s)"):
        rows = []
        for no, inv in sp_invoices.iterrows():
            rows.append({
                "invoice_no": no,
                "customer": inv["customer"],
                "status": "ignored" if inv["ignored"] else commission.payout_status(inv),
                "commission": commission.invoice_rollup(line_items, no)["commission_total"],
            })
        st.dataframe(rows, use_container_width=True, hide_index=True)

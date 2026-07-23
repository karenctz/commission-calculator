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
if eligible:
    st.subheader("Approve multiple")
    b1, b2 = st.columns([3, 1])
    with b1:
        selected = st.multiselect(
            "Pick invoices to approve at once",
            options=eligible,
            format_func=lambda no: f"{no} — {queue.loc[no, 'customer']} ({queue.loc[no, 'salesperson']})",
        )
    with b2:
        st.write("")
        st.write("")
        approve_all = st.button(f"Approve ALL {len(eligible)}")
    approve_selected = st.button("Approve selected", disabled=not selected)

    to_approve = eligible if approve_all else (selected if approve_selected else [])
    if to_approve:
        for no in to_approve:
            invoices.loc[no, "commission_approved"] = True
            invoices.loc[no, "commission_approved_date"] = "2026-07-23"
        st.session_state["invoices"] = invoices
        st.success(f"Approved {len(to_approve)} invoice(s).")
        st.rerun()
    st.divider()

for invoice_no, inv in queue.iterrows():
    rollup = commission.invoice_rollup(line_items, invoice_no)
    with st.container(border=True):
        approved_badge = "✅ approved" if inv["commission_approved"] else "⏳ awaiting approval"
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

        p1, p2, p3 = st.columns(3)
        with p1:
            paid = st.checkbox("Paid by customer", value=bool(inv["paid_by_customer"]), key=f"paid_{invoice_no}")
        with p2:
            paid_date = st.text_input("Paid date", value=inv["paid_date"] or "", key=f"paiddate_{invoice_no}")
        with p3:
            ignored = st.checkbox("Ignore (e.g. voided)", value=bool(inv["ignored"]), key=f"ignore_{invoice_no}")
        if paid != inv["paid_by_customer"] or paid_date != (inv["paid_date"] or "") or ignored != inv["ignored"]:
            invoices.loc[invoice_no, "paid_by_customer"] = paid
            invoices.loc[invoice_no, "paid_date"] = paid_date
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

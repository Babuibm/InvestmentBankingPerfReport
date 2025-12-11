
import streamlit as st
from app_core.analytics import run_analytics
from app_core.charts.num_deals_chart import plot_deal_volumes
from app_core.charts.val_deals_chart import plot_deal_value
from app_core.charts.trade_cap_stp_chart import plot_trade_cap_stp
from app_core.charts.settlement_stp_chart import plot_settlement_stp
from app_core.charts.unconfirmed_deals_chart import plot_deals_unconfirmed
from app_core.charts.unsettled_deals_chart import plot_deals_unsettled
from app_core.charts.disputed_margin_calls_chart import plot_disputed_margin_calls


def _show_fig_in_column(col, fig, caption=None):
    """Safe helper: shows fig if not None"""
    if fig is None:
        col.write("_No data available_")
    else:
        if caption:
            col.subheader(caption)
        col.pyplot(fig)

def main():
    st.set_page_config(layout="wide")
    st.title("Investment Banking Performance Analytics Dashboard")

    results = run_analytics()  # uses default cutoff_date_str
    deals_4w = results.get("deals_4w")
    subproduct_metrics = results["subproduct_metrics"]
    df_margincalls = results["df_margincalls"]
    
    fig1 = plot_deal_volumes(subproduct_metrics)
    fig2 = plot_deal_value(subproduct_metrics)
    fig3 = plot_trade_cap_stp(subproduct_metrics)
    fig4 = plot_settlement_stp(subproduct_metrics, deals_4w=deals_4w)
    fig5 = plot_deals_unconfirmed(subproduct_metrics)
    fig6 = plot_deals_unsettled(subproduct_metrics)
    fig_counts, fig_amounts = plot_disputed_margin_calls(df_margincalls)

    # Tabs: first tab is Weekly Highlights (free-text bullets)
    tab_names = ["Weekly Highlights","Summary", "Deal Vol/Value", "STP", "Breaks", "Collateral Disputes"]
    tabs = st.tabs(tab_names)

    # Tab 0: Weekly Highlights (multiline text area for bullets)
    with tabs[0]:
        st.header("Weekly Highlights")
        st.caption("Enter 8–10 bullet points (each bullet on a new line). Use plain text or Markdown.")
        # restore from session_state if present; otherwise default empty
        default_text = st.session_state.get("weekly_highlights", "")
        highlights = st.text_area(
            "Enter highlights (each bullet on new line):",
            value=default_text,
            height=220,
            key="weekly_highlights_input",
            placeholder="- Bullet 1\n- Bullet 2\n- Bullet 3\n"
        )

        # Save to session_state so it persists for the session
        if st.button("Save highlights to session"):
            st.session_state["weekly_highlights"] = highlights
            st.success("Highlights saved for this session.")

        # Provide a quick preview rendered as Markdown (so bullets show nicely)
        if highlights.strip():
            st.subheader("Preview")
            st.markdown(highlights)
            # download button to export as .txt
            st.download_button(
                label="Download highlights (.txt)",
                data=highlights,
                file_name="weekly_highlights.txt",
                mime="text/plain"
            )
        else:
            st.info("No highlights entered yet. Start typing above.")

    # Tab 1: Summary
    with tabs[1]:
        st.header("Weekly Metrics — Summary")

        if not subproduct_metrics or len(subproduct_metrics) == 0:
            st.warning("No summary metrics available.")
        else:
            # product list and default selection
            product_list = sorted(subproduct_metrics.keys())
            default_product = "Bonds" if "Bonds" in product_list else product_list[0]

            selected_product = st.selectbox(
                "Select product subtype",
                product_list,
                index=product_list.index(default_product),
                help="Choose the product subtype to view weekly metrics"
            )

            # get the metrics dataframe for selected product
            metrics_df = subproduct_metrics.get(selected_product)

            if metrics_df is None or metrics_df.empty:
                st.info(f"No metrics for {selected_product}")
            else:
                st.subheader(f"Metrics for: {selected_product}")
                # show as interactive dataframe (allows sorting)
                st.dataframe(metrics_df, height=420, use_container_width=True)

                # Provide CSV download and copy-to-clipboard option
                csv = metrics_df.to_csv(index=True)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"{selected_product}_weekly_metrics.csv",
                    mime="text/csv"
                )
                # Also provide copy button (small UX convenience)
                if st.button("Copy table as CSV to clipboard"):
                    # copying to clipboard via browser requires frontend; provide raw CSV in text area for manual copy
                    st.text_area("CSV (select & copy)", value=csv, height=200)  

        # Tab 1: Deal Vol/Value (fig1, fig2)
    with tabs[2]:
        c1, c2 = st.columns(2)
        _show_fig_in_column(c1, fig1, caption="Deal Volumes (last weeks)")
        _show_fig_in_column(c2, fig2, caption="Deal Values (USD Mn)")

    # Tab 2: STP (fig3, fig4)
    with tabs[3]:
        c1, c2 = st.columns(2)
        _show_fig_in_column(c1, fig3, caption="Trade Capture STP")
        _show_fig_in_column(c2, fig4, caption="Settlement STP")

    # Tab 3: Breaks (fig5, fig6)
    with tabs[4]:
        c1, c2 = st.columns(2)
        _show_fig_in_column(c1, fig5, caption="Breaks: # of Deals not confirmed")
        _show_fig_in_column(c2, fig6, caption="Breaks: # of Deals not settled")

    # Tab 4: Collateral Disputes (fig7, fig8)
    with tabs[5]:
        c1, c2 = st.columns(2)
        _show_fig_in_column(c1, fig_counts, caption="Disputed Margin Calls: counts")
        _show_fig_in_column(c2, fig_amounts, caption="Disputed Margin Calls: amounts")

if __name__ == "__main__":
    main()

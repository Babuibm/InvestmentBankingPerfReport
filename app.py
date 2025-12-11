
import streamlit as st
from app_core.analytics import run_analytics
from app_core.charts.num_deals_chart import plot_deal_volumes
from app_core.charts.val_deals_chart import plot_deal_value
from app_core.charts.trade_cap_stp_chart import plot_trade_cap_stp
from app_core.charts.settlement_stp_chart import plot_settlement_stp
from app_core.charts.unconfirmed_deals_chart import plot_deals_unconfirmed
from app_core.charts.unsettled_deals_chart import plot_deals_unsettled
from app_core.charts.disputed_margin_calls_chart import plot_disputed_margin_calls


def main():
    st.title("Investment Banking Performance Analytics Dashboard")

    results = run_analytics()  # uses default cutoff_date_str
    subproduct_metrics = results["subproduct_metrics"]
    df_margincalls = results["df_margincalls"]

    st.header("Weekly Deal Volumes by Product Group (Last 4 Weeks)")
    fig1 = plot_deal_volumes(subproduct_metrics)
    st.pyplot(fig1)

    st.header("Weekly Deal Value by Product Group (Last 4 Weeks)")
    fig2 = plot_deal_value(subproduct_metrics)
    st.pyplot(fig2)

    st.header("Trade Capture STP % by Product Group (Last 4 Weeks)")
    fig3 = plot_trade_cap_stp(subproduct_metrics)
    st.pyplot(fig3)

    st.header("Settlement STP % by Product Group (Last 4 Weeks)")
    deals_4w = results.get("deals_4w")
    fig4 = plot_settlement_stp(subproduct_metrics, deals_4w=deals_4w)
    st.pyplot(fig4)

    st.header("Weekly volume of unconfirmed deals by Product Group (Last 4 Weeks)")
    fig5 = plot_deals_unconfirmed(subproduct_metrics)
    st.pyplot(fig5)

    st.header("Weekly volume of unsettled deals by Product Group (Last 4 Weeks)")
    fig6 = plot_deals_unsettled(subproduct_metrics)
    st.pyplot(fig6)

    st.header("Disputed Margin Calls – Counts and Amounts")
    fig_counts, fig_amounts = plot_disputed_margin_calls(df_margincalls)
    st.pyplot(fig_counts)
    st.pyplot(fig_amounts)

if __name__ == "__main__":
    main()

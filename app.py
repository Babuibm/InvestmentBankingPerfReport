
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
    
    # Tabs: first tab is Weekly Highlights (free-text bullets)
    tab_names = ["Weekly Highlights", "Deal Vol/Value", "STP", "Breaks", "Collateral Disputes"]
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
        
        # Tab 1: Deal Vol/Value (fig1, fig2)
    with tabs[1]:
        c1, c2 = st.columns(2)
        _show_fig_in_column(c1, fig1, caption="Deal Volumes (last weeks)")
        _show_fig_in_column(c2, fig2, caption="Deal Values (USD Mn)")

    # Tab 2: STP (fig3, fig4)
    with tabs[2]:
        c1, c2 = st.columns(2)
        _show_fig_in_column(c1, fig3, caption="Trade Capture STP")
        _show_fig_in_column(c2, fig4, caption="Settlement STP")

    # Tab 3: Breaks (fig5, fig6)
    with tabs[3]:
        c1, c2 = st.columns(2)
        _show_fig_in_column(c1, fig5, caption="Breaks: counts")
        _show_fig_in_column(c2, fig6, caption="Breaks: amounts")

    # Tab 4: Collateral Disputes (fig7, fig8)
    with tabs[4]:
        c1, c2 = st.columns(2)
        _show_fig_in_column(c1, fig_counts, caption="Disputed Calls: counts")
        _show_fig_in_column(c2, fig_amounts, caption="Disputed Calls: amounts")

if __name__ == "__main__":
    main()

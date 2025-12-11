
import streamlit as st
import numpy as np
from app_core.analytics import run_analytics
from app_core.charts.num_deals_chart import plot_deal_volumes
from app_core.charts.val_deals_chart import plot_deal_value
from app_core.charts.trade_cap_stp_chart import plot_trade_cap_stp
from app_core.charts.settlement_stp_chart import plot_settlement_stp
from app_core.charts.unconfirmed_deals_chart import plot_deals_unconfirmed
from app_core.charts.unsettled_deals_chart import plot_deals_unsettled
from app_core.charts.disputed_margin_calls_chart import plot_disputed_margin_calls
from st_aggrid import AgGrid, GridOptionsBuilder, DataReturnMode, GridUpdateMode
from st_aggrid.shared import JsCode


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
        st.header("Weekly Metrics — Summary - 2025")

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
              st.info("No metrics for selected product")
            else:
              st.subheader(f"Metrics for: {selected_product}")

              latest_col = metrics_df.columns[-1]

              def safe_float(x):
                  try:
                      s = str(x).replace(",", "").replace("%", "").strip()
                      return float(s)
                  except:
                      return float("nan")

              total_deals = safe_float(metrics_df.loc["Number of deals", latest_col])
              deal_value = safe_float(metrics_df.loc["Deal value (in USD mn)", latest_col])
              unconfirmed_pct = safe_float(metrics_df.loc["Unconfirmed deals % change WoW", latest_col])
              stp_pct = safe_float(metrics_df.loc["Trade capture STP %", latest_col])

              k1, k2, k3, k4 = st.columns(4)
              k1.metric("Deals (latest week)", f"{total_deals:,.0f}" if not np.isnan(total_deals) else "-")
              k2.metric("Deal Value (USD Mn)", f"{deal_value:,.0f}" if not np.isnan(deal_value) else "-")
              k3.metric("Unconfirmed deals % WoW", f"{unconfirmed_pct:.1f}%" if not np.isnan(unconfirmed_pct) else "-")
              k4.metric("Trade Cap STP %", f"{stp_pct:.1f}%" if not np.isnan(stp_pct) else "-")

              st.divider()

              # Convert index to a proper column for AgGrid
              df_for_grid = metrics_df.reset_index().rename(columns={"index": "Metric"})
              # optional: re-order columns so Metric is first
              cols = list(df_for_grid.columns)
              cols = [cols[-1]] + cols[:-1] if cols[-1] == 'Metric' else cols
              df_for_grid = df_for_grid[cols]

              # Center align data cells
              cell_style_jscode = JsCode("""
              function(params) {
                  return {
                      'text-align': 'center'
                  }
              }
              """)

              header_template = """
                <div class='ag-cell-label-container' role='presentation' 
                    style='background-color:#E5E7E9; color:#000000; font-weight:bold; text-align:center; padding:6px;'>
                  <span ref='eLabel'></span>
                </div>
              """

              # # Header style (background + bold text)
              # header_style_jscode = JsCode("""
              # function(params) {
              #     return {
              #         'background-color':'#E5E7E9',
              #         'color':'#000000',
              #         'font-weight': 'bold',
              #         'text-align': 'center'
              #     }
              # }
              # """)

              # Build grid options
              gb = GridOptionsBuilder.from_dataframe(df_for_grid)
              gb.configure_default_column(editable=False, resizable=True, filter=True, sortable=True,cellStyle=cell_style_jscode,headerClass="custom-header")
              gb.configure_column("Metric", pinned="left", wrapText=True, autoHeight=True, width=300,headerTooltip="Metric name")
              # enable quick filter and pagination
              gb.configure_grid_options(domLayout='normal')
              gb.configure_selection(selection_mode="single", use_checkbox=False)
              gb.configure_pagination(enabled=True, paginationPageSize=10)
              grid_options = gb.build()
              grid_options["defaultColDef"]["headerComponentParams"] = {
                        "template": header_template }                          

              # Display
              grid_response = AgGrid(
                  df_for_grid,
                  gridOptions=grid_options,
                  height=520,
                  data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
                  update_mode=GridUpdateMode.MODEL_CHANGED,
                  allow_unsafe_jscode=True,
              )

              # export current view to CSV
              csv = grid_response["data"].to_csv(index=False)
              st.download_button("Download visible table as CSV", csv, file_name=f"{selected_product}_metrics_view.csv", mime="text/csv")

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

from pathlib import Path
import pandas as pd
import numpy as np

# this file is in: my-streamlit-app/app_core/analytics.py
BASE_DIR = Path(__file__).resolve().parents[1]  # -> my-streamlit-app/
DATA_DIR = BASE_DIR / "data"

def load_data():
  """
    Load all deal data, compute weekly metrics per Product_subtype,
    and return a dictionary with results usable by app.py and chart modules.
    """

    # ---- Load all CSVs ----
    eq_data_path = DATA_DIR / "df_equity.csv"
    fi_data_path = DATA_DIR / "df_fixedincome.csv"
    repo_data_path = DATA_DIR / "df_repos.csv"
    fxspot_data_path = DATA_DIR / "df_fxspot.csv"
    derfx_data_path = DATA_DIR / "df_derfx.csv"
    dereq_data_path = DATA_DIR / "df_dereq.csv"
    derint_data_path = DATA_DIR / "df_derint.csv"
    dercr_data_path = DATA_DIR / "df_dercr.csv"
    call_data_path = DATA_DIR / "df_margincalls.csv"


    df_equity = pd.read_csv(eq_data_path)
    df_fixedincome = pd.read_csv(fi_data_path)
    df_repos = pd.read_csv(repo_data_path)
    df_fxspot = pd.read_csv(fxspot_data_path)
    df_derfx = pd.read_csv(derfx_data_path)
    df_dereq = pd.read_csv(dereq_data_path)
    df_derint = pd.read_csv(derint_data_path)
    df_dercr = pd.read_csv(dercr_data_path)
    df_margincalls = pd.read_csv(call_data_path)

    return {
        "equity": df_equity,
        "fixedincome": df_fixedincome,
        "repos": df_repos,
        "fxspot": df_fxspot,
        "derfx": df_derfx,
        "dereq": df_dereq,
        "derint": df_derint,
        "dercr": df_dercr,
        "margincalls": df_margincalls,
    }

def run_analytics(cutoff_date_str: str = "2025-12-06"):
    
    raw = load_data()

    df_equity     = raw["equity"]
    df_fixedincome = raw["fixedincome"]
    df_repos      = raw["repos"]
    df_fxspot     = raw["fxspot"]
    df_derfx      = raw["derfx"]
    df_dereq      = raw["dereq"]
    df_derint     = raw["derint"]
    df_dercr      = raw["dercr"]
    df_margincalls = raw["margincalls"]

    # ---- Common deal_value_usd field per product ----
    df_equity["deal_value_usd"] = df_equity["Gross_amount_USD"]
    df_fixedincome["deal_value_usd"] = df_fixedincome["Gross_amount_USD"]
    df_repos["deal_value_usd"] = df_repos["Cash_leg_amt_usd"]
    df_fxspot["deal_value_usd"] = df_fxspot["Base_amount_usd"]
    df_derfx["deal_value_usd"] = df_derfx["Base_amount_usd"]
    df_derint["deal_value_usd"] = df_derint["Notional"]
    df_dercr["deal_value_usd"] = df_dercr["Notional"]

    # ---- Special handling for df_dereq ----
    eq_sub = df_dereq["Product_subtype"].str.strip()

    is_contract = eq_sub.isin(["EqFutures", "EqOptions", "IndFutures", "IndOptions"])
    is_swap = eq_sub.eq("EqSwaps")  # kept for clarity if you extend logic

    df_dereq["deal_value_usd"] = np.where(
        is_contract,
        df_dereq["Contract_amount"],
        df_dereq["Notional"],  # default for swaps or anything else
    )

    # ---- Concatenate all products into a single deals DF ----
    deal_dfs = [
        df_equity,
        df_fixedincome,
        df_repos,
        df_fxspot,
        df_derfx,
        df_dereq,
        df_derint,
        df_dercr,
    ]
    deals = pd.concat(deal_dfs, ignore_index=True)

    # ---- Date handling ----
    cols = [
        "Trade_date",
        "Value_date",
        "Confirmation Date",
        "Settlement_date",
        "Return_leg_date",
        "Expiry_date",
        "Near_leg_date",
        "Far_leg_date",
        "Maturity_date_fut",
        "Maturity_date_fra",
    ]
    deals[cols] = deals[cols].apply(pd.to_datetime, errors="coerce")

    # Week bucket
    deals["week"] = deals["Trade_date"].dt.to_period("W-SUN")

    # Cutoff date for unsettled logic
    cutoff_date = pd.to_datetime(cutoff_date_str)

    deals["_unsettled_bool"] = (
        deals["Settlement_status"].astype(str).str.strip().eq("N")
        & deals["Settlement_date"].lt(cutoff_date)
    )

    # ---- Filter to last 4 weeks ----
    all_weeks = sorted(deals["week"].dropna().unique())
    last_weeks = all_weeks[-4:] if len(all_weeks) >= 4 else all_weeks
    deals_4w = deals[deals["week"].isin(last_weeks)].copy()

    week_order = sorted(deals_4w["week"].unique())
    #week_labels = [str(w) for w in week_order]
    week_labels = [
    f"{w.start_time.strftime('%d-%b')} to {w.end_time.strftime('%d-%b')}"
    for w in week_order
    ]

    subproduct_metrics = {}  # dict: sub_product -> metrics_df

    # ---- Loop over Product_subtype ----
    for sp, df_sp in deals_4w.groupby("Product_subtype"):
        g = df_sp.groupby("week")

        # core weekly metrics
        num_deals = g.size().reindex(week_order, fill_value=0).astype(float)

        deal_value = (
            g["deal_value_usd"]
            .sum(min_count=1)
            .reindex(week_order)
            .fillna(0.0)
        )

        stp_yes = (
            g["Trade_capture_stp"]
            .apply(lambda s: (s == "Y").sum())
            .reindex(week_order, fill_value=0)
        )
        stp_total = g["Trade_capture_stp"].size().reindex(week_order, fill_value=0)
        trade_capture_stp_pct = np.where(
            stp_total > 0,
            stp_yes / stp_total * 100.0,
            np.nan,
        )

        num_unconfirmed = (
            g["Confirmation_flg"]
            .apply(lambda s: (s == "N").sum())
            .reindex(week_order, fill_value=0)
            .astype(float)
        )

        num_unsettled = (
            g["_unsettled_bool"]
            .sum()
            .reindex(week_order, fill_value=0)
            .astype(float)
        )

        # settlement STP by type
        def stp_pct_for_type(df_group, settlement_type_value):
            subset = df_group[df_group["Settlement_type"] == settlement_type_value]
            if subset.empty:
                return np.nan
            total = len(subset)
            stp_yes_local = (subset["Settlement_stp"] == "Y").sum()
            return (stp_yes_local / total) * 100.0

        cash_stp_pct = []
        sec_stp_pct = []
        for w in week_order:
            df_w = df_sp[df_sp["week"] == w]
            cash_stp_pct.append(stp_pct_for_type(df_w, "Cash"))
            sec_stp_pct.append(stp_pct_for_type(df_w, "Physical"))

        cash_stp_pct = pd.Series(cash_stp_pct, index=week_order, dtype="float64")
        sec_stp_pct = pd.Series(sec_stp_pct, index=week_order, dtype="float64")

        # WoW % changes
        num_deals_pct_chg = (
            num_deals.pct_change().replace([np.inf, -np.inf], np.nan) * 100
        )
        deal_value_pct_chg = (
            deal_value.pct_change().replace([np.inf, -np.inf], np.nan) * 100
        )
        num_unconfirmed_pct_chg = (
            num_unconfirmed.pct_change().replace([np.inf, -np.inf], np.nan) * 100
        )
        num_unsettled_pct_chg = (
            num_unsettled.pct_change().replace([np.inf, -np.inf], np.nan) * 100
        )

        # assemble metrics_df for this sub_product
        metrics_df = pd.DataFrame(
            index=[
                "Number of deals",
                "Number of deals % change WoW",
                "Deal value (in USD mn)",
                "Deal value % change WoW",
                "Trade capture STP %",
                "Number of unconfirmed deals",
                "Unconfirmed deals % change WoW",
                "Number of unsettled deals",
                "Unsettled deals % change WoW",
                "Settlement cash STP %",
                "Settlement securities STP %",
            ],
            columns=week_labels,
            dtype="object",
        )

        for i, w in enumerate(week_order):
            col = week_labels[i]
            metrics_df.loc["Number of deals", col] = num_deals.loc[w]
            metrics_df.loc["Number of deals % change WoW", col] = num_deals_pct_chg.loc[
                w
            ]
            metrics_df.loc["Deal value (in USD mn)", col] = deal_value.loc[w]
            metrics_df.loc["Deal value % change WoW", col] = deal_value_pct_chg.loc[w]
            metrics_df.loc["Trade capture STP %", col] = trade_capture_stp_pct[i]
            metrics_df.loc["Number of unconfirmed deals", col] = num_unconfirmed.loc[w]
            metrics_df.loc["Unconfirmed deals % change WoW", col] = (
                num_unconfirmed_pct_chg.loc[w]
            )
            metrics_df.loc["Number of unsettled deals", col] = num_unsettled.loc[w]
            metrics_df.loc["Unsettled deals % change WoW", col] = (
                num_unsettled_pct_chg.loc[w]
            )
            metrics_df.loc["Settlement cash STP %", col] = cash_stp_pct.loc[w]
            metrics_df.loc["Settlement securities STP %", col] = sec_stp_pct.loc[w]

        # format: counts as integers
        count_rows = [
            "Number of deals",
            "Number of unconfirmed deals",
            "Number of unsettled deals",
        ]
        for row in count_rows:
            metrics_df.loc[row] = metrics_df.loc[row].apply(
                lambda x: "" if pd.isna(x) else f"{int(round(float(x))):d}"
            )

        # percentages rows
        pct_rows = [
            "Trade capture STP %",
            "Settlement cash STP %",
            "Settlement securities STP %",
            "Number of deals % change WoW",
            "Deal value % change WoW",
            "Unconfirmed deals % change WoW",
            "Unsettled deals % change WoW",
        ]
        for row in pct_rows:
            metrics_df.loc[row] = metrics_df.loc[row].apply(
                lambda x: "" if pd.isna(x) or x == "" else f"{float(x):.1f}%"
            )

        # deal value convert to USD mn (no decimals)
        for col in metrics_df.columns:
            val = metrics_df.at["Deal value (in USD mn)", col]
            if val == "" or pd.isna(val):
                continue
            val_mn = float(val) / 1_000_000
            metrics_df.at["Deal value (in USD mn)", col] = f"{val_mn:,.0f}"

        subproduct_metrics[sp] = metrics_df

    # rules for cash-only / physical-only products
    physical_only_products = {
        "Cash Equity",
        "Bonds",
        "NCD",
        "Secured Notes",
        "Repo",
        "ReverseRepo",
        "Forex-Spot",
        "FxForwards",
        "FxFutures",
    }

    cash_only_products = {
        "FxSwaps",
        "IntRateSwaps",
        "IntRateFRA",
    }

    for sub_product, df in subproduct_metrics.items():
        if sub_product in cash_only_products:
            df.loc["Settlement securities STP %"] = "NA"

        if sub_product in physical_only_products:
            df.loc["Settlement cash STP %"] = "NA"

        df.loc["Settlement cash STP %"] = df.loc["Settlement cash STP %"].apply(
            lambda x: "NA" if (pd.isna(x) or x == "") else x
        )
        df.loc["Settlement securities STP %"] = df.loc[
            "Settlement securities STP %"
        ].apply(lambda x: "NA" if (pd.isna(x) or x == "") else x)

    wow_pct_rows = {
        "Trade capture STP %",
        "Number of deals % change WoW",
        "Deal value % change WoW",
        "Unconfirmed deals % change WoW",
        "Unsettled deals % change WoW",
    }
    for sub_product, df in subproduct_metrics.items():
        for row in wow_pct_rows:
            if row in df.index:
                df.loc[row] = df.loc[row].apply(
                    lambda x: "NA" if (pd.isna(x) or x == "" or x == "nan") else x
                )

    # return all key outputs for app.py / charts
    return {
        "deals": deals,
        "deals_4w": deals_4w,
        "week_order": week_order,
        "week_labels": week_labels,
        "subproduct_metrics": subproduct_metrics,
        "df_margincalls": df_margincalls,
    }

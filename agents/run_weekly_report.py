from data_quality_agent import run_data_quality
from analytics_agent import run_analytics_and_notify
from chart_agent import run_charts_and_interpret
from config import DATA_DIR

def run_all(file_list):
    # step 1: data quality
    counts_by_subproduct, details = run_data_quality(file_list)
    # step 2: analytics
    results = run_analytics_and_notify()
    # step 3: charts and interpretation
    highlights, images = run_charts_and_interpret(results)
    # optionally persist highlights to a file used by Streamlit for Weekly Highlights textbox
    with open("data/weekly_highlights.txt", "w", encoding="utf8") as f:
        f.write(highlights)
    return True

if __name__ == "__main__":
    # list of expected files in landing area
    file_list = [
        "df_equity.csv", "df_fixedincome.csv", "df_repos.csv", "df_fxspot.csv",
        "df_derfx.csv", "df_dereq.csv", "df_derint.csv", "df_dercr.csv","df_margincalls.csv"
    ]
    run_all(file_list)

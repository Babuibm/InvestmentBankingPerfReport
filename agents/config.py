from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[1]  # project root
#DATA_LANDING = ROOT / "data" / "landing"    # where uploaded CSVs go
DATA_DIR = ROOT / "data"              # where analytics reads from
OUT_DIR = ROOT / "reports"
OUT_DIR.mkdir(exist_ok=True, parents=True)

# Email settings (read these from environment or CI secrets)
EMAIL_FROM = os.environ.get("REPORT_EMAIL_FROM")
EMAIL_TO = os.environ.get("REPORT_EMAIL_TO", "").split(",")  # comma-separated recipients
SMTP_HOST = os.environ.get("SMTP_HOST")
SMTP_PORT = int(os.environ.get("SMTP_PORT"))
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASS = os.environ.get("SMTP_PASS")

STREAMLIT_URL = os.environ.get("STREAMLIT_URL", "https://investmentbankingperfreport.streamlit.app/")

# LLM config (LangChain model key or local runner)
LLM_TYPE = os.environ.get("LLM_TYPE", "gemma")  # your choice

import pandas as pd
import numpy as np
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from config import DATA_ANALYTICS, OUT_DIR, EMAIL_FROM, EMAIL_TO, SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS

# Example: you will supply these
MANDATORY_FIELDS = {
    "df_equity.csv":["Trade_date", "Gross_amount_USD", "Product_subtype"],
    "df_fixedincome.csv":["Trade_date", "Gross_amount_USD", "Product_subtype"],
    "df_repos.csv":["Trade_date", "Cash_leg_amt_usd", "Product_subtype"],
    "df_fxspot.csv":["Trade_date", "Base_amount_usd", "Product_subtype"],
    "df_derfx.csv":["Trade_date", "Base_amount_usd", "Product_subtype"],
    "df_dereq.csv":["Trade_date", "Confirmation_flg","Product_subtype"],
    "df_derint.csv":["Trade_date", "Notional", "Product_subtype"],
    "df_dercr.csv":["Trade_date", "Notional", "Product_subtype"],
    "df_margincalls.csv":["Call_amount","Call_result","Call_date"]

}
VALID_VALUE_RULES = {
    # column -> allowed values set (strings)
    "Trade_capture_stp": {"Y", "N"},
    "Confirmation_flg": {"Y", "N"},
    "Settlement_stp": {"Y", "N"},
    "Settlement_status": {"Y", "N"},
}
NO_NEGATIVE_COLS = {
    "df_equity.csv":"Gross_amount_USD",
    "df_fixedincome.csv":"Gross_amount_USD",
    "df_repos.csv": "Cash_leg_amt_usd",
    "df_fxspot.csv":"Base_amount_usd",
    "df_derfx.csv":"Base_amount_usd",
    "df_derint.csv":"Notional",
    "df_dercr.csv":"Notional"
}

def send_email(subject, body_text):
    msg = MIMEMultipart()
    msg["From"] = EMAIL_FROM
    msg["To"] = ",".join(EMAIL_TO)
    msg["Subject"] = subject
    msg.attach(MIMEText(body_text, "plain"))
    s = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
    s.starttls()
    s.login(SMTP_USER, SMTP_PASS)
    s.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
    s.quit()

def run_data_quality(file_list):
    findings = []
    counts_by_subproduct = {}
    details_problem_rows = []
    for fname in file_list:
        path = sorted((DATA_DIR).glob("*.csv"))
        if not path.exists():
            findings.append(f"File missing: {fname}")
            continue
        df = pd.read_csv(path)
        # standard clean: trim strings
        df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
        # mandatory fields
        missing_mask = df[MANDATORY_FIELDS.get(fname, [])].isna().any(axis=1) if MANDATORY_FIELDS.get(fname) else pd.Series(False, index=df.index)
        # invalid values
        invalid_mask = pd.Series(False, index=df.index)
        for col, allowed in VALID_VALUE_RULES.items():
            if col in df.columns:
                invalid_mask = invalid_mask | (~df[col].astype(str).isin(allowed))
        # negative
        neg_mask = pd.Series(False, index=df.index)
        for c in NO_NEGATIVE_COLS:
            if c in df.columns:
                neg_mask = neg_mask | (pd.to_numeric(df[c], errors='coerce') < 0)
        # produce per-file report
        total = len(df)
        ok_mask = ~(missing_mask | invalid_mask | neg_mask)
        accepted = df[ok_mask].copy()
        rejected = df[~ok_mask].copy()
        # persist accepted file into analytics location (overwrite)
        accepted.to_csv(DATA_ANALYTICS / fname, index=False)
        counts_by_subproduct[fname] = len(accepted)
        if not rejected.empty:
            details_problem_rows.append((fname, rejected.head(50)))  # include top 50 problem rows
        findings.append(f"{fname}: total={total}, accepted={len(accepted)}, rejected={len(rejected)}")
    # build email body
    body = "Data Quality Findings\n\n" + "\n".join(findings) + "\n\nDetails for problem rows:\n"
    for fname, dfp in details_problem_rows:
        body += f"\n\nFile: {fname}\n" + dfp.to_csv(index=False)
    # send email
    send_email("Weekly Report - Data Quality Findings", body)
    return counts_by_subproduct, details_problem_rows

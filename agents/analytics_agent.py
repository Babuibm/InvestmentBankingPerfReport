import traceback
from config import OUT_DIR, EMAIL_FROM, EMAIL_TO, SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS
from config import DATA_DIR
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

def send_email(subject, body_text):
    # same as prior; factor into a shared utility if you want
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

def run_analytics_and_notify():
    try:
        # import your run_analytics function (it reads CSVs from DATA_ANALYTICS)
        from app_core.analytics import run_analytics
        results = run_analytics()
        # quick validation
        if "subproduct_metrics" not in results:
            raise RuntimeError("run_analytics did not return subproduct_metrics")
        # send success email
        body = "Analytics completed successfully.\n\nKeys returned:\n" + "\n".join(results.keys())
        send_email("Weekly Report - Analytics Completed", body)
        return results
    except Exception as e:
        tb = traceback.format_exc()
        send_email("Weekly Report - Analytics FAILED", f"Analytics failed with error:\n\n{tb}")
        raise

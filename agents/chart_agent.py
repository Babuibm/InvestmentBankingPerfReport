import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
from config import OUT_DIR, EMAIL_FROM, EMAIL_TO, SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import smtplib
from typing import Dict
from pathlib import Path

# LLM: use LangChain wrapper. Example using a generic LLM interface placeholder.
# Replace this with your LangChain/Gemma client setup.
from langchain import LLMChain, PromptTemplate
#from langchain_community.llms import HuggingFacePipeline
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from app_core.llm.gemma_llm import create_gemma_llm
#from langchain.llms import OpenAI  # replace with your Gemma wrapper if available

def send_email_with_images(subject, body_text, image_paths):
    msg = MIMEMultipart()
    msg["From"] = EMAIL_FROM
    msg["To"] = ",".join(EMAIL_TO)
    msg["Subject"] = subject
    # text first (URL message)
    msg.attach(MIMEText(body_text, "plain"))
    # attach images in order
    for p in image_paths:
        with open(p, "rb") as f:
            img = MIMEImage(f.read())
            img.add_header("Content-Disposition", "attachment", filename=Path(p).name)
            msg.attach(img)
    s = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
    s.starttls()
    s.login(SMTP_USER, SMTP_PASS)
    s.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
    s.quit()

def classify_change(pct_change: float) -> str:
    """Return High/Medium/Low rule-based classification"""
    if np.isnan(pct_change):
        return "No change"
    a = abs(pct_change)
    if a >= 50:
        return "High"
    if a >= 15:
        return "Medium"
    return "Low"

def run_charts_and_interpret(results: Dict):
    # results from analytics_agent (contains subproduct_metrics and perhaps deals_4w)
    subproduct_metrics = results["subproduct_metrics"]
    # build each chart by calling your chart functions and saving as PNG
    # Example for chart1
    from app_core.charts.num_deals_chart import plot_deal_volumes
    from app_core.charts.val_deals_chart import plot_deal_value
    from app_core.charts.trade_cap_stp_chart import plot_trade_cap_stp
    from app_core.charts.settlement_stp_chart import plot_settlement_stp
    from app_core.charts.unconfirmed_deals_chart import plot_deals_unconfirmed
    from app_core.charts.unsettled_deals_chart import plot_deals_unsettled
    from app_core.charts.disputed_margin_calls_chart import plot_disputed_margin_calls


    images = []
    # call each plot and save
    fig1 = plot_deal_volumes(subproduct_metrics)
    p1 = OUT_DIR / "chart1_volumes.png"; fig1.savefig(p1, bbox_inches="tight"); images.append(str(p1))
    fig2 = plot_deal_value(subproduct_metrics)
    p2 = OUT_DIR / "chart2_values.png"; fig2.savefig(p2, bbox_inches="tight"); images.append(str(p2))
    fig3 = plot_trade_cap_stp(subproduct_metrics)
    p3 = OUT_DIR / "chart3_tradecap.png"; fig3.savefig(p3, bbox_inches="tight"); images.append(str(p3))
    fig4 = plot_settlement_stp(subproduct_metrics, deals_4w=deals_4w)
    p4 = OUT_DIR / "chart4_settlement.png"; fig4.savefig(p4, bbox_inches="tight"); images.append(str(p4))
    fig5 = plot_deals_unconfirmed(subproduct_metrics)
    p5 = OUT_DIR / "chart5_breaks_counts.png"; fig5.savefig(p5, bbox_inches="tight"); images.append(str(p5))
    fig6 = plot_deals_unsettled(subproduct_metrics)
    p6 = OUT_DIR / "chart6_breaks_amounts.png"; fig6.savefig(p6, bbox_inches="tight"); images.append(str(p6))
    fig_counts, fig_amounts = plot_disputed_margin_calls(df_margincalls)
    p7 = OUT_DIR / "chart7_disc_counts.png"; fig7.savefig(p7, bbox_inches="tight"); images.append(str(p7))
    p8 = OUT_DIR / "chart8_disc_amounts.png"; fig8.savefig(p8, bbox_inches="tight"); images.append(str(p8))

    # Interpretation: for each chart compute a key metric (example: % change last two weeks)

    llm = create_gemma_llm()

    interpretations = []  # list of (name, text)

    chart_items = [
        ("Deal Volumes", p1),
        ("Deal Values", p2),
        ("Trade Capture STP", p3),
        ("Settlement STP", p4),
        ("Unconfirmed deals (counts)", p5),
        ("Unsettled deals (counts)", p6),
        ("Disputed Calls (counts)", p7),
        ("Disputed Amounts", p8),
    ]

    for name, fig_path in chart_items:

        prompt = f"""
    You are analyzing weekly metrics for '{name}'.

    Provide:
    1. One-line summary of whether the % change is High, Medium, or Low.
    2. Two bullet reasons (insights).
    3. One short action recommendation.

    Format EXACTLY like this:

    - Classification: High/Medium/Low
    - Reasons:
      • Reason 1
      • Reason 2
    - Action: <short actionable suggestion>
    """

        llm_text = llm(prompt).strip()
        interpretations.append((name, llm_text))

    # Build Weekly highlights text from interpretations (concatenate)
    highlights = "Weekly Highlights (auto-generated)\n\n"
    for name, txt in interpretations:
        highlights += f"### {name}\n{txt}\n\n"

    # Now prepare and send email: first short message with URL (configurable), then attach images
    web_url = os.environ.get("STREAMLIT_URL", "https://investmentbankingperfreport.streamlit.app/")
    body_intro = f"The weekly report is available here: {web_url}\n\nAuto-generated highlights below:\n\n" + highlights
    # For email order per your requirement: first message (URL), then Weekly highlights image, then Summary image
    # To render the Weekly Highlights text as an image, you can use PIL to write text to image:
    from PIL import Image, ImageDraw, ImageFont
    def text_to_image(text, out_path):
        # very simple multi-line renderer
        font = ImageFont.load_default()
        lines = text.splitlines()
        width = 1200
        line_height = 16
        height = max(600, line_height * (len(lines) + 2))
        im = Image.new("RGB", (width, height), color="white")
        draw = ImageDraw.Draw(im)
        y = 10
        for line in lines:
            draw.text((10, y), line, fill="black", font=font)
            y += line_height
        im.save(out_path)

    highlights_png = OUT_DIR / "weekly_highlights.png"
    text_to_image(highlights, highlights_png)

    # Create a 'Summary' pic: render the summary DataFrame to image (pandas -> HTML -> image)
    # A simple approach: convert metrics_df to image using dfi (pandas) or mpl table. Here's a simple matplotlib table:
    import matplotlib.pyplot as plt
    sample_product = next(iter(subproduct_metrics.keys()))
    sample_df = subproduct_metrics[sample_product]
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.axis("off")
    tbl = ax.table(cellText=sample_df.values, colLabels=sample_df.columns, rowLabels=sample_df.index, loc="center")
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(10)
    tbl.scale(1, 1.5)
    summary_png = OUT_DIR / "summary_table.png"
    fig.savefig(summary_png, bbox_inches="tight")
    plt.close(fig)

    # Email order: body (URL), then weekly highlights image, then summary table image
    send_email_with_images("Weekly Report: Automated", f"Weekly report URL: {web_url}\n\nSee attached images", [str(highlights_png), str(summary_png)])

    # return highlights text, images list
    return highlights, images

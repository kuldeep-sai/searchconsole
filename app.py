import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from openai import OpenAI
import pandas as pd
import json
import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

# ============ CONFIG ============
SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
SITE_URL = "https://www.example.com/"   # Replace with your property
OPENAI_API_KEY = "your_openai_api_key"

# Initialize OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

# ============ FUNCTIONS ============
def get_gsc_service(creds_json):
    """Authenticate and return GSC service."""
    creds = service_account.Credentials.from_service_account_info(creds_json, scopes=SCOPES)
    return build("searchconsole", "v1", credentials=creds)

def fetch_index_coverage(service):
    """Fetch index coverage issues (demo using inspection API)."""
    try:
        request = service.urlInspection().index().inspect(
            body={
                "inspectionUrl": SITE_URL,
                "siteUrl": SITE_URL
            }
        )
        return request.execute()
    except Exception as e:
        return {"error": str(e)}

def fetch_cwv(service):
    """Fetch Core Web Vitals (placeholder via search analytics)."""
    try:
        request = service.searchanalytics().query(
            siteUrl=SITE_URL,
            body={
                "startDate": "2025-08-01",
                "endDate": "2025-09-01",
                "dimensions": ["page"],
                "rowLimit": 10
            }
        )
        return request.execute()
    except Exception as e:
        return {"error": str(e)}

def fetch_mobile_usability(service):
    """Fetch Mobile Usability issues (demo)."""
    try:
        request = service.urlTestingTools().mobileFriendlyTest().run(
            body={"url": SITE_URL}
        )
        return request.execute()
    except Exception as e:
        return {"error": str(e)}

def analyze_with_ai(category, error_data):
    """Send GSC errors to GPT for SEO solutioning with priority scoring."""
    prompt = f"""
    You are an SEO expert. Analyze this {category} report from Google Search Console.
    Provide:
    1. Root causes
    2. Actionable SEO solutions (step by step)
    3. Priority level (High / Medium / Low with reasoning)
    4. Best practices for long-term fix

    Report Data:
    {error_data}
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": "You are an SEO consultant."},
                  {"role": "user", "content": prompt}],
        temperature=0.4
    )
    return response.choices[0].message.content

def generate_summary_with_ai(results):
    """Generate Executive Summary from AI based on all sections."""
    prompt = f"""
    Create an SEO Executive Summary for this site audit. 
    Summarize in 3 parts:
    1. Overall SEO Health (positive + negative highlights)
    2. Key Priority Issues
    3. Recommended Roadmap (short term vs long term)

    Results:
    {results}
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": "You are an SEO consultant."},
                  {"role": "user", "content": prompt}],
        temperature=0.5
    )
    return response.choices[0].message.content

def generate_pdf(site_url, results, summary_text):
    """Generate a professional PDF SEO Audit Report with executive summary."""
    filename = "SEO_Audit_Report.pdf"
    doc = SimpleDocTemplate(filename, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # Cover Page
    story.append(Paragraph(f"<b>SEO Audit Report</b>", styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Site: {site_url}", styles["Normal"]))
    story.append(Paragraph(f"Date: {datetime.date.today().strftime('%d-%m-%Y')}", styles["Normal"]))
    story.append(Spacer(1, 24))

    # Executive Summary
    story.append(Paragraph("<b>📑 Executive Summary</b>", styles["Heading2"]))
    story.append(Paragraph(summary_text, styles["Normal"]))
    story.append(Spacer(1, 24))

    # Section: Index Coverage
    story.append(Paragraph("<b>📊 Index Coverage</b>", styles["Heading2"]))
    story.append(Paragraph("Raw Data:", styles["Heading3"]))
    story.append(Paragraph(str(results['index_coverage']["raw"]), styles["Code"]))
    story.append(Spacer(1, 6))
    story.append(Paragraph("AI SEO Recommendations:", styles["Heading3"]))
    story.append(Paragraph(results['index_coverage']["ai_solution"], styles["Normal"]))
    story.append(Spacer(1, 12))

    # Section: Core Web Vitals
    story.append(Paragraph("<b>⚡ Core Web Vitals</b>", styles["Heading2"]))
    story.append(Paragraph("Raw Data:", styles["Heading3"]))
    story.append(Paragraph(str(results['core_web_vitals']["raw"]), styles["Code"]))
    story.append(Spacer(1, 6))
    story.append(Paragraph("AI SEO Recommendations:", styles["Heading3"]))
    story.append(Paragraph(results['core_web_vitals']["ai_solution"], styles["Normal"]))
    story.append(Spacer(1, 12))

    # Section: Mobile Usability
    story.append(Paragraph("<b>📱 Mobile Usability</b>", styles["Heading2"]))
    story.append(Paragraph("Raw Data:", styles["Heading3"]))
    story.append(Paragraph(str(results['mobile_usability']["raw"]), styles["Code"]))
    story.append(Spacer(1, 6))
    story.append(Paragraph("AI SEO Recommendations:", styles["Heading3"]))
    story.append(Paragraph(results['mobile_usability']["ai_solution"], styles["Normal"]))
    story.append(Spacer(1, 12))

    # Build PDF
    doc.build(story)
    return filename

# ============ STREAMLIT APP ============
st.title("🔍 AI SEO Agent for Google Search Console")

uploaded_file = st.file_uploader("Upload your Google Service Account JSON", type="json")

if uploaded_file:
    creds_json = uploaded_file.read().decode("utf-8")
    creds_dict = json.loads(creds_json)

    try:
        # Authenticate
        service = get_gsc_service(creds_dict)
        st.success("✅ Connected to Google Search Console")

        results = {}

        # -------- INDEX COVERAGE --------
        st.subheader("📊 Index Coverage Report")
        index_data = fetch_index_coverage(service)
        st.json(index_data)
        index_ai = analyze_with_ai("Index Coverage", index_data)
        st.write(index_ai)
        results["index_coverage"] = {"raw": index_data, "ai_solution": index_ai}

        # -------- CORE WEB VITALS --------
        st.subheader("⚡ Core Web Vitals Report")
        cwv_data = fetch_cwv(service)
        st.json(cwv_data)
        cwv_ai = analyze_with_ai("Core Web Vitals", cwv_data)
        st.write(cwv_ai)
        results["core_web_vitals"] = {"raw": cwv_data, "ai_solution": cwv_ai}

        # -------- MOBILE USABILITY --------
        st.subheader("📱 Mobile Usability Report")
        mobile_data = fetch_mobile_usability(service)
        st.json(mobile_data)
        mobile_ai = analyze_with_ai("Mobile Usability", mobile_data)
        st.write(mobile_ai)
        results["mobile_usability"] = {"raw": mobile_data, "ai_solution": mobile_ai}

        # -------- EXECUTIVE SUMMARY --------
        st.subheader("📝 Executive Summary")
        summary_text = generate_summary_with_ai(results)
        st.write(summary_text)

        # -------- EXPORT TO PDF --------
        if st.button("📥 Generate PDF SEO Audit"):
            pdf_file = generate_pdf(SITE_URL, results, summary_text)
            with open(pdf_file, "rb") as f:
                st.download_button(
                    label="Download SEO Audit PDF",
                    data=f,
                    file_name=pdf_file,
                    mime="application/pdf"
                )

    except Exception as e:
        st.error(f"⚠️ Error: {e}")

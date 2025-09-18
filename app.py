import streamlit as st
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from openai import OpenAI

# ============ CONFIG ============
SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
SITE_URL = "https://www.example.com/"   # Replace with your site
client = OpenAI(api_key=st.secrets["openai"]["api_key"])

# ============ FUNCTIONS ============
def get_gsc_service():
    """Authenticate and return GSC service."""
    creds = service_account.Credentials.from_service_account_info(
        st.secrets["google_service_account"],
        scopes=SCOPES
    )
    return build("searchconsole", "v1", credentials=creds)

def fetch_index_coverage(service):
    """Fetch coverage inspection for home URL (example)."""
    request = service.urlInspection().index().inspect(
        body={"inspectionUrl": SITE_URL, "siteUrl": SITE_URL}
    )
    return request.execute()

def analyze_with_ai(error_data):
    """Send GSC errors to GPT for SEO solutioning."""
    prompt = f"""
    You are an SEO consultant. Analyze this Google Search Console error data and suggest
    root causes + actionable SEO solutions in clear steps. Keep it relevant to Indian websites.

    Error Data:
    {error_data}
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an SEO consultant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.4
    )
    return response.choices[0].message.content

# ============ STREAMLIT UI ============
st.title("🔍 AI SEO Agent for Search Console Errors")

try:
    service = get_gsc_service()
    st.success("✅ Connected to Google Search Console")

    st.subheader("📊 Index Coverage Report")
    data = fetch_index_coverage(service)
    st.json(data)

    st.subheader("🤖 AI SEO Recommendations")
    ai_output = analyze_with_ai(data)
    st.write(ai_output)

    if st.button("📥 Export to CSV"):
        df = pd.DataFrame([{"error_data": data, "ai_solution": ai_output}])
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, "seo_solutions.csv", "text/csv")

except Exception as e:
    st.error(f"⚠️ Error: {e}")

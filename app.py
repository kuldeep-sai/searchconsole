import streamlit as st
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build

# -----------------------------
# AUTHENTICATION
# -----------------------------
SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]

credentials = service_account.Credentials.from_service_account_info(
    st.secrets["google_service_account"],
    scopes=SCOPES,
)

service = build("searchconsole", "v1", credentials=credentials)

# -----------------------------
# WEBSITE PROPERTY
# -----------------------------
SITE_URL = "sc-domain:naukri.com"   # change if different

# -----------------------------
# STREAMLIT UI
# -----------------------------
st.title("SEO Search Console Dashboard")

if st.button("Fetch Search Console Data"):

    request = {
        "startDate": "2025-01-01",
        "endDate": "2025-03-01",
        "dimensions": ["query"],
        "rowLimit": 1000
    }

    try:
        response = service.searchanalytics().query(
            siteUrl=SITE_URL,
            body=request
        ).execute()

        rows = response.get("rows", [])

        data = []
        for row in rows:
            data.append({
                "query": row["keys"][0],
                "clicks": row["clicks"],
                "impressions": row["impressions"],
                "ctr": row["ctr"],
                "position": row["position"]
            })

        df = pd.DataFrame(data)

        st.success("✅ Data Loaded Successfully")
        st.dataframe(df)

    except Exception as e:
        st.error(f"Error: {e}")

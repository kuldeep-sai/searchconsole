import streamlit as st
import pandas as pd
import plotly.express as px
from google.oauth2 import service_account
from googleapiclient.discovery import build

st.title("AI SEO Intelligence Dashboard")

SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]

SITE_URL = "https://www.naukri.com"

credentials = service_account.Credentials.from_service_account_info(
    st.secrets["google_service_account"],
    scopes=SCOPES
)

service = build("searchconsole", "v1", credentials=credentials)

request = {
    "startDate": "2025-01-01",
    "endDate": "2025-03-01",
    "dimensions": ["query","page"],
    "rowLimit": 25000
}

response = service.searchanalytics().query(
    siteUrl=SITE_URL, body=request).execute()

rows = response.get("rows", [])

data = []

for row in rows:
    data.append({
        "query": row["keys"][0],
        "page": row["keys"][1],
        "clicks": row["clicks"],
        "impressions": row["impressions"],
        "ctr": row["ctr"],
        "position": row["position"]
    })

df = pd.DataFrame(data)

# Overview metrics
st.subheader("SEO Overview")

c1,c2,c3,c4 = st.columns(4)

c1.metric("Clicks", int(df["clicks"].sum()))
c2.metric("Impressions", int(df["impressions"].sum()))
c3.metric("CTR", round(df["ctr"].mean()*100,2))
c4.metric("Avg Position", round(df["position"].mean(),1))

# Top keywords
st.subheader("Top Keywords")

top_kw = df.groupby("query").sum().sort_values("clicks",ascending=False).head(20)

fig = px.bar(top_kw, x=top_kw.index, y="clicks")

st.plotly_chart(fig,use_container_width=True)

# Opportunity keywords
st.subheader("SEO Opportunity Keywords")

opp = df[
    (df["position"] > 8) &
    (df["position"] < 20) &
    (df["impressions"] > 500)
]

st.dataframe(opp.sort_values("impressions",ascending=False).head(20))

# CTR leakage
st.subheader("CTR Leakage")

leak = df[
    (df["impressions"] > 1000) &
    (df["ctr"] < 0.02) &
    (df["position"] < 10)
]

st.dataframe(leak.sort_values("impressions",ascending=False).head(20))

# Page opportunities
st.subheader("Top Pages")

pages = df.groupby("page").sum().sort_values("impressions",ascending=False).head(20)

fig2 = px.bar(pages, x=pages.index, y="impressions")

st.plotly_chart(fig2,use_container_width=True)

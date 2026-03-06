import streamlit as st
import pandas as pd
import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build

st.set_page_config(layout="wide")

st.title("SEO Intelligence Dashboard v2")

SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]

credentials = service_account.Credentials.from_service_account_info(
    st.secrets["google_service_account"],
    scopes=SCOPES,
)

service = build("searchconsole", "v1", credentials=credentials)

site_url = "https://www.naukri.com"

# ------------------------
# SIDEBAR FILTERS
# ------------------------

st.sidebar.header("Filters")

end_date = datetime.date.today()
start_date = end_date - datetime.timedelta(days=30)

prev_start = start_date - datetime.timedelta(days=30)
prev_end = start_date - datetime.timedelta(days=1)

device_filter = st.sidebar.selectbox(
    "Device",
    ["All","DESKTOP","MOBILE","TABLET"]
)

brand_keywords = ["naukri","naukri.com","naukri jobs","naukri login"]

# ------------------------
# FUNCTION TO FETCH DATA
# ------------------------

def fetch_data(start,end):

    request = {
        "startDate": str(start),
        "endDate": str(end),
        "dimensions": ["query","page","device","date"],
        "rowLimit": 25000
    }

    response = service.searchanalytics().query(
        siteUrl=site_url,
        body=request
    ).execute()

    rows = response.get("rows", [])

    data = []

    for row in rows:
        data.append({
            "keyword": row["keys"][0],
            "page": row["keys"][1],
            "device": row["keys"][2],
            "date": row["keys"][3],
            "clicks": row["clicks"],
            "impressions": row["impressions"],
            "ctr": row["ctr"],
            "position": row["position"]
        })

    return pd.DataFrame(data)

# ------------------------
# FETCH DATA
# ------------------------

current_df = fetch_data(start_date,end_date)
prev_df = fetch_data(prev_start,prev_end)

if current_df.empty:
    st.warning("No data found")
    st.stop()

current_df["date"] = pd.to_datetime(current_df["date"])

# ------------------------
# DEVICE FILTER
# ------------------------

if device_filter != "All":
    current_df = current_df[current_df["device"]==device_filter]

# ------------------------
# BRAND CLASSIFICATION
# ------------------------

def classify_keyword(k):

    for b in brand_keywords:
        if b in k.lower():
            return "Brand"

    return "Non Brand"

current_df["keyword_type"] = current_df["keyword"].apply(classify_keyword)

# ------------------------
# KPI METRICS
# ------------------------

st.header("SEO Performance Overview")

col1,col2,col3,col4 = st.columns(4)

col1.metric("Clicks",int(current_df["clicks"].sum()))
col2.metric("Impressions",int(current_df["impressions"].sum()))
col3.metric("Avg CTR",round(current_df["ctr"].mean()*100,2))
col4.metric("Avg Position",round(current_df["position"].mean(),2))

# ------------------------
# BRAND VS NON BRAND
# ------------------------

st.header("Brand vs Non Brand Traffic")

brand_data = current_df.groupby("keyword_type").agg({
    "clicks":"sum",
    "impressions":"sum"
}).reset_index()

st.bar_chart(brand_data.set_index("keyword_type"))

# ------------------------
# TOP KEYWORDS
# ------------------------

st.header("Top Keywords")

top_kw = current_df.groupby("keyword").agg({
    "clicks":"sum",
    "impressions":"sum",
    "position":"mean"
}).sort_values("clicks",ascending=False).head(20)

st.dataframe(top_kw)

# ------------------------
# QUICK WIN KEYWORDS
# ------------------------

st.header("Quick Win Keywords (Position 8-20)")

quick = current_df[
(current_df["position"]>=8) &
(current_df["position"]<=20) &
(current_df["impressions"]>1000)
]

quick_kw = quick.groupby("keyword").agg({
    "clicks":"sum",
    "impressions":"sum",
    "position":"mean"
}).sort_values("impressions",ascending=False).head(20)

st.dataframe(quick_kw)

# ------------------------
# CTR OPPORTUNITIES
# ------------------------

st.header("CTR Optimization Opportunities")

ctr_df = current_df[
(current_df["position"]<=5) &
(current_df["ctr"]<0.03)
]

ctr_kw = ctr_df.groupby("keyword").agg({
    "clicks":"sum",
    "impressions":"sum",
    "ctr":"mean",
    "position":"mean"
}).sort_values("impressions",ascending=False).head(20)

st.dataframe(ctr_kw)

# ------------------------
# PAGE OPPORTUNITIES
# ------------------------

st.header("Page Optimization Opportunities")

page_df = current_df.groupby("page").agg({
    "clicks":"sum",
    "impressions":"sum",
    "position":"mean"
}).sort_values("impressions",ascending=False).head(20)

st.dataframe(page_df)

# ------------------------
# TREND CHART
# ------------------------

st.header("Traffic Trend")

trend = current_df.groupby("date").agg({
    "clicks":"sum",
    "impressions":"sum"
})

st.line_chart(trend)

# ------------------------
# PREVIOUS MONTH COMPARISON
# ------------------------

st.header("Keyword Ranking Drops vs Previous Month")

prev_kw = prev_df.groupby("keyword").agg({
    "position":"mean"
})

curr_kw = current_df.groupby("keyword").agg({
    "position":"mean"
})

compare = curr_kw.join(prev_kw,lsuffix="_current",rsuffix="_prev")

compare["drop"] = compare["position_current"] - compare["position_prev"]

drop_kw = compare.sort_values("drop",ascending=False).head(20)

st.dataframe(drop_kw)

# ------------------------
# NEW KEYWORDS
# ------------------------

st.header("New Keywords Discovered")

new_kw = set(current_df["keyword"]) - set(prev_df["keyword"])

new_kw_df = current_df[current_df["keyword"].isin(new_kw)]

new_kw_table = new_kw_df.groupby("keyword").agg({
    "clicks":"sum",
    "impressions":"sum",
    "position":"mean"
}).sort_values("impressions",ascending=False).head(20)

st.dataframe(new_kw_table)

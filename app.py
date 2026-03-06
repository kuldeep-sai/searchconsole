import streamlit as st
import pandas as pd
import numpy as np
import re

st.set_page_config(page_title="SEO Search Console Analyzer", layout="wide")

st.title("🔎 SEO Search Console Analyzer")

uploaded_file = st.file_uploader("Upload Search Console CSV", type=["csv"])

if uploaded_file:

    df = pd.read_csv(uploaded_file)

    df.columns = df.columns.str.lower()

    df["date"] = pd.to_datetime(df["date"])

    df["month"] = df["date"].dt.to_period("M").astype(str)

    # -------------------------------
    # URL Folder Classification
    # -------------------------------

    def classify_folder(url):

        if "/blog/" in url:
            return "Blog"

        elif "/career-advice/" in url:
            return "Career Advice"

        elif "/resume-maker/" in url:
            return "Resume Maker"

        elif "/naukri360/" in url:
            return "Naukri360"

        elif "/code360/" in url:
            return "Code360"

        elif "/recruit/" in url:
            return "Recruit"

        elif "/campus/career-guidance/" in url:
            return "Campus Career Guidance"

        elif re.search(r"jobs-in-[a-z-]+", url):
            return "City Jobs"

        elif re.search(r"[a-z-]+-jobs-in-[a-z-]+", url):
            return "Keyword + City Jobs"

        elif re.search(r"[a-z-]+-jobs", url):
            return "Keyword Jobs"

        elif url.endswith(".com/"):
            return "Homepage"

        else:
            return "Other"

    df["folder"] = df["page"].apply(classify_folder)

    # -------------------------------
    # Month Filter
    # -------------------------------

    months = sorted(df["month"].unique())

    selected_month = st.selectbox("Select Month", months)

    prev_month_index = months.index(selected_month) - 1

    if prev_month_index >= 0:
        prev_month = months[prev_month_index]
    else:
        prev_month = None

    current = df[df["month"] == selected_month]

    if prev_month:
        previous = df[df["month"] == prev_month]

    # -------------------------------
    # Aggregate Data
    # -------------------------------

    curr_page = current.groupby("page").agg(
        clicks=("clicks", "sum"),
        impressions=("impressions", "sum"),
        ctr=("ctr", "mean"),
        position=("position", "mean")
    ).reset_index()

    prev_page = previous.groupby("page").agg(
        clicks=("clicks", "sum")
    ).reset_index()

    merged = curr_page.merge(prev_page, on="page", how="left", suffixes=("_curr", "_prev"))

    merged["click_loss"] = merged["clicks_prev"] - merged["clicks_curr"]

    # -------------------------------
    # 🔴 Traffic Loss Section
    # -------------------------------

    st.header("🚨 Pages Losing Traffic")

    loss_df = merged.sort_values("click_loss", ascending=False).head(20)

    st.dataframe(loss_df)

    # -------------------------------
    # 🟡 Quick Win Opportunities
    # -------------------------------

    st.header("⚡ Quick Win Opportunities (Position 8-20)")

    quick_wins = curr_page[
        (curr_page["position"] >= 8) &
        (curr_page["position"] <= 20) &
        (curr_page["impressions"] > 1000)
    ]

    st.dataframe(quick_wins.sort_values("impressions", ascending=False).head(20))

    # -------------------------------
    # 🟢 High Impression Low CTR
    # -------------------------------

    st.header("📉 High Impressions but Low CTR")

    ctr_opportunities = curr_page[
        (curr_page["impressions"] > 5000) &
        (curr_page["ctr"] < 0.02)
    ]

    st.dataframe(ctr_opportunities.sort_values("impressions", ascending=False).head(20))

    # -------------------------------
    # 🔽 Query Drop Analysis
    # -------------------------------

    st.header("🔻 Keywords Losing Traffic")

    curr_query = current.groupby("query").agg(
        clicks=("clicks", "sum"),
        impressions=("impressions", "sum"),
        position=("position", "mean")
    ).reset_index()

    prev_query = previous.groupby("query").agg(
        clicks=("clicks", "sum")
    ).reset_index()

    query_merge = curr_query.merge(prev_query, on="query", how="left", suffixes=("_curr", "_prev"))

    query_merge["click_loss"] = query_merge["clicks_prev"] - query_merge["clicks_curr"]

    st.dataframe(query_merge.sort_values("click_loss", ascending=False).head(20))

    # -------------------------------
    # 📂 Folder Performance
    # -------------------------------

    st.header("📁 Folder Performance")

    folder_perf = current.groupby("folder").agg(
        clicks=("clicks", "sum"),
        impressions=("impressions", "sum"),
        ctr=("ctr", "mean"),
        position=("position", "mean")
    ).reset_index()

    st.dataframe(folder_perf.sort_values("clicks", ascending=False))

    # -------------------------------
    # 📊 Overall Performance
    # -------------------------------

    st.header("📊 Overall Performance Summary")

    summary = current.groupby("month").agg(
        clicks=("clicks", "sum"),
        impressions=("impressions", "sum")
    )

    st.dataframe(summary)

    # -------------------------------
    # 🤖 SEO Agent Recommendations
    # -------------------------------

    st.header("🤖 SEO Agent Recommendations")

    insights = []

    if len(loss_df) > 0:
        insights.append("Focus on pages losing the most clicks compared to last month.")

    if len(quick_wins) > 0:
        insights.append("Optimize pages ranking between positions 8–20 to push them into top 5.")

    if len(ctr_opportunities) > 0:
        insights.append("Improve title tags and meta descriptions for pages with high impressions but low CTR.")

    if len(query_merge) > 0:
        insights.append("Investigate keywords that lost clicks and refresh content targeting those queries.")

    for i in insights:
        st.write("•", i)

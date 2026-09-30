#!/usr/bin/env python
# coding: utf-8

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st


st.set_page_config(page_title="Netflix Insights", page_icon="N", layout="wide")
st.markdown(
    """
    <style>
    :root { --ink:#f5f2ee; --muted:#aaa5a1; --line:#34312f; --red:#e50914; }
    .stApp { background:radial-gradient(ellipse at 12% 0%,#33201f 0,#171615 42%,#111110 100%); color:var(--ink); }
    [data-testid="stSidebar"] { background:#151413; border-right:1px solid var(--line); }
    .block-container { padding-top:2.2rem; padding-bottom:3rem; }
    .eyebrow { color:#ff777d; font-size:.75rem; font-weight:700; letter-spacing:.12em; text-transform:uppercase; }
    .hero-title { color:var(--ink); font-family:Georgia,'Times New Roman',serif; font-size:2.7rem; line-height:1.05; margin:.25rem 0 .5rem; }
    .hero-copy,.section-note { color:var(--muted); }
    [data-testid="stMetric"] { background:rgba(25,24,23,.82); border:1px solid var(--line); border-top:2px solid var(--red); padding:1rem 1.1rem; }
    [data-testid="stMetricLabel"] { color:var(--muted); }
    [data-testid="stMetricValue"] { color:var(--ink); }
    h2,h3 { color:var(--ink); }
    .records-heading { display:flex; align-items:center; gap:.7rem; margin-top:1.6rem; }
    .records-heading h2 { color:var(--red); font-size:1.5rem; margin:0; }
    .records-marker { width:4px; height:1.35rem; background:var(--red); }
    </style>
    """,
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="eyebrow">Viewing habits, at a glance</div>'
    '<div class="hero-title">Netflix Insights</div>'
    '<div class="hero-copy">Explore viewing activity, audience ratings, and monthly revenue.</div>',
    unsafe_allow_html=True,
)

st.sidebar.markdown("## Your data")
uploaded = st.sidebar.file_uploader("Upload a Netflix CSV", type=["csv"])
st.sidebar.caption(
    "Expected fields include Region, Category, Rating, Subscription_Plan, "
    "Monthly_Revenue, and Watch_Date."
)

try:
    if uploaded is not None:
        data = pd.read_csv(uploaded)
    else:
        local_csv = next(
            (
                path
                for path in (
                    Path("netflix.csv"),
                    Path("Netflix_100_Customers_Dataset (1).csv"),
                )
                if path.is_file()
            ),
            None,
        )
        data = pd.read_csv(local_csv) if local_csv is not None else None
except Exception as error:
    st.error(f"We couldn't read that CSV: {error}")
    st.stop()

if data is None:
    st.info("Upload your Netflix CSV from the sidebar to explore the dashboard.")
    st.stop()
if data.empty:
    st.warning("This CSV has column headers but no data rows.")
    st.stop()

data = data.copy()
if "Watch_Date" in data.columns:
    data["Watch_Date"] = pd.to_datetime(data["Watch_Date"], errors="coerce")
for column in ("Monthly_Revenue", "Rating"):
    if column in data.columns:
        data[column] = pd.to_numeric(data[column], errors="coerce")

st.sidebar.markdown("## Filters")
filtered = data.copy()
for column, label in (
    ("Region", "Region"),
    ("Subscription_Plan", "Subscription plan"),
    ("Category", "Category"),
):
    if column in filtered.columns:
        options = sorted(filtered[column].dropna().astype(str).unique().tolist())
        selected = st.sidebar.multiselect(label, options, default=options)
        filtered = filtered[filtered[column].astype(str).isin(selected)]

if "Watch_Date" in filtered.columns:
    dates = filtered["Watch_Date"].dropna()
    if not dates.empty and dates.min().date() < dates.max().date():
        selected_dates = st.sidebar.date_input(
            "Watch date",
            value=(dates.min().date(), dates.max().date()),
            min_value=dates.min().date(),
            max_value=dates.max().date(),
        )
        if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
            first, last = selected_dates
            in_range = filtered["Watch_Date"].dt.date.between(first, last)
            filtered = filtered[filtered["Watch_Date"].isna() | in_range]

if filtered.empty:
    st.warning("No rows match these filters. Adjust the selections in the sidebar.")
    st.stop()

revenue = filtered["Monthly_Revenue"].sum(min_count=1) if "Monthly_Revenue" in filtered else None
rating = filtered["Rating"].mean() if "Rating" in filtered else None
region = (
    filtered["Region"].mode().iloc[0]
    if "Region" in filtered.columns and not filtered["Region"].dropna().empty
    else "—"
)
metrics = st.columns(4)
metrics[0].metric("Records", f"{len(filtered):,}")
metrics[1].metric("Monthly revenue", f"${revenue:,.0f}" if pd.notna(revenue) else "—")
metrics[2].metric("Average rating", f"{rating:.1f}" if pd.notna(rating) else "—")
metrics[3].metric("Leading region", str(region))

st.markdown("## Audience and revenue")
red, blush, text, grid = "#e50914", "#f29b8f", "#d8d2ce", "#393533"
left, right = st.columns(2, gap="large")
if "Region" in filtered and "Monthly_Revenue" in filtered:
    with left:
        st.markdown("### Revenue by region")
        values = filtered.groupby("Region")["Monthly_Revenue"].sum().sort_values()
        fig, ax = plt.subplots(figsize=(7, 4), facecolor="#191817")
        ax.set_facecolor("#191817")
        ax.barh(values.index.astype(str), values.values, color=red, height=.62)
        ax.set_xlabel("Monthly revenue", color=text)
        ax.tick_params(colors=text)
        ax.spines[:].set_visible(False)
        ax.xaxis.grid(True, color=grid, linewidth=.7)
        ax.set_axisbelow(True)
        fig.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
else:
    with left:
        st.caption("Revenue by region needs Region and Monthly_Revenue columns.")

if "Category" in filtered and "Monthly_Revenue" in filtered:
    with right:
        st.markdown("### Revenue mix by category")
        values = filtered.groupby("Category")["Monthly_Revenue"].sum()
        fig, ax = plt.subplots(figsize=(7, 4), facecolor="#191817")
        ax.set_facecolor("#191817")
        if not values.empty:
            ax.pie(
                values.values,
                labels=values.index.astype(str),
                autopct="%1.0f%%",
                startangle=90,
                colors=[red, blush, "#8e292d", "#d8b5a8", "#6d625d"],
                textprops={"color": text},
                wedgeprops={"width": .42, "edgecolor": "#191817"},
            )
        fig.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
else:
    with right:
        st.caption("Category revenue needs Category and Monthly_Revenue columns.")

left, right = st.columns(2, gap="large")
if "Rating" in filtered:
    with left:
        st.markdown("### Rating distribution")
        values = filtered["Rating"].dropna().value_counts().sort_index()
        fig, ax = plt.subplots(figsize=(7, 3.5), facecolor="#191817")
        ax.set_facecolor("#191817")
        ax.bar(values.index.astype(str), values.values, color=blush, width=.68)
        ax.set_ylabel("Records", color=text)
        ax.tick_params(colors=text)
        ax.spines[:].set_visible(False)
        ax.yaxis.grid(True, color=grid, linewidth=.7)
        ax.set_axisbelow(True)
        fig.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
else:
    with left:
        st.caption("Rating distribution needs a Rating column.")

if "Rating" in filtered and "Subscription_Plan" in filtered:
    with right:
        st.markdown("### Average rating by plan")
        values = filtered.groupby("Subscription_Plan")["Rating"].mean().dropna()
        fig, ax = plt.subplots(figsize=(7, 3.5), facecolor="#191817")
        ax.set_facecolor("#191817")
        ax.bar(values.index.astype(str), values.values, color="#c94d53", width=.62)
        ax.set_ylabel("Average rating", color=text)
        ax.tick_params(colors=text)
        ax.spines[:].set_visible(False)
        ax.yaxis.grid(True, color=grid, linewidth=.7)
        ax.set_axisbelow(True)
        fig.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
else:
    with right:
        st.caption("Plan ratings need Subscription_Plan and Rating columns.")

st.markdown(
    '<div class="records-heading"><span class="records-marker"></span>'
    '<h2>Viewing records</h2></div>',
    unsafe_allow_html=True,
)
st.markdown('<div class="section-note">Filtered rows from your uploaded dataset.</div>', unsafe_allow_html=True)
record_table = filtered.style.set_table_styles(
    [
        {
            "selector": "thead th",
            "props": [
                ("background-color", "#e50914"),
                ("color", "#ffffff"),
                ("font-weight", "700"),
                ("border", "none"),
                ("padding", "12px 14px"),
                ("text-align", "left"),
            ],
        },
        {
            "selector": "tbody td",
            "props": [
                ("background-color", "#191817"),
                ("color", "#f5f2ee"),
                ("border-bottom", "1px solid #34312f"),
                ("padding", "10px 14px"),
            ],
        },
        {
            "selector": "tbody tr:nth-child(even) td",
            "props": [("background-color", "#242220")],
        },
        {
            "selector": "tbody tr:hover td",
            "props": [("background-color", "#382022")],
        },
    ]
)
record_column_config = {}
if "Watch_Date" in filtered.columns:
    record_column_config["Watch_Date"] = st.column_config.DateColumn(
        "Watch date", format="MMM D, YYYY"
    )
if "Monthly_Revenue" in filtered.columns:
    record_column_config["Monthly_Revenue"] = st.column_config.NumberColumn(
        "Monthly revenue", format="$%.2f"
    )
if "Rating" in filtered.columns:
    record_column_config["Rating"] = st.column_config.NumberColumn(
        "Rating", format="%.1f"
    )
st.dataframe(
    record_table,
    column_config=record_column_config,
    use_container_width=True,
    hide_index=True,
    height=420,
)
st.download_button(
    "Download filtered CSV",
    data=filtered.to_csv(index=False).encode("utf-8"),
    file_name="netflix_filtered.csv",
    mime="text/csv",
)
with st.expander("Data quality"):
    columns = st.columns(3)
    columns[0].metric("Rows", f"{len(data):,}")
    columns[1].metric("Duplicate rows", f"{int(data.duplicated().sum()):,}")
    columns[2].metric("Missing values", f"{int(data.isna().sum().sum()):,}")
    st.dataframe(
        pd.DataFrame({"Column": data.columns, "Data type": data.dtypes.astype(str).values}),
        use_container_width=True,
        hide_index=True,
    )

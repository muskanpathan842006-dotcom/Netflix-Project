#!/usr/bin/env python
# coding: utf-8

# In[42]:


import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st


# In[43]:


netflix=pd.read_csv("netflix.csv")


# In[44]:


netflix


# In[45]:


# data cleaning 

netflix.shape #is use for find how many rows and columns in dataset 


# In[46]:


netflix.info() # is use for find all information of data like data type and null value 


# In[47]:


netflix.isnull().sum() # to check total  null values in data 


# In[48]:


netflix.duplicated().sum()


# In[49]:


netflix.describe() #  is used for see statastical information in dataset


# In[50]:


netflix["Watch_Date"]=pd.to_datetime(netflix["Watch_Date"])


# In[51]:


netflix.info()


# In[52]:


netflix.dtypes


# In[57]:


netflix.groupby("Region")["Monthly_Revenue"].sum().plot(kind="bar",ylabel="Monthly_Revenue",title="region wise revenue")


# In[61]:


netflix.groupby("Subscription_Plan")["Rating"].sum().plot(kind="pie",title="subscription plan wise rating")


# In[64]:


netflix["Rating"].value_counts().plot(kind="bar")


# In[68]:


netflix.groupby("Category")["Monthly_Revenue"].sum().plot(kind="pie",title="category wise revenue")

#!/usr/bin/env python
# coding: utf-8

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st


st.set_page_config(
	page_title="Netflix Insights",
	page_icon="N",
	layout="wide",
)

st.markdown(
	"""
	<style>
	:root {
		--ink: #f5f2ee;
		--muted: #aaa5a1;
		--surface: #191817;
		--accent: #e50914;
		--line: #34312f;
	}
	.stApp {
		background: radial-gradient(ellipse at 12% 0%, #33201f 0, #171615 42%, #111110 100%);
		color: var(--ink);
	}
	[data-testid="stSidebar"] {
		background: #151413;
		border-right: 1px solid var(--line);
	}
	.block-container { padding-top: 2.2rem; padding-bottom: 3rem; }
	.eyebrow {
		color: #ff777d; font-size: 0.75rem; font-weight: 700;
		letter-spacing: 0.12em; text-transform: uppercase;
	}
	.hero-title {
		color: var(--ink); font-family: Georgia, 'Times New Roman', serif;
		font-size: 2.7rem; line-height: 1.05; margin: 0.25rem 0 0.5rem;
	}
	.hero-copy { color: var(--muted); font-size: 1rem; margin-bottom: 1.5rem; }
	[data-testid="stMetric"] {
		background: rgba(25, 24, 23, 0.82); border: 1px solid var(--line);
		border-top: 2px solid var(--accent); padding: 1rem 1.1rem;
	}
	[data-testid="stMetricLabel"] { color: var(--muted); }
	[data-testid="stMetricValue"] { color: var(--ink); }
	h2, h3 { color: var(--ink); }
	.section-note { color: var(--muted); font-size: 0.9rem; }
	div[data-testid="stDataFrame"] { border: 1px solid var(--line); }
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
uploaded_file = st.sidebar.file_uploader("Upload a Netflix CSV", type=["csv"])
st.sidebar.caption("Expected fields include Region, Category, Rating, Subscription_Plan, Monthly_Revenue, and Watch_Date.")

try:
	if uploaded_file is not None:
		netflix = pd.read_csv(uploaded_file)
	elif Path("netflix.csv").is_file():
		netflix = pd.read_csv("netflix.csv")
	else:
		netflix = None
except Exception as error:
	st.error(f"We couldn't read that CSV: {error}")
	st.stop()

if netflix is None:
	st.info("Upload your Netflix CSV from the sidebar to explore the dashboard.")
	st.stop()

if netflix.empty:
	st.warning("This CSV has column headers but no data rows.")
	st.stop()

netflix = netflix.copy()
if "Watch_Date" in netflix.columns:
	netflix["Watch_Date"] = pd.to_datetime(netflix["Watch_Date"], errors="coerce")
if "Monthly_Revenue" in netflix.columns:
	netflix["Monthly_Revenue"] = pd.to_numeric(netflix["Monthly_Revenue"], errors="coerce")
if "Rating" in netflix.columns:
	netflix["Rating"] = pd.to_numeric(netflix["Rating"], errors="coerce")

st.sidebar.markdown("## Filters")
filtered = netflix.copy()
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
	valid_dates = filtered["Watch_Date"].dropna()
	if not valid_dates.empty and valid_dates.min().date() < valid_dates.max().date():
		date_range = st.sidebar.date_input(
			"Watch date",
			value=(valid_dates.min().date(), valid_dates.max().date()),
			min_value=valid_dates.min().date(),
			max_value=valid_dates.max().date(),
		)
		if isinstance(date_range, tuple) and len(date_range) == 2:
			start_date, end_date = date_range
			filtered = filtered[
				filtered["Watch_Date"].isna()
				| filtered["Watch_Date"].dt.date.between(start_date, end_date)
			]

if filtered.empty:
	st.warning("No rows match these filters. Adjust the selections in the sidebar.")
	st.stop()

revenue = filtered["Monthly_Revenue"].sum(min_count=1) if "Monthly_Revenue" in filtered else None
average_rating = filtered["Rating"].mean() if "Rating" in filtered else None
top_region = (
	filtered["Region"].mode().iloc[0]
	if "Region" in filtered.columns and not filtered["Region"].dropna().empty
	else "—"
)
metric_columns = st.columns(4)
metric_columns[0].metric("Records", f"{len(filtered):,}")
metric_columns[1].metric(
	"Monthly revenue",
	f"${revenue:,.0f}" if pd.notna(revenue) else "—",
)
metric_columns[2].metric(
	"Average rating",
	f"{average_rating:.1f}" if pd.notna(average_rating) else "—",
)
metric_columns[3].metric("Leading region", str(top_region))

st.markdown("## Audience and revenue")
left_chart, right_chart = st.columns(2, gap="large")
chart_color = "#e50914"
text_color = "#d8d2ce"
grid_color = "#393533"

if "Monthly_Revenue" in filtered and "Region" in filtered:
	with left_chart:
		st.markdown("### Revenue by region")
		grouped = filtered.groupby("Region", dropna=True)["Monthly_Revenue"].sum().sort_values()
		figure, axis = plt.subplots(figsize=(7, 4), facecolor="#191817")
		axis.set_facecolor("#191817")
		axis.barh(grouped.index.astype(str), grouped.values, color=chart_color, height=0.62)
		axis.set_xlabel("Monthly revenue", color=text_color)
		axis.tick_params(colors=text_color)
		axis.spines[:].set_visible(False)
		axis.xaxis.grid(True, color=grid_color, linewidth=0.7)
		axis.set_axisbelow(True)
		figure.tight_layout()
		st.pyplot(figure, use_container_width=True)
		plt.close(figure)
elif "Monthly_Revenue" not in filtered or "Region" not in filtered:
	with left_chart:
		st.caption("Revenue by region needs both Region and Monthly_Revenue columns.")

if "Monthly_Revenue" in filtered and "Category" in filtered:
	with right_chart:
		st.markdown("### Revenue mix by category")
		grouped = filtered.groupby("Category", dropna=True)["Monthly_Revenue"].sum()
		figure, axis = plt.subplots(figsize=(7, 4), facecolor="#191817")
		axis.set_facecolor("#191817")
		if not grouped.empty:
			axis.pie(
				grouped.values,
				labels=grouped.index.astype(str),
				autopct="%1.0f%%",
				startangle=90,
				colors=["#e50914", "#f29b8f", "#8e292d", "#d8b5a8", "#6d625d"],
				textprops={"color": text_color},
				wedgeprops={"width": 0.42, "edgecolor": "#191817"},
			)
		figure.tight_layout()
		st.pyplot(figure, use_container_width=True)
		plt.close(figure)
elif "Monthly_Revenue" not in filtered or "Category" not in filtered:
	with right_chart:
		st.caption("Category revenue needs both Category and Monthly_Revenue columns.")

lower_left, lower_right = st.columns(2, gap="large")
if "Rating" in filtered:
	with lower_left:
		st.markdown("### Rating distribution")
		ratings = filtered["Rating"].dropna().value_counts().sort_index()
		figure, axis = plt.subplots(figsize=(7, 3.5), facecolor="#191817")
		axis.set_facecolor("#191817")
		axis.bar(ratings.index.astype(str), ratings.values, color="#f29b8f", width=0.68)
		axis.set_ylabel("Records", color=text_color)
		axis.tick_params(colors=text_color)
		axis.spines[:].set_visible(False)
		axis.yaxis.grid(True, color=grid_color, linewidth=0.7)
		axis.set_axisbelow(True)
		figure.tight_layout()
		st.pyplot(figure, use_container_width=True)
		plt.close(figure)
else:
	with lower_left:
		st.caption("Rating distribution needs a Rating column.")

if "Rating" in filtered and "Subscription_Plan" in filtered:
	with lower_right:
		st.markdown("### Average rating by plan")
		grouped = filtered.groupby("Subscription_Plan", dropna=True)["Rating"].mean().dropna()
		figure, axis = plt.subplots(figsize=(7, 3.5), facecolor="#191817")
		axis.set_facecolor("#191817")
		axis.bar(grouped.index.astype(str), grouped.values, color="#c94d53", width=0.62)
		axis.set_ylabel("Average rating", color=text_color)
		axis.tick_params(colors=text_color)
		axis.spines[:].set_visible(False)
		axis.yaxis.grid(True, color=grid_color, linewidth=0.7)
		axis.set_axisbelow(True)
		figure.tight_layout()
		st.pyplot(figure, use_container_width=True)
		plt.close(figure)
else:
	with lower_right:
		st.caption("Plan ratings need both Subscription_Plan and Rating columns.")

st.markdown("## Viewing records")
st.markdown('<div class="section-note">Filtered rows from your uploaded dataset.</div>', unsafe_allow_html=True)
st.dataframe(filtered, use_container_width=True, hide_index=True)
st.download_button(
	"Download filtered CSV",
	data=filtered.to_csv(index=False).encode("utf-8"),
	file_name="netflix_filtered.csv",
	mime="text/csv",
)

with st.expander("Data quality"):
	quality_columns = st.columns(3)
	quality_columns[0].metric("Rows", f"{len(netflix):,}")
	quality_columns[1].metric("Duplicate rows", f"{int(netflix.duplicated().sum()):,}")
	quality_columns[2].metric("Missing values", f"{int(netflix.isna().sum().sum()):,}")
	st.dataframe(
		pd.DataFrame({"Column": netflix.columns, "Data type": netflix.dtypes.astype(str).values}),
		use_container_width=True,
		hide_index=True,
	)





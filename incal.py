import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. Load Data ---
# Assuming your cleaned data is in a CSV file named 'top_instagram_influencers.csv'
# Make sure this file is in the same directory as your app.py or provide the full path/URL.
try:
    df = pd.read_csv('top_instagram_influencers.csv')
except FileNotFoundError:
    st.error("Error: 'top_instagram_influencers.csv' not found. Please upload the file or check the path.")
    st.stop()

# --- 2. Data Preprocessing and Calculated Fields ---
# Ensure data types are correct (as per your document)
df['rank'] = df['rank'].astype(int)
df['influence_score'] = df['influence_score'].astype(float)
df['posts'] = df['posts'].astype(int)
df['followers'] = df['followers'].astype(int)
df['avg_likes'] = df['avg_likes'].astype(float)
df['60_day_eng_rate'] = df['60_day_eng_rate'].astype(float)
df['new_post_avg_like'] = df['new_post_avg_like'].astype(float)
df['total_likes'] = df['total_likes'].astype(int)
df['country'] = df['country'].astype(str)

# Handle potential nulls (example: fill numerical NaNs with 0, or median for robust analysis)
# You might want to refine this based on your specific data and needs.
for col in ['influence_score', 'posts', 'followers', 'avg_likes',
            '60_day_eng_rate', 'new_post_avg_like', 'total_likes']:
    if df[col].isnull().any():
        df[col] = df[col].fillna(0) # or df[col].fillna(df[col].median())

# Calculated Fields (from your provided document)
# Engagement Rate (ER) Calculation: ((avg_likes) / (followers]) * 100 [cite: 45, 46]
df['Engagement Rate (Calculated)'] = (df['avg_likes'] / df['followers']) * 100
# Growth Rate in New Post Likes: ([new_post_avg_like] - [avg_likes]) / [avg_likes] * 100 [cite: 49, 50]
df['Growth Rate in New Post Likes'] = ((df['new_post_avg_like'] - df['avg_likes']) / df['avg_likes']) * 100
# Like-to-Follower Ratio: [total_likes) / (followers] [cite: 53]
df['Like-to-Follower Ratio'] = df['total_likes'] / df['followers']
# Post Efficiency: [total_likes] / [posts] [cite: 253]
df['Post Efficiency'] = df['total_likes'] / df['posts']


# --- 3. Streamlit App Layout ---
st.set_page_config(layout="wide", page_title="Instagram Influencers Dashboard", page_icon="📸")

st.title("📸 Top Instagram Influencers Dashboard")
st.markdown("---")

# Sidebar for filters and navigation
st.sidebar.header("Dashboard Controls")
selected_country = st.sidebar.multiselect(
    "Filter by Country:",
    options=df['country'].unique(),
    default=df['country'].unique()
)

# Filter dataframe based on selected country
filtered_df = df[df['country'].isin(selected_country)]

# Check if filtered_df is empty
if filtered_df.empty:
    st.warning("No data available for the selected country/countries. Please adjust your filters.")
    st.stop()


# --- 4. Dashboard 1: Overview of Influencer Performance ---
st.header("📊 Overview of Influencer Performance")

col1, col2, col3, col4 = st.columns(4)

with col1:
    total_influencers = len(filtered_df)
    st.metric(label="Total Influencers", value=f"{total_influencers:,}")

with col2:
    avg_engagement_rate = filtered_df['60_day_eng_rate'].mean()
    st.metric(label="Average Engagement Rate (60-Day)", value=f"{avg_engagement_rate:.2f}%")

with col3:
    total_followers = filtered_df['followers'].sum()
    st.metric(label="Total Followers Across Influencers", value=f"{total_followers:,}")

with col4:
    avg_likes_per_post = filtered_df['avg_likes'].mean()
    st.metric(label="Average Likes per Post", value=f"{avg_likes_per_post:,.0f}")

st.markdown("---")

# Top 10 Influencers by Influence Score
st.subheader("Top 10 Influencers by Influence Score")
top_10_influencers = filtered_df.sort_values(by='influence_score', ascending=False).head(10)
fig_top_influencers = px.bar(
    top_10_influencers,
    x='channel_info',
    y='influence_score',
    color='influence_score',
    title='Top 10 Influencers by Influence Score',
    labels={'channel_info': 'Influencer', 'influence_score': 'Influence Score'},
    hover_data=['followers', 'avg_likes']
)
st.plotly_chart(fig_top_influencers, use_container_width=True)

st.markdown("---")

# Geographic Distribution of Influencers by Country (Map Visualization) [cite: 72]
st.subheader("Geographic Distribution of Influencers by Country")
# Aggregate data for map: count of influencers and average engagement rate per country
country_summary = filtered_df.groupby('country').agg(
    num_influencers=('channel_info', 'count'),
    avg_engagement_rate=('60_day_eng_rate', 'mean')
).reset_index()

fig_map = px.choropleth(
    country_summary,
    locations="country",
    locationmode="country names",
    color="avg_engagement_rate",
    hover_name="country",
    color_continuous_scale=px.colors.sequential.Plasma,
    title="Average Engagement Rate by Country",
    hover_data={'num_influencers': True, 'avg_engagement_rate': ':.2f'}
)
st.plotly_chart(fig_map, use_container_width=True)

st.markdown("---")


# --- 5. Dashboard 2: Engagement and Influence Metrics ---
st.header("📈 Engagement and Influence Metrics")

# Followers vs. Avg Likes with Influence Score as size [cite: 75]
st.subheader("Followers vs. Average Likes (Size by Influence Score)")
fig_scatter = px.scatter(
    filtered_df,
    x='followers',
    y='avg_likes',
    size='influence_score',
    color='country',
    hover_name='channel_info',
    log_x=True, # Log scale for followers as it can vary widely
    title='Followers vs. Average Likes (Size indicates Influence Score)',
    labels={'followers': 'Followers (Log Scale)', 'avg_likes': 'Average Likes', 'influence_score': 'Influence Score'}
)
st.plotly_chart(fig_scatter, use_container_width=True)

st.markdown("---")

# Engagement Rate Distribution (Histogram) [cite: 224]
st.subheader("60-Day Engagement Rate Distribution")
fig_eng_hist = px.histogram(
    filtered_df,
    x='60_day_eng_rate',
    nbins=20,
    title='Distribution of 60-Day Engagement Rate',
    labels={'60_day_eng_rate': '60-Day Engagement Rate (%)'}
)
st.plotly_chart(fig_eng_hist, use_container_width=True)

st.markdown("---")


# --- 6. Dashboard 3: Country-Specific Insights ---
st.header("🌍 Country-Specific Insights")

# Total Influencers and Average Influence Score per Country [cite: 78]
country_influence_summary = filtered_df.groupby('country').agg(
    total_influencers=('channel_info', 'count'),
    avg_influence_score=('influence_score', 'mean')
).reset_index().sort_values(by='total_influencers', ascending=False)

fig_country_bar = px.bar(
    country_influence_summary,
    x='country',
    y='total_influencers',
    color='avg_influence_score',
    title='Total Influencers and Average Influence Score per Country',
    labels={'total_influencers': 'Total Influencers', 'country': 'Country', 'avg_influence_score': 'Avg Influence Score'},
    hover_data={'avg_influence_score': ':.2f'}
)
st.plotly_chart(fig_country_bar, use_container_width=True)

st.markdown("---")

# Bubble Chart: Like-to-Follower Ratio by Country [cite: 79]
# Aggregate for bubble chart if needed, or use influencer level data
fig_bubble = px.scatter(
    filtered_df,
    x='Like-to-Follower Ratio',
    y='Engagement Rate (Calculated)',
    size='followers',
    color='country',
    hover_name='channel_info',
    title='Like-to-Follower Ratio vs. Engagement Rate by Country (Size by Followers)',
    labels={'Like-to-Follower Ratio': 'Like-to-Follower Ratio', 'Engagement Rate (Calculated)': 'Engagement Rate (%)'},
    log_x=True # Ratio can vary widely
)
st.plotly_chart(fig_bubble, use_container_width=True)

st.markdown("---")

# --- 7. Dashboard 4: Engagement Trends ---
st.header("📊 Engagement Trends")

# Heatmap: 60_day_eng_rate by Influencer Rank and Country (simplified for demo) [cite: 82]
# For a full heatmap, you might need to pivot or reshape your data if you have multiple entries per rank/country
# For this example, let's show average engagement rate per country, which is more practical for a heatmap-like view
engagement_pivot = filtered_df.pivot_table(index='country', values='60_day_eng_rate', aggfunc='mean')
fig_heatmap = px.imshow(
    engagement_pivot,
    text_auto=".2f",
    color_continuous_scale="Viridis",
    title="Average 60-Day Engagement Rate by Country (Heatmap)"
)
st.plotly_chart(fig_heatmap, use_container_width=True)

st.markdown("---")

# --- 8. About Section ---
st.sidebar.markdown("---")
st.sidebar.header("About This Dashboard")
st.sidebar.info(
    "This dashboard visualizes data of top Instagram influencers, providing insights into their performance, "
    "engagement, and geographical distribution. "
    "Data from 'Top Instagram Influencers Data (Cleaned) Dashboard (Business Analyst).pdf'."
)

import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np # Import numpy for np.nan

# Helper function to clean numeric strings (e.g., '3.3k', '1.2M', '1.39%')
def clean_numeric_value(value):
    if pd.isna(value):
        return np.nan # Handle NaN values
    s = str(value).strip().lower().replace(',', '').replace('%', '') # Remove commas and percentage sign, convert to lowercase
    if 'k' in s:
        try:
            return float(s.replace('k', '')) * 1_000
        except ValueError:
            return np.nan # Return NaN if conversion fails after removing 'k'
    elif 'm' in s:
        try:
            return float(s.replace('m', '')) * 1_000_000
        except ValueError:
            return np.nan # Return NaN if conversion fails after removing 'm'
    else:
        try:
            return float(s) # Try converting directly to float
        except ValueError:
            return np.nan # Return NaN if conversion fails (e.g., garbage string)

# --- 1. Load Data ---
st.sidebar.header("Upload Your Data")
uploaded_file = st.sidebar.file_uploader("Choose a CSV file", type="csv")

df = None # Initialize df as None outside the conditional block

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        st.sidebar.success("File uploaded successfully!")
    except Exception as e:
        st.sidebar.error(f"Error reading file: {e}. Please ensure it's a valid CSV.")
        st.stop() # Stop execution if file cannot be read
else:
    st.info("Please upload a CSV file to proceed with the dashboard.")
    st.stop() # Stop execution here if no file is uploaded yet

# --- All subsequent code that relies on 'df' must be inside this block ---
if df is not None:
    # --- 2. Data Preprocessing and Calculated Fields ---
    required_columns = [
        'rank', 'influence_score', 'posts', 'followers', 'avg_likes',
        '60_day_eng_rate', 'new_post_avg_like', 'total_likes', 'country', 'channel_info'
    ]

    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        st.error(f"Missing required columns in the uploaded CSV: {', '.join(missing_columns)}. Please check your file.")
        st.stop() # Stop if essential columns are missing

    # Apply cleaning function to relevant columns
    columns_to_clean = ['rank', 'followers', 'posts', 'avg_likes', 'new_post_avg_like', 'total_likes', '60_day_eng_rate', 'influence_score'] # Added 'rank' and 'influence_score' as they might also contain non-numeric string values
    for col in columns_to_clean:
        if col in df.columns:
            df[col] = df[col].apply(clean_numeric_value)
        else:
            st.warning(f"Column '{col}' not found for cleaning. Skipping.")

    # --- Crucial Correction: Fill NaNs BEFORE final type conversion for integer columns ---
    # Fill all numerical NaNs with 0. You might choose another strategy (e.g., median) if appropriate for your analysis.
    numeric_columns = ['rank', 'influence_score', 'posts', 'followers', 'avg_likes',
                       '60_day_eng_rate', 'new_post_avg_like', 'total_likes']
    for col in numeric_columns:
        if col in df.columns and df[col].isnull().any():
            df[col] = df[col].fillna(0) # Fill NaN with 0 for numeric columns

    # Type conversions
    try:
        # Convert to float first for all numeric columns to handle decimal places potentially introduced by 'k'/'m' cleaning
        # Then convert to int for columns that should strictly be integers
        df['rank'] = df['rank'].astype(int)
        df['influence_score'] = df['influence_score'].astype(float)
        df['posts'] = df['posts'].astype(int)
        df['followers'] = df['followers'].astype(int)
        df['avg_likes'] = df['avg_likes'].astype(float)
        df['60_day_eng_rate'] = df['60_day_eng_rate'].astype(float)
        df['new_post_avg_like'] = df['new_post_avg_like'].astype(float)
        df['total_likes'] = df['total_likes'].astype(int)

        df['country'] = df['country'].astype(str)
        df['channel_info'] = df['channel_info'].astype(str)
    except Exception as e:
        st.error(f"Final error converting column types. This might indicate persistent non-numeric data or other issues: {e}")
        st.stop() # Stop if type conversion fails

    # Calculated Fields (from your provided document)
    # Ensure no division by zero for calculated fields
    df['Engagement Rate (Calculated)'] = df.apply(
        lambda row: (row['avg_likes'] / row['followers']) * 100 if row['followers'] != 0 else 0,
        axis=1
    )
    df['Growth Rate in New Post Likes'] = df.apply(
        lambda row: ((row['new_post_avg_like'] - row['avg_likes']) / row['avg_likes']) * 100 if row['avg_likes'] != 0 else 0,
        axis=1
    )
    df['Like-to-Follower Ratio'] = df.apply(
        lambda row: row['total_likes'] / row['followers'] if row['followers'] != 0 else 0,
        axis=1
    )
    df['Post Efficiency'] = df.apply(
        lambda row: row['total_likes'] / row['posts'] if row['posts'] != 0 else 0,
        axis=1
    )


    # --- 3. Streamlit App Layout ---
    st.set_page_config(layout="wide", page_title="Instagram Influencers Dashboard", page_icon="📸")

    st.title("📸 Top Instagram Influencers Dashboard")
    st.markdown("---")

    # Sidebar for filters and navigation
    st.sidebar.subheader("Data Filters")
    selected_country = st.sidebar.multiselect(
        "Filter by Country:",
        options=df['country'].unique(),
        default=df['country'].unique()
    )

    # Filter dataframe based on selected country
    filtered_df = df[df['country'].isin(selected_country)]

    # Check if filtered_df is empty after applying filters
    if filtered_df.empty:
        st.warning("No data available for the selected country/countries. Please adjust your filters or upload a different dataset.")
        st.stop() # Stop if no data matches filters


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

    # Geographic Distribution of Influencers by Country (Map Visualization)
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

    # Followers vs. Avg Likes with Influence Score as size
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

    # Engagement Rate Distribution (Histogram)
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

    # Total Influencers and Average Influence Score per Country
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

    # Bubble Chart: Like-to-Follower Ratio by Country
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

    # Heatmap: 60_day_eng_rate by Influencer Rank and Country (simplified for demo)
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
        "Please upload your 'top_insta_influencers_data.csv' file to use the dashboard."
    )

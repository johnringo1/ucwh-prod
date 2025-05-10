import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from utils.db_utils import load_wash_data

# Page configuration
st.set_page_config(page_title="United Car Wash Analytics", layout="wide")
st.title("United Car Wash Time Series Analysis")

# Custom function to format year-month as "MMM 'YY"
def format_year_month(year_month_str):
    """Convert 'YYYY-MM' to 'MMM 'YY' format (e.g., 'Jan '23')"""
    try:
        date = datetime.strptime(year_month_str, '%Y-%m')
        return date.strftime("%b '%y")  # Format as "Mar '25"
    except:
        return year_month_str

# Add a try/except block to handle database connection issues gracefully
try:
    # Load the data
    with st.spinner("Loading data from database..."):
        df = load_wash_data()
    
    # Calculate date range
    min_date = df['date'].min().date()  # Convert to Python date for the date picker
    max_date = df['date'].max().date()  # Convert to Python date for the date picker
    
    # Create sidebar for filters
    st.sidebar.header("Filters")
    
    # Date range selector
    date_range = st.sidebar.date_input(
        "Select Date Range",
        [max_date - timedelta(days=90), max_date],
        min_value=min_date,
        max_value=max_date
    )
    
    if len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date = date_range[0]
        end_date = max_date
    
    # Filter data - IMPORTANT: Convert the date objects back to strings for filtering
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    
    # Site selector
    all_sites = sorted(df['site_id'].unique())
    selected_sites = st.sidebar.multiselect(
        "Select Sites",
        options=all_sites,
        default=all_sites[:5] if len(all_sites) > 5 else all_sites
    )
    
    # Rolling average period
    rolling_window = st.sidebar.slider("Rolling Average Window (days)", 1, 60, 7)
    
    # Filter data using string comparison to avoid type issues
    if selected_sites:
        filtered_df = df[(df['date'].dt.strftime('%Y-%m-%d') >= start_date_str) & 
                        (df['date'].dt.strftime('%Y-%m-%d') <= end_date_str) & 
                        (df['site_id'].isin(selected_sites))]
    else:
        filtered_df = df[(df['date'].dt.strftime('%Y-%m-%d') >= start_date_str) & 
                        (df['date'].dt.strftime('%Y-%m-%d') <= end_date_str)]
    
    # Check if data exists after filtering
    if filtered_df.empty:
        st.warning("No data available for the selected filters. Please adjust your selection.")
    else:
        # Calculate aggregate statistics first for consistency
        total_washes = filtered_df['count'].sum()
        total_rewashes = filtered_df['rewash_count'].sum()
        total_combined = total_washes + total_rewashes
        rewash_pct = total_rewashes / total_washes * 100 if total_washes > 0 else 0
        
        # Statistics section at top for reference
        st.header("Key Statistics")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Washes", f"{total_washes:,}")
            
        with col2:
            st.metric("Total Rewashes", f"{total_rewashes:,}")
            
        with col3:
            st.metric("Rewash Percentage", f"{rewash_pct:.2f}%")
        
        # Time Series Analysis
        st.header("Time Series Analysis")
        
        # Aggregate by date first - THIS MUST MATCH THE TOTALS ABOVE
        daily_totals = filtered_df.groupby(filtered_df['date'].dt.date).agg({
            'count': 'sum',
            'rewash_count': 'sum',
            'total_count': 'sum'
        }).reset_index()
        
        # Verify data consistency
        time_series_total = daily_totals['count'].sum()
        if abs(time_series_total - total_washes) > 1:  # Allow for small rounding differences
            st.warning(f"Data consistency check: Time series total ({time_series_total:,}) doesn't match statistics total ({total_washes:,})")
        
        # Convert back to datetime for plotting
        daily_totals['date'] = pd.to_datetime(daily_totals['date'])
        
        # Sort by date
        daily_totals = daily_totals.sort_values('date')
        
        # Calculate rolling averages
        daily_totals[f'{rolling_window}d_avg'] = daily_totals['count'].rolling(rolling_window).mean()
        
        # Create main visualization - REMOVED REWASH COUNT
        fig = go.Figure()
        
        fig.add_trace(
            go.Scatter(x=daily_totals['date'], y=daily_totals['count'], 
                    mode='lines', name='Daily Wash Count')
        )
        
        fig.add_trace(
            go.Scatter(x=daily_totals['date'], y=daily_totals[f'{rolling_window}d_avg'], 
                    mode='lines', name=f'{rolling_window}-Day Rolling Avg',
                    line=dict(color='red'))
        )
        
        fig.update_layout(
            title_text="Car Wash Counts Over Time",
            xaxis_title="Date",
            yaxis_title="Wash Count",
            legend=dict(x=0, y=1.1, orientation='h')
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Site comparison
        if selected_sites and len(selected_sites) > 1:
            st.header("Site Comparison")
            
            # Group by site and date, matching the same logic as above
            site_daily = filtered_df.groupby(['site_id', filtered_df['date'].dt.date]).agg({
                'count': 'sum',
                'rewash_count': 'sum',
                'total_count': 'sum'
            }).reset_index()
            
            # Convert back to datetime
            site_daily['date'] = pd.to_datetime(site_daily['date'])
            
            # Sort
            site_daily = site_daily.sort_values(['site_id', 'date'])
            
            site_fig = px.line(site_daily, x='date', y='count', color='site_id',
                            title='Daily Wash Counts by Site',
                            labels={'count': 'Wash Count', 'date': 'Date', 'site_id': 'Site'})
            
            st.plotly_chart(site_fig, use_container_width=True)
        
        # Show wash type breakdown
        if 'name' in filtered_df.columns:
            st.header("Wash Type Analysis")
            wash_types = filtered_df.groupby('name').agg({
                'count': 'sum',
                'rewash_count': 'sum'
            }).reset_index()
            
            wash_types['total'] = wash_types['count'] + wash_types['rewash_count']
            wash_types = wash_types.sort_values('total', ascending=False)
            
            # Modified to only show count, not rewash count
            wash_fig = px.bar(wash_types, x='name', y='count', 
                            title='Wash Counts by Type',
                            labels={'name': 'Wash Type', 'count': 'Wash Count'})
            
            st.plotly_chart(wash_fig, use_container_width=True)
            
            # Add wash type by site if multiple sites are selected
            if selected_sites and len(selected_sites) > 1:
                st.header("Wash Types by Site")
                
                site_type_data = filtered_df.groupby(['site_id', 'name']).agg({
                    'count': 'sum'  # Removed rewash_count
                }).reset_index()
                
                site_type_fig = px.bar(site_type_data, x='site_id', y='count', 
                                    color='name', 
                                    title='Wash Types Distribution by Site',
                                    labels={'count': 'Wash Count', 'site_id': 'Site', 'name': 'Wash Type'})
                
                st.plotly_chart(site_type_fig, use_container_width=True)
        
        # Add time-based analysis (day of week patterns)
        st.header("Temporal Analysis")
        
        # Extract day of week from date
        if 'date' in filtered_df.columns:
            filtered_df['day_of_week'] = filtered_df['date'].dt.day_name()
            
            day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            dow_data = filtered_df.groupby('day_of_week').agg({
                'count': 'sum'  # Removed rewash_count
            }).reset_index()
            
            # Ensure days are in correct order
            dow_data['day_of_week'] = pd.Categorical(dow_data['day_of_week'], categories=day_order, ordered=True)
            dow_data = dow_data.sort_values('day_of_week')
            
            # Modified to only show count, not rewash count
            dow_fig = px.bar(dow_data, x='day_of_week', y='count',
                           title='Wash Distribution by Day of Week',
                           labels={'day_of_week': 'Day of Week', 'count': 'Wash Count'})
            
            st.plotly_chart(dow_fig, use_container_width=True)

            # Month over month analysis
            st.header("Month over Month Analysis")
            
            # Extract year and month and store both raw and formatted versions
            filtered_df['year_month'] = filtered_df['date'].dt.strftime('%Y-%m')
            
            # Group by year-month
            monthly_data = filtered_df.groupby('year_month').agg({
                'count': 'sum'  # Removed rewash_count
            }).reset_index()
            
            # Sort chronologically
            monthly_data = monthly_data.sort_values('year_month')
            
            # Add formatted month column for display
            monthly_data['formatted_month'] = monthly_data['year_month'].apply(format_year_month)
            
            # Create month-over-month chart with nicely formatted x-axis
            mom_fig = px.bar(monthly_data, x='formatted_month', y='count',
                            title='Monthly Wash Volumes',
                            labels={'formatted_month': 'Month', 'count': 'Wash Count'})
            
            # Ensure x-axis is in chronological order
            mom_fig.update_layout(
                xaxis={'categoryorder': 'array', 'categoryarray': monthly_data['formatted_month'].tolist()}
            )
            
            st.plotly_chart(mom_fig, use_container_width=True)

except Exception as e:
    st.error(f"An error occurred: {e}")
    st.error("If this is a database connection error, please check your connection string and credentials.")
    
    # Provide detailed troubleshooting information
    with st.expander("Troubleshooting Tips"):
        st.markdown("""
        ### Database Connection Issues
        
        1. Verify your connection parameters in .streamlit/secrets.toml or environment variables
        
        2. Check network connectivity:
           - Make sure you have access to the Azure SQL Server
           - Check if any firewalls might be blocking the connection
        
        3. Database Driver Issues:
           - This app uses pymssql instead of pyodbc for better cloud compatibility
        
        ### SQL Query Issues
        
        If the database connection works but the query fails:
        - Verify the table names and column names exist
        - Try simplifying the query for testing
        """)
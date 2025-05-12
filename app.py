import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from utils.db_utils import load_wash_data, load_subscription_data
import os

# Password protection function
def check_password():
    """Returns `True` if the user had the correct password."""
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        # Get the password from secrets or use the default for local development
        try:
            dashboard_password = st.secrets.get("DASHBOARD_PASSWORD", "UCWashDashboard2025")
        except:
            # If running locally without secrets.toml, use default password
            dashboard_password = "UCWashDashboard2025"
            
        if st.session_state["password"] == dashboard_password:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password
        else:
            st.session_state["password_correct"] = False

    # Return True if the password is validated
    if st.session_state.get("password_correct", False):
        return True

    # Show input for password
    st.title("United Car Wash Dashboard")
    st.write("Please enter the password to access this dashboard.")
    st.text_input(
        "Password", type="password", on_change=password_entered, key="password"
    )
    if "password_correct" in st.session_state:
        if not st.session_state["password_correct"]:
            st.error("😕 Password incorrect")
    return False

# Custom function to format year-month as "MMM 'YY"
def format_year_month(year_month_str):
    """Convert 'YYYY-MM' to 'MMM 'YY' format (e.g., 'Jan '23')"""
    try:
        date = datetime.strptime(year_month_str, '%Y-%m')
        return date.strftime("%b '%y")  # Format as "Mar '25"
    except:
        return year_month_str

# Check password before proceeding
if not check_password():
    st.stop()  # Stop execution if password is incorrect

# Page configuration - only runs if password is correct
st.set_page_config(page_title="United Car Wash Analytics", layout="wide")
st.title("United Car Wash Time Series Analysis")

# Create tabs for better organization
tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Site Analysis", "Wash Types", "Subscriptions"])

# Add a try/except block to handle database connection issues gracefully
try:
    # Load the data
    with st.spinner("Loading data from database..."):
        df = load_wash_data()
        
        # Load subscription data
        with st.spinner("Loading subscription data..."):
            sub_df = load_subscription_data()
    
    # Calculate date range
    min_date = df['date'].min().date()  # Convert to Python date for the date picker
    max_date = df['date'].max().date()  # Convert to Python date for the date picker
    
    # Calculate subscription date range
    sub_min_date = sub_df['date'].min().date() if not sub_df.empty else min_date
    sub_max_date = sub_df['date'].max().date() if not sub_df.empty else max_date
    
    # Use the overall min and max dates for consistency
    overall_min_date = min(min_date, sub_min_date)
    overall_max_date = max(max_date, sub_max_date)
    
    # Create sidebar for filters
    st.sidebar.header("Filters")
    
    # Date range selector
    date_range = st.sidebar.date_input(
        "Select Date Range",
        [overall_max_date - timedelta(days=90), overall_max_date],
        min_value=overall_min_date,
        max_value=overall_max_date
    )
    
    if len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date = date_range[0]
        end_date = overall_max_date
    
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
        
        # Filter subscription data similarly
        filtered_sub_df = sub_df[(sub_df['date'].dt.strftime('%Y-%m-%d') >= start_date_str) & 
                              (sub_df['date'].dt.strftime('%Y-%m-%d') <= end_date_str) & 
                              (sub_df['site_id'].isin(selected_sites))]
    else:
        filtered_df = df[(df['date'].dt.strftime('%Y-%m-%d') >= start_date_str) & 
                        (df['date'].dt.strftime('%Y-%m-%d') <= end_date_str)]
        
        # Filter subscription data similarly
        filtered_sub_df = sub_df[(sub_df['date'].dt.strftime('%Y-%m-%d') >= start_date_str) & 
                              (sub_df['date'].dt.strftime('%Y-%m-%d') <= end_date_str)]
    
    # Add data export feature in sidebar
    st.sidebar.markdown("---")
    st.sidebar.header("Data Export")
    
    # Add data source information
    st.sidebar.caption(f"Data updated through: {max_date.strftime('%b %d, %Y')}")
    
    # Create export options
    export_options = st.sidebar.expander("Export Options")
    with export_options:
        # Raw data export
        csv_raw = filtered_df.to_csv(index=False)
        st.download_button(
            "Download Wash Data (CSV)",
            csv_raw,
            f"ucw_raw_data_{start_date_str}_to_{end_date_str}.csv",
            "text/csv",
            key="download-raw-csv",
            help="Export the raw filtered wash data to a CSV file"
        )
        
        # Subscription data export
        if not filtered_sub_df.empty:
            csv_sub = filtered_sub_df.to_csv(index=False)
            st.download_button(
                "Download Subscription Data (CSV)",
                csv_sub,
                f"ucw_subscription_data_{start_date_str}_to_{end_date_str}.csv",
                "text/csv",
                key="download-sub-csv",
                help="Export the subscription data to a CSV file"
            )
        
        # Daily aggregated data export
        if not filtered_df.empty:
            daily_agg = filtered_df.groupby([filtered_df['date'].dt.date, 'site_id']).agg({
                'count': 'sum',
                'rewash_count': 'sum',
                'total_count': 'sum'
            }).reset_index()
            csv_daily = daily_agg.to_csv(index=False)
            st.download_button(
                "Download Daily Summary (CSV)",
                csv_daily,
                f"ucw_daily_summary_{start_date_str}_to_{end_date_str}.csv",
                "text/csv",
                key="download-daily-csv",
                help="Export daily aggregated data by site"
            )
        
        # Monthly aggregated data export
        if not filtered_df.empty:
            filtered_df['year_month'] = filtered_df['date'].dt.strftime('%Y-%m')
            monthly_agg = filtered_df.groupby(['year_month', 'site_id']).agg({
                'count': 'sum',
                'rewash_count': 'sum',
                'total_count': 'sum'
            }).reset_index()
            csv_monthly = monthly_agg.to_csv(index=False)
            st.download_button(
                "Download Monthly Summary (CSV)",
                csv_monthly,
                f"ucw_monthly_summary_{start_date_str}_to_{end_date_str}.csv",
                "text/csv",
                key="download-monthly-csv",
                help="Export monthly aggregated data by site"
            )
    
    # Check if data exists after filtering
    if filtered_df.empty:
        st.warning("No wash data available for the selected filters. Please adjust your selection.")
    else:
        # Calculate aggregate statistics first for consistency
        total_washes = filtered_df['count'].sum()
        total_rewashes = filtered_df['rewash_count'].sum()
        total_combined = total_washes + total_rewashes
        rewash_pct = total_rewashes / total_washes * 100 if total_washes > 0 else 0
        
        # Time Series data preparation
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
        
        # Create main visualization
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
        
        # Site comparison preparation
        if selected_sites and len(selected_sites) > 1:
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
        
        # Wash type breakdown preparation
        if 'name' in filtered_df.columns:
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
            
            # Add wash type by site if multiple sites are selected
            if selected_sites and len(selected_sites) > 1:
                site_type_data = filtered_df.groupby(['site_id', 'name']).agg({
                    'count': 'sum'  # Removed rewash_count
                }).reset_index()
                
                site_type_fig = px.bar(site_type_data, x='site_id', y='count', 
                                    color='name', 
                                    title='Wash Types Distribution by Site',
                                    labels={'count': 'Wash Count', 'site_id': 'Site', 'name': 'Wash Type'})
        
        # Day of week analysis preparation
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
            
            # Month over month analysis
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
        
        # Subscription data visualization preparation
        if not filtered_sub_df.empty:
            # Calculate subscription metrics
            total_active = filtered_sub_df['active_count'].sum()
            total_created = filtered_sub_df['created_count'].sum()
            total_canceled = filtered_sub_df['canceled_count'].sum()
            net_change = total_created - total_canceled
            
            # Active subscriptions over time
            sub_daily = filtered_sub_df.groupby(filtered_sub_df['date'].dt.date).agg({
                'active_count': 'sum',
                'created_count': 'sum',
                'canceled_count': 'sum',
                'trial_count': 'sum',
                'recurring_count': 'sum',
                'net_change': 'sum'
            }).reset_index()
            
            # Convert back to datetime for plotting
            sub_daily['date'] = pd.to_datetime(sub_daily['date'])
            
            # Sort by date
            sub_daily = sub_daily.sort_values('date')
            
            # Calculate rolling averages for subscriptions
            sub_daily[f'{rolling_window}d_active_avg'] = sub_daily['active_count'].rolling(rolling_window).mean()
            
            # Create active subscriptions chart
            active_fig = go.Figure()
            
            active_fig.add_trace(
                go.Scatter(x=sub_daily['date'], y=sub_daily['active_count'], 
                        mode='lines', name='Active Subscriptions')
            )
            
            active_fig.add_trace(
                go.Scatter(x=sub_daily['date'], y=sub_daily[f'{rolling_window}d_active_avg'], 
                        mode='lines', name=f'{rolling_window}-Day Rolling Avg',
                        line=dict(color='red'))
            )
            
            active_fig.update_layout(
                title_text="Active Subscriptions Over Time",
                xaxis_title="Date",
                yaxis_title="Number of Subscriptions",
                legend=dict(x=0, y=1.1, orientation='h')
            )
            
            # Create new subscriptions by day visualization
            daily_created_fig = go.Figure()
            
            daily_created_fig.add_trace(
                go.Bar(x=sub_daily['date'], y=sub_daily['created_count'], 
                    name='New Subscriptions', marker_color='green')
            )
            
            daily_created_fig.update_layout(
                title_text="New Subscriptions Created By Day",
                xaxis_title="Date",
                yaxis_title="Number of Subscriptions",
                legend=dict(x=0, y=1.1, orientation='h')
            )
            
            # Monthly subscription metrics
            # Extract year and month
            filtered_sub_df['year_month'] = filtered_sub_df['date'].dt.strftime('%Y-%m')
            
            # Group by year-month
            monthly_sub_data = filtered_sub_df.groupby('year_month').agg({
                'created_count': 'sum',
                'canceled_count': 'sum',
                'active_count': 'mean',  # average active count for the month
                'trial_count': 'mean',   # average trial count for the month
                'recurring_count': 'mean' # average recurring count for the month
            }).reset_index()
            
            # Calculate net change by month
            monthly_sub_data['net_change'] = monthly_sub_data['created_count'] - monthly_sub_data['canceled_count']
            
            # Calculate churn rate (canceled / active at start of period)
            # We'll use the previous month's active count as the denominator where possible
            monthly_sub_data = monthly_sub_data.sort_values('year_month')
            
            # Make a copy of active_count shifted by one month for previous month's value
            monthly_sub_data['prev_active'] = monthly_sub_data['active_count'].shift(1)
            
            # Calculate churn rate safely with error handling
            try:
                # Handle division by zero by using fillna
                monthly_sub_data['churn_rate'] = monthly_sub_data.apply(
                    lambda x: (x['canceled_count'] / x['prev_active'] * 100) if x['prev_active'] > 0 else 0, 
                    axis=1
                )
            except:
                # Fallback if the above fails
                monthly_sub_data['churn_rate'] = 0
            
            # Add formatted month column for display
            monthly_sub_data['formatted_month'] = monthly_sub_data['year_month'].apply(format_year_month)
            
            # Create waterfall chart for monthly new vs canceled
            monthly_sub_fig = go.Figure()
            
            monthly_sub_fig.add_trace(
                go.Bar(
                    x=monthly_sub_data['formatted_month'],
                    y=monthly_sub_data['created_count'],
                    name='New Subscriptions',
                    marker_color='green'
                )
            )
            
            monthly_sub_fig.add_trace(
                go.Bar(
                    x=monthly_sub_data['formatted_month'],
                    y=-monthly_sub_data['canceled_count'],
                    name='Canceled Subscriptions',
                    marker_color='red'
                )
            )
            
            monthly_sub_fig.add_trace(
                go.Scatter(
                    x=monthly_sub_data['formatted_month'],
                    y=monthly_sub_data['net_change'],
                    mode='lines+markers',
                    name='Net Change',
                    line=dict(color='blue', width=3)
                )
            )
            
            monthly_sub_fig.update_layout(
                title_text="Monthly Subscription Creation vs Cancellation",
                xaxis_title="Month",
                yaxis_title="Number of Subscriptions",
                barmode='relative',
                legend=dict(x=0, y=1.1, orientation='h'),
                xaxis={'categoryorder': 'array', 'categoryarray': monthly_sub_data['formatted_month'].tolist()}
            )
            
            # Create churn rate visualization
            churn_fig = go.Figure()
            
            churn_fig.add_trace(
                go.Bar(
                    x=monthly_sub_data['formatted_month'],
                    y=monthly_sub_data['churn_rate'],
                    name='Monthly Churn Rate',
                    marker_color='orange'
                )
            )
            
            # Add a line for average churn rate
            avg_churn = monthly_sub_data['churn_rate'].mean() if not monthly_sub_data.empty else 0
            if not pd.isna(avg_churn):  # Check if average is a valid number
                churn_fig.add_trace(
                    go.Scatter(
                        x=monthly_sub_data['formatted_month'],
                        y=[avg_churn] * len(monthly_sub_data),
                        mode='lines',
                        name=f'Average ({avg_churn:.1f}%)',
                        line=dict(color='red', width=2, dash='dash')
                    )
                )
            
            churn_fig.update_layout(
                title_text="Monthly Churn Rate",
                xaxis_title="Month",
                yaxis_title="Churn Rate (%)",
                legend=dict(x=0, y=1.1, orientation='h'),
                xaxis={'categoryorder': 'array', 'categoryarray': monthly_sub_data['formatted_month'].tolist()}
            )
            
            # Trial vs recurring visualization
            type_fig = go.Figure()
            
            type_fig.add_trace(
                go.Scatter(x=sub_daily['date'], y=sub_daily['trial_count'], 
                        mode='lines', name='Trial Subscriptions',
                        line=dict(color='orange'))
            )
            
            type_fig.add_trace(
                go.Scatter(x=sub_daily['date'], y=sub_daily['recurring_count'], 
                        mode='lines', name='Recurring Subscriptions',
                        line=dict(color='blue'))
            )
            
            type_fig.update_layout(
                title_text="Trial vs Recurring Subscriptions",
                xaxis_title="Date",
                yaxis_title="Number of Subscriptions",
                legend=dict(x=0, y=1.1, orientation='h')
            )
            
            # Site comparison for subscriptions
            if selected_sites and len(selected_sites) > 1:
                # Group by site and date
                site_sub_daily = filtered_sub_df.groupby(['site_id', filtered_sub_df['date'].dt.date]).agg({
                    'active_count': 'sum',
                    'created_count': 'sum',
                    'canceled_count': 'sum'
                }).reset_index()
                
                # Convert back to datetime
                site_sub_daily['date'] = pd.to_datetime(site_sub_daily['date'])
                
                # Sort
                site_sub_daily = site_sub_daily.sort_values(['site_id', 'date'])
                
                site_sub_fig = px.line(site_sub_daily, x='date', y='active_count', color='site_id',
                                    title='Active Subscriptions by Site',
                                    labels={'active_count': 'Active Subscriptions', 'date': 'Date', 'site_id': 'Site'})
        
        # Display in tabs
        with tab1:
            st.header("Key Statistics")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Washes", f"{total_washes:,}")
                
            with col2:
                st.metric("Total Rewashes", f"{total_rewashes:,}")
                
            with col3:
                st.metric("Rewash Percentage", f"{rewash_pct:.2f}%")
            
            st.header("Time Series Analysis")
            st.plotly_chart(fig, use_container_width=True)
            
            # Temporal Analysis
            st.header("Temporal Analysis")
            st.plotly_chart(dow_fig, use_container_width=True)
            st.plotly_chart(mom_fig, use_container_width=True)
        
        with tab2:
            st.header("Site Comparison")
            if selected_sites and len(selected_sites) > 1:
                st.plotly_chart(site_fig, use_container_width=True)
                
                if 'name' in filtered_df.columns and 'site_type_fig' in locals():
                    st.header("Wash Types by Site")
                    st.plotly_chart(site_type_fig, use_container_width=True)
            else:
                st.info("Please select multiple sites in the sidebar to enable site comparison.")
        
        with tab3:
            if 'name' in filtered_df.columns:
                st.header("Wash Type Analysis")
                st.plotly_chart(wash_fig, use_container_width=True)
            else:
                st.info("Wash type data is not available.")
        
        with tab4:
            st.header("Subscription Analysis")
            
            if not filtered_sub_df.empty:
                # Key subscription metrics
                st.subheader("Key Subscription Metrics")
                sub_col1, sub_col2, sub_col3, sub_col4 = st.columns(4)
                
                with sub_col1:
                    st.metric("Active Subscriptions", f"{total_active:,}")
                
                with sub_col2:
                    st.metric("New Subscriptions", f"{total_created:,}")
                
                with sub_col3:
                    st.metric("Canceled Subscriptions", f"{total_canceled:,}")
                
                with sub_col4:
                    # Convert numpy.int64 to Python int for delta parameter
                    st.metric("Net Change", f"{net_change:+,}", delta=int(net_change))
                
                # Subscription charts
                st.plotly_chart(active_fig, use_container_width=True)
                
                # Daily subscriptions created
                st.subheader("Daily Subscription Activity")
                st.plotly_chart(daily_created_fig, use_container_width=True)
                
                # Monthly subscription metrics
                st.subheader("Monthly Subscription Trends")
                st.plotly_chart(monthly_sub_fig, use_container_width=True)
                
                # Churn rate visualization
                st.subheader("Membership Churn Analysis")
                st.plotly_chart(churn_fig, use_container_width=True)
                
                # Trial vs recurring
                st.subheader("Subscription Types")
                st.plotly_chart(type_fig, use_container_width=True)
                
                # Site comparison
                if selected_sites and len(selected_sites) > 1:
                    st.header("Subscription Comparison by Site")
                    st.plotly_chart(site_sub_fig, use_container_width=True)
            else:
                st.info("No subscription data available for the selected filters. Please adjust your selection.")

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
           - This app uses pyodbc for database connectivity
           - If you're having issues, try switching to another driver in db_utils.py
        
        ### SQL Query Issues
        
        If the database connection works but the query fails:
        - Verify the table names and column names exist
        - Try simplifying the query for testing
        """)
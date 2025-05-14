import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from utils.db_utils import load_wash_data, load_subscription_data, load_sales_data  
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
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Overview", "Site Analysis", "Wash Types", "Subscriptions", "Sales Analysis"])

# Add a try/except block to handle database connection issues gracefully
try:
    # Load the data
    with st.spinner("Loading data from database..."):
        df = load_wash_data()
        
        # Load subscription data
        with st.spinner("Loading subscription data..."):
            sub_df = load_subscription_data()

        # Load sales data
        with st.spinner("Loading sales data from database..."):
            sales_df = load_sales_data()
    
    # Calculate date range
    min_date = df['date'].min().date()  # Convert to Python date for the date picker
    max_date = df['date'].max().date()  # Convert to Python date for the date picker

    # Calculate sales date range
    sales_min_date = sales_df['date'].min().date() if not sales_df.empty else min_date
    sales_max_date = sales_df['date'].max().date() if not sales_df.empty else max_date
    
    # Calculate subscription date range
    sub_min_date = sub_df['date'].min().date() if not sub_df.empty else min_date
    sub_max_date = sub_df['date'].max().date() if not sub_df.empty else max_date
    
    # Use the overall min and max dates for consistency
    overall_min_date = min(min_date, sub_min_date, sales_min_date)
    overall_max_date = max(max_date, sub_max_date, sales_max_date)
    
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
    
    # Site selector - MOVED UP BEFORE ANY USAGE
    all_sites = sorted(df['site_id'].unique())
    selected_sites = st.sidebar.multiselect(
        "Select Sites",
        options=all_sites,
        default=all_sites[:5] if len(all_sites) > 5 else all_sites
    )
    
    # Rolling average period
    rolling_window = st.sidebar.slider("Rolling Average Window (days)", 1, 60, 7)
    
    # Filter data - IMPORTANT: Convert the date objects back to strings for filtering
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')

    # Filter data using string comparison to avoid type issues
    if selected_sites:
        filtered_df = df[(df['date'].dt.strftime('%Y-%m-%d') >= start_date_str) & 
                        (df['date'].dt.strftime('%Y-%m-%d') <= end_date_str) & 
                        (df['site_id'].isin(selected_sites))]
        
        # Filter subscription data similarly
        filtered_sub_df = sub_df[(sub_df['date'].dt.strftime('%Y-%m-%d') >= start_date_str) & 
                            (sub_df['date'].dt.strftime('%Y-%m-%d') <= end_date_str) & 
                            (sub_df['site_id'].isin(selected_sites))]
                            
        # Filter sales data
        filtered_sales_df = sales_df[(sales_df['date'] >= pd.to_datetime(start_date)) & 
                            (sales_df['date'] <= pd.to_datetime(end_date)) & 
                            (sales_df['site_id'].isin(selected_sites))]
    else:
        filtered_df = df[(df['date'].dt.strftime('%Y-%m-%d') >= start_date_str) & 
                        (df['date'].dt.strftime('%Y-%m-%d') <= end_date_str)]
        
        # Filter subscription data similarly
        filtered_sub_df = sub_df[(sub_df['date'].dt.strftime('%Y-%m-%d') >= start_date_str) & 
                            (sub_df['date'].dt.strftime('%Y-%m-%d') <= end_date_str)]
                            
        # Filter sales data
        filtered_sales_df = sales_df[(sales_df['date'] >= pd.to_datetime(start_date)) & 
                            (sales_df['date'] <= pd.to_datetime(end_date))]
    
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
        
        # Sales data export
        if not filtered_sales_df.empty:
            csv_sales = filtered_sales_df.to_csv(index=False)
            st.download_button(
                "Download Sales Data (CSV)",
                csv_sales,
                f"ucw_sales_data_{start_date_str}_to_{end_date_str}.csv",
                "text/csv",
                key="download-sales-csv",
                help="Export the sales data to a CSV file"
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
        
        # Tab 4 - Subscriptions tab content
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

        # Tab 5 - Sales Analysis tab content - ADD THIS RIGHT AFTER TAB 4
        with tab5:
            st.header("Sales Analysis")
            
            if not filtered_sales_df.empty:
                # Calculate key metrics
                total_revenue = filtered_sales_df['revenue'].sum()
                total_expenses = filtered_sales_df['expense_total'].sum()
                net_income = total_revenue - total_expenses
                total_cash_sales = filtered_sales_df['cash_sales'].sum()
                total_credit_card_sales = filtered_sales_df['credit_card_sales'].sum()
                total_club_ppw_sales = filtered_sales_df['club_and_ppw_sales'].sum()
                
                # Display key metrics
                st.subheader("Key Financial Metrics")
                fin_col1, fin_col2, fin_col3 = st.columns(3)
                
                with fin_col1:
                    st.metric("Total Revenue", f"${total_revenue:,.2f}")
                
                with fin_col2:
                    st.metric("Total Expenses", f"${total_expenses:,.2f}")
                
                with fin_col3:
                    st.metric("Net Income", f"${net_income:,.2f}", 
                            delta=f"${net_income:,.2f}" if net_income > 0 else f"-${abs(net_income):,.2f}")
                
                # Sales breakdown
                st.subheader("Sales Breakdown")
                sales_col1, sales_col2, sales_col3 = st.columns(3)
                
                with sales_col1:
                    st.metric("Cash Sales", f"${total_cash_sales:,.2f}")
                
                with sales_col2:
                    st.metric("Credit Card Sales", f"${total_credit_card_sales:,.2f}")
                
                with sales_col3:
                    st.metric("Club & PPW Sales", f"${total_club_ppw_sales:,.2f}")
                
                # Create time series data for revenue
                daily_revenue = filtered_sales_df.groupby(filtered_sales_df['date'].dt.date).agg({
                    'revenue': 'sum',
                    'expense_total': 'sum',
                    'cash_sales': 'sum',
                    'credit_card_sales': 'sum',
                    'club_and_ppw_sales': 'sum'
                }).reset_index()
                
                # Convert back to datetime for plotting
                daily_revenue['date'] = pd.to_datetime(daily_revenue['date'])
                
                # Sort by date
                daily_revenue = daily_revenue.sort_values('date')
                
                # Calculate rolling averages
                daily_revenue[f'{rolling_window}d_revenue_avg'] = daily_revenue['revenue'].rolling(rolling_window).mean()
                
                # Create revenue over time visualization
                revenue_fig = go.Figure()
                
                revenue_fig.add_trace(
                    go.Scatter(x=daily_revenue['date'], y=daily_revenue['revenue'], 
                            mode='lines', name='Daily Revenue')
                )
                
                revenue_fig.add_trace(
                    go.Scatter(x=daily_revenue['date'], y=daily_revenue[f'{rolling_window}d_revenue_avg'], 
                            mode='lines', name=f'{rolling_window}-Day Rolling Avg',
                            line=dict(color='red'))
                )
                
                revenue_fig.update_layout(
                    title_text="Revenue Over Time",
                    xaxis_title="Date",
                    yaxis_title="Revenue ($)",
                    legend=dict(x=0, y=1.1, orientation='h')
                )
                
                st.plotly_chart(revenue_fig, use_container_width=True)
                
                # Revenue vs Expenses
                rev_exp_fig = go.Figure()
                
                rev_exp_fig.add_trace(
                    go.Scatter(x=daily_revenue['date'], y=daily_revenue['revenue'], 
                            mode='lines', name='Revenue',
                            line=dict(color='green'))
                )
                
                rev_exp_fig.add_trace(
                    go.Scatter(x=daily_revenue['date'], y=daily_revenue['expense_total'], 
                            mode='lines', name='Expenses',
                            line=dict(color='red'))
                )
                
                # Add net income
                daily_revenue['net_income'] = daily_revenue['revenue'] - daily_revenue['expense_total']
                
                rev_exp_fig.add_trace(
                    go.Scatter(x=daily_revenue['date'], y=daily_revenue['net_income'], 
                            mode='lines', name='Net Income',
                            line=dict(color='blue'))
                )
                
                rev_exp_fig.update_layout(
                    title_text="Revenue vs Expenses Over Time",
                    xaxis_title="Date",
                    yaxis_title="Amount ($)",
                    legend=dict(x=0, y=1.1, orientation='h')
                )
                
                st.plotly_chart(rev_exp_fig, use_container_width=True)
                
                # Sales breakdown chart
                sales_breakdown_fig = go.Figure()
                
                sales_breakdown_fig.add_trace(
                    go.Scatter(x=daily_revenue['date'], y=daily_revenue['cash_sales'], 
                            mode='lines', name='Cash Sales',
                            line=dict(color='green'))
                )
                
                sales_breakdown_fig.add_trace(
                    go.Scatter(x=daily_revenue['date'], y=daily_revenue['credit_card_sales'], 
                            mode='lines', name='Credit Card Sales',
                            line=dict(color='blue'))
                )
                
                sales_breakdown_fig.add_trace(
                    go.Scatter(x=daily_revenue['date'], y=daily_revenue['club_and_ppw_sales'], 
                            mode='lines', name='Club & PPW Sales',
                            line=dict(color='purple'))
                )
                
                sales_breakdown_fig.update_layout(
                    title_text="Sales Breakdown Over Time",
                    xaxis_title="Date",
                    yaxis_title="Sales ($)",
                    legend=dict(x=0, y=1.1, orientation='h')
                )
                
                st.plotly_chart(sales_breakdown_fig, use_container_width=True)
                
                # Monthly analysis
                filtered_sales_df['year_month'] = filtered_sales_df['date'].dt.strftime('%Y-%m')
                
                # Group by year-month
                monthly_sales = filtered_sales_df.groupby('year_month').agg({
                    'revenue': 'sum',
                    'expense_total': 'sum',
                    'cash_sales': 'sum',
                    'credit_card_sales': 'sum',
                    'club_and_ppw_sales': 'sum'
                }).reset_index()
                
                # Calculate net income
                monthly_sales['net_income'] = monthly_sales['revenue'] - monthly_sales['expense_total']
                
                # Sort chronologically
                monthly_sales = monthly_sales.sort_values('year_month')
                
                # Add formatted month column for display
                monthly_sales['formatted_month'] = monthly_sales['year_month'].apply(format_year_month)
                
                # Create monthly revenue chart
                monthly_fig = go.Figure()
                
                monthly_fig.add_trace(
                    go.Bar(
                        x=monthly_sales['formatted_month'],
                        y=monthly_sales['revenue'],
                        name='Revenue',
                        marker_color='green'
                    )
                )
                
                monthly_fig.add_trace(
                    go.Bar(
                        x=monthly_sales['formatted_month'],
                        y=monthly_sales['expense_total'],
                        name='Expenses',
                        marker_color='red'
                    )
                )
                
                monthly_fig.add_trace(
                    go.Scatter(
                        x=monthly_sales['formatted_month'],
                        y=monthly_sales['net_income'],
                        mode='lines+markers',
                        name='Net Income',
                        line=dict(color='blue', width=3)
                    )
                )
                
                monthly_fig.update_layout(
                    title_text="Monthly Revenue and Expenses",
                    xaxis_title="Month",
                    yaxis_title="Amount ($)",
                    barmode='group',
                    legend=dict(x=0, y=1.1, orientation='h'),
                    xaxis={'categoryorder': 'array', 'categoryarray': monthly_sales['formatted_month'].tolist()}
                )
                
                st.plotly_chart(monthly_fig, use_container_width=True)
                
                # Monthly sales breakdown
                st.subheader("Monthly Sales Breakdown")
                
                # Create stacked bar chart for types of sales
                monthly_breakdown_fig = px.bar(monthly_sales, 
                                            x='formatted_month', 
                                            y=['cash_sales', 'credit_card_sales', 'club_and_ppw_sales'],
                                            title='Monthly Sales by Type',
                                            labels={'value': 'Sales ($)', 'formatted_month': 'Month', 'variable': 'Sales Type'},
                                            barmode='stack')
                
                # Update names for legend
                monthly_breakdown_fig.update_layout(
                    xaxis={'categoryorder': 'array', 'categoryarray': monthly_sales['formatted_month'].tolist()},
                    legend_title_text='Sales Type',
                    legend=dict(
                        yanchor="top",
                        y=0.99,
                        xanchor="left",
                        x=0.01
                    )
                )
                
                # Rename series in legend
                monthly_breakdown_fig.for_each_trace(lambda t: t.update(
                    name=t.name.replace("_sales", "").replace("_", " ").title(),
                    legendgroup=t.name.replace("_sales", "").replace("_", " ").title(),
                    hovertemplate=t.hovertemplate.replace("_sales", "").replace("_", " ").title()
                ))
                
                st.plotly_chart(monthly_breakdown_fig, use_container_width=True)
                
                # Expense breakdown
                st.subheader("Expense Analysis")
                
                # Get expense columns
                expense_cols = [
                    'wkly_sub_credit_card_fees', 'technology_fee', 'brand_development_fee', 
                    'royalty_fee', 'fee_adjustments', 'radar_fee_amt', 'pre_auth_fee_amt',
                    'volume_billing_fee_amt', 'payout_fee_amt', 'auto_card_update_fee_amt',
                    'active_account_billing_fee_amt', 'active_reader_fee_amt', 'app_adjustment'
                ]
                
                # Sum up expenses
                expense_total = filtered_sales_df[expense_cols].sum().reset_index()
                expense_total.columns = ['expense_type', 'amount']
                
                # Remove expenses that are zero
                expense_total = expense_total[expense_total['amount'] > 0]
                
                # Sort by amount
                expense_total = expense_total.sort_values('amount', ascending=False)
                
                # Create expense breakdown chart if data exists
                if not expense_total.empty:
                    expense_pie = px.pie(
                        expense_total, 
                        values='amount', 
                        names='expense_type',
                        title='Expense Breakdown',
                        hole=0.4,
                    )
                    
                    # Improve expense type labels
                    expense_pie.update_traces(
                        textinfo='percent+label',
                        texttemplate='%{label}: $%{value:,.2f}<br>(%{percent})',
                        hovertemplate='%{label}<br>$%{value:,.2f}<br>%{percent}'
                    )
                    
                    st.plotly_chart(expense_pie, use_container_width=True)
                else:
                    st.info("No expense data available for the selected period.")
                
                # PPW vs Club Wash Count Comparison
                st.subheader("PPW vs Club Wash Count Comparison")
                
                # Calculate revenue totals first (to avoid the "not defined" error)
                # Calculate PPW revenue
                total_ppw_quality = filtered_sales_df['gross_ppw_payments_quality'].sum() - filtered_sales_df['gross_ppw_refunds_quality'].sum()
                total_ppw_works = filtered_sales_df['gross_ppw_payments_works'].sum() - filtered_sales_df['gross_ppw_refunds_works'].sum()
                total_ppw_ultimate = filtered_sales_df['gross_ppw_payments_ultimate'].sum() - filtered_sales_df['gross_ppw_refunds_ultimate'].sum()
                total_ppw_super = filtered_sales_df['gross_ppw_payments_super'].sum() - filtered_sales_df['gross_ppw_refunds_super'].sum()
                
                # Calculate total PPW revenue
                total_ppw_revenue = total_ppw_quality + total_ppw_works + total_ppw_ultimate + total_ppw_super
                
                # Calculate Club revenue (if these columns exist)
                try:
                    total_club_quality = filtered_sales_df['gross_club_payments_quality'].sum() - filtered_sales_df['gross_club_refunds_quality'].sum() if 'gross_club_payments_quality' in filtered_sales_df.columns else 0
                    total_club_works = filtered_sales_df['gross_club_payments_works'].sum() - filtered_sales_df['gross_club_refunds_works'].sum() if 'gross_club_payments_works' in filtered_sales_df.columns else 0
                    total_club_ultimate = filtered_sales_df['gross_club_payments_ultimate'].sum() - filtered_sales_df['gross_club_refunds_ultimate'].sum() if 'gross_club_payments_ultimate' in filtered_sales_df.columns else 0
                    total_club_super = filtered_sales_df['gross_club_payments_super'].sum() - filtered_sales_df['gross_club_refunds_super'].sum() if 'gross_club_payments_super' in filtered_sales_df.columns else 0
                    
                    # Calculate total Club revenue
                    total_club_revenue = total_club_quality + total_club_works + total_club_ultimate + total_club_super
                except:
                    # If the club revenue columns don't exist, estimate club revenue
                    # by subtracting PPW revenue from total club_and_ppw_sales
                    total_club_revenue = filtered_sales_df['club_and_ppw_sales'].sum() - total_ppw_revenue
                    
                # Calculate PPW vs Club wash counts
                try:
                    # Sum up PPW counts across all membership tiers
                    total_ppw_count = (
                        filtered_sales_df['ppw_quality_count'].sum() +
                        filtered_sales_df['ppw_works_count'].sum() +
                        filtered_sales_df['ppw_ultimate_count'].sum() +
                        filtered_sales_df['ppw_super_count'].sum()
                    )
                    
                    # Sum up Club counts across all membership tiers
                    total_club_count = (
                        filtered_sales_df['club_quality_count'].sum() +
                        filtered_sales_df['club_works_count'].sum() +
                        filtered_sales_df['club_ultimate_count'].sum() +
                        filtered_sales_df['club_super_count'].sum()
                    )
                    
                    # Create comparison dataframe
                    wash_counts = pd.DataFrame({
                        'program': ['Pay Per Wash (PPW)', 'Club Membership'],
                        'wash_count': [total_ppw_count, total_club_count]
                    })
                    
                    # Create charts only if we have wash count data
                    if total_ppw_count > 0 or total_club_count > 0:
                        # Create pie chart
                        wash_count_pie = px.pie(
                            wash_counts,
                            values='wash_count',
                            names='program',
                            title='PPW vs Club Wash Count Distribution',
                            hole=0.4,
                            color_discrete_map={'Pay Per Wash (PPW)': 'royalblue', 'Club Membership': 'darkgreen'}
                        )
                        
                        wash_count_pie.update_traces(
                            textinfo='percent+label+value',
                            texttemplate='%{label}<br>%{value:,} washes<br>(%{percent})',
                            hovertemplate='%{label}<br>%{value:,} washes<br>(%{percent})'
                        )
                        
                        st.plotly_chart(wash_count_pie, use_container_width=True)
                        
                        # Create detailed breakdown by wash type
                        wash_types_data = pd.DataFrame({
                            'wash_type': ['Quality', 'Works', 'Ultimate', 'Super'],
                            'PPW': [
                                filtered_sales_df['ppw_quality_count'].sum(),
                                filtered_sales_df['ppw_works_count'].sum(),
                                filtered_sales_df['ppw_ultimate_count'].sum(),
                                filtered_sales_df['ppw_super_count'].sum()
                            ],
                            'Club': [
                                filtered_sales_df['club_quality_count'].sum(),
                                filtered_sales_df['club_works_count'].sum(),
                                filtered_sales_df['club_ultimate_count'].sum(),
                                filtered_sales_df['club_super_count'].sum()
                            ]
                        })
                        
                        # Remove rows where both PPW and Club are zero
                        wash_types_data = wash_types_data[(wash_types_data['PPW'] > 0) | (wash_types_data['Club'] > 0)]
                        
                        if not wash_types_data.empty:
                            # Create grouped bar chart
                            wash_types_fig = px.bar(
                                wash_types_data,
                                x='wash_type',
                                y=['PPW', 'Club'],
                                title='PPW vs Club Wash Counts by Wash Type',
                                labels={
                                    'value': 'Number of Washes', 
                                    'wash_type': 'Wash Type',
                                    'variable': 'Program'
                                },
                                barmode='group',
                                color_discrete_map={'PPW': 'royalblue', 'Club': 'darkgreen'},
                                text_auto=True
                            )
                            
                            st.plotly_chart(wash_types_fig, use_container_width=True)
                            
                            # Calculate and display average washes per revenue dollar
                            if total_ppw_revenue > 0 and total_ppw_count > 0:
                                ppw_efficiency = total_ppw_count / total_ppw_revenue
                                st.metric("PPW Washes per Revenue Dollar", f"{ppw_efficiency:.4f}")
                            
                            if total_club_revenue > 0 and total_club_count > 0:
                                club_efficiency = total_club_count / total_club_revenue
                                st.metric("Club Washes per Revenue Dollar", f"{club_efficiency:.4f}")
                        
                        # Try to create time series of wash counts if possible
                        try:
                            # Group by date to get daily wash counts
                            daily_wash_counts = filtered_sales_df.groupby(filtered_sales_df['date'].dt.date).agg({
                                'date': 'first',
                                'ppw_quality_count': 'sum',
                                'ppw_works_count': 'sum',
                                'ppw_ultimate_count': 'sum',
                                'ppw_super_count': 'sum',
                                'club_quality_count': 'sum',
                                'club_works_count': 'sum',
                                'club_ultimate_count': 'sum',
                                'club_super_count': 'sum'
                            }).reset_index(drop=True)
                            
                            # Calculate totals
                            daily_wash_counts['ppw_total'] = (
                                daily_wash_counts['ppw_quality_count'] +
                                daily_wash_counts['ppw_works_count'] +
                                daily_wash_counts['ppw_ultimate_count'] +
                                daily_wash_counts['ppw_super_count']
                            )
                            
                            daily_wash_counts['club_total'] = (
                                daily_wash_counts['club_quality_count'] +
                                daily_wash_counts['club_works_count'] +
                                daily_wash_counts['club_ultimate_count'] +
                                daily_wash_counts['club_super_count']
                            )
                            
                            # Convert date to datetime
                            daily_wash_counts['date'] = pd.to_datetime(daily_wash_counts['date'])
                            
                            # Sort by date
                            daily_wash_counts = daily_wash_counts.sort_values('date')
                            
                            # Create time series visualization
                            wash_count_trend = go.Figure()
                            
                            wash_count_trend.add_trace(
                                go.Scatter(
                                    x=daily_wash_counts['date'], 
                                    y=daily_wash_counts['ppw_total'],
                                    mode='lines', 
                                    name='PPW Wash Count',
                                    line=dict(color='royalblue')
                                )
                            )
                            
                            wash_count_trend.add_trace(
                                go.Scatter(
                                    x=daily_wash_counts['date'], 
                                    y=daily_wash_counts['club_total'],
                                    mode='lines', 
                                    name='Club Wash Count',
                                    line=dict(color='darkgreen')
                                )
                            )
                            
                            wash_count_trend.update_layout(
                                title_text="PPW vs Club Wash Counts Over Time",
                                xaxis_title="Date",
                                yaxis_title="Number of Washes",
                                legend=dict(x=0, y=1.1, orientation='h')
                            )
                            
                            st.plotly_chart(wash_count_trend, use_container_width=True)
                        except Exception as e:
                            st.info(f"Could not generate wash count time series: {e}")
                    else:
                        st.info("No PPW or Club wash count data available for the selected period.")
                except Exception as e:
                    st.info(f"Could not generate PPW vs Club wash count comparison: {e}")
                
                # Membership breakdown
                st.subheader("Membership Revenue Analysis")
                
                # Calculate membership stats for PPW
                total_ppw_quality = filtered_sales_df['gross_ppw_payments_quality'].sum() - filtered_sales_df['gross_ppw_refunds_quality'].sum()
                total_ppw_works = filtered_sales_df['gross_ppw_payments_works'].sum() - filtered_sales_df['gross_ppw_refunds_works'].sum()
                total_ppw_ultimate = filtered_sales_df['gross_ppw_payments_ultimate'].sum() - filtered_sales_df['gross_ppw_refunds_ultimate'].sum()
                total_ppw_super = filtered_sales_df['gross_ppw_payments_super'].sum() - filtered_sales_df['gross_ppw_refunds_super'].sum()
                
                # Calculate total PPW revenue
                total_ppw_revenue = total_ppw_quality + total_ppw_works + total_ppw_ultimate + total_ppw_super
                
                # Calculate membership stats for Club (if these columns exist)
                # Assuming the Club sales follow a similar naming pattern - adjust if different
                try:
                    total_club_quality = filtered_sales_df['gross_club_payments_quality'].sum() - filtered_sales_df['gross_club_refunds_quality'].sum() if 'gross_club_payments_quality' in filtered_sales_df.columns else 0
                    total_club_works = filtered_sales_df['gross_club_payments_works'].sum() - filtered_sales_df['gross_club_refunds_works'].sum() if 'gross_club_payments_works' in filtered_sales_df.columns else 0
                    total_club_ultimate = filtered_sales_df['gross_club_payments_ultimate'].sum() - filtered_sales_df['gross_club_refunds_ultimate'].sum() if 'gross_club_payments_ultimate' in filtered_sales_df.columns else 0
                    total_club_super = filtered_sales_df['gross_club_payments_super'].sum() - filtered_sales_df['gross_club_refunds_super'].sum() if 'gross_club_payments_super' in filtered_sales_df.columns else 0
                    
                    # Calculate total Club revenue
                    total_club_revenue = total_club_quality + total_club_works + total_club_ultimate + total_club_super
                except:
                    # If the club revenue columns don't exist, estimate club revenue
                    # by subtracting PPW revenue from total club_and_ppw_sales
                    total_club_revenue = filtered_sales_df['club_and_ppw_sales'].sum() - total_ppw_revenue
                    total_club_quality = 0
                    total_club_works = 0
                    total_club_ultimate = 0
                    total_club_super = 0
                
                # Create membership revenue data
                membership_data = pd.DataFrame({
                    'membership_type': ['Quality', 'Works', 'Ultimate', 'Super'],
                    'revenue': [total_ppw_quality, total_ppw_works, total_ppw_ultimate, total_ppw_super]
                })
                
                # Remove zero revenue membership types
                membership_data = membership_data[membership_data['revenue'] > 0]
                
                # Create membership counts data
                membership_counts = pd.DataFrame({
                    'membership_type': ['Quality', 'Works', 'Ultimate', 'Super'],
                    'ppw_count': [
                        filtered_sales_df['ppw_quality_count'].sum(),
                        filtered_sales_df['ppw_works_count'].sum(),
                        filtered_sales_df['ppw_ultimate_count'].sum(),
                        filtered_sales_df['ppw_super_count'].sum()
                    ],
                    'club_count': [
                        filtered_sales_df['club_quality_count'].sum(),
                        filtered_sales_df['club_works_count'].sum(),
                        filtered_sales_df['club_ultimate_count'].sum(),
                        filtered_sales_df['club_super_count'].sum()
                    ]
                })
                
                # Remove zero count membership types
                membership_counts = membership_counts[(membership_counts['ppw_count'] > 0) | (membership_counts['club_count'] > 0)]
                
                # Generate membership revenue chart if data exists
                if not membership_data.empty:
                    membership_rev_fig = px.bar(
                        membership_data,
                        x='membership_type',
                        y='revenue',
                        title='Membership Revenue by Type',
                        labels={'revenue': 'Revenue ($)', 'membership_type': 'Membership Type'},
                        color='membership_type',
                        text_auto='.2s'
                    )
                    
                    membership_rev_fig.update_traces(
                        texttemplate='$%{y:,.2f}', 
                        textposition='outside'
                    )
                    
                    st.plotly_chart(membership_rev_fig, use_container_width=True)
                
                # Generate membership counts chart if data exists
                if not membership_counts.empty:
                    membership_counts_fig = px.bar(
                        membership_counts,
                        x='membership_type',
                        y=['ppw_count', 'club_count'],
                        title='Membership Counts by Type',
                        labels={
                            'value': 'Count', 
                            'membership_type': 'Membership Type',
                            'variable': 'Program'
                        },
                        barmode='group',
                        text_auto=True
                    )
                    
                    # Update names for legend
                    membership_counts_fig.for_each_trace(lambda t: t.update(
                        name=t.name.replace("_count", "").replace("_", " ").title(),
                        legendgroup=t.name.replace("_count", "").replace("_", " ").title(),
                        hovertemplate=t.hovertemplate.replace("_count", "").replace("_", " ").title()
                    ))
                    
                    st.plotly_chart(membership_counts_fig, use_container_width=True)
                
                # Add PPW vs Club Sales Analysis
                st.subheader("PPW vs Club Sales Comparison")
                
                # Create dataframe for PPW vs Club comparison
                ppw_club_data = pd.DataFrame({
                    'program': ['Pay Per Wash (PPW)', 'Club Membership'],
                    'revenue': [total_ppw_revenue, total_club_revenue]
                })
                
                # Create pie chart comparing PPW vs Club revenue
                ppw_club_fig = px.pie(
                    ppw_club_data,
                    values='revenue',
                    names='program',
                    title='PPW vs Club Revenue Distribution',
                    hole=0.4,
                    color_discrete_map={'Pay Per Wash (PPW)': 'royalblue', 'Club Membership': 'darkgreen'}
                )
                
                ppw_club_fig.update_traces(
                    textinfo='percent+label+value',
                    texttemplate='%{label}<br>$%{value:,.2f}<br>(%{percent})',
                    hovertemplate='%{label}<br>$%{value:,.2f}<br>(%{percent})'
                )
                
                st.plotly_chart(ppw_club_fig, use_container_width=True)
                
                # If we have detailed breakdown by tier for both programs, show this
                if total_club_quality > 0 or total_club_works > 0 or total_club_ultimate > 0 or total_club_super > 0:
                    # Create detail comparison by membership tier
                    program_tiers = pd.DataFrame({
                        'membership_type': ['Quality', 'Works', 'Ultimate', 'Super'],
                        'PPW': [total_ppw_quality, total_ppw_works, total_ppw_ultimate, total_ppw_super],
                        'Club': [total_club_quality, total_club_works, total_club_ultimate, total_club_super]
                    })
                    
                    # Remove rows where both PPW and Club are zero
                    program_tiers = program_tiers[(program_tiers['PPW'] > 0) | (program_tiers['Club'] > 0)]
                    
                    if not program_tiers.empty:
                        # Create side-by-side bar chart
                        program_tier_fig = px.bar(
                            program_tiers,
                            x='membership_type',
                            y=['PPW', 'Club'],
                            title='PPW vs Club Revenue by Membership Tier',
                            labels={
                                'value': 'Revenue ($)', 
                                'membership_type': 'Membership Tier',
                                'variable': 'Program'
                            },
                            barmode='group',
                            color_discrete_map={'PPW': 'royalblue', 'Club': 'darkgreen'}
                        )
                        
                        program_tier_fig.update_traces(texttemplate='$%{y:,.2f}', textposition='outside')
                        
                        st.plotly_chart(program_tier_fig, use_container_width=True)
                
                # Time series analysis of PPW vs Club over time
                # We'll need to calculate this from the daily data if available
                st.subheader("PPW vs Club Revenue Trends")
                
                try:
                    # Attempt to create time series if we can identify the columns
                    # Check if PPW columns exist in daily revenue
                    if 'ppw_revenue' not in daily_revenue.columns:
                        # Calculate daily PPW revenue
                        ppw_cols = [c for c in filtered_sales_df.columns if 'ppw_' in c.lower() and ('payment' in c.lower() or 'refund' in c.lower())]
                        
                        if ppw_cols:
                            # Group by date and calculate PPW and Club revenue
                            daily_program_revenue = filtered_sales_df.groupby(filtered_sales_df['date'].dt.date).agg({
                                'date': 'first',  # Keep one date per group
                                'club_and_ppw_sales': 'sum'
                            }).reset_index(drop=True)
                            
                            # Add PPW and estimate Club
                            daily_program_revenue['ppw_revenue'] = filtered_sales_df.groupby(filtered_sales_df['date'].dt.date)[ppw_cols].sum().sum(axis=1).reset_index(drop=True)
                            daily_program_revenue['club_revenue'] = daily_program_revenue['club_and_ppw_sales'] - daily_program_revenue['ppw_revenue']
                            
                            # Convert date to datetime
                            daily_program_revenue['date'] = pd.to_datetime(daily_program_revenue['date'])
                            
                            # Create time series visualization
                            program_trend_fig = go.Figure()
                            
                            program_trend_fig.add_trace(
                                go.Scatter(
                                    x=daily_program_revenue['date'], 
                                    y=daily_program_revenue['ppw_revenue'],
                                    mode='lines', 
                                    name='PPW Revenue',
                                    line=dict(color='royalblue')
                                )
                            )
                            
                            program_trend_fig.add_trace(
                                go.Scatter(
                                    x=daily_program_revenue['date'], 
                                    y=daily_program_revenue['club_revenue'],
                                    mode='lines', 
                                    name='Club Revenue',
                                    line=dict(color='darkgreen')
                                )
                            )
                            
                            program_trend_fig.update_layout(
                                title_text="PPW vs Club Revenue Over Time",
                                xaxis_title="Date",
                                yaxis_title="Revenue ($)",
                                legend=dict(x=0, y=1.1, orientation='h')
                            )
                            
                            st.plotly_chart(program_trend_fig, use_container_width=True)
                            
                            # Calculate and show monthly trend
                            filtered_sales_df['year_month'] = filtered_sales_df['date'].dt.strftime('%Y-%m')
                            
                            # Group by year-month
                            monthly_program = filtered_sales_df.groupby('year_month').agg({
                                'club_and_ppw_sales': 'sum'
                            }).reset_index()
                            
                            # Add PPW data
                            monthly_program['ppw_revenue'] = filtered_sales_df.groupby('year_month')[ppw_cols].sum().sum(axis=1).reset_index(drop=True)
                            monthly_program['club_revenue'] = monthly_program['club_and_ppw_sales'] - monthly_program['ppw_revenue']
                            
                            # Format month for display
                            monthly_program['formatted_month'] = monthly_program['year_month'].apply(format_year_month)
                            
                            # Sort chronologically 
                            monthly_program = monthly_program.sort_values('year_month')
                            
                            # Create monthly program comparison
                            monthly_program_fig = go.Figure()
                            
                            monthly_program_fig.add_trace(
                                go.Bar(
                                    x=monthly_program['formatted_month'],
                                    y=monthly_program['ppw_revenue'],
                                    name='PPW Revenue',
                                    marker_color='royalblue'
                                )
                            )
                            
                            monthly_program_fig.add_trace(
                                go.Bar(
                                    x=monthly_program['formatted_month'],
                                    y=monthly_program['club_revenue'],
                                    name='Club Revenue',
                                    marker_color='darkgreen'
                                )
                            )
                            
                            monthly_program_fig.update_layout(
                                title_text="Monthly PPW vs Club Revenue",
                                xaxis_title="Month",
                                yaxis_title="Revenue ($)",
                                barmode='group',
                                legend=dict(x=0, y=1.1, orientation='h'),
                                xaxis={'categoryorder': 'array', 'categoryarray': monthly_program['formatted_month'].tolist()}
                            )
                            
                            st.plotly_chart(monthly_program_fig, use_container_width=True)
                    else:
                        st.info("PPW vs Club time series data not available with the current dataset.")
                
                except Exception as e:
                    st.info(f"Could not generate PPW vs Club trends: {e}")
                
                # Single washes analysis
                st.subheader("Single Wash Analysis")
                
                single_wash_data = pd.DataFrame({
                    'wash_type': ['Quality', 'Works', 'Ultimate', 'Super'],
                    'count': [
                        filtered_sales_df['single_wash_quality_count'].sum(),
                        filtered_sales_df['single_wash_works_count'].sum(),
                        filtered_sales_df['single_wash_ultimate_count'].sum(),
                        filtered_sales_df['single_wash_super_count'].sum()
                    ]
                })
                
                # Remove zero counts
                single_wash_data = single_wash_data[single_wash_data['count'] > 0]
                
                # Create single wash chart if data exists
                if not single_wash_data.empty:
                    single_wash_fig = px.pie(
                        single_wash_data,
                        values='count',
                        names='wash_type',
                        title='Single Wash Distribution',
                        hole=0.4
                    )
                    
                    single_wash_fig.update_traces(
                        textinfo='percent+label',
                        hovertemplate='%{label}<br>Count: %{value}<br>(%{percent})'
                    )
                    
                    st.plotly_chart(single_wash_fig, use_container_width=True)
                else:
                    st.info("No single wash data available for the selected period.")
                
                # Site comparisons
                if selected_sites and len(selected_sites) > 1:
                    st.subheader("Site Revenue Comparison")
                    
                    # Group by site
                    site_revenue = filtered_sales_df.groupby('site_id').agg({
                        'revenue': 'sum',
                        'expense_total': 'sum',
                        'cash_sales': 'sum',
                        'credit_card_sales': 'sum',
                        'club_and_ppw_sales': 'sum'
                    }).reset_index()
                    
                    # Calculate net income
                    site_revenue['net_income'] = site_revenue['revenue'] - site_revenue['expense_total']
                    
                    # Sort by revenue
                    site_revenue = site_revenue.sort_values('revenue', ascending=False)
                    
                    # Create site revenue comparison chart
                    site_rev_fig = px.bar(
                        site_revenue,
                        x='site_id',
                        y=['revenue', 'expense_total', 'net_income'],
                        title='Revenue and Expenses by Site',
                        labels={
                            'value': 'Amount ($)',
                            'site_id': 'Site',
                            'variable': 'Category'
                        },
                        barmode='group'
                    )
                    
                    # Update names for legend
                    site_rev_fig.for_each_trace(lambda t: t.update(
                        name=t.name.replace("_", " ").title(),
                        legendgroup=t.name.replace("_", " ").title(),
                        hovertemplate=t.hovertemplate.replace("_", " ").title()
                    ))
                    
                    st.plotly_chart(site_rev_fig, use_container_width=True)
                    
                    # Sales type by site
                    site_sales_type = px.bar(
                        site_revenue,
                        x='site_id',
                        y=['cash_sales', 'credit_card_sales', 'club_and_ppw_sales'],
                        title='Sales Types by Site',
                        labels={
                            'value': 'Sales ($)',
                            'site_id': 'Site',
                            'variable': 'Sales Type'
                        },
                        barmode='stack'
                    )
                    
                    # Update names for legend
                    site_sales_type.for_each_trace(lambda t: t.update(
                        name=t.name.replace("_sales", "").replace("_", " ").title(),
                        legendgroup=t.name.replace("_sales", "").replace("_", " ").title(),
                        hovertemplate=t.hovertemplate.replace("_sales", "").replace("_", " ").title()
                    ))
                    
                    st.plotly_chart(site_sales_type, use_container_width=True)
            else:
                st.info("No sales data available for the selected filters. Please adjust your selection.")      

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
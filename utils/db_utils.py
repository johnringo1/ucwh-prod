import pandas as pd
import os
import pyodbc
import streamlit as st

def load_wash_data():
    """Load wash data from database"""
    # Get credentials from Streamlit secrets
    try:
        server = st.secrets.get("DB_SERVER")
        database = st.secrets.get("DB_NAME")
        username = st.secrets.get("DB_USER")
        password = st.secrets.get("DB_PASSWORD")
    except Exception as e:
        # Just log the error without exposing any credentials
        st.error("Error loading database credentials. Please configure in Streamlit secrets.")
        return pd.DataFrame()  # Return empty DataFrame
    
    # Now safely check if all credentials are available
    if not all([server, database, username, password]):
        st.error("Database connection parameters are not properly configured.")
        return pd.DataFrame()  # Return empty DataFrame

    # Build connection string for Azure SQL with ODBC 17 or 18 (whichever is available)
    try:
        connection_string = (
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"UID={username};"
            f"PWD={password};"
            f"TrustServerCertificate=yes;"
            f"Encrypt=yes;"
        )
        conn = pyodbc.connect(connection_string)
    except:
        # Try with ODBC 17 if 18 is not available
        try:
            connection_string = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={server};"
                f"DATABASE={database};"
                f"UID={username};"
                f"PWD={password};"
                f"TrustServerCertificate=yes;"
                f"Encrypt=yes;"
            )
            conn = pyodbc.connect(connection_string)
        except Exception as e:
            st.error(f"Failed to connect to database: {e}")
            return pd.DataFrame()  # Return empty DataFrame
    
    # SQL query
    query = """
    SELECT 
        site_id,
        CONVERT(DATE, CAST(date_key AS CHAR(8)), 112) AS date,
        name,
        count,
        rewash_count
    FROM 
        f_dly_wash_count
    ORDER BY 
        site_id, date_key
    """
    
    # Execute query and load into pandas DataFrame
    try:
        df = pd.read_sql(query, conn)
        
        # Close connection
        conn.close()
        
        # Process data
        df['date'] = pd.to_datetime(df['date'])
        df['total_count'] = df['count'] + df['rewash_count']
        df['rewash_percentage'] = (df['rewash_count'] * 100 / df['count']).fillna(0)
        
        return df
    except Exception as e:
        st.error(f"Error loading wash data: {e}")
        return pd.DataFrame()  # Return empty DataFrame

def load_subscription_data():
    """Load subscription data from database"""
    # Get credentials from Streamlit secrets
    try:
        server = st.secrets.get("DB_SERVER")
        database = st.secrets.get("DB_NAME")
        username = st.secrets.get("DB_USER")
        password = st.secrets.get("DB_PASSWORD")
    except Exception as e:
        # Just log the error without exposing any credentials
        st.error("Error loading database credentials. Please configure in Streamlit secrets.")
        return pd.DataFrame()  # Return empty DataFrame
    
    # Check if credentials are valid
    if not all([server, database, username, password]):
        st.error("Database connection parameters are not properly configured.")
        return pd.DataFrame()  # Return empty DataFrame
    
    # Build connection string for Azure SQL with ODBC 17 or 18 (whichever is available)
    try:
        connection_string = (
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"UID={username};"
            f"PWD={password};"
            f"TrustServerCertificate=yes;"
            f"Encrypt=yes;"
        )
        conn = pyodbc.connect(connection_string)
    except:
        # Try with ODBC 17 if 18 is not available
        try:
            connection_string = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={server};"
                f"DATABASE={database};"
                f"UID={username};"
                f"PWD={password};"
                f"TrustServerCertificate=yes;"
                f"Encrypt=yes;"
            )
            conn = pyodbc.connect(connection_string)
        except Exception as e:
            st.error(f"Failed to connect to database: {e}")
            return pd.DataFrame()  # Return empty DataFrame
    
    # SQL query for subscription data
    query = """
    SELECT 
        site_id,
        CONVERT(DATE, CAST(date_key AS CHAR(8)), 112) AS date,
        active_count,
        created_count,
        canceled_count,
        trial_count,
        recurring_count,
        ending_count
    FROM 
        f_dly_subscription_counts
    ORDER BY 
        site_id, date_key
    """
    
    # Execute query and load into pandas DataFrame
    try:
        df = pd.read_sql(query, conn)
        
        # Close connection
        conn.close()
        
        # Process data
        df['date'] = pd.to_datetime(df['date'])
        
        # Calculate net change
        df['net_change'] = df['created_count'] - df['canceled_count']
        
        # Calculate conversion rate (from trial to recurring)
        df['conversion_rate'] = (df['recurring_count'] / df['trial_count'] * 100).fillna(0)
        
        return df
    except Exception as e:
        st.error(f"Error loading subscription data: {e}")
        return pd.DataFrame()  # Return empty DataFrame

def load_sales_data():
    """Load sales and expense data from database"""
    # Get credentials from Streamlit secrets
    try:
        server = st.secrets.get("DB_SERVER")
        database = st.secrets.get("DB_NAME")
        username = st.secrets.get("DB_USER")
        password = st.secrets.get("DB_PASSWORD")
    except Exception as e:
        # Just log the error without exposing any credentials
        st.error("Error loading database credentials. Please configure in Streamlit secrets.")
        return pd.DataFrame()  # Return empty DataFrame
    
    # Check if credentials are valid
    if not all([server, database, username, password]):
        st.error("Database connection parameters are not properly configured.")
        return pd.DataFrame()  # Return empty DataFrame
    
    # Build connection string for Azure SQL with ODBC 17 or 18 (whichever is available)
    try:
        connection_string = (
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"UID={username};"
            f"PWD={password};"
            f"TrustServerCertificate=yes;"
            f"Encrypt=yes;"
        )
        conn = pyodbc.connect(connection_string)
    except:
        # Try with ODBC 17 if 18 is not available
        try:
            connection_string = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={server};"
                f"DATABASE={database};"
                f"UID={username};"
                f"PWD={password};"
                f"TrustServerCertificate=yes;"
                f"Encrypt=yes;"
            )
            conn = pyodbc.connect(connection_string)
        except Exception as e:
            st.error(f"Failed to connect to database: {e}")
            return pd.DataFrame()  # Return empty DataFrame
    
    # SQL query for sales and expense data
    query = """
    SELECT 
        site_id,
        date_key,
        CONVERT(DATE, CAST(date_key AS CHAR(8)), 112) AS date, -- Convert date_key to date in SQL
        cash_sales,
        cash_sales_tax,
        credit_card_sales,
        credit_card_sales_tax,
        gross_sub_payments,
        gross_sub_refunds,
        gross_ppw_payments,
        gross_ppw_refunds,
        club_and_ppw_sales,
        club_and_ppw_sales_tax,
        sales,
        sales_tax,
        total_less_sales_tax,
        total_less_club_and_ppw_sales_tax,
        redeemed_gift_cards,
        total_activated_gift_cards,
        combined_total_less_sales_tax,
        redeemed_less_activated_gift_cards,
        revenue,
        wkly_sub_credit_card_fees,
        technology_fee,
        brand_development_fee,
        royalty_fee,
        fee_adjustments,
        expense_total,
        ppw_quality_count,
        ppw_works_count,
        ppw_ultimate_count,
        ppw_super_count,
        club_quality_count,
        club_works_count,
        club_ultimate_count,
        club_super_count,
        club_count_total,
        app_payments_count,
        non_app_payments_count,
        vending_sales,
        cross_over_total,
        dispute_total,
        gross_ppw_payments_quality,
        gross_ppw_refunds_quality,
        gross_ppw_payments_works,
        gross_ppw_refunds_works,
        gross_ppw_payments_ultimate,
        gross_ppw_refunds_ultimate,
        gross_ppw_payments_super,
        gross_ppw_refunds_super,
        weeks_open,
        gc_quality_1_month_count,
        gc_quality_3_month_count,
        gc_works_1_month_count,
        gc_works_3_month_count,
        gc_redeemed_quality_1_month_count,
        gc_redeemed_quality_3_month_count,
        gc_redeemed_works_1_month_count,
        gc_redeemed_works_3_month_count,
        single_wash_quality_count,
        single_wash_works_count,
        single_wash_ultimate_count,
        single_wash_super_count,
        radar_fee_amt,
        pre_auth_fee_amt,
        volume_billing_fee_amt,
        payout_fee_amt,
        auto_card_update_fee_amt,
        active_account_billing_fee_amt,
        active_reader_fee_amt,
        app_adjustment
    FROM 
        ags_sales_expense
    WHERE
        date_key IS NOT NULL
        AND LEN(CAST(date_key AS VARCHAR)) = 8  -- Ensure date_key is a valid 8-digit number
    ORDER BY 
        site_id, date_key
    """
    
    # Execute query and load into pandas DataFrame
    try:
        df = pd.read_sql(query, conn)
        
        # Close connection
        conn.close()
        
        # Process data - use pandas to_datetime to safely convert the date column
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        
        # Drop rows with invalid dates
        df = df.dropna(subset=['date'])
        
        return df
    except Exception as e:
        st.error(f"Error loading sales data: {e}")
        return pd.DataFrame()  # Return empty DataFrame
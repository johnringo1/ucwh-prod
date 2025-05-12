import pandas as pd
import os
import pyodbc
import streamlit as st

def load_wash_data():
    """Load wash data from database"""
    # Get credentials from Streamlit secrets or environment variables
    try:
        server = st.secrets.get("DB_SERVER")
        database = st.secrets.get("DB_NAME")
        username = st.secrets.get("DB_USER")
        password = st.secrets.get("DB_PASSWORD")
    except:
        # For local development without secrets.toml
        server = "ucw.database.windows.net"
        database = "UnitedCarwashProduction"
        username = "ucwreader"
        password = "mBSzLC4frVCJglpmSbbg"
    
    # Check if credentials are available
    if not all([server, database, username, password]):
        raise ValueError("Database credentials not properly configured")
    
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
    df = pd.read_sql(query, conn)
    
    # Close connection
    conn.close()
    
    # Process data
    df['date'] = pd.to_datetime(df['date'])
    df['total_count'] = df['count'] + df['rewash_count']
    df['rewash_percentage'] = (df['rewash_count'] * 100 / df['count']).fillna(0)
    
    return df

def load_subscription_data():
    """Load subscription data from database"""
    # Get credentials from Streamlit secrets or environment variables
    try:
        server = st.secrets.get("DB_SERVER")
        database = st.secrets.get("DB_NAME")
        username = st.secrets.get("DB_USER")
        password = st.secrets.get("DB_PASSWORD")
    except:
        # For local development without secrets.toml
        server = "ucw.database.windows.net"
        database = "UnitedCarwashProduction"
        username = "ucwreader"
        password = "mBSzLC4frVCJglpmSbbg"
    
    # Check if credentials are available
    if not all([server, database, username, password]):
        raise ValueError("Database credentials not properly configured")
    
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
import pandas as pd
import os
import pyodbc
import streamlit as st

def load_wash_data():
    """Load wash data from database"""
    # Get credentials from Streamlit secrets
    server = st.secrets.get("DB_SERVER")
    database = st.secrets.get("DB_NAME")
    username = st.secrets.get("DB_USER")
    password = st.secrets.get("DB_PASSWORD")
    
    # Check if credentials are available
    if not all([server, database, username, password]):
        raise ValueError("Database credentials not properly configured")
    
    # Build connection string for Azure SQL
    connection_string = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
    
    try:
        # Connect to database
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
        
    except Exception as e:
        raise Exception(f"Error loading data: {str(e)}")
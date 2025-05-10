import pyodbc
import pandas as pd
import os
from streamlit import secrets

def get_connection():
    """Create a connection to the database"""
    # Try to get credentials from streamlit secrets first, then environment variables
    server = secrets.get("DB_SERVER", os.environ.get("DB_SERVER"))
    database = secrets.get("DB_NAME", os.environ.get("DB_NAME"))
    username = secrets.get("DB_USER", os.environ.get("DB_USER"))
    password = secrets.get("DB_PASSWORD", os.environ.get("DB_PASSWORD"))
    
    # Check if credentials are available
    if not all([server, database, username, password]):
        raise ValueError("Database credentials not properly configured. Please set them in Streamlit secrets or environment variables.")
    
    conn_str = (
        f"Driver={{ODBC Driver 18 for SQL Server}};"
        f"Server={server};"
        f"Database={database};"
        f"UID={username};"
        f"PWD={password};"
    )
    
    try:
        return pyodbc.connect(conn_str)
    except Exception as e:
        raise ConnectionError(f"Failed to connect to database: {str(e)}")

def load_wash_data():
    """Load wash data from database"""
    conn = get_connection()
    
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
    
    try:
        df = pd.read_sql(query, conn)
        df['date'] = pd.to_datetime(df['date'])
        df['total_count'] = df['count'] + df['rewash_count']
        df['rewash_percentage'] = (df['rewash_count'] * 100 / df['count']).fillna(0)
        return df
    except Exception as e:
        raise Exception(f"Error loading data: {str(e)}")
    finally:
        conn.close()
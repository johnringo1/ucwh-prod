# United Car Wash Dashboard

Interactive dashboard for analyzing car wash data across multiple locations.

## Features

- Time series analysis of wash counts
- Site comparison
- Wash type breakdown
- Day of week and monthly trend analysis

## Setup for Development

1. Clone this repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Configure database credentials (see below)
6. Run the app: `streamlit run app.py`

## Database Configuration

For local development, create a file `.streamlit/secrets.toml` with:

```toml
DB_SERVER = "your_azure_server.database.windows.net"
DB_NAME = "your_database_name"
DB_USER = "your_username"
DB_PASSWORD = "your_password"
DASHBOARD_PASSWORD = "your_dashboard_password"
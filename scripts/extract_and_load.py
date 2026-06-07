import os
import requests
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

# Load configuration secrets from your hidden .env file
load_dotenv()
API_TOKEN = os.getenv("AUSTIN_CRIME_TOKEN")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_DB = os.getenv("POSTGRES_DB")

def extract_data():
    """Extracts raw data from the Austin Crime API."""
    url = "https://data.austintexas.gov/resource/hbc5-hmey.json"
    headers = {"X-App-Token": API_TOKEN}
    # Pulling a small batch of 500 records for our pipeline setup test
    params = {"$limit": 500}
    
    print("🚀 Extracting data from Austin Data Portal...")
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        raw_data = response.json()
        df = pd.DataFrame(raw_data)
        print(f"✅ Extraction successful! Retrieved {len(df)} rows.")
        return df
    else:
        raise Exception(f"❌ API Extraction failed with status code: {response.status_code}")

def load_data(df):
    """Loads the raw dataframe into the staging layer of Postgres."""
    if df.empty:
        print("⚠️ No data to load.")
        return
        
    print("🔌 Connecting to Postgres Database...")
    # Constructing the SQLAlchemy connection string using your .env secrets
    # Note: We use 'localhost' for running locally, which will match our upcoming Docker setup
    connection_string = f"postgresql://{DB_USER}:{DB_PASSWORD}@localhost:5432/{DB_DB}"
    engine = create_engine(connection_string)
    
    print("📥 Loading raw records into 'src_austin_crime' table...")
    # if_exists='replace' drops the old table and makes a fresh copy for this raw staging step
    df.to_sql(name="src_austin_crime", con=engine, if_exists="replace", index=False)
    print("✅ Load complete! Raw data is safely in the database.")

if __name__ == "__main__":
    try:
        # Run the full pipeline sequence
        raw_df = extract_data()
        load_data(raw_df)
        print("🎉 Script finished successfully!")
    except Exception as e:
        print(f"💥 Pipeline step failed: {e}")
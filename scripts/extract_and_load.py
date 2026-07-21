import os
import requests
import pandas as pd
from dotenv import load_dotenv, dotenv_values
from sqlalchemy import create_engine
from pathlib import Path

# Find the .env file 1 directory up from scripts/
env_path = Path(__file__).resolve().parent.parent / ".env"

# 1. Force override any lingering system variables
load_dotenv(dotenv_path=env_path, override=True)

# 2. Inspect direct dictionary parse
parsed_config = dotenv_values(env_path)

print(f"1. Env File Path: {env_path}")
print(f"2. File Exists: {env_path.exists()}")
print(f"3. Parsed Keys in .env: {list(parsed_config.keys())}")
print(f"4. DB User via getenv: {os.getenv('POSTGRES_USER')}")

# Load environment variables
API_TOKEN = os.getenv("AUSTIN_CRIME_TOKEN")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_DB = os.getenv("POSTGRES_DB")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5433")


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
    # Constructing the SQLAlchemy connection string using your .env secrets and port 5433
    connection_string = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_DB}"
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
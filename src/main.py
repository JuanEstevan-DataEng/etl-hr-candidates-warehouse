import logging
import os
from dotenv import load_dotenv
from extract import extract_data
from transform import transform_data
from load import load_data

# Basic logging configuration for the main orchestrator
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(module)s - %(message)s'
)

def run_pipeline():
    """
    Main orchestration function for the ETL pipeline.
    Loads environment variables and executes the Extract, Transform, and Load phases sequentially.
    """
    logging.info("--- Starting ETL Pipeline ---")
    
    # Environment variables are loaded from the .env file
    load_dotenv()
    
    # Database connection parameters are retrieved
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")
    db_name = os.getenv("DB_NAME")
    
    if not all([db_user, db_password, db_host, db_port, db_name]):
        logging.error("Missing database credentials in the .env file. Pipeline aborted.")
        return

    # The connection URI is constructed
    db_uri = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

    try:
        # Phase 1: Extract
        logging.info("Initiating Extract Phase...")
        df_raw = extract_data()
        
        # Phase 2: Transform
        logging.info("Initiating Transform Phase...")
        df_transformed = transform_data(df_raw)
        
        # Phase 3: Load
        logging.info("Initiating Load Phase...")
        load_data(df_transformed, db_uri)
        
        logging.info("--- ETL Pipeline Completed Successfully ---")
        
    except Exception as e:
        logging.critical(f"Pipeline failed: {e}")
        
if __name__ == "__main__":
    run_pipeline()

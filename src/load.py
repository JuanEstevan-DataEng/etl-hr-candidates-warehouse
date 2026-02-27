import pandas as pd
from sqlalchemy import create_engine
import logging
import os

# Basic logging configuration for the pipeline
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_dimension(df: pd.DataFrame, engine, table_name: str, natural_key: str, columns: list) -> pd.DataFrame:
    """
    Loads unique records into a dimension table using an anti-join approach to avoid duplicates.
    Returns a dataframe with the mapping of the natural key to the newly generated surrogate key.
    """
    logging.info(f"Processing dimension: {table_name}")
    
    # 1. Unique records are extracted from the current batch
    dim_df = df[columns].drop_duplicates(subset=[natural_key]).copy()
    
    # 2. Existing natural keys are read from the database
    try:
        existing_records = pd.read_sql(f"SELECT {natural_key} FROM {table_name}", engine)
        existing_keys = existing_records[natural_key].tolist()
    except Exception:
        # Table might be empty or not exist yet
        existing_keys = []
        
    # 3. Only new records are filtered (Anti-Join)
    new_records = dim_df[~dim_df[natural_key].isin(existing_keys)]
    
    # 4. New records are inserted into the database
    if not new_records.empty:
        logging.info(f"Inserting {len(new_records)} new records into {table_name}.")
        new_records.to_sql(name=table_name, con=engine, if_exists='append', index=False)
    else:
        logging.info(f"No new records to insert into {table_name}.")
        
    # 5. The full dimension is read back to get the Surrogate Keys (SKs)
    # The SK column is assumed to be named by removing 'dim_' and adding '_sk' (e.g., dim_candidate -> candidate_sk)
    entity_name = table_name.replace('dim_', '')
    sk_column = f"{entity_name}_sk"
    
    mapping_df = pd.read_sql(f"SELECT {sk_column}, {natural_key} FROM {table_name}", engine)
    return mapping_df

def load_data(df: pd.DataFrame, db_uri: str):
    """
    Orchestrates the loading of dimensions and the fact table into the Data Warehouse.
    """
    engine = create_engine(db_uri)
    
    try:
        logging.info("Starting load phase to Data Warehouse.")
        
        # --- 1. Dimensions are loaded and SK mappings are retrieved ---
        
        # Location (Country)
        loc_mapping = load_dimension(df, engine, 'dim_location', 'country', ['country'])
        df = df.merge(loc_mapping, on='country', how='left')
        
        # Technology
        df['technology_name'] = df['technology']
        tech_mapping = load_dimension(df, engine, 'dim_technology', 'technology_name', ['technology_name'])
        df = df.merge(tech_mapping, on='technology_name', how='left')
        
        # Seniority
        df['seniority_name'] = df['seniority']
        sen_mapping = load_dimension(df, engine, 'dim_seniority', 'seniority_name', ['seniority_name'])
        df = df.merge(sen_mapping, on='seniority_name', how='left')
        
        # Candidate
        cand_mapping = load_dimension(df, engine, 'dim_candidate', 'email', ['first_name', 'last_name', 'email'])
        df = df.merge(cand_mapping, on='email', how='left')
        
        # Date (Special case because SK is derived, not auto-increment)
        df['full_date'] = df['application_date'].dt.date
        _ = load_dimension(df, engine, 'dim_date', 'date_sk', ['date_sk', 'full_date', 'year', 'month', 'day', 'quarter'])
        # No merge is needed for date_sk because it was already generated in the transform phase
        
        # --- 2. Fact Table is loaded ---
        logging.info("Preparing fact_application table.")
        
        fact_columns = [
            'candidate_sk', 'seniority_sk', 'technology_sk', 'location_sk', 'date_sk',
            'yoe', 'code_challenge_score', 'technical_interview_score', 'is_hired'
        ]
        
        fact_df = df[fact_columns].copy()
        
        # Fact records are inserted
        logging.info(f"Inserting {len(fact_df)} records into fact_application.")
        fact_df.to_sql(name='fact_application', con=engine, if_exists='append', index=False)
        
        logging.info("Load phase completed successfully.")
        
    except Exception as e:
        logging.error(f"Error during the load phase: {e}")
        raise
    finally:
        engine.dispose()


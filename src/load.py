import pandas as pd
from sqlalchemy import create_engine, text
import logging
from pathlib import Path

# Basic logging configuration for the pipeline
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_sql_queries(file_path: Path) -> dict:
    """
    Parses a SQL file and returns a dictionary of queries mapped by their comment headers.
    
    Args:
        file_path (Path): The pathlib.Path object pointing to the SQL file containing the queries.
        
    Returns:
        dict: A dictionary where keys are the comment headers (without '-- ') and values are the SQL query strings.
    """
    queries = {}
    current_name = None
    current_query = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('-- '):
                if current_name:
                    queries[current_name] = " ".join(current_query).strip()
                current_name = line[3:].strip()
                current_query = []
            elif line and current_name:
                current_query.append(line)
                
    if current_name:
        queries[current_name] = " ".join(current_query).strip()
        
    return queries

def init_database(db_uri: str, db_name: str, create_sql_path: Path):
    """
    Checks if the database exists. If not, it creates it and executes the schema script.
    
    Args:
        db_uri (str): The SQLAlchemy connection URI including the database name.
        db_name (str): The name of the database to check or create.
        create_sql_path (Path): The path to the SQL script file containing the schema definition.
        
    Returns:
        None
    """
    # Create engine without connecting to a specific database first
    base_uri = db_uri.rsplit('/', 1)[0]
    engine = create_engine(base_uri)
    
    try:
        with engine.connect() as conn:
            # Check if database exists
            res = conn.execute(text(f"SHOW DATABASES LIKE '{db_name}'"))
            if not res.fetchone():
                logging.warning(f"Database '{db_name}' not found. Initializing schema...")
                
                # Execute the create tables script
                with open(create_sql_path, 'r', encoding='utf-8') as f:
                    sql_script = f.read()
                    
                # Split commands by semicolon to execute them sequentially
                # We need to handle statements specifically or rely on PyMySQL multi-statements
                # But a simple split works for basic scripts
                commands = sql_script.split(';')
                for command in commands:
                    command = command.strip()
                    if command:
                        conn.execute(text(command))
                
                logging.info(f"Schema initialized successfully in '{db_name}'.")
            else:
                logging.info(f"Database '{db_name}' already exists. Skipping initialization.")
    except Exception as e:
        logging.error(f"Error initializing the database: {e}")
        raise
    finally:
        engine.dispose()

def load_dimension(df: pd.DataFrame, engine, table_name: str, natural_key: str, columns: list, queries: dict) -> pd.DataFrame:
    """
    Loads unique records into a dimension table using an anti-join approach to avoid duplicates.
    Returns a dataframe with the mapping of the natural key to the newly generated surrogate key.
    
    Args:
        df (pd.DataFrame): The transformed dataframe containing the dimension data.
        engine (sqlalchemy.engine.Engine): The SQLAlchemy engine connected to the database.
        table_name (str): The name of the dimension table in the database (e.g., 'dim_location').
        natural_key (str): The column name in the dataframe that acts as the unique business key.
        columns (list): A list of column names to extract from the dataframe for this dimension.
        queries (dict): A dictionary containing the pre-loaded SQL query templates.
        
    Returns:
        pd.DataFrame: A dataframe containing two columns: the generated surrogate key and the natural key,
                      used for merging back into the fact table.
    """
    logging.info(f"Processing dimension: {table_name}")
    
    # 1. Unique records are extracted from the current batch
    dim_df = df[columns].drop_duplicates(subset=[natural_key]).copy()
    
    # 2. Existing natural keys are read from the database using external SQL query
    query_existing = text(queries['get_existing_keys'].format(natural_key=natural_key, table_name=table_name))
    try:
        existing_records = pd.read_sql(query_existing, engine)
        existing_keys = existing_records[natural_key].tolist()
    except Exception as e:
        # Table might be empty or not exist yet
        logging.debug(f"Could not fetch existing keys for {table_name}: {e}")
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
    entity_name = table_name.replace('dim_', '')
    sk_column = f"{entity_name}_sk"
    
    query_mapping = text(queries['get_mapping'].format(sk_column=sk_column, natural_key=natural_key, table_name=table_name))
    mapping_df = pd.read_sql(query_mapping, engine)
    
    return mapping_df

def load_data(df: pd.DataFrame, db_uri: str):
    """
    Orchestrates the loading of dimensions and the fact table into the Data Warehouse.
    
    Args:
        df (pd.DataFrame): The fully transformed and cleaned dataframe.
        db_uri (str): The SQLAlchemy connection URI including the target database name.
        
    Returns:
        None
    """
    # Project paths
    current_dir = Path(__file__).resolve().parent
    sql_dir = current_dir.parent / 'sql'
    create_sql_path = sql_dir / 'create_tables.sql'
    load_sql_path = sql_dir / 'load_tables.sql'
    
    # Initialize the database if it doesn't exist
    db_name = db_uri.split('/')[-1]
    init_database(db_uri, db_name, create_sql_path)
    
    # Load SQL templates
    queries = load_sql_queries(load_sql_path)
    
    engine = create_engine(db_uri)
    
    try:
        logging.info("Starting load phase to Data Warehouse.")
        
        # --- 1. Dimensions are loaded and SK mappings are retrieved ---
        
        # Location (Country)
        loc_mapping = load_dimension(df, engine, 'dim_location', 'country', ['country'], queries)
        df = df.merge(loc_mapping, on='country', how='left')
        
        # Technology
        df['technology_name'] = df['technology']
        tech_mapping = load_dimension(df, engine, 'dim_technology', 'technology_name', ['technology_name'], queries)
        df = df.merge(tech_mapping, on='technology_name', how='left')
        
        # Seniority
        df['seniority_name'] = df['seniority']
        sen_mapping = load_dimension(df, engine, 'dim_seniority', 'seniority_name', ['seniority_name'], queries)
        df = df.merge(sen_mapping, on='seniority_name', how='left')
        
        # Candidate
        cand_mapping = load_dimension(df, engine, 'dim_candidate', 'email', ['first_name', 'last_name', 'email'], queries)
        df = df.merge(cand_mapping, on='email', how='left')
        
        # Date (Special case because SK is derived, not auto-increment)
        df['full_date'] = df['application_date'].dt.date
        _ = load_dimension(df, engine, 'dim_date', 'date_sk', ['date_sk', 'full_date', 'year', 'month', 'day', 'quarter'], queries)
        
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

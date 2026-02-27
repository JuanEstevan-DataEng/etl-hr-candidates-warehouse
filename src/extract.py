import pandas as pd
from pathlib import Path
import logging

# Basic logging configuration for the pipeline
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def extract_data(file_name: str = 'candidates.csv') -> pd.DataFrame:
    """
    Reads the raw CSV file and returns a Pandas DataFrame.
    Ensures cross-platform reproducibility using pathlib.
    """
    try:
        # The absolute path of the script directory (src/) is obtained,
        # and navigation goes up to data/raw/
        current_dir = Path(__file__).resolve().parent
        file_path = current_dir.parent / 'data' / 'raw' / file_name

        logging.info(f"Starting extraction from: {file_path}")

        # It is verified that the file exists before attempting to read it
        if not file_path.exists():
            raise FileNotFoundError(f"The file does not exist at the path: {file_path}")

        # The CSV is read (based on the EDA it is known that the separator is ';')
        df = pd.read_csv(file_path, sep=';')
        
        # Quick structural validation (10 columns are expected according to the EDA)
        expected_columns = 10
        if df.shape[1] != expected_columns:
            logging.warning(f"Expected {expected_columns} columns, but found {df.shape[1]}.")
        
        logging.info(f"Successful extraction. {len(df)} records loaded.")
        return df

    except Exception as e:
        logging.error(f"Error during the extraction phase: {e}")
        raise

# Test block (only executed if this script is run directly)
if __name__ == "__main__":
    df_raw = extract_data()
    print(df_raw.head())

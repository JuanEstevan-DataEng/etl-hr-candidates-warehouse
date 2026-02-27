import pandas as pd
import numpy as np
import logging

# Basic logging configuration for the pipeline
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def transform_data(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Main orchestration function for the transformation phase.
    Performs data cleaning, business rules application, and date dimension expansion
    in a single cohesive flow.
    """
    try:
        df = df_raw.copy()
        logging.info("Starting transformation phase.")

        # --- 1. Data Cleaning & Normalization ---
        # Column names are converted to lowercase
        df.columns = df.columns.str.lower()
        
        # Categorical columns are converted to lowercase
        text_columns = df.select_dtypes(include=['object', 'string']).columns
        for col in text_columns:
            if col != 'email':
                df[col] = df[col].str.lower()
                
        # Duplicated emails are dropped entirely as discussed in EDA
        initial_rows = len(df)
        df = df.drop_duplicates(subset=['email'], keep=False)
        logging.info(f"Dropped {initial_rows - len(df)} rows due to email duplication.")

        # --- 2. Business Rules Application ---
        # Rule 1: 'is_hired' logic (Requirement)
        condition_hired = (df['code challenge score'] >= 7) & (df['technical interview score'] >= 7)
        df['is_hired'] = condition_hired.astype(int) # Cast to int (1/0) for TINYINT MySQL
        
        # Rule 2: Fixing Seniority anomalies (Cross-referencing YOE and Technical Score)
        senior_roles = ['architect', 'lead', 'senior']
        junior_roles = ['intern', 'trainee', 'junior']
        
        # Condition 1: Fake Seniors (High label, but low experience OR low technical skills)
        cond_fake_senior = (df['seniority'].isin(senior_roles)) & ((df['yoe'] < 3) | (df['technical interview score'] < 5))
        
        # Condition 2: Hidden Talents (Low label, but high experience AND excellent technical skills)
        cond_hidden_talent = (df['seniority'].isin(junior_roles)) & (df['yoe'] >= 7) & (df['technical interview score'] >= 8)
        
        # Condition 3: Experienced but average (Low label, high experience, but average/poor technical skills)
        cond_experienced_average = (df['seniority'].isin(junior_roles)) & (df['yoe'] >= 7) & (df['technical interview score'] < 8)
        
        # Apply conditions vectorized
        conditions = [cond_fake_senior, cond_hidden_talent, cond_experienced_average]
        choices = ['junior', 'senior', 'mid-level']
        
        # np.select applies the choices based on conditions. The default keeps the original value.
        df['seniority'] = np.select(conditions, choices, default=df['seniority'])
        logging.info("Applied business rules (HIRED logic and Seniority corrections).")

        # --- 3. Date Dimension Expansion ---
        # Conversion to datetime object
        df['application date'] = pd.to_datetime(df['application date'], errors='coerce')
        
        # Dropping rows where date conversion failed (if any)
        df = df.dropna(subset=['application date'])
        
        # Extracting parts
        df['year'] = df['application date'].dt.year
        df['month'] = df['application date'].dt.month
        df['day'] = df['application date'].dt.day
        df['quarter'] = df['application date'].dt.quarter
        
        # Creating date_sk as an integer (e.g., 20210226)
        df['date_sk'] = df['application date'].dt.strftime('%Y%m%d').astype(int)
        
        # Replace spaces with underscores in all column names to match database schema
        df.columns = df.columns.str.replace(' ', '_')
        
        logging.info("Expanded date components for dimension modeling.")

        logging.info("Transformation phase completed successfully.")
        return df
        
    except Exception as e:
        logging.error(f"Error during the transformation phase: {e}")
        raise


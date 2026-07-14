import os
import glob
import pandas as pd
from sqlalchemy import create_engine
import warnings
warnings.filterwarnings('ignore')

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    raw_dir = os.path.join(root_dir, 'data', 'raw')
    db_path = os.path.join(root_dir, 'data', 'olist.db')
    
    if not os.path.exists(raw_dir):
        print(f"Error: {raw_dir} does not exist. Please download Olist Kaggle dataset into this folder.")
        return

    csv_files = glob.glob(os.path.join(raw_dir, '*.csv'))
    if not csv_files:
        print(f"Error: No CSV files found in {raw_dir}.")
        return

    print(f"Building SQLite database at {db_path}...")
    engine = create_engine(f'sqlite:///{db_path}')

    for file_path in csv_files:
        file_name = os.path.basename(file_path)
        table_name = file_name.replace('olist_', '').replace('_dataset.csv', '').replace('.csv', '')
        
        print(f"  Ingesting {file_name} -> table: {table_name}")
        try:
            df = pd.read_csv(file_path)
            df.to_sql(table_name, engine, if_exists='replace', index=False)
        except Exception as e:
            print(f"  [!] Failed to load {file_name}: {e}")
        
    print("Database built successfully.")

if __name__ == "__main__":
    main()

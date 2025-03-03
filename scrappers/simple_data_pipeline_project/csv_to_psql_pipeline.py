import os
import time
import pandas as pd
import psycopg2
from psycopg2 import sql
from sqlalchemy import create_engine
from flask import Flask, render_template, request, redirect
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

class CSVToPostgreSQLPipeline:
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST'),
            'port': int(os.getenv('DB_PORT')),
            'database': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USERNAME'),
            'password': os.getenv('DB_PASSWORD'),
        }

        self.engine = create_engine(
            f"postgresql://{self.db_config['user']}:{self.db_config['password']}@{self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}"
        )
        self.processed_files = set()
        self.logs = []

    def log_event(self, event):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.logs.append(f"[{timestamp}] {event}")

    def create_table(self, table_name, df):
        with psycopg2.connect(**self.db_config) as conn:
            with conn.cursor() as cursor:
                columns = [
                    f"{col} TEXT" for col in df.columns
                ]  # Assuming TEXT for all columns
                create_table_query = sql.SQL(
                    "CREATE TABLE IF NOT EXISTS {table} ({columns})"
                ).format(
                    table=sql.Identifier(table_name),
                    columns=sql.SQL(", ").join(map(sql.SQL, columns)),
                )
                cursor.execute(create_table_query)
                conn.commit()
        self.log_event(f"Table created: {table_name}")

    def save_csv_to_db(self, csv_file_path, table_name):
        df = pd.read_csv(csv_file_path)
        self.create_table(table_name, df)
        df.to_sql(table_name, self.engine, if_exists='append', index=False)

    def retrieve_data(self, table_name):
        query = f"SELECT * FROM {table_name}"
        with psycopg2.connect(**self.db_config) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                return pd.DataFrame(rows, columns=columns)

    def list_tables(self):
        query = "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
        with psycopg2.connect(**self.db_config) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                return [row[0] for row in cursor.fetchall()]

    def delete_table(self, table_name):
        with psycopg2.connect(**self.db_config) as conn:
            with conn.cursor() as cursor:
                drop_query = sql.SQL("DROP TABLE IF EXISTS {table}").format(
                    table=sql.Identifier(table_name)
                )
                cursor.execute(drop_query)
                conn.commit()
        self.log_event(f"Table deleted: {table_name}")

    def monitor_folder(self, folder_path):
        csv_files = [f for f in os.listdir(folder_path) if f.endswith('.csv')]
        existing_tables = self.list_tables()
        for csv_file in csv_files:
            file_path = os.path.join(folder_path, csv_file)
            table_name = os.path.splitext(csv_file)[0]  # Use file name as table name

            if table_name not in existing_tables:
                print(f"Processing new file: {csv_file} into table: {table_name}")
                self.save_csv_to_db(file_path, table_name)
                self.processed_files.add(csv_file)
                self.log_event(f"File processed: {csv_file}, Table created: {table_name}")
            else:
                print(f"Table '{table_name}' already exists. Skipping.")

# Flask app
app = Flask(__name__)
pipeline = CSVToPostgreSQLPipeline()

@app.before_request
def check_new_files():
    folder_path = os.getenv('CSV_FOLDER_PATH')  # Specify the folder path in .env
    pipeline.monitor_folder(folder_path)

@app.route('/')
def index():
    tables = pipeline.list_tables()
    return render_template('psql_data_modify.html', tables=tables, logs=pipeline.logs)

@app.route('/view/<table_name>')
def view_table(table_name):
    data = pipeline.retrieve_data(table_name)
    return render_template('view_table.html', table_name=table_name, data=data.to_dict(orient='records'), columns=data.columns)

@app.route('/delete/<table_name>', methods=['POST'])
def delete_table(table_name):
    pipeline.delete_table(table_name)
    return redirect('/')

@app.route('/clear_logs', methods=['POST'])
def clear_logs():
    pipeline.logs.clear()
    return redirect('/')

@app.route('/manual_scan', methods=['POST'])
def manual_scan():
    folder_path = os.getenv('CSV_FOLDER_PATH')
    previous_log_length = len(pipeline.logs)
    pipeline.processed_files.clear()  # Clear processed files to detect changes
    pipeline.monitor_folder(folder_path)
    # Check if new logs were added during the scan
    if len(pipeline.logs) == previous_log_length:
        pipeline.log_event("Manual scan: No file changes detected.")
    return redirect('/')

if __name__ == "__main__":
    app.run(debug=True)

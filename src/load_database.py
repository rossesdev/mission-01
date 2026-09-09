import sqlite3
from pathlib import Path
from contextlib import closing

# Define the root directory of the project
root_dir = Path(__file__).resolve().parent.parent
print(f"Root directory: {Path(__file__)}")
print(f"Root directory: {Path(__file__).resolve()}")
print(f"Root directory: {root_dir.parent}")
schema_path = root_dir / "sql" / "schema.sql"
db_path = root_dir / "output" / "orders.db"

# Create the output directory if it doesn't exist
db_path.parent.mkdir(parents=True, exist_ok=True)

with closing(sqlite3.connect(db_path)) as connection:
    with connection:
        # Execute the SQL script to create the schema
        connection.executescript(schema_path.read_text(encoding="utf-8"))
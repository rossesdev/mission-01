import sqlite3
from pathlib import Path
from contextlib import closing

from pipeline import load_orders, process_orders

# Define the root directory of the project
root_dir = Path(__file__).resolve().parent.parent
schema_path = root_dir / "sql" / "schema.sql"
db_path = root_dir / "output" / "orders.db"
csv_path = root_dir / "data" / "orders.csv"

def load_database():
    # Load orders from the CSV file and process them
    orders = load_orders(csv_path)
    valid_orders, invalid_orders = process_orders(orders)

    # Create the output directory if it doesn't exist
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with closing(sqlite3.connect(db_path)) as connection:
        with connection:
            # Execute the SQL script to create the schema
            connection.executescript(schema_path.read_text(encoding="utf-8"))

            # Delete existing records from the tables
            connection.execute("DELETE FROM rejected_orders")
            connection.execute("DELETE FROM orders")

            for order in valid_orders:
                order["amount_cents"] = int(order["amount"] * 100)

            connection.executemany(
                """INSERT INTO orders
                    (order_id, created_at, customer_id, amount_cents, status)
                    VALUES (:order_id, :created_at, :customer_id, :amount_cents, :status)""",
                valid_orders,
            )

            connection.executemany(
                """INSERT INTO rejected_orders
                    (order_id, created_at, customer_id, amount, status, rejection_reason)
                    VALUES (:order_id, :created_at, :customer_id, :amount, :status, :rejection_reason)""",
                invalid_orders,
            )

if __name__ == "__main__":
    load_database()
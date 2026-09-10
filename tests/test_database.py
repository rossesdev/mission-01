import tempfile
import unittest
from pathlib import Path
import src.load_database
import sqlite3


class TestLoadDatabase(unittest.TestCase):

    def setUp(self):
        self.tmpdir = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.db_path = self.tmpdir / "orders.db"
        src.load_database.load_database(self.db_path)

    def test_load_database(self):
        self.assertTrue(self.db_path.exists())

    def test_orders_table_exists(self):
        with sqlite3.connect(self.db_path) as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
        self.assertIn("orders", tables)
        self.assertIn("rejected_orders", tables)

    def test_orders_count(self):
        with sqlite3.connect(self.db_path) as conn:
            (count,) = conn.execute("SELECT COUNT(*) FROM orders").fetchone()
        self.assertEqual(count, 6)

    def test_rejected_orders_count(self):
        with sqlite3.connect(self.db_path) as conn:
            (count,) = conn.execute("SELECT COUNT(*) FROM rejected_orders").fetchone()
        self.assertEqual(count, 7)

    def test_all_orders_count(self):
        with sqlite3.connect(self.db_path) as conn:
            (orders_count,) = conn.execute("SELECT COUNT(*) FROM orders").fetchone()
            (rejected_count,) = conn.execute("SELECT COUNT(*) FROM rejected_orders").fetchone()
        self.assertEqual(orders_count + rejected_count, 13)

    def test_sum_amount(self):
        with sqlite3.connect(self.db_path) as conn:
            (orders_sum,) = conn.execute("SELECT SUM(amount_cents) FROM orders").fetchone()
        self.assertEqual(orders_sum, 19265)

    def test_paid_sum_amount(self):
        with sqlite3.connect(self.db_path) as conn:
            (paid_orders_sum,) = conn.execute("SELECT SUM(amount_cents) AS total_paid_amount FROM orders WHERE status = 'paid'").fetchone()
        self.assertEqual(paid_orders_sum, 14025)

    def test_insert_duplicated(self):
        with sqlite3.connect(self.db_path) as conn:
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute("INSERT INTO orders (order_id,created_at,customer_id,amount_cents,status) VALUES ('1001','2026-09-01T09:15:00-05:00','C001',4590,'paid')")
            (count,) = conn.execute("SELECT COUNT(*) FROM orders WHERE order_id = '1001'").fetchone()
        self.assertEqual(count, 1)

    def test_insert_negative_amount(self):
        with sqlite3.connect(self.db_path) as conn:
            with self.assertRaises(sqlite3.IntegrityError):
                with conn:  # commit if it is OK, rollback if there is an exception
                    conn.execute("INSERT INTO orders (order_id,created_at,customer_id,amount_cents,status) VALUES ('1014','2026-09-01T09:15:00-05:00','C002',1000,'paid')")
                    conn.execute("INSERT INTO orders (order_id,created_at,customer_id,amount_cents,status) VALUES ('1015','2026-09-01T09:15:00-05:00','C002',-1000,'paid')")

            (count,) = conn.execute("SELECT COUNT(*) FROM orders WHERE order_id IN ('1014','1015')").fetchone()
        self.assertEqual(count, 0)

    def test_add_new_row_end_to_end(self):
        # Full round-trip through the CSV: add order 1013, reload, remove it, reload.
        csv_copy = self.tmpdir / "orders.csv"
        original_csv_path = src.load_database.csv_path
        baseline_csv = original_csv_path.read_text(encoding="utf-8")

        # Ensure the baseline CSV ends with a newline before appending the new row
        if not baseline_csv.endswith("\n"):
            baseline_csv += "\n"
        new_row = "1013,2026-09-02T09:00:00-05:00,C013,10.35,pending"

        src.load_database.csv_path = csv_copy
        self.addCleanup(setattr, src.load_database, "csv_path", original_csv_path)

        csv_copy.write_text(baseline_csv + new_row, encoding="utf-8")
    
        src.load_database.load_database(self.db_path)
        with sqlite3.connect(self.db_path) as conn:
            (has_1013,) = conn.execute(
                "SELECT COUNT(*) FROM orders WHERE order_id = '1013'"
            ).fetchone()
            (total, amount_sum) = conn.execute(
                "SELECT COUNT(*), SUM(amount_cents) FROM orders"
            ).fetchone()

        self.assertEqual(has_1013, 1)
        self.assertEqual(total, 7)
        self.assertEqual(amount_sum, 20300)

        csv_copy.write_text(baseline_csv, encoding="utf-8")
        src.load_database.load_database(self.db_path)
        
        with sqlite3.connect(self.db_path) as conn:
            (has_1013,) = conn.execute(
                "SELECT COUNT(*) FROM orders WHERE order_id = '1013'"
            ).fetchone()
            (total, amount_sum) = conn.execute(
                "SELECT COUNT(*), SUM(amount_cents) FROM orders"
            ).fetchone()
        self.assertEqual(has_1013, 0)
        self.assertEqual(total, 6)
        self.assertEqual(amount_sum, 19265)

    def test_load_is_idempotent(self):
        src.load_database.load_database(self.db_path)
        with sqlite3.connect(self.db_path) as conn:
            (count,) = conn.execute("SELECT COUNT(*) FROM orders").fetchone()
            (count_rejected,) = conn.execute("SELECT COUNT(*) FROM rejected_orders").fetchone()
        self.assertEqual(count_rejected, 7)
        self.assertEqual(count, 6)
# Mission 1: Order Pipeline

## Objective

This mission teaches Python fundamentals, basic data manipulation, normalization, validation, directory creation, CSV and JSON file handling, and file reading.

## Structure

- `data` contains the initial CSV data.
- `output` contains the generated files.
- `src` contains the main pipeline and all processing logic.
- `tests` contains the automated tests.

## Input Data

The CSV must contain the following columns:

- order_id
- created_at
- customer_id
- amount
- status

The generated `rejected_orders.csv` file includes one additional column:

- rejection_reason

## Validation Rules

Fields cannot be empty. Each field also follows these rules:

- `order_id`: Must be unique. When duplicates exist, the first valid row is kept.
- `created_at`: Must be a valid ISO 8601 date and time.
- `customer_id`: Must not be empty.
- `amount`: Must be a positive, finite number.
- `status`: Must be one of the values defined in `VALID_STATUSES`.

## Running the Pipeline

Run the following command from the project root:

```bash
python3 src/pipeline.py
```

## Generated Files

- `rejected_orders.csv` contains rejected rows and their rejection reasons.
- `valid_orders.csv` contains normalized, valid rows.
- `summary.json` contains aggregate results after normalization.

## Tests

Run the tests from the project root with:

```bash
python3 -m unittest discover tests
```

## Technical Decisions

`Decimal` is used for monetary values because it represents decimal amounts more accurately than binary floating-point numbers.

An `order_id` is marked as seen only after every field in its row passes validation. This allows a later valid row to use an ID first encountered in an invalid row.

The pipeline is idempotent because the same input always produces the same results, and each run overwrites the generated output files.

## Limitations

The pipeline does not yet support more exhaustive validation, multiple input files, or command-line input options.

## Lessons Learned

- Cleaning and normalizing CSV data.
- Reading, creating, and modifying CSV files.
- Working with lists and dictionaries.

---

# Mission 2: SQLite Loader

## Objective

Persist the pipeline results into a SQLite database, enforcing schema constraints and transactional integrity.

## Flow

1. Read `data/orders.csv`.
2. `process_orders` returns `valid_orders` and `invalid_orders`.
3. `load_database` opens (or creates) `output/orders.db`.
4. The schema defined in `sql/schema.sql` creates the `orders` and `rejected_orders` tables.
5. Both tables are cleared and repopulated with `valid_orders` and `invalid_orders`.

## Schema

Table definitions live in `sql/schema.sql`.

## Cent Conversion

`amount` arrives from `process_orders` as a `Decimal`. It is multiplied by `100` and cast to `int` to be stored as `amount_cents` (integer cents), avoiding floating-point rounding errors.

## How to Run

Load the database (from the project root):

```bash
python3 -m src.load_database
```

Run the queries:

```bash
sqlite3 output/orders.db < sql/queries.sql
```

Run the tests:

```bash
python3 -m unittest discover tests
```

Rebuild `orders.db` from scratch: run the load command again — it overwrites any existing data.

## Transaction Guarantees

The whole load runs inside a single transaction ("all or nothing"):

- Both tables are cleared.
- Valid and rejected rows are inserted.
- On success, `COMMIT` persists everything.
- On any error, `ROLLBACK` undoes the clear and any prior insert, leaving the previous state intact.

## Reconciliation

The initial CSV (`data/orders.csv`) contains **13** rows. After processing they split cleanly:

- **6 valid rows** → `orders` table.
- **7 rejected rows** → `rejected_orders` table.
- **6 + 7 = 13** → matches the input row count.

Monetary totals over the `orders` table (in cents):

- `SUM(amount_cents)` = **19,265** (`$192.65`).
- `SUM(amount_cents) WHERE status = 'paid'` = **14,025** (`$140.25`).

These numbers are pinned in the tests, so any change in the CSV, validation rules, or cent conversion will be caught immediately.

## Controlled Failure Example

`test_insert_negative_amount` exercises the rollback path with a two-statement transaction:

1. **Before**: the DB holds 6 rows in `orders` (baseline from the CSV load).
2. **First insert** (`order_id = '1014'`, `amount_cents = 1000`) succeeds — but is not yet committed.
3. **Second insert** (`order_id = '1015'`, `amount_cents = -1000`) violates `CHECK(amount_cents > 0)` and raises `sqlite3.IntegrityError`.
4. The `with conn:` context manager sees the exception and issues **`ROLLBACK`**, which discards _both_ pending inserts.
5. **After**: `orders` still holds the original 6 rows. Neither `1014` nor `1015` are present.

## Why the Load is Idempotent

Running `load_database` any number of times produces the same final database state: each run clears both tables and reinserts the same rows derived from the same input CSV.

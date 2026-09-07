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

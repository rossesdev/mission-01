import csv
from datetime import datetime
from decimal import Decimal
import json
import os


VALID_STATUSES = {"paid", "pending", "cancelled", "refunded"}
GENERIC_FIELDS = [
    "order_id",
    "created_at",
    "customer_id",
    "amount",
    "status",
]
ERROR_DUPLICATED_ORDER_ID = "duplicated_order_id"
REQUIRED_COLUMNS = {"order_id", "created_at", "customer_id", "amount", "status"}

def valid_amount(val):
    cleaned_val = val.strip()
    if not cleaned_val:
        return (False, cleaned_val, "Empty value")

    try:
        amount = round(Decimal(cleaned_val), 2)

    except (ValueError, ArithmeticError):
        return (False, cleaned_val, "Invalid amount")

    if not amount.is_finite():
        return False, cleaned_val, "Amount must be finite"
    
    if amount <= 0:
        return (False, cleaned_val, "Non-positive value")

    return (True, amount, None)


def valid_order_id(val, seen):
    cleaned_val = val.strip()
    if not cleaned_val:
        return (False, cleaned_val, "Empty value")

    if cleaned_val in seen:
        return (False, cleaned_val, ERROR_DUPLICATED_ORDER_ID)

    return (True, cleaned_val, None)


def valid_created_at(val):
    cleaned_val = val.strip()
    if not cleaned_val:
        return (False, cleaned_val, "Empty value")

    try:
        parsed_date = datetime.fromisoformat(cleaned_val)
        formatted_date = parsed_date.isoformat()
    except ValueError:
        return (False, cleaned_val, "Invalid date")

    return (True, formatted_date, None)


def valid_customer_id(val):
    cleaned_val = val.strip()
    if not cleaned_val:
        return (False, cleaned_val, "Empty value")

    return (True, cleaned_val, None)


def valid_status(val):
    cleaned_val = val.strip()
    if not cleaned_val:
        return (False, cleaned_val, "Empty value")

    val = cleaned_val.lower()

    if val not in VALID_STATUSES:
        return (False, cleaned_val, "Invalid status")

    return (True, val, None)


def validate_order(order, seen_order_ids):
    result = {}
    rejected_order = order.copy()

    is_valid, value, error = valid_order_id(order.get("order_id", ""), seen_order_ids)
    result["order_id"] = value

    if not is_valid:
        rejected_order["rejection_reason"] = error
        return rejected_order

    is_valid, value, error = valid_created_at(order.get("created_at", ""))
    result["created_at"] = value

    if not is_valid:
        rejected_order["rejection_reason"] = error
        return rejected_order

    is_valid, value, error = valid_customer_id(order.get("customer_id", ""))
    result["customer_id"] = value

    if not is_valid:
        rejected_order["rejection_reason"] = error
        return rejected_order

    is_valid, value, error = valid_amount(order.get("amount", ""))
    result["amount"] = value

    if not is_valid:
        rejected_order["rejection_reason"] = error
        return rejected_order

    is_valid, value, error = valid_status(order.get("status", ""))
    result["status"] = value

    if not is_valid:
        rejected_order["rejection_reason"] = error
        return rejected_order

    seen_order_ids.add(result["order_id"])
    return result


def load_orders(path):
    try:
        with open(path, mode='r', encoding='utf-8', newline='') as file:
            reader = csv.DictReader(file)

            if reader.fieldnames is None:
                raise ValueError("The CSV file is completely empty")

            missing_columns = REQUIRED_COLUMNS - set(reader.fieldnames)

            if missing_columns:
                raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")

            orders = list(reader)

            if not orders:
                raise ValueError("The CSV has headers but contains no orders")

            return orders
    except FileNotFoundError as error:
        raise FileNotFoundError(
            f"The file '{path}' was not found. "
            "Check the path and file name."
        ) from error


def process_orders(orders):
    seen_order_ids = set()
    valid_orders = []
    invalid_orders = []

    for order in orders:
        result = validate_order(order, seen_order_ids)
        if "rejection_reason" in result:
            invalid_orders.append(result)
        else:
            valid_orders.append(result)

    return valid_orders, invalid_orders

def calculate_summary(valid_orders, invalid_orders):
    group_by_status = {}
    sum_amount = 0
    sum_paid_amount = 0
    
    
    initial_rows = len(valid_orders) + len(invalid_orders)
    valid_rows = len(valid_orders)
    invalid_rows = len(invalid_orders)
    duplicated_rows = sum(1 for row in invalid_orders if row.get('rejection_reason') == ERROR_DUPLICATED_ORDER_ID)
  
    for valid_order in valid_orders:
        status = valid_order.get("status")
        amount = valid_order.get("amount", 0)
        if status not in group_by_status:
            group_by_status[status] = 0
        group_by_status[status] += 1
        sum_amount += amount
        if status == "paid":
            sum_paid_amount += amount

    return {
        "initial_rows": initial_rows,
        "valid_rows": valid_rows,
        "invalid_rows": invalid_rows,
        "duplicated_rows": duplicated_rows,
        "rows_by_status": group_by_status,
        "total_amount": float(sum_amount),
        "paid_amount": float(sum_paid_amount),
    }


def create_summary_json(valid_orders, invalid_orders):
    summary = calculate_summary(valid_orders, invalid_orders)

    with open("output/summary.json", mode="w", encoding="utf-8") as file:
        json.dump(summary, file, indent=4, ensure_ascii=False)


def create_csv(rows, filename, fields):
    with open(f"output/{filename}", mode="w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

def validate_folder(folder):
    if not os.path.isdir(folder):
        try:
            os.makedirs(folder)
        except OSError as e:
            raise RuntimeError(f"Failed to create folder {folder}: {e}")


def main():
  
    orders = load_orders('data/orders.csv')
    valid_orders, invalid_orders = process_orders(orders)

    validate_folder("output")
    create_summary_json(valid_orders, invalid_orders)
    create_csv(invalid_orders, 'rejected_orders.csv', fields=GENERIC_FIELDS + ["rejection_reason"])
    create_csv(valid_orders, 'valid_orders.csv', fields=GENERIC_FIELDS)

if __name__ == "__main__":
    main()
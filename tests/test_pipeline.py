
import unittest

from src.pipeline import validate_order


class TestPipeline(unittest.TestCase):
    def test_rejects_order_when_amount_is_negative(self):
        order = {
            "order_id": "1",
            "created_at": "2026-09-07T10:00:00",
            "customer_id": "123",
            "amount": "-10.50",
            "status": "paid",
        }

        result = validate_order(order, set())

        self.assertEqual(result["rejection_reason"], "Non-positive value")

    def test_accepts_order_when_all_fields_are_valid(self):
        order = {
            "order_id": "2",
            "created_at": "2026-09-07T11:00:00",
            "customer_id": "124",
            "amount": "20.00",
            "status": "paid",
        }

        result = validate_order(order, set())

        self.assertIsNone(result.get("rejection_reason"))
        self.assertEqual(result["order_id"], "2")


    def test_rejects_order_when_order_id_is_duplicate(self):
        order = {
            "order_id": "1",
            "created_at": "2026-09-07T12:00:00",
            "customer_id": "125",
            "amount": "15.00",
            "status": "paid",
        }

        duplicated_order = {
            "order_id": "1",
            "created_at": "2026-12-07T12:00:00",
            "customer_id": "126",
            "amount": "16.00",
            "status": "cancelled",
        }
        seen_order_ids = set()
        result = validate_order(order, seen_order_ids)
        duplicate_result = validate_order(duplicated_order, seen_order_ids)

        self.assertIsNone(result.get("rejection_reason"))
        self.assertEqual(duplicate_result["rejection_reason"], "duplicated_order_id")
   

    def test_rejects_order_when_customer_id_is_empty(self):
        order = {
            "order_id": "3",
            "created_at": "2026-09-07T13:00:00",
            "customer_id": "",
            "amount": "25.00",
            "status": "paid",
        }

        result = validate_order(order, set())

        self.assertEqual(result["rejection_reason"], "Empty value")
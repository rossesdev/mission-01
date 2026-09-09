SELECT COUNT(*) AS total_valid FROM orders;

SELECT COUNT(*) AS total_rejected FROM rejected_orders;

SELECT (SELECT COUNT(*) FROM orders) + (SELECT COUNT(*) FROM rejected_orders) AS total;

SELECT SUM(amount_cents) AS total_amount FROM orders;

SELECT SUM(amount_cents) AS total_paid_amount FROM orders WHERE status = 'paid';
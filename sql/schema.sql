 CREATE TABLE IF NOT EXISTS orders (
    order_id TEXT PRIMARY KEY NOT NULL,
    created_at TEXT NOT NULL,
    customer_id TEXT NOT NULL,
    amount_cents INTEGER NOT NULL CHECK(amount_cents > 0),
	status TEXT NOT NULL CHECK(status in ('paid', 'pending', 'cancelled', 'refunded'))
);

CREATE TABLE IF NOT EXISTS rejected_orders (
  	ID INTEGER PRIMARY KEY,
    order_id TEXT,
    created_at TEXT,
    customer_id TEXT,
    amount TEXT,
	status TEXT,
    rejection_reason TEXT NOT NULL
)
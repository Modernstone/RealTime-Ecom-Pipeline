-- ============================================================
-- Real-Time E-Commerce Data Pipeline - Indexes
-- ============================================================

-- Foreign key indexes
CREATE INDEX IF NOT EXISTS idx_products_category_id       ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_orders_customer_id         ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_order_items_order_id       ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_product_id     ON order_items(product_id);
CREATE INDEX IF NOT EXISTS idx_payments_order_id          ON payments(order_id);

-- Query-filter indexes
CREATE INDEX IF NOT EXISTS idx_orders_order_date          ON orders(order_date);
CREATE INDEX IF NOT EXISTS idx_orders_order_status        ON orders(order_status);
CREATE INDEX IF NOT EXISTS idx_orders_payment_status      ON orders(payment_status);
CREATE INDEX IF NOT EXISTS idx_orders_payment_method      ON orders(payment_method);
CREATE INDEX IF NOT EXISTS idx_customers_email            ON customers(email);
CREATE INDEX IF NOT EXISTS idx_products_category          ON products(category_id);

-- Composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_orders_customer_date       ON orders(customer_id, order_date);
CREATE INDEX IF NOT EXISTS idx_orders_status_date         ON orders(order_status, order_date);

-- Pipeline logs indexes
CREATE INDEX IF NOT EXISTS idx_pipeline_logs_run_id       ON pipeline_logs(run_id);
CREATE INDEX IF NOT EXISTS idx_pipeline_logs_status       ON pipeline_logs(status);

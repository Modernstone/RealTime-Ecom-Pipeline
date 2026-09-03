-- ============================================================
-- Real-Time E-Commerce Data Pipeline - Seed Data
-- ============================================================

-- Insert categories (idempotent via ON CONFLICT DO NOTHING)
INSERT INTO categories (category_id, category_name, description)
VALUES
    ('CAT01', 'Electronics',      'Electronic devices, gadgets, and accessories'),
    ('CAT02', 'Clothing',         'Apparel and fashion items for all ages'),
    ('CAT03', 'Footwear',         'Shoes, sandals, boots, and athletic footwear'),
    ('CAT04', 'Home & Kitchen',   'Home appliances, furniture, and kitchen essentials'),
    ('CAT05', 'Beauty',           'Skincare, makeup, haircare, and personal care products'),
    ('CAT06', 'Sports',           'Sporting goods, fitness equipment, and outdoor gear'),
    ('CAT07', 'Books',            'Physical and digital books across all genres'),
    ('CAT08', 'Accessories',      'Bags, watches, jewelry, and fashion accessories')
ON CONFLICT (category_id) DO NOTHING;

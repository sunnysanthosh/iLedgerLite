-- System Categories (available to all users)
-- These are seeded once during database setup.

-- Income categories
INSERT INTO categories (id, user_id, name, type, icon, is_system) VALUES
    (gen_random_uuid(), NULL, 'Salary', 'income', 'briefcase', TRUE),
    (gen_random_uuid(), NULL, 'Freelance', 'income', 'laptop', TRUE),
    (gen_random_uuid(), NULL, 'Business Income', 'income', 'store', TRUE),
    (gen_random_uuid(), NULL, 'Investment Returns', 'income', 'trending-up', TRUE),
    (gen_random_uuid(), NULL, 'Rental Income', 'income', 'home', TRUE),
    (gen_random_uuid(), NULL, 'Gift Received', 'income', 'gift', TRUE),
    (gen_random_uuid(), NULL, 'Refund', 'income', 'rotate-ccw', TRUE),
    (gen_random_uuid(), NULL, 'Other Income', 'income', 'plus-circle', TRUE);

-- Expense categories
INSERT INTO categories (id, user_id, name, type, icon, is_system) VALUES
    (gen_random_uuid(), NULL, 'Food & Dining', 'expense', 'utensils', TRUE),
    (gen_random_uuid(), NULL, 'Groceries', 'expense', 'shopping-cart', TRUE),
    (gen_random_uuid(), NULL, 'Transport', 'expense', 'car', TRUE),
    (gen_random_uuid(), NULL, 'Fuel', 'expense', 'fuel', TRUE),
    (gen_random_uuid(), NULL, 'Rent', 'expense', 'home', TRUE),
    (gen_random_uuid(), NULL, 'Utilities', 'expense', 'zap', TRUE),
    (gen_random_uuid(), NULL, 'Mobile & Internet', 'expense', 'smartphone', TRUE),
    (gen_random_uuid(), NULL, 'Shopping', 'expense', 'shopping-bag', TRUE),
    (gen_random_uuid(), NULL, 'Healthcare', 'expense', 'heart', TRUE),
    (gen_random_uuid(), NULL, 'Education', 'expense', 'book', TRUE),
    (gen_random_uuid(), NULL, 'Entertainment', 'expense', 'film', TRUE),
    (gen_random_uuid(), NULL, 'Travel', 'expense', 'map', TRUE),
    (gen_random_uuid(), NULL, 'Insurance', 'expense', 'shield', TRUE),
    (gen_random_uuid(), NULL, 'EMI / Loan Payment', 'expense', 'credit-card', TRUE),
    (gen_random_uuid(), NULL, 'Subscription', 'expense', 'repeat', TRUE),
    (gen_random_uuid(), NULL, 'Gift / Donation', 'expense', 'gift', TRUE),
    (gen_random_uuid(), NULL, 'Taxes', 'expense', 'file-text', TRUE),
    (gen_random_uuid(), NULL, 'Maintenance', 'expense', 'tool', TRUE),
    (gen_random_uuid(), NULL, 'Salary Expense', 'expense', 'users', TRUE),
    (gen_random_uuid(), NULL, 'Supplier Payment', 'expense', 'truck', TRUE),
    (gen_random_uuid(), NULL, 'Other Expense', 'expense', 'minus-circle', TRUE);

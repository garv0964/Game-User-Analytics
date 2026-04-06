-- ==========================================
-- 1. DATABASE SCHEMA & DATA LOADING
-- ==========================================

-- USERS TABLE
CREATE TABLE users (
    user_id VARCHAR(255) PRIMARY KEY,
    install_date TIMESTAMP,
    city VARCHAR(100),
    device_type VARCHAR(50)
);

-- SESSIONS TABLE
CREATE TABLE sessions (
    session_id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) REFERENCES users(user_id),
    session_date TIMESTAMP,
    session_duration_minutes DECIMAL(10, 2)
);

-- EVENTS TABLE
CREATE TABLE events (
    event_id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) REFERENCES users(user_id),
    event_type VARCHAR(50),
    event_time TIMESTAMP,
    level_number INT
);

-- TRANSACTIONS TABLE
CREATE TABLE transactions (
    transaction_id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) REFERENCES users(user_id),
    amount_inr DECIMAL(10, 2),
    purchase_time TIMESTAMP
);

-- NOTE: Depending on your specific DB (PostgreSQL, MySQL, SQL Server),
-- you would use the exact COPY/LOAD DATA command here. 
-- Example for PostgreSQL:
-- COPY users FROM '/path/to/data/users.csv' DELIMITER ',' CSV HEADER;
-- COPY sessions FROM '/path/to/data/sessions.csv' DELIMITER ',' CSV HEADER;
-- COPY events FROM '/path/to/data/events.csv' DELIMITER ',' CSV HEADER;
-- COPY transactions FROM '/path/to/data/transactions.csv' DELIMITER ',' CSV HEADER;


-- ==========================================
-- 2. KPI QUERIES
-- ==========================================

-- DAU (Daily Active Users)
SELECT 
    DATE(session_date) as activity_date, 
    COUNT(DISTINCT user_id) as dau
FROM sessions
GROUP BY DATE(session_date)
ORDER BY activity_date;

-- MAU (Monthly Active Users)
SELECT 
    DATE_TRUNC('month', session_date) as activity_month, 
    COUNT(DISTINCT user_id) as mau
FROM sessions
GROUP BY DATE_TRUNC('month', session_date)
ORDER BY activity_month;

-- ARPU (Average Revenue Per User) for the platform (Overall)
SELECT 
    SUM(amount_inr) / (SELECT COUNT(DISTINCT user_id) FROM users) as arpu_inr
FROM transactions;

-- ARPPU (Average Revenue Per Paying User)
SELECT 
    SUM(amount_inr) / COUNT(DISTINCT user_id) as arppu_inr
FROM transactions;

-- Conversion Rate (Free -> Paid Users)
SELECT 
    (SELECT COUNT(DISTINCT user_id) FROM transactions) * 100.0 / 
    (SELECT COUNT(user_id) FROM users) as conversion_rate_percentage;

-- Churn Rate (Percentage of users inactive in the last 14 days)
-- Assuming '2023-12-31' is the current date
WITH last_activity AS (
    SELECT user_id, MAX(session_date) as last_session
    FROM sessions
    GROUP BY user_id
)
SELECT 
    SUM(CASE WHEN last_session < '2023-12-17' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as churn_rate_percentage
FROM last_activity;


-- ==========================================
-- 3. RETENTION ANALYSIS (Day 1, Day 7)
-- ==========================================

WITH user_installs AS (
    SELECT user_id, DATE(install_date) as install_dt
    FROM users
),
user_activity AS (
    SELECT DISTINCT user_id, DATE(session_date) as activity_dt
    FROM sessions
)
SELECT 
    install_dt,
    COUNT(DISTINCT i.user_id) as cohort_size,
    SUM(CASE WHEN a.activity_dt = i.install_dt + INTERVAL '1 day' THEN 1 ELSE 0 END) as day_1_retained,
    SUM(CASE WHEN a.activity_dt = i.install_dt + INTERVAL '7 day' THEN 1 ELSE 0 END) as day_7_retained,
    ROUND(SUM(CASE WHEN a.activity_dt = i.install_dt + INTERVAL '1 day' THEN 1 ELSE 0 END) * 100.0 / COUNT(DISTINCT i.user_id), 2) as day_1_retention_pct,
    ROUND(SUM(CASE WHEN a.activity_dt = i.install_dt + INTERVAL '7 day' THEN 1 ELSE 0 END) * 100.0 / COUNT(DISTINCT i.user_id), 2) as day_7_retention_pct
FROM user_installs i
LEFT JOIN user_activity a ON i.user_id = a.user_id
GROUP BY install_dt
ORDER BY install_dt;


-- ==========================================
-- 4. FUNNEL ANALYSIS (Install -> Login -> Gameplay -> Purchase)
-- ==========================================

-- Tracking the % of total users reaching each milestone
WITH funnel AS (
    SELECT
        COUNT(DISTINCT u.user_id) as total_installs,
        COUNT(DISTINCT e_log.user_id) as logged_in,
        COUNT(DISTINCT e_play.user_id) as played_game,
        COUNT(DISTINCT txn.user_id) as made_purchase
    FROM users u
    LEFT JOIN events e_log ON u.user_id = e_log.user_id AND e_log.event_type = 'login'
    LEFT JOIN events e_play ON u.user_id = e_play.user_id AND e_play.event_type = 'level_start'
    LEFT JOIN transactions txn ON u.user_id = txn.user_id
)
SELECT 
    total_installs,
    logged_in,
    ROUND(logged_in * 100.0 / total_installs, 2) as pct_login,
    played_game,
    ROUND(played_game * 100.0 / total_installs, 2) as pct_played_game,
    made_purchase,
    ROUND(made_purchase * 100.0 / total_installs, 2) as pct_made_purchase
FROM funnel;


-- ==========================================
-- 5. COHORT ANALYSIS (Monthly Retention)
-- ==========================================

WITH cohort_items AS (
    SELECT 
        user_id,
        DATE_TRUNC('month', install_date) as cohort_month
    FROM users
),
activities AS (
    SELECT 
        user_id,
        DATE_TRUNC('month', session_date) as activity_month
    FROM sessions
),
cohort_sizes AS (
    SELECT cohort_month, COUNT(DISTINCT user_id) as num_users
    FROM cohort_items
    GROUP BY cohort_month
),
retention AS (
    SELECT 
        c.cohort_month,
        DATE_PART('month', AGE(a.activity_month, c.cohort_month)) as month_number,
        COUNT(DISTINCT a.user_id) as users_active
    FROM cohort_items c
    JOIN activities a ON c.user_id = a.user_id
    GROUP BY c.cohort_month, month_number
)
SELECT 
    r.cohort_month,
    s.num_users as cohort_size,
    r.month_number,
    r.users_active,
    ROUND(r.users_active * 100.0 / s.num_users, 2) as retention_percentage
FROM retention r
JOIN cohort_sizes s ON r.cohort_month = s.cohort_month
ORDER BY r.cohort_month, r.month_number;

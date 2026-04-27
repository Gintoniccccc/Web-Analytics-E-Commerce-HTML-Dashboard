-- ============================================================
-- E-Commerce Web Analytics – SQL Analysis
-- Database: ecommerce
-- Author: [Gintoniccccc]
-- Date: 2024
-- ============================================================


-- ============================================================
-- 1. DATABASE & TABLE SETUP
-- ============================================================

CREATE DATABASE ecommerce;
USE ecommerce;

CREATE TABLE users (
    user_id VARCHAR(10),
    registration_date DATE,
    channel VARCHAR(50),
    device VARCHAR(20),
    country VARCHAR(50)
);

CREATE TABLE sessions (
    session_id VARCHAR(10),
    user_id VARCHAR(10),
    session_date DATE,
    page_views INT,
    session_duration_sec INT,
    bounced INT,
    device VARCHAR(20),
    channel VARCHAR(50)
);

CREATE TABLE events (
    event_id VARCHAR(10),
    session_id VARCHAR(10),
    user_id VARCHAR(10),
    event_type VARCHAR(20),
    product_id VARCHAR(10),
    product_name VARCHAR(100),
    category VARCHAR(50),
    price DECIMAL(10,2),
    event_timestamp DATE
);

CREATE TABLE transactions (
    transaction_id VARCHAR(10),
    user_id VARCHAR(10),
    session_id VARCHAR(10),
    product_id VARCHAR(10),
    product_name VARCHAR(100),
    category VARCHAR(50),
    amount DECIMAL(10,2),
    quantity INT,
    transaction_date DATE,
    channel VARCHAR(50),
    device VARCHAR(20),
    country VARCHAR(50)
);


-- ============================================================
-- 2. FUNNEL ANALYSIS – Overall
-- ============================================================
-- Business question: How many users progress through each stage
-- of the purchase funnel, and what are the conversion rates?

SELECT
    (SELECT COUNT(DISTINCT user_id) FROM events WHERE event_type = 'view') AS view_users,
    (SELECT COUNT(DISTINCT user_id) FROM events WHERE event_type = 'cart') AS cart_users,
    (SELECT COUNT(DISTINCT user_id) FROM events WHERE event_type = 'purchase') AS purchase_users,

    (SELECT COUNT(DISTINCT user_id) FROM events WHERE event_type = 'cart') /
    NULLIF((SELECT COUNT(DISTINCT user_id) FROM events WHERE event_type = 'view'), 0)
        AS cart_conversion_rate,

    (SELECT COUNT(DISTINCT user_id) FROM events WHERE event_type = 'purchase') /
    NULLIF((SELECT COUNT(DISTINCT user_id) FROM events WHERE event_type = 'cart'), 0)
        AS purchase_conversion_rate;

-- Result: cart CVR = 89.15%, purchase CVR = 52.85%


-- ============================================================
-- 3. FUNNEL ANALYSIS – By Acquisition Channel
-- ============================================================
-- Business question: Which channel drives the highest purchase
-- conversion rate? Where is drop-off most severe?

SELECT
    u.channel,
    COUNT(DISTINCT CASE WHEN e.event_type = 'view'     THEN e.user_id END) AS view_users,
    COUNT(DISTINCT CASE WHEN e.event_type = 'cart'     THEN e.user_id END) AS cart_users,
    COUNT(DISTINCT CASE WHEN e.event_type = 'purchase' THEN e.user_id END) AS purchase_users,

    COUNT(DISTINCT CASE WHEN e.event_type = 'cart' THEN e.user_id END) /
    NULLIF(COUNT(DISTINCT CASE WHEN e.event_type = 'view' THEN e.user_id END), 0)
        AS cart_conversion_rate,

    COUNT(DISTINCT CASE WHEN e.event_type = 'purchase' THEN e.user_id END) /
    NULLIF(COUNT(DISTINCT CASE WHEN e.event_type = 'cart' THEN e.user_id END), 0)
        AS purchase_conversion_rate

FROM events e
LEFT JOIN users u ON e.user_id = u.user_id
GROUP BY u.channel
ORDER BY purchase_conversion_rate DESC;

-- Key finding: Direct has highest purchase CVR (67%)
-- Social Media has lowest purchase CVR (36%) despite high cart CVR (91%)
-- → Social Media users browse but don't buy (cart abandonment = 64%)


-- ============================================================
-- 4. CART ABANDONMENT RATE – By Channel
-- ============================================================
-- Business question: Which channel has the highest cart abandonment?
-- Cart abandonment = 1 - (purchase users / cart users)

SELECT
    u.channel,
    COUNT(DISTINCT CASE WHEN e.event_type = 'cart'     THEN e.user_id END) AS cart_users,
    COUNT(DISTINCT CASE WHEN e.event_type = 'purchase' THEN e.user_id END) AS purchase_users,

    1 - COUNT(DISTINCT CASE WHEN e.event_type = 'purchase' THEN e.user_id END) /
    NULLIF(COUNT(DISTINCT CASE WHEN e.event_type = 'cart' THEN e.user_id END), 0)
        AS cart_abandonment_rate

FROM events e
LEFT JOIN users u ON e.user_id = u.user_id
GROUP BY u.channel
ORDER BY cart_abandonment_rate DESC;


-- ============================================================
-- 5. BOUNCE RATE – By Channel
-- ============================================================
-- Business question: Which channel brings the least engaged users?

SELECT
    channel,
    COUNT(*) AS total_sessions,
    SUM(bounced) AS bounced_sessions,
    SUM(bounced) / COUNT(*) AS bounce_rate
FROM sessions
GROUP BY channel
ORDER BY bounce_rate DESC;

-- Result: All channels ~29-31%, Referral and Social Media slightly higher


-- ============================================================
-- 6. REVENUE ANALYSIS – By Channel
-- ============================================================
-- Business question: Which channel generates the most revenue?

SELECT
    channel,
    SUM(amount) AS total_revenue,
    COUNT(DISTINCT transaction_id) AS total_transactions,
    SUM(amount) / COUNT(DISTINCT transaction_id) AS avg_order_value
FROM transactions
GROUP BY channel
ORDER BY total_revenue DESC;


-- ============================================================
-- 7. MONTHLY REVENUE TREND
-- ============================================================
-- Business question: How does revenue trend across the year?

SELECT
    DATE_FORMAT(transaction_date, '%Y-%m') AS month,
    SUM(amount) AS total_revenue,
    COUNT(DISTINCT transaction_id) AS total_transactions
FROM transactions
GROUP BY DATE_FORMAT(transaction_date, '%Y-%m')
ORDER BY month;

-- Key finding: December is peak revenue month


-- ============================================================
-- 8. WINDOW FUNCTIONS – Cumulative Spend per User
-- ============================================================
-- Business question: What is each user's cumulative spend over time?

SELECT
    user_id,
    transaction_date,
    amount,
    SUM(amount) OVER (
        PARTITION BY user_id
        ORDER BY transaction_date
    ) AS cumulative_spend
FROM transactions
ORDER BY user_id, transaction_date;


-- ============================================================
-- 9. WINDOW FUNCTIONS – Transaction Rank per User
-- ============================================================
-- Business question: Which transaction was each user's highest spend?

SELECT
    user_id,
    transaction_date,
    amount,
    product_name,
    RANK() OVER (
        PARTITION BY user_id
        ORDER BY amount DESC
    ) AS amount_rank
FROM transactions;


-- ============================================================
-- 10. TOP TRANSACTION PER CHANNEL
-- ============================================================
-- Business question: What is the highest single transaction in each channel?

SELECT *
FROM (
    SELECT
        *,
        RANK() OVER (
            PARTITION BY channel
            ORDER BY amount DESC
        ) AS amount_rank_by_channel
    FROM transactions
) AS ranked
WHERE amount_rank_by_channel = 1;


-- ============================================================
-- 11. SAVED VIEWS
-- ============================================================

-- ============================================================
-- View 1: Bounce Rate by Channel
-- ============================================================
DROP VIEW IF EXISTS bounce_by_channel;
CREATE VIEW bounce_by_channel AS
SELECT
    sessions.channel AS channel,
    COUNT(0)  AS total_sessions,
    SUM(sessions.bounced) AS bounced_sessions,
    ROUND((SUM(sessions.bounced) / COUNT(0)) * 100, 1) AS bounce_rate
FROM sessions
GROUP BY sessions.channel;
 
 
-- ============================================================
-- View 2: Funnel by Channel
-- ============================================================
DROP VIEW IF EXISTS funnel_chaannel;
CREATE VIEW funnel_chaannel AS
SELECT
    u.channel,
    COUNT(DISTINCT CASE WHEN e.event_type = 'view'     THEN e.user_id END) AS view_users,
    COUNT(DISTINCT CASE WHEN e.event_type = 'cart'     THEN e.user_id END) AS cart_users,
    COUNT(DISTINCT CASE WHEN e.event_type = 'purchase' THEN e.user_id END) AS purchase_users,
 
    COUNT(DISTINCT CASE WHEN e.event_type = 'cart' THEN e.user_id END) /
    NULLIF(COUNT(DISTINCT CASE WHEN e.event_type = 'view' THEN e.user_id END), 0)
        AS cart_conversion_rate,
 
    COUNT(DISTINCT CASE WHEN e.event_type = 'purchase' THEN e.user_id END) /
    NULLIF(COUNT(DISTINCT CASE WHEN e.event_type = 'cart' THEN e.user_id END), 0)
        AS purchase_conversion_rate
 
FROM events e
LEFT JOIN users u ON e.user_id = u.user_id
GROUP BY u.channel;
 
 
-- ============================================================
-- View 3: Overall Funnel KPIs
-- ============================================================
DROP VIEW IF EXISTS funnel_overall;
CREATE VIEW funnel_overall AS
SELECT
    (SELECT COUNT(DISTINCT user_id) FROM events WHERE event_type = 'view')     AS view_users,
    (SELECT COUNT(DISTINCT user_id) FROM events WHERE event_type = 'cart')     AS cart_users,
    (SELECT COUNT(DISTINCT user_id) FROM events WHERE event_type = 'purchase') AS purchase_users,
 
    (SELECT COUNT(DISTINCT user_id) FROM events WHERE event_type = 'cart') /
    NULLIF((SELECT COUNT(DISTINCT user_id) FROM events WHERE event_type = 'view'), 0)
        AS cart_conversion_rate,
 
    (SELECT COUNT(DISTINCT user_id) FROM events WHERE event_type = 'purchase') /
    NULLIF((SELECT COUNT(DISTINCT user_id) FROM events WHERE event_type = 'cart'), 0)
        AS purchase_conversion_rate;
 
 
-- ============================================================
-- View 4: Monthly Revenue Trend
-- ============================================================
DROP VIEW IF EXISTS monthly_revenue;
CREATE VIEW monthly_revenue AS
SELECT
    DATE_FORMAT(transaction_date, '%Y-%m') AS month,
    ROUND(SUM(amount), 0) AS total_revenue
FROM transactions
GROUP BY DATE_FORMAT(transaction_date, '%Y-%m')
ORDER BY month;
 
 
-- ============================================================
-- View 5: Revenue by Channel
-- ============================================================
DROP VIEW IF EXISTS revenue_by_channel;
CREATE VIEW revenue_by_channel AS
SELECT
    channel,
    ROUND(SUM(amount), 0) AS total_revenue
FROM transactions
GROUP BY channel
ORDER BY total_revenue DESC;
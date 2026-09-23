WITH user_sessions AS (
    SELECT
        user_id,
        session_id,
        viewed,
        added_to_cart,
        purchased,
        session_revenue,
        session_start
    FROM {{ ref('fct_sessions') }}
),

user_product_views AS (
    SELECT
        user_id,
        product_name,
        COUNT(*) AS view_count
    FROM {{ ref('stg_events') }}
    WHERE event_type = 'view'
    GROUP BY user_id, product_name
),

most_viewed_product AS (
    SELECT
        user_id,
        product_name AS most_viewed_product,
        view_count AS most_viewed_product_count,
        ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY view_count DESC) AS rn
    FROM user_product_views
)

SELECT
    us.user_id,
    COUNT(DISTINCT us.session_id) AS total_sessions,
    SUM(us.viewed) AS total_view_sessions,
    SUM(us.added_to_cart) AS total_cart_sessions,
    SUM(us.purchased) AS total_purchase_sessions,
    SUM(us.session_revenue) AS lifetime_revenue,
    ROUND(SUM(us.purchased) / NULLIF(COUNT(DISTINCT us.session_id), 0), 2) AS purchase_rate,
    mvp.most_viewed_product,
    mvp.most_viewed_product_count,
    MIN(us.session_start) AS first_seen,
    MAX(us.session_start) AS last_seen
FROM user_sessions us
LEFT JOIN most_viewed_product mvp
    ON us.user_id = mvp.user_id AND mvp.rn = 1
GROUP BY us.user_id, mvp.most_viewed_product, mvp.most_viewed_product_count

WITH session_events AS (
    SELECT
        session_id,
        user_id,
        event_type,
        product_id,
        product_name,
        price,
        event_timestamp
    FROM {{ ref('stg_events') }}
)

SELECT
    session_id,
    user_id,

    -- what was viewed/purchased in this session
    MAX(CASE WHEN event_type = 'view' THEN product_name END) AS viewed_product,
    MAX(CASE WHEN event_type = 'purchase' THEN product_name END) AS purchased_product,

    -- did this session reach each funnel stage?
    MAX(CASE WHEN event_type = 'view' THEN 1 ELSE 0 END) AS viewed,
    MAX(CASE WHEN event_type = 'add_to_cart' THEN 1 ELSE 0 END) AS added_to_cart,
    MAX(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) AS purchased,

    -- revenue from this session (0 if no purchase)
    COALESCE(SUM(CASE WHEN event_type = 'purchase' THEN price END), 0) AS session_revenue,

    -- timing
    MIN(event_timestamp) AS session_start,
    MAX(event_timestamp) AS session_end,
    DATEDIFF('second', MIN(event_timestamp), MAX(event_timestamp)) AS session_duration_seconds,

    COUNT(*) AS total_events

FROM session_events
GROUP BY session_id, user_id

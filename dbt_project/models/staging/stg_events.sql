SELECT
    EVENT_DATA:event_id::STRING       AS event_id,
    EVENT_DATA:user_id::STRING        AS user_id,
    EVENT_DATA:session_id::STRING     AS session_id,
    EVENT_DATA:event_type::STRING     AS event_type,
    EVENT_DATA:product_id::STRING     AS product_id,
    EVENT_DATA:product_name::STRING   AS product_name,
    EVENT_DATA:price::FLOAT           AS price,
    EVENT_DATA:timestamp::TIMESTAMP_NTZ AS event_timestamp,
    LOADED_AT
FROM {{ source('raw', 'raw_events') }}
WHERE EVENT_DATA:event_type IS NOT NULL

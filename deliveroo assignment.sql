CREATE OR REPLACE TABLE `head-of-data-2.group_6.enriched_synthetic_deliveroo_plus_dataset` AS
WITH
  params AS (SELECT 3 AS threshold),  -- change 3 -> 20 easily

  base AS (
    SELECT
      id_customer_synth,
      order_datetime_synth,
      is_free_delivery,

      -- a new "block" starts every time we see a paid delivery (is_free_delivery = 0)
      SUM(CASE WHEN is_free_delivery = 0 THEN 1 ELSE 0 END) OVER (
        PARTITION BY id_customer_synth
        ORDER BY order_datetime_synth
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
      ) AS streak_id
    FROM `head-of-data-2.assignment_data.synthetic_deliveroo_plus_dataset`
  ),

  streak_stats AS (
    SELECT
      *,
      COUNTIF(is_free_delivery = 1) OVER (
        PARTITION BY id_customer_synth, streak_id
      ) AS free_streak_len,
      MIN(IF(is_free_delivery = 1, order_datetime_synth, NULL)) OVER (
        PARTITION BY id_customer_synth, streak_id
      ) AS streak_start_dt,
      MAX(IF(is_free_delivery = 1, order_datetime_synth, NULL)) OVER (
        PARTITION BY id_customer_synth, streak_id
      ) AS streak_end_dt
    FROM base
  )

SELECT
  id_customer_synth,
  order_datetime_synth,
  is_free_delivery,

  CASE
    WHEN is_free_delivery = 1
     AND free_streak_len >= (SELECT threshold FROM params)
    THEN 1 ELSE 0
  END AS is_order_made_during_subscription,

  CASE
    WHEN is_free_delivery = 1
     AND free_streak_len >= (SELECT threshold FROM params)
    THEN streak_start_dt ELSE NULL
  END AS current_subscription_start_datetime,

  CASE
    WHEN is_free_delivery = 1
     AND free_streak_len >= (SELECT threshold FROM params)
    THEN streak_end_dt ELSE NULL
  END AS current_subscription_end_datetime

FROM streak_stats;

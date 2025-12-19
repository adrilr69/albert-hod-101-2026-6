-- Tests Deliveroo Plus tagging
-- Objectif : vérifier que la table enrichie est cohérente et conforme à l'énoncé.

-- TEST 1 — Output = Input (pas de perte / pas de doublons)
SELECT
  (SELECT COUNT(*) FROM `head-of-data-2.assignment_data.synthetic_deliveroo_plus_dataset`) AS source_rows,
  (SELECT COUNT(*) FROM `head-of-data-2.group_6.enriched_synthetic_deliveroo_plus_dataset`) AS output_rows;

-- TEST 2 — Aucune commande payante ne doit être taggée comme "subscription"
SELECT
  COUNTIF(is_order_made_during_subscription = 1 AND is_free_delivery != 1) AS bad_rows
FROM `head-of-data-2.group_6.enriched_synthetic_deliveroo_plus_dataset`;

-- TEST 3 — Toutes les lignes taggées doivent avoir start/end non NULL
SELECT
  COUNTIF(is_order_made_during_subscription = 1
          AND (current_subscription_start_datetime IS NULL OR current_subscription_end_datetime IS NULL)
  ) AS bad_rows
FROM `head-of-data-2.group_6.enriched_synthetic_deliveroo_plus_dataset`;

-- TEST 4 — Cohérence temporelle : start <= end pour toutes les lignes taggées
SELECT
  COUNTIF(is_order_made_during_subscription = 1
          AND current_subscription_start_datetime > current_subscription_end_datetime
  ) AS bad_rows
FROM `head-of-data-2.group_6.enriched_synthetic_deliveroo_plus_dataset`;

-- TEST 5 — Seuil respecté : chaque (client, start, end) taggé doit contenir au moins 3 commandes gratuites taggées
-- (ici threshold = 3 ; si tu changes le seuil dans le script, change aussi la valeur ci-dessous)
SELECT
  COUNT(*) AS bad_periods
FROM (
  SELECT
    id_customer_synth,
    current_subscription_start_datetime,
    current_subscription_end_datetime,
    COUNT(*) AS tagged_free_orders
  FROM `head-of-data-2.group_6.enriched_synthetic_deliveroo_plus_dataset`
  WHERE is_order_made_during_subscription = 1
  GROUP BY 1,2,3
)
WHERE tagged_free_orders < 3;

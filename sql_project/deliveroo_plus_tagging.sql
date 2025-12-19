-- Deliveroo Plus 
--
-- Contexte : on n'a pas l'historique réel des abonnements (start/cancel). On doit donc inférer
--           des "périodes d'abonnement" uniquement à partir de is_free_delivery.
--
-- Hypothèse (celle des slides) :
-- - Un client est considéré abonné si on observe au moins N commandes d'affilée sans frais de livraison.
-- - Si un run gratuit atteint ce seuil, alors toutes les commandes gratuites de ce run
--   (les N premières et les suivantes) sont expliquées par l'abonnement.
--
-- Ce qu'on produit :
-- - Une table enrichie avec, pour chaque commande :
--     1) is_order_made_during_subscription (0/1)
--     2) current_subscription_start_datetime (datetime ou NULL)
--     3) current_subscription_end_datetime (datetime ou NULL)
--
-- Le seuil N est paramétrable en un seul endroit (3, 5, 20...).
-- On découpe le travail en 3 scripts/tables pour que la logique soit facile à relire et à tester.


-- SCRIPT 1/3
-- On crée une table d'entrée propre avec uniquement les colonnes utiles.
-- On renomme les champs pour éviter de mélanger les noms "synth" avec le raisonnement.
CREATE OR REPLACE TABLE `head-of-data-2.group_6.tmp_deliveroo_orders_prepared` AS
SELECT
  id_customer_synth AS customer_id,
  order_datetime_synth AS order_datetime,
  CAST(is_free_delivery AS INT64) AS is_free_delivery
FROM `head-of-data-2.assignment_data.synthetic_deliveroo_plus_dataset`;


-- SCRIPT 2/3
-- On identifie les périodes de livraisons gratuites consécutives ("runs gratuits").
-- Un run gratuit commence quand :
-- - la commande est gratuite (is_free_delivery = 1)
-- - et la commande précédente du même client n'était pas gratuite (0) ou n'existe pas.
--
-- Pour obtenir la fin du run :
-- - on cherche la prochaine commande payante après le début du run,
-- - puis on prend la dernière commande gratuite juste avant cette commande payante.
-- S'il n'y a pas de commande payante après, le run se termine à la dernière commande gratuite du client.
CREATE OR REPLACE TABLE `head-of-data-2.group_6.tmp_deliveroo_free_runs` AS
WITH ordered AS (
  SELECT
    customer_id,
    order_datetime,
    is_free_delivery,
    LAG(is_free_delivery) OVER (
      PARTITION BY customer_id
      ORDER BY order_datetime
    ) AS prev_is_free
  FROM `head-of-data-2.group_6.tmp_deliveroo_orders_prepared`
),
starts AS (
  SELECT
    customer_id,
    order_datetime AS start_free_datetime
  FROM ordered
  WHERE is_free_delivery = 1
    AND (prev_is_free IS NULL OR prev_is_free != 1)
),
ends AS (
  SELECT
    s.customer_id,
    s.start_free_datetime,
    (
      SELECT MIN(o2.order_datetime)
      FROM `head-of-data-2.group_6.tmp_deliveroo_orders_prepared` o2
      WHERE o2.customer_id = s.customer_id
        AND o2.order_datetime > s.start_free_datetime
        AND o2.is_free_delivery = 0
    ) AS next_paid_datetime
  FROM starts s
)
SELECT
  e.customer_id,
  e.start_free_datetime,
  (
    SELECT MAX(o3.order_datetime)
    FROM `head-of-data-2.group_6.tmp_deliveroo_orders_prepared` o3
    WHERE o3.customer_id = e.customer_id
      AND o3.order_datetime >= e.start_free_datetime
      AND (e.next_paid_datetime IS NULL OR o3.order_datetime < e.next_paid_datetime)
      AND o3.is_free_delivery = 1
  ) AS end_free_datetime
FROM ends e
WHERE (
  SELECT MAX(o3.order_datetime)
  FROM `head-of-data-2.group_6.tmp_deliveroo_orders_prepared` o3
  WHERE o3.customer_id = e.customer_id
    AND o3.order_datetime >= e.start_free_datetime
    AND (e.next_paid_datetime IS NULL OR o3.order_datetime < e.next_paid_datetime)
    AND o3.is_free_delivery = 1
) IS NOT NULL;


-- SCRIPT 3/3
-- On qualifie les runs : un run est considéré "abonnement Deliveroo Plus" si le nombre de
-- commandes gratuites dans le run est >= threshold.
--
-- Ensuite on enrichit chaque commande :
-- - is_order_made_during_subscription = 1 uniquement pour les commandes gratuites
--   qui appartiennent à un run qualifié.
-- - current_subscription_start_datetime = début du run gratuit (première commande gratuite du run)
-- - current_subscription_end_datetime   = fin du run gratuit (dernière commande gratuite du run)
--
-- Les commandes payantes restent à 0 et n'ont pas de start/end (NULL), car elles ne sont pas
-- expliquées par Deliveroo Plus dans l'approximation des slides.
CREATE OR REPLACE TABLE `head-of-data-2.group_6.enriched_synthetic_deliveroo_plus_dataset` AS
WITH
params AS (
  SELECT 3 AS threshold
),
runs AS (
  SELECT
    r.customer_id,
    r.start_free_datetime,
    r.end_free_datetime,
    (
      SELECT COUNT(*)
      FROM `head-of-data-2.group_6.tmp_deliveroo_orders_prepared` o
      WHERE o.customer_id = r.customer_id
        AND o.order_datetime BETWEEN r.start_free_datetime AND r.end_free_datetime
        AND o.is_free_delivery = 1
    ) AS free_orders_in_run
  FROM `head-of-data-2.group_6.tmp_deliveroo_free_runs` r
),
runs_qualified AS (
  SELECT
    *,
    CASE
      WHEN free_orders_in_run >= (SELECT threshold FROM params) THEN 1
      ELSE 0
    END AS run_is_qualified
  FROM runs
)
SELECT
  o.customer_id AS id_customer_synth,
  o.order_datetime AS order_datetime_synth,
  o.is_free_delivery,
  CASE
    WHEN o.is_free_delivery = 1 AND rq.run_is_qualified = 1 THEN 1
    ELSE 0
  END AS is_order_made_during_subscription,
  CASE
    WHEN o.is_free_delivery = 1 AND rq.run_is_qualified = 1 THEN rq.start_free_datetime
    ELSE NULL
  END AS current_subscription_start_datetime,
  CASE
    WHEN o.is_free_delivery = 1 AND rq.run_is_qualified = 1 THEN rq.end_free_datetime
    ELSE NULL
  END AS current_subscription_end_datetime
FROM `head-of-data-2.group_6.tmp_deliveroo_orders_prepared` o
LEFT JOIN runs_qualified rq
  ON rq.customer_id = o.customer_id
 AND o.order_datetime BETWEEN rq.start_free_datetime AND rq.end_free_datetime;

 -- On a vérifié : 
 --   - qu'il n'y a pas de doublons (customer_id, order_datetime) -> l'ordre temporel est non ambigu.
--    - qu'aucune ligne taggée ne soit pas gratuite


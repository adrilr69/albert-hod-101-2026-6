Deliveroo Plus  

-------------------------------------------------
Objectif: Construire une table enrichie à partir du dataset `assignment_data.synthetic_deliveroo_plus_dataset` afin d’inférer des périodes d’abonnement “Deliveroo Plus” à partir des commandes gratuites (`is_free_delivery = 1`).

La table finale créée est :
- `head-of-data-2.group_6.enriched_synthetic_deliveroo_plus_dataset`

Elle contient les colonnes demandées :
- `id_customer_synth`
- `order_datetime_synth`
- `is_free_delivery`
- `is_order_made_during_subscription`
- `current_subscription_start_datetime`
- `current_subscription_end_datetime`
-------------------------------------------------
Hypothèse (celle des slides)
Nous n’avons pas l’historique réel des abonnements (start/cancel). On approxime donc l’abonnement à partir du comportement observable :

- Un client est considéré abonné si on observe **au moins N commandes consécutives** sans frais de livraison.
- Si un run gratuit atteint ce seuil, alors **toutes** les commandes gratuites de ce run (les N premières et les suivantes) sont expliquées par l’abonnement.
Le seuil N est paramétrable dans le script (par défaut N = 3).

-------------------------------------------------
Approche (logique en 3 étapes)
Le script est découpé en 3 parties (3 tables) pour que la logique soit simple à relire et à tester.

1) Input clean
On crée une table intermédiaire avec uniquement les colonnes utiles, et des noms cohérents :
- `customer_id`
- `order_datetime`
- `is_free_delivery`

Table créée :
- `head-of-data-2.group_6.tmp_deliveroo_orders_prepared`

2) Identifier les périodes (runs gratuits)
On repère les séquences consécutives de commandes gratuites (“runs”) pour chaque client :
- Un run commence quand la commande est gratuite et que la précédente ne l’était pas (transition 0 → 1).
- Le run se termine juste avant la prochaine commande payante (ou à la dernière commande gratuite du client s’il n’y a pas de commande payante ensuite).

Table créée :
- `head-of-data-2.group_6.tmp_deliveroo_free_runs`
Champs :
- `customer_id`
- `start_free_datetime`
- `end_free_datetime`

3) Qualifier + enrichir
- On compte le nombre de commandes gratuites par run.
- Un run est qualifié “Deliveroo Plus” si ce nombre est >= threshold.
- On enrichit chaque commande :
  - `is_order_made_during_subscription = 1` uniquement pour les commandes gratuites appartenant à un run qualifié.
  - `current_subscription_start_datetime = start du run`
  - `current_subscription_end_datetime = end du run`
  - Les commandes payantes restent à 0 et ont start/end à NULL.

Table créée :
- `head-of-data-2.group_6.enriched_synthetic_deliveroo_plus_dataset`

-------------------------------------------------
Fichiers du repo
- `deliveroo_plus_tagging.sql` : script principal (les 3 parties).
- `deliveroo_plus_tests.sql` : requêtes de validation (3–5 tests simples).

-------------------------------------------------
Exécution dans BigQuery (pas à pas)
1. Ouvrir BigQuery et sélectionner le projet `head-of-data-2`.
2. Ouvrir un nouvel onglet SQL.
3. Copier-coller et exécuter `deliveroo_plus_tagging.sql` :
   - soit en une fois,
   - soit en exécutant chaque “SCRIPT 1/3”, puis “SCRIPT 2/3”, puis “SCRIPT 3/3”.
4. Vérifier dans le dataset `group_6` que les tables ont été créées.

Tables attendues :
- `tmp_deliveroo_orders_prepared`
- `tmp_deliveroo_free_runs`
- `enriched_synthetic_deliveroo_plus_dataset`

-------------------------------------------------
Si vous messieurs le correcteurs souhaitez modifier le seuil (N)
Dans le script, modifier uniquement :
        params AS (SELECT 3 AS threshold)

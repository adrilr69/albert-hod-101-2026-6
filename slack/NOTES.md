Contexte

Ce projet a pour objectif de manipuler l’API Slack avec un bot. Le script Python est découpé en trois parties indépendantes : envoyer un message, envoyer des fichiers image, puis interagir avec les messages des utilisateurs via Socket Mode.

Sécurité et configuration

Les secrets Slack ne sont jamais écrits en dur dans le code. Les tokens sont stockés dans un fichier .env local, qui n’est pas publié sur GitHub. Cette approche évite toute fuite de clés et respecte les bonnes pratiques de sécurité.

Partie 1 : message de test

La première partie envoie un message simple dans le canal principal. Le but est de valider que le bot est correctement installé dans le workspace, qu’il dispose des permissions nécessaires, et qu’il peut publier un message.

Partie 2 : envoi d’images

La deuxième partie parcourt un dossier d’images et envoie automatiquement chaque image dans le canal de groupe. Le script ne suppose pas le nombre d’images à l’avance : il liste les fichiers du dossier, filtre les extensions d’image, puis envoie chaque fichier avec l’API Slack. Une courte pause est ajoutée entre deux envois pour éviter de saturer Slack et réduire le risque de limitations.

Partie 3 : interaction “Wikipedia:titre”

La troisième partie met le bot en écoute via Socket Mode afin de recevoir les événements Slack en temps réel sans héberger de serveur web. Lorsque l’utilisateur Woody envoie un message qui commence par Wikipedia:, le script récupère le résumé de la page Wikipédia correspondante et renvoie le premier paragraphe. Le script gère aussi les cas d’erreur : page inexistante, erreur réseau ou réponse inattendue.

Choix techniques

Le code utilise Slack Bolt pour gérer les événements (messages) et Slack SDK pour envoyer des messages et des fichiers. Pour Wikipédia, l’endpoint REST de résumé est utilisé car il renvoie directement un champ texte exploitable. Un User-Agent explicite est envoyé, car c’est une bonne pratique recommandée pour les APIs publiques.

Résultat attendu

À la fin, le bot peut : publier un message de test, envoyer toutes les images d’un dossier vers le canal de groupe, puis répondre automatiquement aux requêtes Wikipedia envoyées par Woody dans le canal principal.

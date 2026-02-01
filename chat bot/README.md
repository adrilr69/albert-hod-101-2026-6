# 📚 RAG Chat App (Streamlit + LM Studio)

Cette app Streamlit te permet de **poser des questions sur un texte/document** (ex: `Othello`) grâce à une approche **RAG** :
1) on **indexe** le document dans une base vectorielle (ChromaDB)
2) au moment de la question, on récupère les **passages les plus pertinents**
3) on envoie ces passages au **LLM** via **LM Studio (serveur local)**

✅ Avantage : le modèle tourne **sur ton ordinateur**, sans clé API.

---

## ✅ Prérequis

- **Python 3.10+** (idéalement 3.11/3.12)
- **LM Studio** installé
- Un terminal (Mac/Linux/Windows)
- (Optionnel mais conseillé) Git

---

## 1) Installer LM Studio

1. Télécharge et installe **LM Studio**
2. Ouvre LM Studio

---

## 2) Télécharger les 2 modèles dans LM Studio

Dans l’onglet **Models** (ou la recherche), télécharge ces 2 modèles :

- **mistralai/ministral-3-3b**
- **mistralai/mistral-7b-instruct-v0.3**

💡 Conseils :
- Si LM Studio te propose plusieurs formats/quantizations, une version **GGUF quantifiée (Q4_K_M)** est généralement un bon compromis **rapidité / qualité**.
- Les modèles restent stockés dans LM Studio, tu n’as rien à copier dans ton projet.

---

## 3) Lancer le serveur local LM Studio

1. Dans LM Studio : **Developer → Local Server**
2. Clique sur **Start Server**
3. Clique sur **Load Model** et charge **les 2 modèles**
4. Vérifie que tu vois :
   - `Status: Running`
   - une URL du type : `http://127.0.0.1:1234`

➡️ Garde LM Studio ouvert pendant que tu utilises l’app.

---

## 4) Installer / lancer l’app Streamlit en local

### A) Récupérer le projet + créer un environnement Python

Place-toi dans le dossier du projet (là où il y a `app.py`, `rag.py`, `requirements.txt`).

```bash
cd "/chemin/vers/ton/projet"
python -m venv .venv

------------------------------
Commandes importante:

Créer environemment Venv
Mac= source .venv/bin/activate
Windows= .\.venv\Scripts\Activate.ps1

Installer les dépendances:
pip install -r requirements.txt

Construire la base vectorielle (ChromaDB):
python build_vector_db.py

Lancer l’app:
streamlit run app.py
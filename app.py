import streamlit as st
import chromadb
from chromadb.utils import embedding_functions
from openai import OpenAI
import os
from dotenv import load_dotenv

# Configuration de la page
st.set_page_config(page_title="Othello Chatbot", layout="wide")
load_dotenv()

# Initialisation du client OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_collection():
    """Récupère la collection ChromaDB pour la recherche."""
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=os.getenv("OPENAI_API_KEY"),
        model_name="text-embedding-3-small"
    )
    return chroma_client.get_collection(name="othello_collection", embedding_function=openai_ef)

# Navigation
page = st.sidebar.selectbox("Navigation", ["HomePage", "Model Choice", "Chat Page"])

# --- PAGE ACCUEIL ---
if page == "HomePage":
    st.title("Bienvenue sur l'IA Othello")
    st.markdown("""
    Cette application est un chatbot intelligent capable de répondre à vos questions sur la pièce de théâtre **Othello** de William Shakespeare.
    
    ### Comment ça marche ?
    1. **Base de connaissance** : Nous avons indexé l'intégralité de l'œuvre dans une base de données vectorielle.
    2. **RAG** : L'IA recherche les passages pertinents avant de vous répondre.
    3. **Modèles** : Vous pouvez choisir le modèle de langage dans l'onglet dédié.
    """)

# --- PAGE CHOIX DU MODÈLE ---
elif page == "Model Choice":
    st.title("Configuration du Modèle")
    
    if "selected_model" not in st.session_state:
        st.session_state.selected_model = "gpt-4o-mini"
    
    model = st.radio(
        "Choisissez votre modèle LLM :",
        ["gpt-4o-mini", "gpt-3.5-turbo", "Local Model (Hugging Face)"],
        index=0
    )
    
    st.session_state.selected_model = model
    st.success(f"Modèle configuré sur : {model}")

# --- PAGE CHAT ---
elif page == "Chat Page":
    st.title("Discuter avec Othello")

    # Initialisation de l'historique
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Affichage des messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Logique du Chat
    if prompt := st.chat_input("Posez une question sur l'intrigue..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Recherche dans ChromaDB
        collection = get_collection()
        results = collection.query(query_texts=[prompt], n_results=3)
        context = "\n".join(results['documents'][0])

        # Appel au LLM
        with st.chat_message("assistant"):
            response = client.chat.completions.create(
                model=st.session_state.get("selected_model", "gpt-4o-mini"),
                messages=[
                    {"role": "system", "content": f"Tu es un expert shakespearien. Réponds en utilisant ce contexte : {context}"},
                    {"role": "user", "content": prompt}
                ]
            )
            full_response = response.choices[0].message.content
            st.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})

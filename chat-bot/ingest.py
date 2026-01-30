import requests
import chromadb
from chromadb.utils import embedding_functions
import os
from dotenv import load_dotenv

# Chargement des variables d'environnement
load_dotenv()

def download_othello():
    """Télécharge le texte d'Othello depuis le Projet Gutenberg."""
    url = "https://www.gutenberg.org/cache/epub/1531/pg1531.txt"
    response = requests.get(url)
    return response.text

def chunk_text(text, chunk_size=1000, overlap=100):
    """Découpe le texte en segments sans utiliser scikit-learn."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

def setup_vector_db(chunks):
    """Initialise ChromaDB et stocke les segments de texte."""
    client = chromadb.PersistentClient(path="./chroma_db")
    
    # Utilisation des embeddings OpenAI par défaut
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=os.getenv("OPENAI_API_KEY"),
        model_name="text-embedding-3-small"
    )
    
    collection = client.get_or_create_collection(
        name="othello_collection",
        embedding_function=openai_ef
    )
    
    # Ajout des documents à la collection
    ids = [f"id_{i}" for i in range(len(chunks))]
    collection.add(
        documents=chunks,
        ids=ids
    )
    print(f"Base de données créée avec {len(chunks)} segments.")

if __name__ == "__main__":
    print("Téléchargement d'Othello...")
    othello_text = download_othello()
    print("Découpage du texte...")
    text_chunks = chunk_text(othello_text)
    print("Initialisation de la base vectorielle...")
    setup_vector_db(text_chunks)

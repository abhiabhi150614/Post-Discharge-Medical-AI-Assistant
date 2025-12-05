import os
import sys
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from app.agents.llm import get_embeddings

load_dotenv()

# Check for API Key
if not os.environ.get("GOOGLE_API_KEY"):
    print("WARNING: GOOGLE_API_KEY not found in environment.")

DATA_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'nephrology_reference.txt')
DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'chroma_db')

def ingest_data():
    if not os.path.exists(DATA_PATH):
        print(f"Data file not found at {DATA_PATH}")
        return

    loader = TextLoader(DATA_PATH)
    documents = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = text_splitter.split_documents(documents)

    print(f"Split into {len(chunks)} chunks.")

    # Use Gemini Embeddings
    embeddings = get_embeddings()
    
    # Initialize Chroma
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=DB_PATH
    )
    
    print(f"Ingested {len(chunks)} chunks into ChromaDB at {DB_PATH}")

if __name__ == "__main__":
    ingest_data()

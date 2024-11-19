from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
import os

DATA_PATH = "data/Skeletron_Prime"
DB_FAISS_PATH = "vectorstores/db_faiss"

def load_documents(data_path, file_pattern="*.pdf"):
    """Load PDF documents from a directory."""
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"The specified data path '{data_path}' does not exist.")
    pdf_loader = DirectoryLoader(data_path, glob=file_pattern, loader_cls=PyPDFLoader)
    return pdf_loader.load()

def split_documents(documents, chunk_size=500, chunk_overlap=50):
    """Split documents into chunks using a text splitter."""
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return text_splitter.split_documents(documents)

def create_embeddings(model_name='sentence-transformers/all-MiniLM-L6-v2', device='cpu'):
    """Initialize the HuggingFace embeddings."""
    return HuggingFaceEmbeddings(model_name=model_name, model_kwargs={'device': device})

def create_vector_store(texts, embeddings, db_path):
    """Create and save a FAISS vector database."""
    db = FAISS.from_documents(texts, embeddings)
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    db.save_local(db_path)
    print(f"Vector database saved at '{db_path}'.")

def create_vector_db():
    """Main function to create the vector database."""
    try:
        print("Loading documents...")
        documents = load_documents(DATA_PATH)

        print("Splitting documents into chunks...")
        texts = split_documents(documents)

        print("Initializing embeddings...")
        embeddings = create_embeddings()

        print("Creating and saving the vector store...")
        create_vector_store(texts, embeddings, DB_FAISS_PATH)
        
        print("Vector database creation completed successfully.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    create_vector_db()

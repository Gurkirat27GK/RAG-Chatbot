from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_chroma import Chroma
from splitter import split
import config
import os

def get_vector_store():
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

    # If Chroma DB already exists, just load it
    if os.path.exists(config.CHROMA_DB_DIR) and os.listdir(config.CHROMA_DB_DIR):
        print("✅ Loading existing Chroma DB...")
        return Chroma(
            embedding_function=embeddings,
            persist_directory=config.CHROMA_DB_DIR,
            collection_name=config.CHROMA_COLLECTION
        )

    # Else, create it from chunks and persist
    print("⚡ Creating new Chroma DB...")

    chunks = split()
    # return FAISS.from_documents(chunks, embeddings)
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=config.CHROMA_DB_DIR,
        collection_name=config.CHROMA_COLLECTION
    )
    print("✅ Chroma DB created and persisted.")
    return vectorstore

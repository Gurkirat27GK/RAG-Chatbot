from langchain_community.document_loaders import PyPDFLoader

def load():
    loader = PyPDFLoader('AppleData-2024.pdf')
    docs = loader.load()
    print(len(docs))
    return docs

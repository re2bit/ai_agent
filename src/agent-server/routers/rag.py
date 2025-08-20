import os

from dependency_injector.wiring import inject, Provide
from fastapi import APIRouter
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_core.documents import Document
from langchain_core.embeddings.embeddings import Embeddings
from langchain_ollama import OllamaEmbeddings
from langchain_postgres import PGEngine, PGVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langfuse import Langfuse

from ..container.container import container


class Routes:
    router: APIRouter
    langfuse_config: dict
    pgengine: PGEngine
    embeddings: Embeddings
    vectorSize: int

    def __call__(self, *args, **kwargs):
        return self.router

    @inject
    def __init__(
            self,
            langfuse_config: dict = Provide[container.langfuse_config],
            pgengine: PGEngine = Provide[container.pgengine],
            ollamaEmbeddings: OllamaEmbeddings = Provide[container.ollamaEmbeddings],
            vectorSize: int = Provide[container.vectorSize],
    ):
        self.langfuse_config = langfuse_config
        self.pgengine = pgengine
        self.embeddings = ollamaEmbeddings
        self.vectorSize = vectorSize

        router = APIRouter()
        self.router = router
        self.router.add_api_route("/rag", self.rag, methods=["GET"])

    async def rag(self):
        loader = PyMuPDFLoader(r"rag-dataset/gym supplements/1. Analysis of Actual Fitness Supplement.pdf")
        loader.load()
        pdfs = []
        for root, dirs, files in os.walk("rag-dataset"):
            for file in files:
                if file.endswith(".pdf"):
                    pdfs.append(os.path.join(root, file))
        pdfs = []
        for root, dirs, files in os.walk("rag-dataset"):
            for file in files:
                if file.endswith(".pdf"):
                    try:
                        pdf_path = os.path.join(root, file)
                        if os.path.isfile(pdf_path) and os.access(pdf_path, os.R_OK):
                            pdfs.append(pdf_path)
                    except Exception as e:
                        print(f"Error accessing file {file}: {str(e)}")
        print(f"Total PDF files found: {len(pdfs)}")

        pdfs
        docs = []
        for pdf in pdfs:
            loader = PyMuPDFLoader(pdf)
            temp = loader.load()
            docs.extend(temp)

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        chunks = text_splitter.split_documents(docs)

        # len(docs), len(chunks)
        # docs[0].metadata
        # len(chunks[0].page_content)
        # chunks[0].metadata
        # chunks[1].metadata
        # chunks[150].metadata

        vector = self.embeddings.embed_query(chunks[0].page_content)

        TABLE_NAME = "nes_documentation"

        self.pgengine.init_vectorstore_table(
            table_name=TABLE_NAME,
            vector_size=self.VECTOR_SIZE,
        )

        store = PGVectorStore.create_sync(
            engine=self.pgengine,
            table_name=TABLE_NAME,
            embedding_service=self.embedding,
            config=self.langfuse_config
        )

        docs = [
            Document(page_content="Apples and oranges"),
            Document(page_content="Cars and airplanes"),
            Document(page_content="Train")
        ]

        store.add_documents(docs)

        query = "I'd like a fruit."
        docs = store.similarity_search(query)
        return docs
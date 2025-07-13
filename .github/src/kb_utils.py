import os

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from pydantic import SecretStr


class KnowledgeBaseUtils:
    """
    A utility class for creating and querying a local knowledge base using FAISS.
    Implements persistence for the FAISS index to improve performance on subsequent runs.
    """

    def __init__(self, samples_dir: str, openai_api_key: str, index_path: str = "./faiss_index"):
        """
        Initializes the KnowledgeBaseUtils and builds/loads the FAISS vector store.

        Args:
            samples_dir (str): Path to the directory containing sample code for the KB.
            openai_api_key (str): API key for OpenAI embeddings.
            index_path (str): Directory where the FAISS index will be saved/loaded.
        """
        self.vector_store = None
        self.openai_api_key = openai_api_key
        self.samples_dir = samples_dir
        self.index_path = index_path
        self._initialize_knowledge_base()

    def _initialize_knowledge_base(self):
        """
        Initializes the local knowledge base using FAISS.
        Attempts to load from disk first. If not found or samples are updated,
        it rebuilds and saves the index.
        If any error occurs during initialization, self.vector_store will be None,
        but no exception will be re-raised to allow the main process to continue.
        """
        # Check if the index already exists and the samples directory hasn't been modified
        samples_dir_mtime = os.path.getmtime(self.samples_dir) if os.path.exists(self.samples_dir) else 0
        index_mtime_file = os.path.join(self.index_path, "last_modified.txt")
        last_index_mtime = 0
        if os.path.exists(index_mtime_file):
            with open(index_mtime_file, "r") as f:
                try:
                    last_index_mtime = float(f.read())
                except ValueError:
                    pass # Invalid content, force rebuild

        if os.path.exists(self.index_path) and samples_dir_mtime <= last_index_mtime:
            try:
                # Load existing FAISS index
                embeddings = OpenAIEmbeddings(api_key=SecretStr(self.openai_api_key))
                self.vector_store = FAISS.load_local(self.index_path, embeddings, allow_dangerous_deserialization=True)
                print(f"FAISS knowledge base loaded from '{self.index_path}'.")
                return
            except Exception as e:
                print(f"Error loading FAISS index from '{self.index_path}': {e}. Rebuilding...")
                # Fall through to rebuild if loading fails

        print(f"Building FAISS knowledge base from '{self.samples_dir}'...")
        if not os.path.exists(self.samples_dir):
            print(f"Warning: Knowledge base samples directory '{self.samples_dir}' not found. Skipping KB initialization.")
            self.vector_store = None
            return

        try:
            loader = DirectoryLoader(self.samples_dir, glob="**/*.txt", loader_cls=TextLoader)
            documents = loader.load()
            print(f"Loaded {len(documents)} documents from KB.")

            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            texts = text_splitter.split_documents(documents)
            print(f"Split documents into {len(texts)} chunks.")

            embeddings = OpenAIEmbeddings(api_key=SecretStr(self.openai_api_key))
            self.vector_store = FAISS.from_documents(texts, embeddings)
            print("FAISS knowledge base built successfully.")

            # Save the index for future runs
            os.makedirs(self.index_path, exist_ok=True)
            self.vector_store.save_local(self.index_path)
            # Save the current modification time of the samples directory
            with open(index_mtime_file, "w") as f:
                f.write(str(samples_dir_mtime))
            print(f"FAISS knowledge base saved to '{self.index_path}'.")

        except Exception as e:
            print(f"Error building knowledge base: {e}")
            self.vector_store = None # Ensure vector_store is None on failure
            # Removed 'raise' here to allow the process to continue

    def query_knowledge_base(self, query: str) -> str:
        """
        Retrieves relevant context from the knowledge base based on a query.

        Args:
            query (str): The query to search the knowledge base with.

        Returns:
            str: A formatted string of retrieved documents, or an empty string if no KB.
        """
        if not self.vector_store:
            return ""

        try:
            docs = self.vector_store.similarity_search(query, k=3) # Retrieve top 3 relevant docs
            context = "\n\n".join([doc.page_content for doc in docs])
            print(f"Retrieved {len(docs)} documents from KB for query.")
            return f"{context}"
        except Exception as e:
            print(f"Error querying knowledge base: {e}")
            return ""


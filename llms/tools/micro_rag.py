import PyPDF2  # pip install pypdf2
from langchain_community.embeddings import OllamaEmbeddings # pip install langchain-community
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma

## This will be the main class for the micro agentic-rag model
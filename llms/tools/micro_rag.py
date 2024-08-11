import os
import openai
import faiss  # pip install faiss-cpu or faiss-gpu
import numpy as np
import pandas as pd
import pdfplumber
import docx
import openpyxl
import csv
from io import StringIO
from tiktoken import encoding_for_model

class InMemoryIndexer:
    def __init__(self, openai_api_key, embedding_model="text-embedding-ada-002", dim=1536, api_type='openai'):
        openai.api_key = openai_api_key
        openai.api_type = api_type
        self.embedding_model = embedding_model
        self.dim = dim
        self.index = faiss.IndexFlatL2(dim)  # L2 (Euclidean) distance
        self.id_counter = 0
        self.id_to_text = {}
        self.tokenizer = encoding_for_model(embedding_model)  # Initialize tokenizer for the model

    def _embed_text(self, text):
        # Correctly access the response data using attribute access
        response = openai.embeddings.create(input=[text], model=self.embedding_model)
        embedding = response.data[0].embedding
        return np.array(embedding, dtype=np.float32).reshape(1, -1)

    def _split_text(self, text, max_tokens=8192):
        # Split text into chunks that are within the token limit
        tokens = self.tokenizer.encode(text)
        chunks = []
        for i in range(0, len(tokens), max_tokens):
            chunk = self.tokenizer.decode(tokens[i:i + max_tokens])
            chunks.append(chunk)
        return chunks

    def _extract_text_from_file(self, filepath):
        ext = os.path.splitext(filepath)[-1].lower()
        if ext in ['.txt']:
            # Explicitly set encoding to handle non-ASCII characters
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as file:
                return file.read()
        elif ext in ['.csv']:
            return self._extract_text_from_csv(filepath)
        elif ext in ['.xlsx', '.xls']:
            return self._extract_text_from_excel(filepath)
        elif ext in ['.pdf']:
            return self._extract_text_from_pdf(filepath)
        elif ext in ['.docx']:
            return self._extract_text_from_docx(filepath)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

    def _extract_text_from_csv(self, filepath):
        text = []
        with open(filepath, newline='', encoding='utf-8', errors='ignore') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                text.append(' '.join(row))
        return ' '.join(text)

    def _extract_text_from_excel(self, filepath):
        text = []
        wb = openpyxl.load_workbook(filepath)
        for sheet in wb:
            for row in sheet.iter_rows():
                text.append(' '.join([str(cell.value) for cell in row if cell.value]))
        return ' '.join(text)

    def _extract_text_from_pdf(self, filepath):
        text = []
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text.append(page_text)
        return ' '.join(text)

    def _extract_text_from_docx(self, filepath):
        doc = docx.Document(filepath)
        text = [paragraph.text for paragraph in doc.paragraphs]
        return ' '.join(text)

    def index_files(self, filepaths):
        for filepath in filepaths:
            try:
                text = self._extract_text_from_file(filepath)
                chunks = self._split_text(text, max_tokens=8192)  # Split text into manageable chunks
                for chunk in chunks:
                    embedding = self._embed_text(chunk)
                    self.index.add(embedding)
                    self.id_to_text[self.id_counter] = chunk
                    self.id_counter += 1
            except Exception as e:
                print(f"Error processing {filepath}: {e}")

    def search(self, query, k=5):
        query_embedding = self._embed_text(query)
        distances, indices = self.index.search(query_embedding, k)
        return [(self.id_to_text[idx], dist) for idx, dist in zip(indices[0], distances[0]) if idx != -1]

# Usage example
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv('environment.env', override=True)
    openai_api_key = os.getenv('OPENAI_API_KEY')
    
    # Ensure the directory exists
    if not os.path.exists('yourfiles'):
        print("Directory 'yourfiles' does not exist.")
        exit(1)
    
    # Ensure directory is not empty
    files = [os.path.join('yourfiles', file) for file in os.listdir('yourfiles') if os.path.isfile(os.path.join('yourfiles', file))]
    if not files:
        print("No files found in 'yourfiles' directory.")
        exit(1)
    
    indexer = InMemoryIndexer(openai_api_key)
    indexer.index_files(files)
    
    results = indexer.search("List critical date relating to Bajoran Orbs")
    for result in results:
       print(result)

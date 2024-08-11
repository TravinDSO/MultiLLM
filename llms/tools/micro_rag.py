import hnswlib
import openai
import pandas as pd
import pdfplumber
import docx
from io import StringIO
import openpyxl
import csv
import os

class InMemoryIndexer:
    def __init__(self, openai_api_key, embedding_model="text-embedding-ada-002", space='cosine', dim=1536):
        openai.api_key = openai_api_key
        self.embedding_model = embedding_model
        self.index = hnswlib.Index(space=space, dim=dim)
        self.index.init_index(max_elements=10000, ef_construction=200, M=16)
        self.index.set_ef(200)
        self.id_counter = 0
        self.id_to_text = {}
    
    def _embed_text(self, text):
        response = openai.Embedding.create(input=[text], model=self.embedding_model)
        return response['data'][0]['embedding']

    def _extract_text_from_file(self, filepath):
        ext = os.path.splitext(filepath)[-1].lower()
        if ext in ['.txt']:
            with open(filepath, 'r') as file:
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
        with open(filepath, newline='') as csvfile:
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
                text.append(page.extract_text())
        return ' '.join(text)

    def _extract_text_from_docx(self, filepath):
        doc = docx.Document(filepath)
        text = [paragraph.text for paragraph in doc.paragraphs]
        return ' '.join(text)

    def index_files(self, filepaths):
        for filepath in filepaths:
            text = self._extract_text_from_file(filepath)
            embedding = self._embed_text(text)
            self.index.add_items([embedding], [self.id_counter])
            self.id_to_text[self.id_counter] = text
            self.id_counter += 1

    def search(self, query, k=5):
        query_embedding = self._embed_text(query)
        labels, distances = self.index.knn_query(query_embedding, k=k)
        return [(self.id_to_text[label], distance) for label, distance in zip(labels[0], distances[0])]

# Usage example
# indexer = InMemoryIndexer(openai_api_key="YOUR_OPENAI_API_KEY")
# indexer.index_files(['path/to/file1.txt', 'path/to/file2.pdf'])
# results = indexer.search("Sample query")
# for result in results:
#     print(result)

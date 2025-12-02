"""
Script para vectorizar documentos PDF y almacenarlos en PostgreSQL
Requiere: pip install pypdf sentence-transformers psycopg2-binary pgvector
"""

import os
import sys
from pathlib import Path
from typing import List, Tuple
import psycopg2
from psycopg2.extras import execute_values, Json
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
import numpy as np


""" 
Clase que realiza la vectorizacion.
El procedimeinto es: 

"""
class PDFVectorizer:
    def __init__(self, db_config: dict):
        """
        Inicializa el vectorizador de PDFs
        
        Args:
            db_config: Diccionario con configuración de BD (host, database, user, password, port)
        """
        self.db_config = db_config
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.chunk_size = 500  # caracteres por chunk
        self.chunk_overlap = 50  # overlap entre chunks
        
    def connect_db(self):
        """Establece conexión con PostgreSQL"""
        return psycopg2.connect(**self.db_config)
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extrae texto de un archivo PDF
        
        Args:
            pdf_path: Ruta al archivo PDF
            
        Returns:
            Texto completo del PDF
        """
        try:
            reader = PdfReader(pdf_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            
            # Limpiar caracteres NUL que postgres no acepta
            text = text.replace('\x00', '')
            
            return text
        except Exception as e:
            print(f"Error al leer PDF {pdf_path}: {e}")
            return ""
    
    def chunk_text(self, text: str) -> List[str]:
        """
        Divide el texto en fragmentos (chunks) con overlap
        
        Args:
            text: Texto completo a dividir
            
        Returns:
            Lista de chunks de texto
        """
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + self.chunk_size
            chunk = text[start:end]
            
            # Intentar cortar en un espacio para no dividir palabras
            if end < text_length:
                last_space = chunk.rfind(' ')
                if last_space > self.chunk_overlap:
                    chunk = chunk[:last_space]
                    end = start + last_space
            
            chunks.append(chunk.strip())
            start = end - self.chunk_overlap
            
        return [c for c in chunks if c]  # Filtrar chunks vacíos
    
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Genera embeddings para una lista de textos
        
        Args:
            texts: Lista de textos
            
        Returns:
            Array numpy con los embeddings
        """
        return self.model.encode(texts, show_progress_bar=True)
    
    def store_chunks(self, document_name: str, chunks: List[str], embeddings: np.ndarray):
        """
        Almacena chunks y embeddings en PostgreSQL
        
        Args:
            document_name: Nombre del documento
            chunks: Lista de chunks de texto
            embeddings: Embeddings correspondientes
        """
        conn = self.connect_db()
        cursor = conn.cursor()
        
        # Preparar datos para inserción
        values = [
            (
                document_name,
                chunk,
                idx,
                embedding.tolist(),
                Json({})  # metadata vacío por ahora
            )
            for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings))
        ]
        
        # Inserción batch
        insert_query = """
            INSERT INTO document_chunks 
            (document_name, chunk_text, chunk_index, embedding, metadata)
            VALUES %s
        """
        
        execute_values(cursor, insert_query, values)
        conn.commit()
        
        print(f"✓ Almacenados {len(chunks)} chunks para '{document_name}'")
        
        cursor.close()
        conn.close()
    
    def process_pdf(self, pdf_path: str):
        """
        Procesa un PDF completo: extrae texto, crea chunks, genera embeddings y almacena
        
        Args:
            pdf_path: Ruta al archivo PDF
        """
        document_name = Path(pdf_path).name
        print(f"\nProcesando: {document_name}")
        
        # 1. Extraer texto
        print("  Extrayendo texto...")
        text = self.extract_text_from_pdf(pdf_path)
        
        if not text:
            print(f"  ✗ No se pudo extraer texto del PDF")
            return
        
        print(f"  Texto extraído: {len(text)} caracteres")
        
        # 2. Crear chunks
        print("  Creando chunks...")
        chunks = self.chunk_text(text)
        print(f"  Creados {len(chunks)} chunks")
        
        # 3. Generar embeddings
        print("  Generando embeddings...")
        embeddings = self.generate_embeddings(chunks)
        
        # 4. Almacenar en BD
        print("  Almacenando en base de datos...")
        self.store_chunks(document_name, chunks, embeddings)
        
    def process_directory(self, directory_path: str):
        """
        Procesa todos los PDFs en un directorio
        
        Args:
            directory_path: Ruta al directorio con PDFs
        """
        pdf_files = list(Path(directory_path).glob("*.pdf"))
        
        if not pdf_files:
            print(f"No se encontraron archivos PDF en {directory_path}")
            return
        
        print(f"Encontrados {len(pdf_files)} archivos PDF")
        
        for pdf_file in pdf_files:
            self.process_pdf(str(pdf_file))
        
        print(f"\n✓ Procesamiento completado: {len(pdf_files)} documentos")


def main():
    """Función principal"""
    
    # Configuración de base de datos
    db_config = {
        'host': 'localhost', # Cambiar según configuración
        'database': 'dbtest',
        'user': 'postgres',  # Cambiar según configuración
        'password': 'postgres',  # Cambiar según configuración
        'port': 5432
    }
    
    # Inicializar vectorizador
    vectorizer = PDFVectorizer(db_config)
    
    # Procesar PDFs
    if len(sys.argv) > 1:
        path = sys.argv[1]
        if os.path.isfile(path) and path.endswith('.pdf'):
            vectorizer.process_pdf(path)
        elif os.path.isdir(path):
            vectorizer.process_directory(path)
        else:
            print("Error: Proporcione una ruta válida a un PDF o directorio")
    else:
        print("Uso: python pdf_vectorizer.py <ruta_pdf_o_directorio>")
        print("Ejemplo: python pdf_vectorizer.py ./documentos/")


if __name__ == "__main__":
    main()
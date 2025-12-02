"""
Servidor MCP para búsqueda semántica en documentos vectorizados
Requiere: pip install mcp psycopg2-binary sentence-transformers
"""

import asyncio
import psycopg2
from sentence_transformers import SentenceTransformer
from mcp.server import Server
from mcp.types import Tool, TextContent
import json

# Configuración de base de datos
DB_CONFIG = {
    'host': 'localhost', # Cambiar segun la configuracion
    'database': 'dbtest', # Cambiar segun la configuracion
    'user': 'postgres', # Cambiar segun la configuracion
    'password': 'postgres', # Cambiar segun la configuracion
    'port': 5432
}

# Inicializar modelo de embeddings
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

# Crear servidor MCP
app = Server("document-search-server")


def get_db_connection():
    """Establece conexión con PostgreSQL"""
    return psycopg2.connect(**DB_CONFIG)


def search_documents(query: str, top_k: int = 5, threshold: float = 0.3) -> list:
    """
    Realiza búsqueda semántica en la base de datos vectorial
    
    Args:
        query: Consulta del usuario
        top_k: Número máximo de resultados
        threshold: Umbral de similitud mínima
        
    Returns:
        Lista de resultados con texto y similitud
    """
    # Generar embedding de la consulta
    query_embedding = embedding_model.encode(query)
    
    # Conectar a la base de datos
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Realizar búsqueda vectorial
    search_query = """
        SELECT 
            document_name,
            chunk_text,
            1 - (embedding <=> %s::vector) as similarity
        FROM document_chunks
        WHERE 1 - (embedding <=> %s::vector) > %s
        ORDER BY embedding <=> %s::vector
        LIMIT %s
    """
    
    cursor.execute(
        search_query,
        (query_embedding.tolist(), query_embedding.tolist(), threshold, query_embedding.tolist(), top_k)
    )
    
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    
    # Formatear resultados
    formatted_results = []
    for doc_name, text, similarity in results:
        formatted_results.append({
            'document': doc_name,
            'text': text,
            'similarity': float(similarity)
        })
    
    return formatted_results


def list_documents() -> list:
    """
    Lista todos los documentos indexados en la base de datos
    
    Returns:
        Lista de nombres de documentos únicos con conteo de chunks
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT document_name, COUNT(*) as chunk_count
        FROM document_chunks
        GROUP BY document_name
        ORDER BY document_name
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return [{'document': doc, 'chunks': count} for doc, count in results]


@app.list_tools()
async def list_tools() -> list[Tool]:
    """Lista las herramientas disponibles en el servidor MCP"""
    return [
        Tool(
            name="search_documents",
            description="Busca información relevante en documentos PDF indexados usando búsqueda semántica. "
                       "Devuelve los fragmentos de texto más similares a la consulta junto con el nombre del documento fuente.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "La pregunta o consulta a buscar en los documentos"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Número máximo de resultados a devolver (default: 5)",
                        "default": 5
                    },
                    "threshold": {
                        "type": "number",
                        "description": "Umbral de similitud mínima (0-1, default: 0.3)",
                        "default": 0.3
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="list_documents",
            description="Lista todos los documentos PDF que han sido indexados en la base de datos vectorial. "
                       "Muestra el nombre de cada documento y el número de fragmentos (chunks) almacenados.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Ejecuta las herramientas del servidor MCP"""
    
    if name == "search_documents":
        query = arguments.get("query")
        top_k = arguments.get("top_k", 5)
        threshold = arguments.get("threshold", 0.3)
        
        if not query:
            return [TextContent(
                type="text",
                text="Error: Se requiere el parámetro 'query'"
            )]
        
        try:
            results = search_documents(query, top_k, threshold)
            
            if not results:
                response = "No se encontraron documentos relevantes para la consulta."
            else:
                response = f"Se encontraron {len(results)} resultados relevantes:\n\n"
                for idx, result in enumerate(results, 1):
                    response += f"--- Resultado {idx} (Similitud: {result['similarity']:.2%}) ---\n"
                    response += f"Documento: {result['document']}\n"
                    response += f"Contenido: {result['text']}\n\n"
            
            return [TextContent(type="text", text=response)]
            
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error al buscar documentos: {str(e)}"
            )]
    
    elif name == "list_documents":
        try:
            documents = list_documents()
            
            if not documents:
                response = "No hay documentos indexados en la base de datos."
            else:
                response = f"Documentos indexados ({len(documents)}):\n\n"
                for doc in documents:
                    response += f"• {doc['document']} ({doc['chunks']} fragmentos)\n"
            
            return [TextContent(type="text", text=response)]
            
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error al listar documentos: {str(e)}"
            )]
    
    else:
        return [TextContent(
            type="text",
            text=f"Herramienta desconocida: {name}"
        )]


async def main():
    """Ejecuta el servidor MCP"""
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
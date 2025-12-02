Para instalar en Claude:
1. Descargar e instalar Claude Desktop desde https://claude.ai/desktop
2. Abrir Claude Desktop e iniciar sesión con su cuenta de Claude.
3. Configurar Claude Desktop para que escuche en el puerto 11435:
   - Ir a "Settings" (Configuración).
   - En "Desarrollador"
   - Presionar "Editar configuracion"
   - En la sección "mcpServers" agregar: 

```json
"document-search": {
    "command": "/Users/informatica/.pyenv/shims/python",
    "args": [
    "/Users/informatica/desarrollo/git/UPSE/charla_mcp/03-mcp-server/mcp-server.py"
    ]
}
```

**Ejemplos de prompts:**

- ¿Qué documentos están disponibles en la base de datos?
- Necesito información sobre evaluación automatizada de competencias linguisticas. ¿Puedes buscar en los documentos y darme un resumen detallado?
- Dame una lista de los documentos más relevantes en el ámbito de la evaluación automatizada de competencias linguisticas dentro de la base de datos.


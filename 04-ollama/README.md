**Instalación de Ollama con Docker**

Ejecute el siguiente comando para instalar Ollama con Docker:

```bash
docker run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama
``` 

**Instalacion de un modelo**

Ejecute el siguiente comando para instalar el modelo deepseek-r1:1.5b:

```bash
docker exec ollama ollama serve --model deepseek-r1:1.5b
docker exec -it ollama ollama run deepseek-r1:1.5b
```


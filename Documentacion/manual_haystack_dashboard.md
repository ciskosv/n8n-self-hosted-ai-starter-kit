
# 🧠 Manual de Plataforma de Conocimiento con Haystack + Qdrant + Ollama

Este sistema combina múltiples herramientas locales de IA para crear una **plataforma privada y auto-gestionada** de conocimiento.

---

## 🔧 Tecnologías Utilizadas

| Herramienta        | Función                          |
|--------------------|----------------------------------|
| n8n                | Orquestación y automatización    |
| Haystack           | Motor RAG (Q&A con contexto)     |
| Qdrant             | Vector DB para documentos        |
| Ollama + Llama3.2  | LLM local para responder         |
| Whisper            | Voz → texto                      |
| Coqui TTS (opcional) | Texto → voz                    |
| Tesseract OCR (opcional) | Imagen → texto            |

---

## 🖥️ Endpoints disponibles

### 📥 `/upload`
Sube e indexa documentos con metadatos.
- Campos: `file`, `cliente`, `tipo_documento`, `producto`

### 🔁 `/replace`
Borra documento por nombre + metadatos, y lo reemplaza por uno nuevo.

### 🧹 `/delete`
Elimina documentos por filtros (`name`, `cliente`, etc.)

### 📊 `/status`
Retorna cuántos documentos hay según filtros.

### 💡 `/query`
Consulta al asistente y obtiene respuesta con contexto desde documentos relevantes.

### 🌐 `/dashboard`
Interfaz web que permite:
- Ver totales de documentos
- Subir, reemplazar o eliminar documentos
- Hacer preguntas directamente al asistente

---

## 📁 Estructura de Metadatos

Cada documento incluye campos como:

```json
{
  "name": "licencia.pdf",
  "cliente": "empresa_x",
  "tipo_documento": "manual",
  "producto": "agente"
}
```

---

## 📈 Dashboard Web

Accede desde: `http://localhost:8000/dashboard`

### Funcionalidades:
- Visualizar documentos por cliente, tipo y producto
- Subir y reemplazar documentos
- Eliminar documentos por nombre
- Consultar al asistente con respuesta en tiempo real

---

## 🚀 Futuras Mejoras Sugeridas

- Soporte para múltiples usuarios con autenticación
- Integración con Coqui TTS para respuesta hablada
- Resumen de documentos largos
- Exportación de logs y respuestas

---

## 🧩 Requisitos Mínimos

- Python 3.9+
- FastAPI
- Docker con Qdrant + Ollama
- Haystack 1.22

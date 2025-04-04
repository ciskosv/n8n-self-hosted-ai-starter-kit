from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import JSONResponse, HTMLResponse
import os
from qdrant_haystack import QdrantDocumentStore
from haystack import Pipeline, Document
from haystack.components.preprocessors import DocumentCleaner, DocumentSplitter
from haystack.components.embedders import SentenceTransformersTextEmbedder
from haystack.components.generators import OpenAIGenerator
from haystack.components.builders import PromptBuilder

#from haystack.components.converters import DocxToDocument
from haystack.components.converters import (
    TextFileToDocument,      # 🔄 Cambio de TextFileToDocument
    #PDFToDocument,       # 🔄 Cambio de PyPDFToDocument  
    MarkdownToDocument   # 🔄 Cambio de MarkdownFileToDocument
)

from fastapi_response_standard import success_response
from fastapi_response_standard import (
    CatchAllMiddleware,
    success_response,
    error_response
)
from fastapi_response_standard.common_exception_handlers import (
    not_found_handler,
    validation_error_handler
)

app = FastAPI()
app.add_middleware(CatchAllMiddleware)

docs_dir = "./docs"
os.makedirs(docs_dir, exist_ok=True)


def index_document(filepath, filename, meta):
    # 1. Configurar el convertidor según la extensión del archivo
    ext = os.path.splitext(filename)[1].lower()
    converters = {
       # ".pdf": PDFToTextConverter(),
        ".txt": TextConverter(),
        ".md": MarkdownConverter(),
      #  ".docx": DocxToTextConverter()
    }

    if ext not in converters:
        raise ValueError(f"Formato {ext} no soportado")

    # 2. Convertir el documento
    converter = converters[ext]
    conversion_result = converter.run(file_path=filepath)
    documents = conversion_result["documents"]
    
    # Añadir metadatos al documento
    for doc in documents:
        doc.meta.update(meta)

    # 3. Preprocesamiento (limpieza y división)
    cleaner = DocumentCleaner(
        remove_empty_lines=True,
        remove_extra_whitespaces=True
    )
    splitter = DocumentSplitter(
        split_by="word",
        split_length=200,
        split_overlap=20,
        split_respect_sentence_boundary=True
    )
    
    # Ejecutar el pipeline de preprocesamiento
    cleaned_docs = cleaner.run(documents=documents)["documents"]
    processed_docs = splitter.run(documents=cleaned_docs)["documents"]

    # 4. Generar embeddings y almacenar
    document_store = QdrantDocumentStore(
        host="qdrant",
        port=6333,
        embedding_dim=384,
        recreate_index=False
    )
    
    embedder = SentenceTransformersDocumentEmbedder(
        model="sentence-transformers/all-MiniLM-L6-v2"
    )
    
    # Generar embeddings
    docs_with_embeddings = embedder.run(processed_docs)["documents"]
    
    # Almacenar documentos
    document_store.write_documents(docs_with_embeddings)

    return len(docs_with_embeddings)



@app.post("/upload")
async def upload_file(file: UploadFile = File(...), cliente: str = "", tipo_documento: str = "", producto: str = ""):
    filename = file.filename
    filepath = os.path.join(docs_dir, filename)

    with open(filepath, "wb") as f:
        f.write(await file.read())

    meta = {
        "name": filename,
        "cliente": cliente,
        "tipo_documento": tipo_documento,
        "producto": producto
    }

    try:
        num_fragmentos = index_document(filepath, filename, meta)
        return {
            "filename": filename,
            "status": "indexed",
            "documentos_indexados": num_fragmentos,
            "meta": meta
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})



@app.post("/query")
async def query_knowledge(request: Request):
    data = await request.json()
    question = data.get("query")
    
    # 1. Configuración
    document_store = QdrantDocumentStore(host="qdrant", port=6333, embedding_dim=384)
    text_embedder = SentenceTransformersTextEmbedder(
        model="sentence-transformers/all-MiniLM-L6-v2"
    )
    retriever = document_store.as_retriever(top_k=3)
    
    # 2. Pipeline
    prompt_template = """
    Basado en los siguientes documentos, responde la pregunta:
    {documents}
    Pregunta: {query}
    """
    
    prompt_builder = PromptBuilder(template=prompt_template)
    llm = OpenAIGenerator(api_base_url="http://ollama:11434/api", model="llama3")
    
    pipeline = Pipeline()
    pipeline.add_component("text_embedder", text_embedder)
    pipeline.add_component("retriever", retriever)
    pipeline.add_component("prompt_builder", prompt_builder)
    pipeline.add_component("llm", llm)
    
    pipeline.connect("text_embedder.embedding", "retriever.query_embedding")
    pipeline.connect("retriever.documents", "prompt_builder.documents")
    pipeline.connect("prompt_builder.prompt", "llm.prompt")
    
    # 3. Ejecución
    result = pipeline.run({
        "text_embedder": {"text": question},
        "prompt_builder": {"query": question}
    })
    
    # 4. Formatear respuesta
    return {
        "respuesta": result["llm"]["replies"][0],
        "contexto_usado": [doc.meta for doc in result["retriever"]["documents"]]
    }

@app.post("/delete")
async def delete_documents(request: Request):
    data = await request.json()
    filtros = data.get("filtros", {})

    if not filtros:
        return JSONResponse(status_code=400, content={"error": "Faltan filtros para borrar"})

    try:
        document_store = QdrantDocumentStore(host="qdrant", port=6333, embedding_dim=384)
        
        # Contar documentos antes de borrarlos
        total_before = document_store.get_document_count(filters=filtros)

        # Borrar documentos
        document_store.delete_documents(filters=filtros)

        return {
            "status": "ok",
            "filtros_usados": filtros,
            "documentos_eliminados": total_before
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

    
@app.post("/replace")
async def replace_document(
    file: UploadFile = File(...),
    cliente: str = "",
    tipo_documento: str = "",
    producto: str = ""
):
    filename = file.filename
    filepath = os.path.join(docs_dir, filename)

    # Construir filtros
    filtros = {"name": [filename]}
    if cliente:
        filtros["cliente"] = [cliente]
    if tipo_documento:
        filtros["tipo_documento"] = [tipo_documento]
    if producto:
        filtros["producto"] = [producto]

    try:
        # 1. Borrar documento(s) existentes
        document_store = QdrantDocumentStore(host="qdrant", port=6333, embedding_dim=384)
        document_store.delete_documents(filters=filtros)

        # 2. Guardar archivo
        with open(filepath, "wb") as f:
            f.write(await file.read())

        # 3. Indexar de nuevo
        meta = {
            "name": filename,
            "cliente": cliente,
            "tipo_documento": tipo_documento,
            "producto": producto
        }
        num_fragmentos = index_document(filepath, filename, meta)

        return {
            "status": "reemplazado",
            "archivo": filename,
            "filtros_usados": filtros,
            "documentos_indexados": num_fragmentos
        }


    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    
    
@app.post("/status")
async def get_status(request: Request):
    data = await request.json()
    filtros = data.get("filtros", {})  # Puede venir vacío

    try:
        document_store = QdrantDocumentStore(host="qdrant", port=6333, embedding_dim=384)
        total = document_store.get_document_count(filters=filtros)

        return {
            "status": "ok",
            "filtros_usados": filtros,
            "documentos_encontrados": total
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    
@app.get("/dashboard", response_class=HTMLResponse)
async def show_dashboard():
    html = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Dashboard Haystack</title>
        <style>
            body { font-family: sans-serif; padding: 2em; background: #f9f9f9; }
            h1 { color: #333; }
            .card { background: white; padding: 1em; margin: 1em 0; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
            .label { font-weight: bold; }
            input, select { margin-top: 0.5em; padding: 0.5em; width: 100%; max-width: 400px; }
            button { margin-top: 1em; padding: 0.7em 1.5em; font-weight: bold; }
        </style>
    </head>
    <body>
        <h1>📊 Dashboard de Documentos (Qdrant)</h1>

        <div class="card" id="total">
            <span class="label">📦 Total de documentos:</span> <span id="total_docs">Cargando...</span>
        </div>

        <div class="card">
            <span class="label">🧑‍💼 Documentos por cliente:</span>
            <ul id="por_cliente"></ul>
        </div>

        <div class="card">
            <span class="label">📄 Documentos por tipo:</span>
            <ul id="por_tipo"></ul>
        </div>

        <div class="card">
            <span class="label">🧠 Documentos por producto:</span>
            <ul id="por_producto"></ul>
        </div>

        <div class="card">
            <h2>📤 Subir documento</h2>
            <form id="uploadForm">
                <label>Archivo: <input type="file" name="file" required /></label><br>
                <label>Cliente: <input type="text" name="cliente" /></label><br>
                <label>Tipo de documento: <input type="text" name="tipo_documento" /></label><br>
                <label>Producto: <input type="text" name="producto" /></label><br>
                <button type="submit">Subir e indexar</button>
                <p id="uploadStatus"></p>
            </form>
        </div>

        <div class="card">
            <h2>🔁 Reemplazar documento</h2>
            <form id="replaceForm">
                <label>Archivo (mismo nombre): <input type="file" name="file" required /></label><br>
                <label>Cliente: <input type="text" name="cliente" /></label><br>
                <label>Tipo de documento: <input type="text" name="tipo_documento" /></label><br>
                <label>Producto: <input type="text" name="producto" /></label><br>
                <button type="submit">Reemplazar</button>
                <p id="replaceStatus"></p>
            </form>
        </div>

        <div class="card">
            <h2>🧨 Eliminar documento</h2>
            <form id="deleteForm">
                <label>Nombre exacto del archivo: <input type="text" name="name" required /></label><br>
                <label>Cliente: <input type="text" name="cliente" /></label><br>
                <button type="submit">Eliminar</button>
                <p id="deleteStatus"></p>
            </form>
        </div>

        <script>
            async function fetchCount(filters) {
                const res = await fetch("/status", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({ filtros: filters })
                });
                const json = await res.json();
                return json.documentos_encontrados || 0;
            }

            async function cargarDashboard() {
                document.getElementById("total_docs").innerText = await fetchCount({});

                const clientes = ["acme", "empresa_x", "empresa_y"];
                const tipos = ["manual", "factura", "soporte"];
                const productos = ["agente", "n8n", "infraestructura"];

                const porCliente = document.getElementById("por_cliente");
                const porTipo = document.getElementById("por_tipo");
                const porProducto = document.getElementById("por_producto");

                porCliente.innerHTML = "";
                porTipo.innerHTML = "";
                porProducto.innerHTML = "";

                for (const c of clientes) {
                    const count = await fetchCount({ cliente: [c] });
                    porCliente.innerHTML += `<li>${c}: ${count}</li>`;
                }

                for (const t of tipos) {
                    const count = await fetchCount({ tipo_documento: [t] });
                    porTipo.innerHTML += `<li>${t}: ${count}</li>`;
                }

                for (const p of productos) {
                    const count = await fetchCount({ producto: [p] });
                    porProducto.innerHTML += `<li>${p}: ${count}</li>`;
                }
            }

            cargarDashboard();

            document.getElementById("uploadForm").addEventListener("submit", async (e) => {
                e.preventDefault();
                const form = e.target;
                const formData = new FormData(form);
                const statusEl = document.getElementById("uploadStatus");
                statusEl.innerText = "Subiendo...";

                try {
                    const res = await fetch("/upload", { method: "POST", body: formData });
                    const json = await res.json();
                    if (json.status === "indexed") {
                        statusEl.innerText = `✅ Se indexaron ${json.documentos_indexados} fragmentos.`;
                        cargarDashboard();
                    } else {
                        statusEl.innerText = "⚠️ Error al subir.";
                    }
                } catch {
                    statusEl.innerText = "❌ Error inesperado.";
                }
            });

            document.getElementById("replaceForm").addEventListener("submit", async (e) => {
                e.preventDefault();
                const form = e.target;
                const formData = new FormData(form);
                const statusEl = document.getElementById("replaceStatus");
                statusEl.innerText = "Reemplazando...";

                try {
                    const res = await fetch("/replace", { method: "POST", body: formData });
                    const json = await res.json();
                    if (json.status === "reemplazado") {
                        statusEl.innerText = `🔁 Reemplazado con ${json.documentos_indexados} fragmentos nuevos.`;
                        cargarDashboard();
                    } else {
                        statusEl.innerText = "⚠️ Error al reemplazar.";
                    }
                } catch {
                    statusEl.innerText = "❌ Error inesperado.";
                }
            });

            document.getElementById("deleteForm").addEventListener("submit", async (e) => {
                e.preventDefault();
                const form = e.target;
                const statusEl = document.getElementById("deleteStatus");
                statusEl.innerText = "Eliminando...";

                const name = form.name.value.trim();
                const cliente = form.cliente.value.trim();
                const filtros = { name: [name] };
                if (cliente) filtros.cliente = [cliente];

                try {
                    const res = await fetch("/delete", {
                        method: "POST",
                        headers: {"Content-Type": "application/json"},
                        body: JSON.stringify({ filtros })
                    });
                    const json = await res.json();
                    if (json.status === "ok") {
                        statusEl.innerText = `🗑️ Se eliminaron ${json.documentos_eliminados} fragmentos.`;
                        cargarDashboard();
                    } else {
                        statusEl.innerText = "⚠️ No se pudo eliminar.";
                    }
                } catch {
                    statusEl.innerText = "❌ Error inesperado.";
                }
            });
        
                <div class="card">
            <h2>🔍 Hacer pregunta al asistente</h2>
            <form id="queryForm">
                <label>Pregunta: <input type="text" name="query" required /></label><br>
                <label>Cliente (opcional): <input type="text" name="cliente" /></label><br>
                <button type="submit">Consultar</button>
            </form>
            <div id="respuesta_llm" style="margin-top:1em; white-space:pre-wrap;"></div>
        </div>

        document.getElementById("queryForm").addEventListener("submit", async (e) => {
            e.preventDefault();
            const form = e.target;
            const query = form.query.value.trim();
            const cliente = form.cliente.value.trim();
            const respuestaEl = document.getElementById("respuesta_llm");
            respuestaEl.innerText = "Consultando...";

            const body = { query };
            if (cliente) body.filtros = { cliente: [cliente] };

            try {
                const res = await fetch("/query", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify(body)
                });
                const json = await res.json();

                if (json.respuesta) {
                    let texto = `🤖 Respuesta:\n${json.respuesta}\n\n📚 Contexto:\n`;
                    json.contexto_usado.forEach((c, i) => {
                        texto += `\n${i + 1}. ${c.documento} (score: ${c.score.toFixed(2)}):\n"${c.texto.slice(0, 300)}..."\n`;
                    });
                    respuestaEl.innerText = texto;
                } else {
                    respuestaEl.innerText = "⚠️ No se recibió respuesta.";
                }
            } catch (err) {
                console.error(err);
                respuestaEl.innerText = "❌ Error al consultar.";
            }
        });


        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

@app.get("/health")
async def health_check():
    return {"status": "ok"}






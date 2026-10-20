import io
import threading

import ollama
import pandas as pd
from flask import Flask, jsonify, render_template, request

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import FAISS

CHAT_MODEL = "mistral:latest"
EMBEDDING_MODEL = "nomic-embed-text"
MAX_UPLOAD_MB = 50
PREVIEW_ROWS = 100
MAX_INDEX_ROWS = 5000      # raise if you want to index bigger files (slower)
EMBED_BATCH = 64

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024
STATE = {"db": None, "filename": None, "columns": [], "rows": 0}
LOCK = threading.Lock()
embedding = OllamaEmbeddings(model=EMBEDDING_MODEL)
splitter = RecursiveCharacterTextSplitter(chunk_size=500,chunk_overlap=100,)

def ollama_ready():
    try:
        ollama.list()
        return True
    except Exception:
        return False
def read_csv_bytes(raw: bytes) -> pd.DataFrame:
    last_err = None
    for enc in ("utf-8-sig", "latin-1"):
        try:
            return pd.read_csv(
                io.BytesIO(raw),
                dtype=str,
                keep_default_na=False,
                encoding=enc,
                sep=None,           
                engine="python",
            )
        except Exception as err:
            last_err = err
    raise ValueError(f"Could not read CSV: {last_err}")


def build_documents(df: pd.DataFrame):
    """One document per CSV row, formatted as 'column: value' lines."""
    docs = []
    for i, row in enumerate(df.head(MAX_INDEX_ROWS).itertuples(index=False), start=1):
        text = "\n".join(f"{col}: {val}" for col, val in zip(df.columns, row))
        docs.append(Document(page_content=text, metadata={"row": i}))
    return splitter.split_documents(docs)


def build_index(chunks):
    """Embed in batches so large files don't hit Ollama in one huge call."""
    db = None
    for i in range(0, len(chunks), EMBED_BATCH):
        batch = chunks[i:i + EMBED_BATCH]
        if db is None:
            db = FAISS.from_documents(batch, embedding)
        else:
            db.add_documents(batch)
    return db
@app.route("/")
def index():
    return render_template("index.html")
@app.route("/health")
def health():
    return jsonify({
        "ollama_ready": ollama_ready(),
        "chat_model": CHAT_MODEL,
        "embedding_model": EMBEDDING_MODEL,
    })
@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify({"success": False, "error": "No file received."}), 400
    if not file.filename.lower().endswith(".csv"):
        return jsonify({"success": False, "error": "Please upload a CSV file."}), 400
    try:
        df = read_csv_bytes(file.read())
    except Exception as err:
        return jsonify({"success": False, "error": str(err)}), 400
    if df.empty or len(df.columns) == 0:
        return jsonify({"success": False, "error": "The CSV file is empty."}), 400
    df.columns = [str(c).strip() for c in df.columns]
    columns = list(df.columns)
    result = {
        "success": True,
        "filename": file.filename,
        "rows": int(len(df)),
        "column_count": len(columns),
        "columns": columns,
        "preview": {"rows": df.head(PREVIEW_ROWS).astype(str).values.tolist()},
        "index_ready": False,
        "embedding_error": None,
    }
    with LOCK:
        STATE.update(db=None, filename=file.filename, columns=columns, rows=len(df))
    try:
        chunks = build_documents(df)
        db = build_index(chunks)
        with LOCK:
            STATE["db"] = db
        result["index_ready"] = True
    except Exception as err:
        result["embedding_error"] = (
            f"Semantic indexing failed: {err}. "
            f"Make sure Ollama is running and '{EMBEDDING_MODEL}' is pulled."
        )
    return jsonify(result)
@app.route("/query", methods=["POST"])
def query():
    data = request.get_json(silent=True) or {}
    question = str(data.get("question") or data.get("query") or "").strip()
    top_k = int(data.get("top_k") or 4)
    if not question:
        return jsonify({"error": "Please enter a question."}), 400
    with LOCK:
        db = STATE["db"]
        columns = STATE["columns"]
        filename = STATE["filename"]
        total_rows = STATE["rows"]
    if db is None:
        return jsonify({"error": "No semantic index available. Upload a CSV first."}), 400
    try:
        results = db.similarity_search_with_score(question, k=top_k)
    except Exception as err:
        return jsonify({"error": f"Retrieval failed: {err}"}), 500
    context = "\n\n".join(doc.page_content for doc, _ in results)
    prompt = f"""
Answer the question using ONLY the context below.
If the answer is not in the context, say you could not find it in the data.
Dataset: {filename} ({total_rows} rows)
Columns: {", ".join(columns)}
Context (matching CSV records):{context}
Question:{question}
Answer:"""
    try:
        response = ollama.chat(
            model=CHAT_MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
        answer = response["message"]["content"]
    except Exception as err:
        return jsonify({"error": f"Ollama chat failed: {err}"}), 500

    sources = [
        {
            "label": f"Row {doc.metadata.get('row', '?')}",
            "score": f"{1 / (1 + float(dist)):.3f}",
            "text": doc.page_content,
        }
        for doc, dist in results
    ]
    return jsonify({"answer": answer, "sources": sources})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
"""
rag_engine.py
台灣美食 RAG 核心引擎
使用 sentence-transformers (免費本地模型) 做 embedding
使用 FAISS 做向量檢索
使用 Google Gemini API 做生成
"""

import os
import re
import pickle
from pathlib import Path
from typing import Optional

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
import google.generativeai as genai


# ── 設定 ───
DATA_PATH   = Path(__file__).parent / "data" / "taiwan_food.txt"
INDEX_PATH  = Path(__file__).parent / "data" / "faiss.index"
CHUNKS_PATH = Path(__file__).parent / "data" / "chunks.pkl"

EMBED_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
TOP_K       = 3
CHUNK_SIZE  = 300


# ── 文字切分 ────
def load_and_chunk(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    sections = re.split(r"\n(?=# )", text.strip())
    chunks = []
    for sec in sections:
        lines = sec.strip().splitlines()
        if not lines:
            continue
        title = lines[0].lstrip("# ").strip()
        content = " ".join(lines[1:]).strip()
        if len(content) <= CHUNK_SIZE:
            chunks.append({"title": title, "text": f"{title}：{content}"})
        else:
            words = list(content)
            for i in range(0, len(words), CHUNK_SIZE):
                snippet = "".join(words[i:i + CHUNK_SIZE])
                chunks.append({"title": title, "text": f"{title}：{snippet}"})
    return chunks


# ── 向量索引建立 ────
def build_index(chunks: list[dict], model: SentenceTransformer) -> faiss.Index:
    texts = [c["text"] for c in chunks]
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
    embeddings = embeddings.astype("float32")
    faiss.normalize_L2(embeddings)
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)
    return index


# ── RAG 引擎主類別 ────
class TaiwanFoodRAG:
    def __init__(self, api_key: Optional[str] = None):
        print("載入 Embedding 模型（首次需下載，約 400 MB）...")
        self.model = SentenceTransformer(EMBED_MODEL)

        if INDEX_PATH.exists() and CHUNKS_PATH.exists():
            print("載入既有向量索引...")
            self.index  = faiss.read_index(str(INDEX_PATH))
            with open(CHUNKS_PATH, "rb") as f:
                self.chunks = pickle.load(f)
        else:
            print("建立向量索引中...")
            self.chunks = load_and_chunk(DATA_PATH)
            self.index  = build_index(self.chunks, self.model)
            faiss.write_index(self.index, str(INDEX_PATH))
            with open(CHUNKS_PATH, "wb") as f:
                pickle.dump(self.chunks, f)
            print(f"索引建立完成，共 {len(self.chunks)} 個段落")

        # Gemini 客戶端
        key = api_key or os.environ.get("GEMINI_API_KEY", "")
        if key:
            genai.configure(api_key=key)
            self.client = genai.GenerativeModel("gemini-2.5-flash")
        else:
            self.client = None

    def retrieve(self, query: str, top_k: int = TOP_K) -> list[dict]:
        q_vec = self.model.encode([query], convert_to_numpy=True).astype("float32")
        faiss.normalize_L2(q_vec)
        scores, indices = self.index.search(q_vec, top_k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0:
                results.append({**self.chunks[idx], "score": float(score)})

        return results

    def generate(self, query: str, context_chunks: list[dict]) -> str:
        if not self.client:
            return "請提供 Gemini API Key 以啟用 AI 回答功能。"

        context = "\n\n".join(
            f"【{c['title']}】\n{c['text']}" for c in context_chunks
        )

        prompt = (
            "你是一位專精台灣美食的知識助手，熱愛分享台灣飲食文化。\n"
            "請根據下方提供的參考資料回答使用者的問題。\n"
            "回答時請：\n"
            "1. 使用繁體中文\n"
            "2. 語氣親切自然，像在跟朋友介紹美食\n"
            "3. 若問題超出資料範圍，誠實告知\n\n"
            f"參考資料：\n{context}\n\n"
            f"使用者問題：{query}"
        )

        response = self.client.generate_content(prompt)
        return response.text

    def ask(self, query: str) -> dict:
        chunks = self.retrieve(query)
        answer = self.generate(query, chunks)

        return {
            "query": query,
            "answer": answer,
            "sources": chunks
        }
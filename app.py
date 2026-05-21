"""
app.py
台灣美食 RAG 系統 — Streamlit 前端介面
執行方式：streamlit run app.py
"""

import os
import streamlit as st
from rag_engine import TaiwanFoodRAG

# ── 頁面設定 ──────────────────────────────────────────
st.set_page_config(
    page_title="台灣美食知識庫",
    layout="centered",
)

# ── 自訂 CSS ──────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #fffdf8; }
    .stTextInput > div > div > input {
        border-radius: 12px;
        border: 2px solid #f0a500;
        padding: 10px 16px;
        font-size: 16px;
    }
    .answer-box {
        background: #fff8ee;
        border-left: 5px solid #f0a500;
        border-radius: 0 12px 12px 0;
        padding: 16px 20px;
        margin: 12px 0;
        font-size: 15px;
        line-height: 1.7;
    }
    .source-card {
        background: #f7f7f7;
        border-radius: 10px;
        padding: 10px 14px;
        margin: 6px 0;
        font-size: 13px;
        color: #555;
        border: 1px solid #e0e0e0;
    }
    .score-badge {
        display: inline-block;
        background: #f0a500;
        color: white;
        border-radius: 20px;
        padding: 2px 10px;
        font-size: 12px;
        margin-left: 8px;
    }
    h1 { color: #c0392b; }
</style>
""", unsafe_allow_html=True)

# ── 標題 ─────────────────────────────────────────────
st.title("台灣美食知識庫")
st.markdown("**用 RAG 技術帶你探索台灣美食文化！**　問什麼都行，例如：")
st.markdown("`珍珠奶茶是哪裡發明的？` ・ `台南有什麼特色小吃？` ・ `鹽酥雞怎麼做？`")
st.divider()

# ── Sidebar：API Key 設定 ─────────────────────────────
with st.sidebar:
    st.header("⚙️設定")
    api_key_input = st.text_input(
        "Anthropic API Key",
        type="password",
        placeholder="sk-ant-...",
        help="從 https://console.anthropic.com 取得你的 API Key"
    )
    st.markdown("---")
    st.markdown("### 關於此專案")
    st.markdown("""
    這是一個 **RAG（檢索增強生成）** 系統，結合：
    - 🔍 **語義搜尋**（sentence-transformers）
    - **向量資料庫**（FAISS）
    - **AI 生成**（Claude API）
    
    知識庫涵蓋 **15 種台灣經典美食**，包含起源、做法、特色與推薦地點。
    """)
    st.markdown("---")
    st.markdown("### 範例問題")
    example_questions = [
        "牛肉麵有哪兩種派系？",
        "珍珠奶茶是誰發明的？",
        "去台南必吃什麼？",
        "刈包為什麼叫虎咬豬？",
        "什麼是三杯雞？",
        "台灣最受歡迎的宵夜是什麼？",
    ]
    for q in example_questions:
        if st.button(q, key=q, use_container_width=True):
            st.session_state["query_input"] = q

# ── 初始化 RAG 引擎（快取避免重複載入）─────────────────
@st.cache_resource(show_spinner="正在載入 AI 模型，請稍候。")
def load_rag(api_key: str) -> TaiwanFoodRAG:
    return TaiwanFoodRAG(api_key=api_key or None)

rag = load_rag(api_key_input)

# 若 API key 更新，重新建立客戶端
if api_key_input and rag.client is None:
    import anthropic
    rag.client = anthropic.Anthropic(api_key=api_key_input)

# ── 問答介面 ──────────────────────────────────────────
query = st.text_input(
    "🔎 請輸入你的問題",
    value=st.session_state.get("query_input", ""),
    placeholder="例如：小籠包要怎麼吃才正確？",
    key="main_query"
)

# 清除 session state
if "query_input" in st.session_state:
    del st.session_state["query_input"]

col1, col2 = st.columns([1, 5])
with col1:
    search_btn = st.button("🍽️ 查詢", type="primary", use_container_width=True)
with col2:
    only_search = st.checkbox("僅顯示檢索結果（不使用 AI 生成）", value=False)

# ── 執行查詢 ──────────────────────────────────────────
if search_btn and query.strip():
    with st.spinner("正在搜尋知識庫..."):
        chunks = rag.retrieve(query)

    if only_search or not api_key_input:
        st.subheader("相關段落")
        if not api_key_input:
            st.info("提示：在左側輸入 API Key 即可獲得 AI 整合回答！")
        for i, chunk in enumerate(chunks, 1):
            score_pct = int(chunk["score"] * 100)
            st.markdown(f"""
            <div class="source-card">
                <b>#{i} {chunk['title']}</b>
                <span class="score-badge">相似度 {score_pct}%</span>
                <br><br>{chunk['text'][:200]}{'...' if len(chunk['text']) > 200 else ''}
            </div>
            """, unsafe_allow_html=True)
    else:
        with st.spinner("AI 正在整理回答..."):
            answer = rag.generate(query, chunks)

        st.subheader("AI 回答")
        st.markdown(f'<div class="answer-box">{answer}</div>', unsafe_allow_html=True)

        with st.expander("參考來源段落", expanded=False):
            for i, chunk in enumerate(chunks, 1):
                score_pct = int(chunk["score"] * 100)
                st.markdown(f"""
                <div class="source-card">
                    <b>#{i} {chunk['title']}</b>
                    <span class="score-badge">相似度 {score_pct}%</span>
                    <br><br>{chunk['text']}
                </div>
                """, unsafe_allow_html=True)

elif search_btn and not query.strip():
    st.warning("請輸入問題再查詢！")

# ── 歷史紀錄 ───
if "history" not in st.session_state:
    st.session_state.history = []

if search_btn and query.strip():
    st.session_state.history.insert(0, query)
    st.session_state.history = st.session_state.history[:10]  # 只保留最近 10 筆

if st.session_state.history:
    st.divider()
    st.markdown("#### 最近查詢")
    for past_q in st.session_state.history[:5]:
        st.markdown(f"- {past_q}")

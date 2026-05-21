#  台灣美食 RAG 知識庫

用 **RAG（檢索增強生成）** 技術打造的台灣美食問答系統，結合語義搜尋與 AI 生成，帶你深入了解台灣飲食文化！

## 功能

-  **語義搜尋**：不用精確關鍵字，用自然語言問問題
-  **AI 整合回答**：Gemini API 整合參考資料生成自然回覆
-  **本地向量資料庫**
-  **15 種台灣美食**

## 架構

```
使用者問題
    │
    ▼
Sentence-Transformers         ← 將問題轉成向量（本地，免費）
paraphrase-multilingual-MiniLM-L12-v2
    │
    ▼
FAISS 向量索引                ← 找出最相關的 3 段知識（本地，免費）
    │
    ▼
相關段落 + 問題
    │
    ▼
Google Gemini API             ← 生成自然語言回答
(gemini-1.5-flash)
    │
    ▼
使用者看到回答
```

## Quick Start

### 1. 安裝虛擬環境

```bash
# 建議使用虛擬環境
python -m venv venv
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate      # Windows

pip install -r requirements.txt
```

> 首次執行會自動下載 embedding 模型（約 400 MB）

### 2. 取得 Gemini API Key

1. 前往 [https://aistudio.google.com](https://aistudio.google.com)
2. 登入 Google 帳號
3. 點選 **Get API Key** → **Create API Key**
4. 複製金鑰（`AIza...` 開頭）

> 不設定 API Key 也能使用，僅會顯示檢索結果，不生成 AI 回答。

### 3. 設定 API Key

**方法 A：在 Streamlit 介面輸入**（推薦，最簡單）
啟動後在左側 Sidebar 直接貼上即可。

**方法 B：環境變數**
```bash
# macOS/Linux
export GEMINI_API_KEY="AIza..."

# Windows
set GEMINI_API_KEY=AIza...
```

**方法 C：Streamlit Secrets**
```toml
# .streamlit/secrets.toml
GEMINI_API_KEY = "AIza..."
```

### 4. 啟動應用程式

```bash
streamlit run app.py
```

瀏覽器會自動開啟 `http://localhost:8501`

## 📁 專案結構

```
taiwan-food-rag/
├── app.py              # Streamlit 前端介面
├── rag_engine.py       # RAG 核心引擎
├── requirements.txt    # Python 依賴套件
├── README.md
└── data/
    ├── taiwan_food.txt  # 台灣美食知識庫（15 種美食）
    ├── faiss.index      # 向量索引（自動生成）
    └── chunks.pkl       # 分段快取（自動生成）
```

## 知識庫涵蓋美食

| 類別 | 美食 |
|------|------|
| 麵食 | 牛肉麵、擔仔麵 |
| 點心 | 小籠包、刈包、肉圓、蚵仔煎 |
| 炸物 | 鹽酥雞、臭豆腐 |
| 飲料 | 珍珠奶茶 |
| 甜品 | 芒果冰、鳳梨酥 |
| 正餐 | 滷肉飯、三杯雞、鐵板燒 |
| 早餐 | 葱抓餅 |

## 範例問題

- 「珍珠奶茶是誰發明的？」
- 「去台南必吃什麼？」
- 「小籠包要怎麼吃才正確？」
- 「台灣最受歡迎的宵夜是什麼？」
- 「鳳梨酥有什麼文化意義？」

## Vibe Coding Prompts

開發過程中使用的主要 AI prompts：

1. **架構設計**：「幫我設計一個台灣美食 RAG 系統，使用免費的 embedding 模型和 FAISS，搭配 Gemini API，前端用 Streamlit」
2. **知識庫建立**：「幫我生成15種台灣經典美食的詳細介紹，包含起源、做法、特色、推薦地點，每篇約200字」
3. **RAG 引擎**：「實作 RAG 核心：文字切分、向量索引建立、相似度檢索、Gemini API 生成」
4. **Streamlit UI**：「設計美觀的 Streamlit 介面，有側邊欄API設定、範例問題按鈕、來源顯示」
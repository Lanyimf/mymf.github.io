"""
Flask RAG 查詢介面 - 法規向量搜尋
"""

from flask import Flask, request, jsonify, render_template_string
import lancedb
from sentence_transformers import SentenceTransformer
import os

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
LANCE_DIR  = os.path.join(BASE_DIR, "regulations_lancedb")
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"

app   = Flask(__name__)
model = None
tbl   = None

def get_resources():
    global model, tbl
    if model is None:
        model = SentenceTransformer(MODEL_NAME)
    if tbl is None:
        db  = lancedb.connect(LANCE_DIR)
        tbl = db.open_table("regulations")
    return model, tbl

HTML = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>法規 RAG 查詢</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, sans-serif; background: #f5f5f5; color: #333; }
  .container { max-width: 960px; margin: 0 auto; padding: 24px; }
  h1 { font-size: 1.4rem; font-weight: 700; margin-bottom: 4px; }
  .subtitle { color: #666; font-size: 0.85rem; margin-bottom: 20px; }
  .stats { display: flex; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; }
  .stat-chip { background: #fff; border: 1px solid #e5e7eb; border-radius: 8px;
    padding: 6px 14px; font-size: 0.8rem; color: #555; }
  .stat-chip b { color: #2563eb; }
  .search-box { display: flex; gap: 8px; margin-bottom: 12px; }
  input[type=text] { flex: 1; padding: 10px 14px; border: 1px solid #ddd;
    border-radius: 8px; font-size: 1rem; }
  .filters { display: flex; gap: 8px; margin-bottom: 20px; flex-wrap: wrap; align-items: center; }
  select, input[type=number] { padding: 6px 10px; border: 1px solid #ddd;
    border-radius: 6px; font-size: 0.875rem; background: #fff; }
  button { padding: 10px 22px; background: #2563eb; color: #fff;
    border: none; border-radius: 8px; cursor: pointer; font-size: 1rem; font-weight: 500; }
  button:hover { background: #1d4ed8; }
  .badge { display: inline-block; padding: 2px 8px; border-radius: 99px;
    font-size: 0.75rem; font-weight: 600; }
  .badge-law    { background: #dbeafe; color: #1e40af; }
  .badge-eval   { background: #dcfce7; color: #166534; }
  .badge-matrix { background: #fef9c3; color: #854d0e; }
  .card { background: #fff; border-radius: 10px; padding: 16px 20px;
    margin-bottom: 12px; border: 1px solid #e5e7eb; transition: box-shadow .15s; }
  .card:hover { box-shadow: 0 2px 12px rgba(0,0,0,.08); }
  .card-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 6px; gap: 8px; }
  .card-title  { font-weight: 600; font-size: 0.95rem; flex: 1; }
  .card-meta   { font-size: 0.8rem; color: #888; margin-bottom: 8px; }
  .card-content { font-size: 0.875rem; line-height: 1.75; white-space: pre-wrap; color: #444; }
  .score-bar { display: flex; align-items: center; gap: 8px; margin-top: 10px; }
  .score-label { font-size: 0.75rem; color: #9ca3af; }
  .score-fill { height: 4px; border-radius: 2px; background: #2563eb; }
  #results-count { font-size: 0.85rem; color: #666; margin-bottom: 12px; font-weight: 500; }
  .empty { text-align: center; color: #bbb; padding: 48px; font-size: 0.95rem; }
  .filter-label { font-size: 0.8rem; color: #888; }
</style>
</head>
<body>
<div class="container">
  <h1>⚖️ 法規 RAG 查詢介面</h1>
  <p class="subtitle">輸入問題或關鍵字，以向量相似度搜尋 1,721 筆法規條文</p>

  <div class="stats" id="stats">
    <div class="stat-chip">原始法規 PDF <b>1,614</b> 段</div>
    <div class="stat-chip">評估條件 <b>78</b> 筆</div>
    <div class="stat-chip">EE 總表 <b>29</b> 筆</div>
    <div class="stat-chip">涵蓋法規 <b>23</b> 部</div>
  </div>

  <div class="search-box">
    <input type="text" id="query" placeholder="例如：農牧用地申請再生能源饋線需要什麼條件？"
      onkeydown="if(event.key==='Enter')search()">
    <button onclick="search()">搜尋</button>
  </div>

  <div class="filters">
    <span class="filter-label">篩選：</span>
    <select id="source_filter">
      <option value="">所有來源</option>
      <option value="原始法規">原始法規 PDF</option>
      <option value="評估條件">評估條件</option>
      <option value="EE總表">EE 總表</option>
    </select>
    <select id="law_filter">
      <option value="">所有法規</option>
      <option value="農業發展條例">農業發展條例</option>
      <option value="非都市土地使用管制規則">非都市土地使用管制規則</option>
      <option value="申請農業用地作農業設施容許使用審查辦法">農業設施容許使用審查辦法</option>
      <option value="畜牧法">畜牧法</option>
      <option value="畜牧場主要設施設置標準">畜牧場主要設施設置標準</option>
      <option value="農業用地興建農舍辦法">農業用地興建農舍辦法</option>
      <option value="水土保持法">水土保持法</option>
      <option value="土壤及地下水污染整治法">土壤及地下水污染整治法</option>
      <option value="土壤污染監測標準">土壤污染監測標準</option>
      <option value="國土計畫法">國土計畫法</option>
      <option value="區域計畫法">區域計畫法</option>
      <option value="建築法">建築法</option>
      <option value="建築技術規則建築設計施工編">建築技術規則建築設計施工編</option>
      <option value="水污染防治法">水污染防治法</option>
      <option value="農田水利法">農田水利法</option>
      <option value="水利法">水利法</option>
      <option value="山坡地保育利用條例">山坡地保育利用條例</option>
      <option value="廢棄物清理法">廢棄物清理法</option>
      <option value="空氣污染防制法">空氣污染防制法</option>
      <option value="放流水標準">放流水標準</option>
      <option value="消防法">消防法</option>
      <option value="食品安全衛生管理法">食品安全衛生管理法</option>
      <option value="動物傳染病防治條例">動物傳染病防治條例</option>
    </select>
    <select id="eval_filter">
      <option value="">所有評估代號</option>
      <option value="EE-1">EE-1 農作使用</option>
      <option value="EE-2">EE-2 農舍</option>
      <option value="EE-3">EE-3 農作產銷設施</option>
      <option value="EE-4">EE-4 畜牧設施</option>
    </select>
    <input type="number" id="top_k" value="5" min="1" max="20" style="width:60px">
    <span class="filter-label">筆</span>
  </div>

  <div id="results-count"></div>
  <div id="results"></div>
</div>

<script>
const BADGE = { "原始法規":"badge-law", "評估條件":"badge-eval", "EE總表":"badge-matrix" };
const LABEL = { "原始法規":"法規條文", "評估條件":"評估條件", "EE總表":"EE總表" };

async function search() {
  const q  = document.getElementById('query').value.trim();
  if (!q) return;
  const sf = document.getElementById('source_filter').value;
  const lf = document.getElementById('law_filter').value;
  const ef = document.getElementById('eval_filter').value;
  const k  = parseInt(document.getElementById('top_k').value) || 5;

  document.getElementById('results').innerHTML = '<p class="empty">搜尋中⋯</p>';
  document.getElementById('results-count').textContent = '';

  const res  = await fetch('/search', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ query: q, top_k: k, source: sf, law_name: lf, eval_code: ef })
  });
  const data = await res.json();

  if (!data.results || data.results.length === 0) {
    document.getElementById('results').innerHTML = '<p class="empty">找不到相關結果，請換個關鍵字試試</p>';
    return;
  }

  document.getElementById('results-count').textContent =
    `找到 ${data.results.length} 筆相關法規`;

  document.getElementById('results').innerHTML = data.results.map(r => {
    const score = Math.max(0, Math.min(1, 1 - r._distance / 5));
    const pct   = Math.round(score * 100);
    return `
    <div class="card">
      <div class="card-header">
        <span class="card-title">${r.condition}</span>
        <span class="badge ${BADGE[r.source]||'badge-law'}">${LABEL[r.source]||r.source}</span>
      </div>
      <div class="card-meta">
        ${r.law_ref ? '📖 ' + r.law_ref : ''}
        ${r.article_no && r.article_no !== r.law_ref ? ' ｜ ' + r.article_no : ''}
        ${r.eval_code ? ' ｜ 評估代號：' + r.eval_code : ''}
      </div>
      <div class="card-content">${r.content.replace(/</g,'&lt;')}</div>
      <div class="score-bar">
        <span class="score-label">相關度</span>
        <div class="score-fill" style="width:${pct}px;max-width:200px"></div>
        <span class="score-label">${pct}%</span>
      </div>
    </div>`;
  }).join('');
}
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/search", methods=["POST"])
def search():
    data        = request.json
    query       = data.get("query", "")
    top_k       = data.get("top_k", 5)
    src_filter  = data.get("source", "")
    law_filter  = data.get("law_name", "")
    eval_filter = data.get("eval_code", "")

    m, t = get_resources()
    vec  = m.encode(query).tolist()

    results = t.search(vec).limit(top_k * 5).to_list()

    if src_filter:
        results = [r for r in results if r["source"] == src_filter]
    if law_filter:
        results = [r for r in results if law_filter in r.get("law_name", "")]
    if eval_filter:
        results = [r for r in results if r.get("eval_code") == eval_filter]

    return jsonify({"results": results[:top_k]})

@app.route("/all")
def all_records():
    _, t = get_resources()
    import pandas as pd
    df = t.to_pandas().drop(columns=["vector"], errors="ignore")
    return jsonify(df.to_dict(orient="records"))

if __name__ == "__main__":
    print("啟動法規 RAG 查詢介面：http://localhost:8002")
    app.run(port=8002, debug=False)

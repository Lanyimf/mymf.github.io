import { QuartzComponent, QuartzComponentConstructor } from "./types"
// @ts-ignore
import script from "./scripts/landevaljump.inline"

// 不渲染任何 DOM，純粹掛載全域點擊事件，讓場址頁面「評估資料」表格的
// 代號連結能跳轉到用地評估工具並帶上 land/rule 參數。
const LandEvalJumpLink: QuartzComponent = () => null

// 讓「評估資料」table 與「目前符合的場址」卡片視覺一致
const evalTableCss = `
table:has(.le-jump-link) {
  border-collapse: collapse;
  width: 100%;
  border: none;
}

table:has(.le-jump-link) thead tr {
  border-bottom: 2px solid var(--lightgray);
}

table:has(.le-jump-link) thead th {
  padding: 0.5rem 0.75rem;
  font-size: 0.85rem;
  color: var(--gray);
  font-weight: 600;
  text-align: left;
  background: none;
  border: none;
}

table:has(.le-jump-link) tbody tr {
  border-bottom: none;
  margin-bottom: 0.5rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.65rem 0.75rem;
  border-radius: 7px;
  background: var(--light);
  transition: box-shadow 0.15s ease;
}

table:has(.le-jump-link) tbody tr:hover {
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

table:has(.le-jump-link) tbody td {
  border: none;
  padding: 0;
  background: none;
}

table:has(.le-jump-link) tbody td:first-child {
  flex-shrink: 0;
  min-width: 4rem;
}

table:has(.le-jump-link) tbody td:nth-child(2) {
  flex: 1;
  font-size: 1rem;
}

table:has(.le-jump-link) tbody td:last-child {
  flex-shrink: 0;
}

table:has(.le-jump-link) .le-jump-link {
  display: inline-block;
  font-size: 0.82rem;
  font-weight: 700;
  padding: 0.2rem 0.55rem;
  border-radius: 5px;
  background: var(--lightgray);
  color: var(--secondary);
  text-decoration: none;
  letter-spacing: 0.02em;
}

table:has(.le-jump-link) .le-jump-link:hover {
  background: var(--secondary);
  color: var(--light);
}

/* 基礎篩選欄位的 badge 樣式 */
table:has(.le-jump-link) tbody td:last-child {
  font-size: 0.8rem;
  font-weight: 600;
  padding: 0.18rem 0.55rem;
  border-radius: 999px;
  background: #fef3c7;
  color: #92400e;
  white-space: nowrap;
}
`

LandEvalJumpLink.css = evalTableCss
LandEvalJumpLink.afterDOMLoaded = script

export default (() => LandEvalJumpLink) satisfies QuartzComponentConstructor

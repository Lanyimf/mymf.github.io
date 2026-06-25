// @ts-nocheck
interface LandRecord {
  id: string
  name: string | null
  address: string | null
  status: string | null
  type_code: string | null
}

interface RuleMeta {
  eval_code: string
  type_code: string
  requires_clean_site: boolean
}

const POLLUTED_STATUSES = ["公告為控制場址", "公告為整治場址"]

function getBaseDir(): string {
  const script = document.querySelector('script[src$="postscript.js"]') as HTMLScriptElement | null
  if (!script) return "/"
  return script.getAttribute("src")!.replace(/postscript\.js$/, "")
}

document.addEventListener("nav", async () => {
  const root = document.querySelector(".rule-matching-lands") as HTMLElement | null
  if (!root) return

  const evalCode = root.dataset.evalCode
  if (!evalCode) return

  const baseDir = getBaseDir()
  const [lands, rules]: [LandRecord[], RuleMeta[]] = await Promise.all([
    fetch(`${baseDir}static/lands-index.json`).then((r) => r.json()),
    fetch(`${baseDir}static/rules-meta.json`).then((r) => r.json()),
  ])

  const rule = rules.find((r) => r.eval_code === evalCode)
  const countEl = root.querySelector(".rml-count") as HTMLElement
  const listEl = root.querySelector(".rml-list") as HTMLOListElement

  if (!rule || !rule.type_code) {
    countEl.textContent = "此規則缺少使用地類別代碼，無法比對資料庫場址。"
    return
  }

  const matched = lands.filter((l) => {
    if (l.type_code !== rule.type_code) return false
    if (rule.requires_clean_site && l.status && POLLUTED_STATUSES.includes(l.status)) return false
    return true
  })

  countEl.textContent = `共找到 ${matched.length} 筆符合基礎篩選的場址（資料庫總計 342 筆）`

  listEl.innerHTML = ""
  for (const l of matched.slice(0, 100)) {
    const li = document.createElement("li")
    li.className = "rfl-item"
    const a = document.createElement("a")
    a.href = `${baseDir}lands/${l.id}`
    a.className = "internal"
    a.textContent = l.name || l.id
    li.appendChild(a)
    if (l.address) {
      const span = document.createElement("span")
      span.style.marginLeft = "0.5rem"
      span.style.fontSize = "0.82rem"
      span.style.color = "var(--gray)"
      span.textContent = l.address
      li.appendChild(span)
    }
    listEl.appendChild(li)
  }
})

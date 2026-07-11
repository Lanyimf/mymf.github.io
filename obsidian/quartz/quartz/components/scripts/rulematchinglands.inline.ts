// @ts-nocheck
interface LandRecord {
  id: string
  name: string | null
  address: string | null
  status: string | null
  type_code: string | null
  area_m2: number | null
  announced_current_value: number | null
  remediation_stage: string | null // 整治階段 1~4，數字越大越接近完成整治解除列管
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

function computeFinance(land: LandRecord, conditional: boolean): { score: number | null; note: string } {
  if (land.announced_current_value == null || land.area_m2 == null) {
    return { score: null, note: "缺少公告現值資料，無法計算" }
  }
  let score = land.announced_current_value * land.area_m2
  let note = `公告現值 ${land.announced_current_value} 元/m² × 面積 ${land.area_m2} m²`
  if (conditional) {
    score *= 0.8
    note += " ×0.8（列管中風險折減）"
  }
  note += ` ≈ ${Math.round(score).toLocaleString()} 元（僅供相對排序參考，非真實財務預測）`
  return { score, note }
}

document.addEventListener("nav", async () => {
  const root = document.querySelector(".rule-matching-lands") as HTMLElement | null
  if (!root) return

  const evalCode = root.dataset.evalCode
  if (!evalCode) return

  // 將元件移到文章內容第一個 H2 標題之前
  const firstH2 = document.querySelector("article h2")
  if (firstH2 && firstH2.parentElement) {
    firstH2.parentElement.insertBefore(root, firstH2)
  }

  const baseDir = getBaseDir()
  const [lands, rules]: [LandRecord[], RuleMeta[]] = await Promise.all([
    fetch(`${baseDir}static/lands-index.json`).then((r) => r.json()),
    fetch(`${baseDir}static/rules-meta.json`).then((r) => r.json()),
  ])

  const rule = rules.find((r) => r.eval_code === evalCode)
  const listEl = root.querySelector(".rml-list") as HTMLOListElement

  if (!rule || !rule.type_code) return

  let hiddenCount = 0
  const items: { land: LandRecord; conditional: boolean; score: number | null; note: string }[] = []
  for (const l of lands) {
    if (l.type_code !== rule.type_code) {
      hiddenCount++
      continue
    }
    const conditional = !!(rule.requires_clean_site && l.status && POLLUTED_STATUSES.includes(l.status))
    const { score, note } = computeFinance(l, conditional)
    items.push({ land: l, conditional, score, note })
  }

  // 排序：有財務分數時依財務分數高低；都沒有財務分數時，改依整治階段高低排
  // （整治階段越高越接近完成解除列管，比起目前任意順序更有意義）
  items.sort((a, b) => {
    if (a.score != null && b.score != null) return b.score - a.score
    if (a.score != null) return -1
    if (b.score != null) return 1
    const stageA = Number(a.land.remediation_stage ?? 0)
    const stageB = Number(b.land.remediation_stage ?? 0)
    if (stageA !== stageB) return stageB - stageA
    return Number(a.conditional) - Number(b.conditional)
  })

  listEl.innerHTML = ""
  for (const it of items.slice(0, 100)) {
    const l = it.land
    const li = document.createElement("li")
    li.className = it.conditional ? "rml-item rml-conditional" : "rml-item"
    li.dataset.landId = l.id
    li.dataset.ruleEvalCode = evalCode

    const title = document.createElement("div")
    title.className = "rml-item-title rml-item-clickable"

    const badge = document.createElement("span")
    badge.className = it.conditional ? "rml-badge rml-badge-cond" : "rml-badge rml-badge-pass"
    badge.textContent = it.conditional ? "初步符合" : "通過篩選"

    const nameEl = document.createElement("span")
    nameEl.className = "rml-item-name"
    nameEl.textContent = l.name || l.id

    const chevron = document.createElement("span")
    chevron.className = "rml-item-chevron"
    chevron.textContent = "›"

    title.appendChild(badge)
    title.appendChild(nameEl)
    title.appendChild(chevron)
    li.appendChild(title)

    listEl.appendChild(li)
  }
})

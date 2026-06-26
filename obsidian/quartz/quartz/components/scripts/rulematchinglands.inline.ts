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

  countEl.textContent = `共找到 ${items.length} 筆可行場址（資料庫總計 ${lands.length} 筆；另有 ${hiddenCount} 筆使用地類別不符，已隱藏不顯示）`

  listEl.innerHTML = ""
  for (const it of items.slice(0, 100)) {
    const l = it.land
    const li = document.createElement("li")
    li.className = "rml-item"

    const title = document.createElement("div")
    title.className = "rml-item-title"
    const badge = it.conditional ? "🟡 條件式通過" : "🟢 通過基礎篩選"
    const financeLabel = it.score != null ? `財務分數約 ${Math.round(it.score).toLocaleString()} 元` : "缺財務資料"
    title.innerHTML = `<span class="rml-caret">▸</span> ${badge} <a href="${baseDir}lands/${l.id}" class="internal">${l.name || l.id}</a> ｜ ${financeLabel}`
    li.appendChild(title)

    const detail = document.createElement("div")
    detail.className = "rml-item-detail"
    detail.style.display = "none"
    if (l.address) {
      const addrEl = document.createElement("div")
      addrEl.textContent = `地址：${l.address}`
      detail.appendChild(addrEl)
    }
    if (it.conditional) {
      const condEl = document.createElement("div")
      condEl.textContent = `此場址目前列管狀態為「${l.status}」，需待整治完成解除列管後才可正式申請`
      detail.appendChild(condEl)
    }
    const financeEl = document.createElement("div")
    financeEl.textContent = `財務分數試算：${it.note}`
    detail.appendChild(financeEl)
    if (it.score == null && l.remediation_stage) {
      const stageEl = document.createElement("div")
      stageEl.textContent = `缺財務資料時，依整治階段排序：目前整治階段 ${l.remediation_stage}/4（數字越大越接近完成解除列管）`
      detail.appendChild(stageEl)
    }
    li.appendChild(detail)

    title.addEventListener("click", () => {
      const isOpen = detail.style.display !== "none"
      detail.style.display = isOpen ? "none" : "block"
      title.querySelector(".rml-caret")!.textContent = isOpen ? "▸" : "▾"
    })

    listEl.appendChild(li)
  }
})

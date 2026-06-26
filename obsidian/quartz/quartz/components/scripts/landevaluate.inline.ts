// @ts-nocheck

// ---- 型別 ----
interface LandRecord {
  id: string
  name: string | null
  address: string | null
  city: string | null
  area_m2: number | null
  status: string | null
  land_type: string | null
  zoning: string | null
  use_class: string | null
  water_protection: string | null
  lat: number | null
  lon: number | null
  announced_current_value: number | null // 公告現值，元/平方公尺
  district: string | null
  section_name: string | null // 段名（取第一筆地號）
  lot_no: string | null // 地號（取第一筆地號）
}

interface RuleMeta {
  rule_id: string
  eval_code: string
  type_code: string
  type_name: string
  use_item: string
  hard_count: number
  weighted_count: number
  requires_clean_site: boolean
}

interface EvalResult {
  rule: RuleMeta
  hardPassed: boolean | null // null = 無法判定
  conditional: boolean // true = 使用地類別符合，但需待整治完成解除列管後才可正式申請
  weightedScore: number | null // 0-100，null = 無法判定
  financeScore: number | null // 簡化財務分數（公告現值 x 面積），僅供相對排序，非真實財務預測
  financeNote: string
  verified: string[] // 已自動驗證的條件
  pending: string[] // 尚待人工查核的條件
  // computed = 有完整 GIS 圖資佐證；basic = 僅用使用地類別/污染狀態做基礎篩選；no_data = 無法判定
  coverage: "computed" | "basic" | "no_data"
  notes: string[]
}

const POLLUTED_STATUSES = ["公告為控制場址", "公告為整治場址"]

function isPollutedSite(land: LandRecord): boolean {
  return !!land.status && POLLUTED_STATUSES.includes(land.status)
}

function getBaseDir(): string {
  const script = document.querySelector('script[src$="postscript.js"]') as HTMLScriptElement | null
  if (!script) return "/"
  return script.getAttribute("src")!.replace(/postscript\.js$/, "")
}

let landsCache: LandRecord[] | null = null
let rulesMetaCache: RuleMeta[] | null = null
let forestAreasCache: any | null = null

async function loadJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${getBaseDir()}${path}`)
  if (!res.ok) throw new Error(`無法載入 ${path}: ${res.status}`)
  return res.json()
}

async function loadAll() {
  landsCache ||= await loadJSON<LandRecord[]>("static/lands-index.json")
  rulesMetaCache ||= await loadJSON<RuleMeta[]>("static/rules-meta.json")
  forestAreasCache ||= await loadJSON<any>("static/forest-recreation-areas.geojson")
  return { lands: landsCache!, rules: rulesMetaCache!, forestAreas: forestAreasCache! }
}

// ---- 幾何工具：point-in-polygon（ray casting，支援 Polygon / MultiPolygon） ----
function pointInRing(lon: number, lat: number, ring: number[][]): boolean {
  let inside = false
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [xi, yi] = ring[i]
    const [xj, yj] = ring[j]
    const intersect =
      yi > lat !== yj > lat && lon < ((xj - xi) * (lat - yi)) / (yj - yi) + xi
    if (intersect) inside = !inside
  }
  return inside
}

function pointInPolygonFeature(lon: number, lat: number, geometry: any): boolean {
  const polys: number[][][][] =
    geometry.type === "Polygon" ? [geometry.coordinates] : geometry.coordinates
  for (const poly of polys) {
    const [outer, ...holes] = poly
    if (pointInRing(lon, lat, outer)) {
      const inHole = holes.some((h: number[][]) => pointInRing(lon, lat, h))
      if (!inHole) return true
    }
  }
  return false
}

function findForestArea(lon: number, lat: number, geojson: any): any | null {
  for (const feature of geojson.features) {
    if (pointInPolygonFeature(lon, lat, feature.geometry)) return feature
  }
  return null
}

// 簡化財務分數：公告現值（元/m²）x 面積（m²），條件式通過再乘以 0.8 風險折減。
// 這純粹是用我們手上唯二的地價資料做的相對排序指標，沒有納入營收、租金、營造成本等真實財務建模要素，
// 不是真正的財務預測，僅供同一場址內不同用途之間粗略比較優先順序。
function computeFinanceScore(
  land: LandRecord,
  conditional: boolean,
): { financeScore: number | null; financeNote: string } {
  if (land.announced_current_value == null || land.area_m2 == null) {
    return { financeScore: null, financeNote: "缺少公告現值資料，無法計算（僅少數場址已查到地價資料）" }
  }
  let financeScore = land.announced_current_value * land.area_m2
  let note = `公告現值 ${land.announced_current_value} 元/m² × 面積 ${land.area_m2} m²`
  if (conditional) {
    financeScore *= 0.8
    note += " ×0.8（列管中風險折減，經驗法則）"
  }
  note += ` ≈ ${Math.round(financeScore).toLocaleString()} 元（僅供相對排序參考，非真實財務預測）`
  return { financeScore, financeNote: note }
}

// ---- 規則評估邏輯（只有確實有資料佐證的規則才寫判定，其餘回傳 no_data） ----
function evaluateRule(land: LandRecord, rule: RuleMeta, ctx: { forestAreas: any }): EvalResult {
  const notes: string[] = []

  if (land.lat == null || land.lon == null) {
    return {
      rule,
      hardPassed: null,
      conditional: false,
      weightedScore: null,
      financeScore: null,
      financeNote: "",
      verified: [],
      pending: [],
      coverage: "no_data",
      notes: ["此地點缺少座標資料"],
    }
  }

  if (rule.rule_id === "R-064") {
    // EG-5 森林遊樂設施：須位於已劃定森林遊樂區範圍內；面積規模加權
    const match = findForestArea(land.lon, land.lat, ctx.forestAreas)
    const hardPassed = !!match
    notes.push(
      hardPassed
        ? `落在「${match.properties.name}」範圍內（公告面積 ${match.properties.area_ha} 公頃，管理單位：${match.properties.manager}）`
        : "未落在任何已劃定森林遊樂區範圍內（依林業及自然保育署 1151 版圖資）",
    )

    let weightedScore: number | null = null
    if (hardPassed) {
      const areaHa = (land.area_m2 ?? 0) / 10000
      // 簡單評分：以該森林遊樂區公告面積為參考，地點落在範圍內即給滿分；
      // 若日後取得地號實際面積與分區界，可再細分計算。
      weightedScore = 100
      notes.push(`場址面積 ${areaHa.toFixed(2)} 公頃（僅供參考，非該森林遊樂區之實際面積）`)
    }

    const { financeScore, financeNote } = computeFinanceScore(land, false)
    return {
      rule,
      hardPassed,
      conditional: false,
      weightedScore,
      financeScore,
      financeNote,
      verified: hardPassed ? ["落於已劃定森林遊樂區範圍內（GIS 圖資比對）"] : [],
      pending: [],
      coverage: "computed",
      notes,
    }
  }

  // 通用基礎篩選：使用地類別代碼是真正的篩選依據，先比對；
  // 「是否列管」不是用來判定不通過，而是標註此用途是否需待整治完成解除列管後才可正式申請
  // （本網站主軸為褐地開發應用，資料庫內場址目前全數仍在列管中）。
  const polluted = isPollutedSite(land)

  if (!land.type_code) {
    notes.push("此場址缺少使用地類別代碼（type_code），無法比對是否符合本規則的用地類型要求")
    return {
      rule,
      hardPassed: null,
      conditional: false,
      weightedScore: null,
      financeScore: null,
      financeNote: "",
      verified: [],
      pending: [],
      coverage: "no_data",
      notes,
    }
  }

  if (land.type_code !== rule.type_code) {
    notes.push(`此場址使用地類別為「${land.type_code}」，與本規則要求的「${rule.type_code}」不符`)
    return {
      rule,
      hardPassed: false,
      conditional: false,
      weightedScore: null,
      financeScore: null,
      financeNote: "",
      verified: [],
      pending: [],
      coverage: "basic",
      notes,
    }
  }

  const verified = [`使用地類別相符（${rule.type_code}）`]
  const pending: string[] = [
    "區位條件（鄰近設施距離、地質敏感區等）：尚無對應資料，需人工查核",
    "空間條件（場址連通面積、設施配置等）：尚無對應資料，需人工查核",
    "加權指標與其餘硬性門檻：尚無對應資料，需人工查核",
  ]

  let conditional = false
  if (rule.requires_clean_site && polluted) {
    conditional = true
    verified.push(`非列管狀態檢查：尚未通過（目前為「${land.status}」，需整治完成解除列管）`)
    notes.push(
      `使用地類別符合（${rule.type_code}），但本規則硬性要求非列管場址；此場址目前列管狀態為「${land.status}」，需待整治完成解除列管後才可正式申請`,
    )
  } else {
    if (rule.requires_clean_site) verified.push("非列管狀態檢查：已符合（非列管場址要求）")
    notes.push(
      `使用地類別符合（${rule.type_code}），且本用途不要求非列管場址，僅完成基礎篩選；區位、空間條件與加權指標尚未驗證，請勿視為最終結論`,
    )
  }

  const { financeScore, financeNote } = computeFinanceScore(land, conditional)
  return {
    rule,
    hardPassed: true,
    conditional,
    weightedScore: null,
    financeScore,
    financeNote,
    verified,
    pending,
    coverage: "basic",
    notes,
  }
}

// ---- UI ----
document.addEventListener("nav", async () => {
  const root = document.querySelector(".land-evaluate") as HTMLElement | null
  if (!root) return

  const select = root.querySelector("#le-land-select") as HTMLSelectElement
  const keywordInput = root.querySelector("#le-keyword") as HTMLInputElement
  const districtSelect = root.querySelector("#le-district") as HTMLSelectElement
  const sectionInput = root.querySelector("#le-section") as HTMLInputElement
  const lotInput = root.querySelector("#le-lot") as HTMLInputElement
  const runBtn = root.querySelector("#le-run") as HTMLButtonElement
  const summaryEl = root.querySelector(".land-evaluate-summary") as HTMLElement
  const resultsEl = root.querySelector(".land-evaluate-results") as HTMLElement

  const { lands, rules, forestAreas } = await loadAll()

  // 鄉鎮市區下拉選單選項（依資料庫實際出現的值，排序後去重）
  const districts = [...new Set(lands.map((l) => l.district).filter(Boolean))].sort((a, b) =>
    a!.localeCompare(b!),
  )
  for (const d of districts) {
    const opt = document.createElement("option")
    opt.value = d!
    opt.textContent = d!
    districtSelect.appendChild(opt)
  }

  function populateOptions() {
    const ft = keywordInput.value.trim().toLowerCase()
    const districtFt = districtSelect.value
    const sectionFt = sectionInput.value.trim()
    const lotFt = lotInput.value.trim()
    const matched = lands.filter((l) => {
      if (ft && !`${l.name ?? ""} ${l.address ?? ""} ${l.id}`.toLowerCase().includes(ft)) return false
      if (districtFt && l.district !== districtFt) return false
      if (sectionFt && !(l.section_name ?? "").includes(sectionFt)) return false
      if (lotFt && l.lot_no !== lotFt) return false
      return true
    })
    select.innerHTML = ""
    const placeholder = document.createElement("option")
    placeholder.value = ""
    placeholder.textContent = `請選擇地點（符合 ${matched.length} 筆）`
    select.appendChild(placeholder)
    for (const l of matched.slice(0, 100)) {
      const opt = document.createElement("option")
      opt.value = l.id
      opt.textContent = `${l.id} ${l.name ?? ""}（${l.city ?? "未知縣市"}）`
      select.appendChild(opt)
    }
  }

  populateOptions()

  function runEvaluation() {
    const land = lands.find((l) => l.id === select.value)
    if (!land) {
      summaryEl.textContent = "請先選擇一個地點"
      resultsEl.innerHTML = ""
      return
    }

    const results = rules.map((r) => evaluateRule(land, r, { forestAreas }))

    const computedPassed = results.filter((r) => r.coverage === "computed" && r.hardPassed)
    const basicPassed = results.filter((r) => r.coverage === "basic" && r.hardPassed && !r.conditional)
    const conditionalPassed = results.filter((r) => r.hardPassed && r.conditional)
    const failed = results.filter((r) => r.hardPassed === false)
    const noData = results.filter((r) => r.coverage === "no_data")

    summaryEl.innerHTML = ""
    const summaryP = document.createElement("p")
    summaryP.innerHTML = `<strong>${land.name ?? land.id}</strong>（${land.address ?? "地址未知"}）— 共比對 72 條規則：<strong>${computedPassed.length + basicPassed.length} 條通過</strong>、<strong>${conditionalPassed.length} 條條件式通過</strong>（需待整治完成解除列管後才可正式申請）。以下僅列出這兩類可行用途；另有 ${failed.length} 條使用地類別不符、${noData.length} 條因資料不足無法判定，已隱藏不顯示。`
    summaryEl.appendChild(summaryP)

    // 僅保留可行的（通過 / 條件式通過），依財務分數排序（無財務分數的排在後面）
    const visible = results.filter((r) => r.hardPassed === true)
    const sorted = visible.sort((a, b) => {
      if (a.financeScore != null && b.financeScore != null) return b.financeScore - a.financeScore
      if (a.financeScore != null) return -1
      if (b.financeScore != null) return 1
      // 同樣缺財務分數時，高信心符合 > 基礎篩選通過 > 條件式通過
      const rank = (r: EvalResult) => (r.coverage === "computed" ? 0 : r.conditional ? 2 : 1)
      return rank(a) - rank(b)
    })

    resultsEl.innerHTML = ""
    const list = document.createElement("ul")
    list.className = "land-evaluate-list"
    for (const r of sorted) {
      const li = document.createElement("li")
      li.className = r.conditional ? "le-passed-conditional" : r.coverage === "computed" ? "le-passed" : "le-passed-basic"
      li.dataset.ruleCode = r.rule.eval_code

      const title = document.createElement("div")
      title.className = "le-item-title le-item-toggle"
      const badge = r.conditional ? "🟡 條件式通過" : r.coverage === "computed" ? "🟢 符合" : "🟢 基礎篩選通過"
      const financeLabel =
        r.financeScore != null ? `財務分數約 ${Math.round(r.financeScore).toLocaleString()} 元` : "缺財務資料"
      title.innerHTML = `<span class="le-caret">▸</span> ${badge} <strong>${r.rule.rule_id} ${r.rule.eval_code}</strong> ${r.rule.type_name}－${r.rule.use_item}${r.weightedScore != null ? ` ｜ 加權分數 ${r.weightedScore}` : ""} ｜ ${financeLabel}`
      li.appendChild(title)

      const detail = document.createElement("div")
      detail.className = "le-item-detail"
      detail.style.display = "none"

      if (r.notes.length > 0) {
        const notesEl = document.createElement("div")
        notesEl.className = "le-item-notes"
        notesEl.textContent = r.notes.join("；")
        detail.appendChild(notesEl)
      }

      const financeP = document.createElement("div")
      financeP.className = "le-item-finance"
      financeP.textContent = `財務分數試算：${r.financeNote}`
      detail.appendChild(financeP)

      if (r.verified.length > 0) {
        const verifiedTitle = document.createElement("div")
        verifiedTitle.className = "le-detail-subtitle"
        verifiedTitle.textContent = "已自動驗證的條件："
        detail.appendChild(verifiedTitle)
        const verifiedList = document.createElement("ul")
        for (const v of r.verified) {
          const item = document.createElement("li")
          item.textContent = `✅ ${v}`
          verifiedList.appendChild(item)
        }
        detail.appendChild(verifiedList)
      }

      if (r.pending.length > 0) {
        const pendingTitle = document.createElement("div")
        pendingTitle.className = "le-detail-subtitle"
        pendingTitle.textContent = "尚待人工查核的條件："
        detail.appendChild(pendingTitle)
        const pendingList = document.createElement("ul")
        for (const p of r.pending) {
          const item = document.createElement("li")
          item.textContent = `⏳ ${p}`
          pendingList.appendChild(item)
        }
        detail.appendChild(pendingList)
      }

      li.appendChild(detail)

      title.addEventListener("click", () => {
        const isOpen = detail.style.display !== "none"
        detail.style.display = isOpen ? "none" : "block"
        title.querySelector(".le-caret")!.textContent = isOpen ? "▸" : "▾"
      })

      list.appendChild(li)
    }
    resultsEl.appendChild(list)
  }

  const onFilterChange = () => populateOptions()
  keywordInput.addEventListener("input", onFilterChange)
  districtSelect.addEventListener("change", onFilterChange)
  sectionInput.addEventListener("input", onFilterChange)
  lotInput.addEventListener("input", onFilterChange)
  window.addCleanup(() => {
    keywordInput.removeEventListener("input", onFilterChange)
    districtSelect.removeEventListener("change", onFilterChange)
    sectionInput.removeEventListener("input", onFilterChange)
    lotInput.removeEventListener("input", onFilterChange)
  })

  runBtn.addEventListener("click", runEvaluation)
  window.addCleanup(() => runBtn.removeEventListener("click", runEvaluation))

  // 從場址頁面的「評估資料」表格點進來時，網址會帶 ?land=B10502&rule=ED-1，
  // 自動選好地點、跑評估，並展開、捲動到對應的規則項目
  const params = new URLSearchParams(window.location.search)
  const deepLand = params.get("land")
  const deepRule = params.get("rule")
  if (deepLand && lands.some((l) => l.id === deepLand)) {
    select.value = deepLand
    runEvaluation()
    if (deepRule) {
      requestAnimationFrame(() => {
        const targetLi = resultsEl.querySelector(`li[data-rule-code="${deepRule}"]`) as HTMLElement | null
        if (targetLi) {
          const title = targetLi.querySelector(".le-item-toggle") as HTMLElement | null
          const detail = targetLi.querySelector(".le-item-detail") as HTMLElement | null
          if (title && detail) {
            detail.style.display = "block"
            title.querySelector(".le-caret")!.textContent = "▾"
          }
          targetLi.scrollIntoView({ behavior: "smooth", block: "center" })
          targetLi.classList.add("le-deep-link-target")
        }
      })
    }
  }
})

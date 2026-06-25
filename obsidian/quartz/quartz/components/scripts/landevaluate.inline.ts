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
  weightedScore: number | null // 0-100，null = 無法判定
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

// ---- 規則評估邏輯（只有確實有資料佐證的規則才寫判定，其餘回傳 no_data） ----
function evaluateRule(land: LandRecord, rule: RuleMeta, ctx: { forestAreas: any }): EvalResult {
  const notes: string[] = []

  if (land.lat == null || land.lon == null) {
    return { rule, hardPassed: null, weightedScore: null, coverage: "no_data", notes: ["此地點缺少座標資料"] }
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

    return { rule, hardPassed, weightedScore, coverage: "computed", notes }
  }

  // 通用基礎篩選：用場址現有的「污染列管狀態」與「使用地類別代碼」
  // 比對規則的硬性門檻第一關。這只能驗證硬性門檻裡最基本的兩項，
  // 其餘區位／空間條件與加權指標仍未驗證，因此標記為 "basic" 而非 "computed"。
  const polluted = isPollutedSite(land)

  if (rule.requires_clean_site && polluted) {
    notes.push(
      `本規則硬性門檻要求「非污染控制/整治場址」，但此場址目前列管狀態為「${land.status}」，不符合`,
    )
    return { rule, hardPassed: false, weightedScore: null, coverage: "basic", notes }
  }

  if (!land.type_code) {
    notes.push("此場址缺少使用地類別代碼（type_code），無法比對是否符合本規則的用地類型要求")
    return { rule, hardPassed: null, weightedScore: null, coverage: "no_data", notes }
  }

  if (land.type_code !== rule.type_code) {
    notes.push(`此場址使用地類別為「${land.type_code}」，與本規則要求的「${rule.type_code}」不符`)
    return { rule, hardPassed: false, weightedScore: null, coverage: "basic", notes }
  }

  notes.push(
    `使用地類別符合（${rule.type_code}）且非污染列管場址，僅完成基礎篩選；區位、空間條件與加權指標尚未驗證，請勿視為最終結論`,
  )
  return { rule, hardPassed: true, weightedScore: null, coverage: "basic", notes }
}

// ---- UI ----
document.addEventListener("nav", async () => {
  const root = document.querySelector(".land-evaluate") as HTMLElement | null
  if (!root) return

  const select = root.querySelector("#le-land-select") as HTMLSelectElement
  const keywordInput = root.querySelector("#le-keyword") as HTMLInputElement
  const runBtn = root.querySelector("#le-run") as HTMLButtonElement
  const summaryEl = root.querySelector(".land-evaluate-summary") as HTMLElement
  const resultsEl = root.querySelector(".land-evaluate-results") as HTMLElement

  const { lands, rules, forestAreas } = await loadAll()

  function populateOptions(filterText: string) {
    const ft = filterText.trim().toLowerCase()
    const matched = ft
      ? lands.filter((l) => `${l.name ?? ""} ${l.address ?? ""} ${l.id}`.toLowerCase().includes(ft))
      : lands
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

  populateOptions("")

  function runEvaluation() {
    const land = lands.find((l) => l.id === select.value)
    if (!land) {
      summaryEl.textContent = "請先選擇一個地點"
      resultsEl.innerHTML = ""
      return
    }

    const results = rules.map((r) => evaluateRule(land, r, { forestAreas }))

    const computedPassed = results.filter((r) => r.coverage === "computed" && r.hardPassed)
    const basicPassed = results.filter((r) => r.coverage === "basic" && r.hardPassed)
    const failed = results.filter((r) => r.hardPassed === false)
    const noData = results.filter((r) => r.coverage === "no_data")

    summaryEl.innerHTML = ""
    const summaryP = document.createElement("p")
    summaryP.innerHTML = `<strong>${land.name ?? land.id}</strong>（${land.address ?? "地址未知"}）— 共比對 72 條規則：<strong>${computedPassed.length} 條高信心符合</strong>、<strong>${basicPassed.length} 條基礎篩選通過</strong>（使用地類別與污染狀態符合，其餘條件未驗證）、${failed.length} 條不符合、<strong>${noData.length} 條因資料不足無法判定</strong>`
    summaryEl.appendChild(summaryP)

    // 排序：高信心符合 → 基礎篩選通過 → 不符合 → 無法判定
    const sorted = [...results].sort((a, b) => {
      const rank = (r: EvalResult) => {
        if (r.coverage === "computed" && r.hardPassed) return 0
        if (r.coverage === "basic" && r.hardPassed) return 1
        if (r.hardPassed === false) return 2
        return 3
      }
      const ra = rank(a)
      const rb = rank(b)
      if (ra !== rb) return ra - rb
      return (b.weightedScore ?? -1) - (a.weightedScore ?? -1)
    })

    resultsEl.innerHTML = ""
    const list = document.createElement("ul")
    list.className = "land-evaluate-list"
    for (const r of sorted) {
      const li = document.createElement("li")
      li.className =
        r.coverage === "no_data"
          ? "le-no-data"
          : r.hardPassed
            ? r.coverage === "computed"
              ? "le-passed"
              : "le-passed-basic"
            : "le-failed"

      const title = document.createElement("div")
      title.className = "le-item-title"
      const badge =
        r.coverage === "no_data"
          ? "資料不足"
          : r.hardPassed
            ? r.coverage === "computed"
              ? "符合"
              : "基礎篩選通過"
            : "不符合"
      title.innerHTML = `${badge} <strong>${r.rule.rule_id} ${r.rule.eval_code}</strong> ${r.rule.type_name}－${r.rule.use_item}${r.weightedScore != null ? ` ｜ 加權分數 ${r.weightedScore}` : ""}`
      li.appendChild(title)

      if (r.notes.length > 0) {
        const notesEl = document.createElement("div")
        notesEl.className = "le-item-notes"
        notesEl.textContent = r.notes.join("；")
        li.appendChild(notesEl)
      }

      list.appendChild(li)
    }
    resultsEl.appendChild(list)
  }

  keywordInput.addEventListener("input", () => populateOptions(keywordInput.value))
  window.addCleanup(() => keywordInput.removeEventListener("input", () => populateOptions(keywordInput.value)))

  runBtn.addEventListener("click", runEvaluation)
  window.addCleanup(() => runBtn.removeEventListener("click", runEvaluation))
})

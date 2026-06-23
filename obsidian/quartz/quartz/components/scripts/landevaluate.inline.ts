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
}

interface EvalResult {
  rule: RuleMeta
  hardPassed: boolean | null // null = 無法判定
  weightedScore: number | null // 0-100，null = 無法判定
  coverage: "computed" | "no_data"
  notes: string[]
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

  return {
    rule,
    hardPassed: null,
    weightedScore: null,
    coverage: "no_data",
    notes: ["此規則尚無對應 GIS 圖資可自動判定，需人工查核或等待資料擴充"],
  }
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

    const computed = results.filter((r) => r.coverage === "computed")
    const passed = computed.filter((r) => r.hardPassed)
    const noData = results.filter((r) => r.coverage === "no_data")

    summaryEl.innerHTML = ""
    const summaryP = document.createElement("p")
    summaryP.innerHTML = `<strong>${land.name ?? land.id}</strong>（${land.address ?? "地址未知"}）— 共比對 72 條規則：<strong>${computed.length} 條可自動判定</strong>（${passed.length} 條通過硬性門檻），<strong>${noData.length} 條因資料不足無法判定</strong>`
    summaryEl.appendChild(summaryP)

    // 排序：可判定且通過的（依分數高低）→ 可判定但未通過 → 無法判定
    const sorted = [...results].sort((a, b) => {
      const rank = (r: EvalResult) =>
        r.coverage === "computed" ? (r.hardPassed ? 0 : 1) : 2
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
            ? "le-passed"
            : "le-failed"

      const title = document.createElement("div")
      title.className = "le-item-title"
      const badge =
        r.coverage === "no_data" ? "⚪ 資料不足" : r.hardPassed ? "🟢 符合" : "🔴 不符合"
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

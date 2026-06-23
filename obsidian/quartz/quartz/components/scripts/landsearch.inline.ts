// @ts-nocheck
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

function getBaseDir(): string {
  const script = document.querySelector('script[src$="postscript.js"]') as HTMLScriptElement | null
  if (!script) return "/"
  return script.getAttribute("src")!.replace(/postscript\.js$/, "")
}

let landsCache: LandRecord[] | null = null

async function loadLands(): Promise<LandRecord[]> {
  if (landsCache) return landsCache
  const res = await fetch(`${getBaseDir()}static/lands-index.json`)
  landsCache = await res.json()
  return landsCache!
}

document.addEventListener("nav", async () => {
  const root = document.querySelector(".land-search") as HTMLElement | null
  if (!root) return

  const citySel = root.querySelector("#ls-city") as HTMLSelectElement
  const useClassSel = root.querySelector("#ls-use-class") as HTMLSelectElement
  const statusSel = root.querySelector("#ls-status") as HTMLSelectElement
  const areaMinInput = root.querySelector("#ls-area-min") as HTMLInputElement
  const keywordInput = root.querySelector("#ls-keyword") as HTMLInputElement
  const resetBtn = root.querySelector("#ls-reset") as HTMLButtonElement
  const countEl = root.querySelector(".land-search-count") as HTMLElement
  const resultsEl = root.querySelector(".land-search-results") as HTMLElement

  const baseDir = getBaseDir()
  const lands = await loadLands()

  function uniqueSorted(values: (string | null)[]): string[] {
    return [...new Set(values.filter((v): v is string => !!v))].sort((a, b) =>
      a.localeCompare(b, "zh-Hant"),
    )
  }

  function populateSelect(sel: HTMLSelectElement, values: string[]) {
    for (const v of values) {
      const opt = document.createElement("option")
      opt.value = v
      opt.textContent = v
      sel.appendChild(opt)
    }
  }

  populateSelect(citySel, uniqueSorted(lands.map((l) => l.city)))
  populateSelect(useClassSel, uniqueSorted(lands.map((l) => l.use_class)))
  populateSelect(statusSel, uniqueSorted(lands.map((l) => l.status)))

  function render() {
    const city = citySel.value
    const useClass = useClassSel.value
    const status = statusSel.value
    const areaMin = parseFloat(areaMinInput.value)
    const keyword = keywordInput.value.trim().toLowerCase()

    const filtered = lands.filter((l) => {
      if (city && l.city !== city) return false
      if (useClass && l.use_class !== useClass) return false
      if (status && l.status !== status) return false
      if (!Number.isNaN(areaMin) && (l.area_m2 ?? 0) < areaMin) return false
      if (keyword) {
        const haystack = `${l.name ?? ""} ${l.address ?? ""} ${l.id}`.toLowerCase()
        if (!haystack.includes(keyword)) return false
      }
      return true
    })

    countEl.textContent = `共找到 ${filtered.length} 筆（資料庫總計 ${lands.length} 筆）`

    resultsEl.innerHTML = ""
    const list = document.createElement("ul")
    list.className = "land-search-list"
    for (const l of filtered.slice(0, 200)) {
      const li = document.createElement("li")
      const a = document.createElement("a")
      a.href = `${baseDir}lands/${l.id}`
      a.className = "internal"
      a.textContent = `${l.id} ${l.name ?? ""}`
      li.appendChild(a)

      const meta = document.createElement("div")
      meta.className = "land-search-meta"
      const parts = [
        l.address,
        l.use_class,
        l.zoning,
        l.area_m2 ? `${l.area_m2.toLocaleString()} m²` : null,
        l.status,
      ].filter(Boolean)
      meta.textContent = parts.join(" ｜ ")
      li.appendChild(meta)

      list.appendChild(li)
    }
    resultsEl.appendChild(list)

    if (filtered.length > 200) {
      const note = document.createElement("p")
      note.className = "land-search-truncate-note"
      note.textContent = `結果過多，僅顯示前 200 筆，請加入更多篩選條件縮小範圍。`
      resultsEl.appendChild(note)
    }
  }

  function reset() {
    citySel.value = ""
    useClassSel.value = ""
    statusSel.value = ""
    areaMinInput.value = ""
    keywordInput.value = ""
    render()
  }

  const handlers: [HTMLElement, string, EventListener][] = [
    [citySel, "change", render],
    [useClassSel, "change", render],
    [statusSel, "change", render],
    [areaMinInput, "input", render],
    [keywordInput, "input", render],
    [resetBtn, "click", reset],
  ]
  for (const [el, ev, fn] of handlers) {
    el.addEventListener(ev, fn)
    window.addCleanup(() => el.removeEventListener(ev, fn))
  }

  render()
})

// @ts-nocheck
interface LandRecord {
  id: string
  name: string | null
  address: string | null
  city: string | null
  district: string | null
  site_category: string | null
  authority: string | null
}

function getBaseDir(): string {
  const script = document.querySelector('script[src$="postscript.js"]') as HTMLScriptElement | null
  if (!script) return "/"
  return script.getAttribute("src")!.replace(/postscript\.js$/, "")
}

// 容錯：「台」「臺」是同一個字的兩種寫法（台北＝臺北、台中＝臺中等），
// 統一轉成「臺」再比對，讓使用者打「台北」也能搜到「臺北市」
function normalizeText(s: string): string {
  return s.replace(/台/g, "臺")
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

  const keywordInput = root.querySelector("#ls-keyword") as HTMLInputElement
  const citySel = root.querySelector("#ls-city") as HTMLSelectElement
  const countEl = root.querySelector(".land-search-count") as HTMLElement
  const listEl = root.querySelector(".land-search-list") as HTMLOListElement

  const baseDir = getBaseDir()
  const lands = await loadLands()

  const cities = [...new Set(lands.map((l) => l.city).filter((c): c is string => !!c))].sort(
    (a, b) => a.localeCompare(b, "zh-Hant"),
  )
  for (const c of cities) {
    const opt = document.createElement("option")
    opt.value = c
    opt.textContent = c
    citySel.appendChild(opt)
  }

  function render() {
    const city = citySel.value
    const keyword = normalizeText(keywordInput.value.trim().toLowerCase())

    const filtered = lands.filter((l) => {
      if (city && l.city !== city) return false
      if (keyword) {
        const haystack = normalizeText(
          `${l.name ?? ""} ${l.address ?? ""} ${l.id} ${l.district ?? ""} ${l.site_category ?? ""} ${l.authority ?? ""}`.toLowerCase(),
        )
        if (!haystack.includes(keyword)) return false
      }
      return true
    })

    countEl.textContent = `共找到 ${filtered.length} 筆（資料庫總計 ${lands.length} 筆）`

    listEl.innerHTML = ""
    for (const l of filtered.slice(0, 200)) {
      const li = document.createElement("li")
      li.className = "land-search-item"
      const a = document.createElement("a")
      a.href = `${baseDir}lands/${l.id}`
      a.className = "internal"
      a.textContent = l.name || l.id
      li.appendChild(a)

      if (l.address) {
        const addr = document.createElement("span")
        addr.className = "land-search-addr"
        addr.textContent = l.address
        li.appendChild(addr)
      }

      listEl.appendChild(li)
    }

    if (filtered.length > 200) {
      const note = document.createElement("li")
      note.className = "land-search-truncate-note"
      note.textContent = "結果過多，僅顯示前 200 筆，請輸入更多關鍵字縮小範圍。"
      listEl.appendChild(note)
    }
  }

  keywordInput.addEventListener("input", render)
  citySel.addEventListener("change", render)
  window.addCleanup(() => {
    keywordInput.removeEventListener("input", render)
    citySel.removeEventListener("change", render)
  })

  render()
})

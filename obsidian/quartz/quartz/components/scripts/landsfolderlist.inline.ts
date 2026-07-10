// @ts-nocheck
interface LandRecord {
  id: string
  name: string | null
  address: string | null
  city: string | null
  area_m2: number | null
  status: string | null
  type_code: string | null
  announced_current_value: number | null
}

// 清理含地號的名稱，例如「臺中市大里區振坤段0001-0000地號」→「臺中市大里區（含振坤段）」
function formatDisplayName(name: string | null): string {
  if (!name) return ""
  // 若名稱含有「地號」，表示是地籍描述而非公司名
  if (!name.includes("地號")) return name
  const m = name.match(/^(.+?[市縣]?.+?[區鄉鎮市])(.+段)/)
  if (m) return `${m[1]}（含${m[2]}）`
  // fallback：移除地號後面的數字部分
  return name.replace(/段[\d\-○零一二三四五六七八九十百千]+.*地號.*$/, "段")
}

function completenessScore(l: LandRecord): number {
  let s = 0
  if (l.type_code) s += 2
  if (l.announced_current_value) s += 1
  return s
}

function getBaseDir(): string {
  const script = document.querySelector('script[src$="postscript.js"]') as HTMLScriptElement | null
  if (!script) return "/"
  return script.getAttribute("src")!.replace(/postscript\.js$/, "")
}

document.addEventListener("nav", async () => {
  const root = document.querySelector(".lands-folder-list") as HTMLElement | null
  if (!root) return

  const citySel = root.querySelector("#lfl-city") as HTMLSelectElement
  const countEl = root.querySelector(".lfl-count") as HTMLElement
  const listEl = root.querySelector(".lfl-list") as HTMLOListElement

  const baseDir = getBaseDir()
  const res = await fetch(`${baseDir}static/lands-index.json`)
  const lands: LandRecord[] = await res.json()

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
    const filtered = (city ? lands.filter((l) => l.city === city) : [...lands])
      .sort((a, b) => completenessScore(b) - completenessScore(a))

    countEl.textContent = `此資料夾下有 ${filtered.length} 條筆記。`

    listEl.innerHTML = ""
    for (const l of filtered) {
      const li = document.createElement("li")
      li.className = "lfl-item"
      const a = document.createElement("a")
      a.href = `${baseDir}lands/${l.id}`
      a.className = "internal"
      a.textContent = formatDisplayName(l.name) || l.id
      li.appendChild(a)
      listEl.appendChild(li)
    }
  }

  citySel.addEventListener("change", render)
  window.addCleanup(() => citySel.removeEventListener("change", render))

  render()
})

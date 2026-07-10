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
      a.textContent = l.name || l.id
      li.appendChild(a)
      listEl.appendChild(li)
    }
  }

  citySel.addEventListener("change", render)
  window.addCleanup(() => citySel.removeEventListener("change", render))

  render()
})

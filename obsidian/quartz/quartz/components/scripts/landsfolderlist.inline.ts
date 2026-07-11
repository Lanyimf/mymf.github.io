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

interface RuleMeta {
  type_code: string
}

function normalizeText(s: string): string {
  return s.replace(/台/g, "臺").toLowerCase()
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

  const keywordInput = root.querySelector("#lfl-keyword") as HTMLInputElement
  const citySel = root.querySelector("#lfl-city") as HTMLSelectElement
  const countEl = root.querySelector(".lfl-count") as HTMLElement
  const listEl = root.querySelector(".lfl-list") as HTMLOListElement

  const baseDir = getBaseDir()
  const [lands, rules]: [LandRecord[], RuleMeta[]] = await Promise.all([
    fetch(`${baseDir}static/lands-index.json`).then((r) => r.json()),
    fetch(`${baseDir}static/rules-meta.json`).then((r) => r.json()),
  ])
  const coveredTypeCodes = new Set(rules.map((r) => r.type_code))

  const cities = [...new Set(lands.map((l) => l.city).filter((c): c is string => !!c))].sort(
    (a, b) => a.localeCompare(b, "zh-Hant"),
  )
  for (const c of cities) {
    const opt = document.createElement("option")
    opt.value = c
    opt.textContent = c
    citySel.appendChild(opt)
  }

  function makeItem(l: LandRecord) {
    const li = document.createElement("li")
    li.className = "lfl-item"
    const a = document.createElement("a")
    a.href = `${baseDir}lands/${l.id}`
    a.className = "internal"
    a.textContent = l.name || l.id
    li.appendChild(a)
    return li
  }

  function makeSectionHeader(title: string, count: number, tag: string) {
    const header = document.createElement("li")
    header.className = "lfl-section-header"
    header.innerHTML = `<span class="lfl-section-title">${title}</span><span class="lfl-section-tag ${tag}">${count} 筆</span>`
    return header
  }

  function render() {
    const city = citySel.value
    const kw = normalizeText(keywordInput.value.trim())

    let filtered = city ? lands.filter((l) => l.city === city) : [...lands]
    if (kw) {
      filtered = filtered.filter((l) =>
        normalizeText(`${l.name ?? ""} ${l.address ?? ""} ${l.id}`).includes(kw),
      )
    }

    const canEval = filtered.filter((l) => !!l.type_code && coveredTypeCodes.has(l.type_code))
      .sort((a, b) => completenessScore(b) - completenessScore(a))
    const noEval = filtered.filter((l) => !l.type_code || !coveredTypeCodes.has(l.type_code))
      .sort((a, b) => (a.name ?? a.id).localeCompare(b.name ?? b.id, "zh-Hant"))

    countEl.textContent = `共 ${filtered.length} 筆場址${kw ? `（關鍵字：${keywordInput.value.trim()}）` : ""}`

    listEl.innerHTML = ""

    if (canEval.length) {
      listEl.appendChild(makeSectionHeader("可進行用地評估", canEval.length, "lfl-tag-eval"))
      for (const l of canEval) listEl.appendChild(makeItem(l))
    }

    if (noEval.length) {
      listEl.appendChild(makeSectionHeader("使用地類別待補齊（暫無法評估）", noEval.length, "lfl-tag-noeval"))
      for (const l of noEval) listEl.appendChild(makeItem(l))
    }
  }

  citySel.addEventListener("change", render)
  keywordInput.addEventListener("input", render)
  window.addCleanup(() => {
    citySel.removeEventListener("change", render)
    keywordInput.removeEventListener("input", render)
  })

  render()
})

// @ts-nocheck
function getBaseDir(): string {
  const script = document.querySelector('script[src$="postscript.js"]') as HTMLScriptElement | null
  if (!script) return "/"
  return script.getAttribute("src")!.replace(/postscript\.js$/, "")
}

function handleClick(e: MouseEvent) {
  const target = (e.target as HTMLElement).closest(".le-jump-link") as HTMLElement | null
  if (!target) return
  e.preventDefault()
  const land = target.dataset.leLand
  const rule = target.dataset.leRule
  if (!land || !rule) return
  window.location.href = `${getBaseDir()}用地評估?land=${encodeURIComponent(land)}&rule=${encodeURIComponent(rule)}`
}

// 將「評估資料」table 轉為與「目前符合的場址」相同的卡片列表
function convertEvalTable() {
  const tables = document.querySelectorAll("table:has(.le-jump-link)")
  tables.forEach((table) => {
    const rows = table.querySelectorAll("tbody tr")
    if (!rows.length) return

    const list = document.createElement("ol")
    list.className = "rml-list eval-card-list"

    rows.forEach((row) => {
      const cells = row.querySelectorAll("td")
      if (cells.length < 3) return

      const codeLink = cells[0].querySelector(".le-jump-link") as HTMLElement | null
      const useName = cells[1].textContent?.trim() ?? ""
      const status = cells[2].textContent?.trim() ?? ""
      const isConditional = status.includes("初步符合")

      const li = document.createElement("li")
      li.className = isConditional ? "rml-item rml-conditional" : "rml-item"

      const row2 = document.createElement("div")
      row2.className = "rml-item-title"
      row2.style.cursor = "default"

      const badge = document.createElement("span")
      badge.className = isConditional ? "rml-badge rml-badge-cond" : "rml-badge rml-badge-pass"
      badge.textContent = isConditional ? "初步符合" : "通過篩選"

      const codeBadge = document.createElement("span")
      codeBadge.className = "eval-code-badge"
      if (codeLink) {
        const btn = document.createElement("a")
        btn.href = "#"
        btn.className = "le-jump-link eval-code-link"
        btn.dataset.leLand = codeLink.dataset.leLand
        btn.dataset.leRule = codeLink.dataset.leRule
        btn.textContent = codeLink.textContent ?? ""
        codeBadge.appendChild(btn)
      }

      const nameEl = document.createElement("span")
      nameEl.className = "rml-item-name"
      nameEl.textContent = useName

      row2.appendChild(badge)
      row2.appendChild(codeBadge)
      row2.appendChild(nameEl)
      li.appendChild(row2)
      list.appendChild(li)
    })

    table.replaceWith(list)
  })
}

document.addEventListener("nav", () => {
  convertEvalTable()
  document.addEventListener("click", handleClick)
  window.addCleanup(() => document.removeEventListener("click", handleClick))
})

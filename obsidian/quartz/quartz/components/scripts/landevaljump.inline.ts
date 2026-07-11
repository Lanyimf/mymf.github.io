// @ts-nocheck
interface LandRecord {
  id: string
  name: string | null
  address: string | null
  status: string | null
  type_code: string | null
  area_m2: number | null
  announced_current_value: number | null
  remediation_stage: string | null
  lat: number | null
  lon: number | null
  water_protection: string | null
  site_category: string | null
  soil_pollutant: string | null
  groundwater_pollutant: string | null
  accelerated: string | null
}

interface RuleMeta {
  rule_id: string
  eval_code: string
  type_code: string
  type_name: string
  use_item: string
  requires_clean_site: boolean
}

const POLLUTED_STATUSES_LJ = ["公告為控制場址", "公告為整治場址"]

function getBaseDir(): string {
  const script = document.querySelector('script[src$="postscript.js"]') as HTMLScriptElement | null
  if (!script) return "/"
  return script.getAttribute("src")!.replace(/postscript\.js$/, "")
}

let _landsCache: LandRecord[] | null = null
let _rulesCache: RuleMeta[] | null = null

async function loadModalData() {
  if (!_landsCache) {
    const base = getBaseDir()
    const [lands, rules] = await Promise.all([
      fetch(`${base}static/lands-index.json`).then((r) => r.json()),
      fetch(`${base}static/rules-meta.json`).then((r) => r.json()),
    ])
    _landsCache = lands
    _rulesCache = rules
  }
  return { lands: _landsCache!, rules: _rulesCache! }
}

function evalLandRule(land: LandRecord, rule: RuleMeta) {
  if (!land.type_code) {
    return {
      status: "no_data" as const,
      verified: [] as string[],
      pending: [] as string[],
      failReasons: [] as string[],
      finance: { score: null as number | null, note: "缺少使用地類別資料" },
    }
  }

  if (land.type_code !== rule.type_code) {
    return {
      status: "fail" as const,
      verified: [],
      pending: [],
      failReasons: [`使用地類別「${land.type_code}」與本規則要求的「${rule.type_code}」不符`],
      finance: { score: null as number | null, note: "" },
    }
  }

  const polluted = !!land.status && POLLUTED_STATUSES_LJ.includes(land.status)
  const conditional = !!(rule.requires_clean_site && polluted)

  const verified: string[] = [`使用地類別相符（${rule.type_code}）`]
  if (conditional) {
    verified.push(`列管狀態：目前為「${land.status}」，須整治完成解除列管後才可申請`)
  } else if (rule.requires_clean_site) {
    verified.push("非列管狀態：已符合（此規則要求非列管場址）")
  }

  const pending = [
    "區位條件（鄰近設施距離、地質敏感區等）：尚無對應資料，需人工查核",
    "空間條件（場址連通面積、設施配置等）：尚無對應資料，需人工查核",
    "其餘硬性門檻與加權指標：尚無對應資料，需人工查核",
  ]

  let financeScore: number | null = null
  let financeNote = "缺少公告現值資料，無法計算"
  if (land.announced_current_value != null && land.area_m2 != null) {
    financeScore = land.announced_current_value * land.area_m2
    financeNote = `公告現值 ${land.announced_current_value.toLocaleString()} 元/m² × 面積 ${land.area_m2.toLocaleString()} m²`
    if (conditional) {
      financeScore *= 0.8
      financeNote += " ×0.8（列管中風險折減）"
    }
    financeNote += ` ≈ ${Math.round(financeScore).toLocaleString()} 元`
  }

  return {
    status: conditional ? ("conditional" as const) : ("pass" as const),
    verified,
    pending,
    failReasons: [] as string[],
    finance: { score: financeScore, note: financeNote },
  }
}

// ---- Modal ----
function ensureModal() {
  if (document.getElementById("eval-modal-overlay")) return
  const overlay = document.createElement("div")
  overlay.id = "eval-modal-overlay"

  const box = document.createElement("div")
  box.id = "eval-modal"
  overlay.appendChild(box)
  document.body.appendChild(overlay)

  overlay.addEventListener("click", (e) => {
    if (e.target === overlay) closeEvalModal()
  })
}

function closeEvalModal() {
  const overlay = document.getElementById("eval-modal-overlay")
  if (!overlay) return
  overlay.classList.remove("eval-modal-open")
  document.body.classList.remove("eval-modal-body-lock")
}

async function openEvalModal(landId: string, ruleEvalCode: string) {
  ensureModal()
  const overlay = document.getElementById("eval-modal-overlay")!
  const box = document.getElementById("eval-modal")!

  box.innerHTML = `<div class="eval-modal-loading">評估中…</div>`
  overlay.classList.add("eval-modal-open")
  document.body.classList.add("eval-modal-body-lock")

  try {
    const { lands, rules } = await loadModalData()
    const land = lands.find((l) => l.id === landId)
    const rule = rules.find((r) => r.eval_code === ruleEvalCode)

    if (!land || !rule) {
      box.innerHTML = `<div class="eval-modal-loading">找不到對應資料（${landId} / ${ruleEvalCode}）</div>`
      return
    }

    const res = evalLandRule(land, rule)

    const statusLabel = {
      pass: "通過篩選",
      conditional: "初步符合",
      fail: "不符合",
      no_data: "資料不足",
    }[res.status]

    const badgeClass = {
      pass: "rml-badge-pass",
      conditional: "rml-badge-cond",
      fail: "eval-badge-fail",
      no_data: "eval-badge-nodata",
    }[res.status]

    let bodyHtml = ""

    if (res.verified.length) {
      bodyHtml += `
        <div class="eval-modal-section">
          <div class="eval-modal-section-label eval-section-pass">已自動驗證</div>
          <ul class="eval-modal-list">${res.verified.map((v) => `<li>${v}</li>`).join("")}</ul>
        </div>`
    }

    if (res.failReasons.length) {
      bodyHtml += `
        <div class="eval-modal-section">
          <div class="eval-modal-section-label eval-section-fail">不符合原因</div>
          <ul class="eval-modal-list">${res.failReasons.map((f) => `<li>${f}</li>`).join("")}</ul>
        </div>`
    }

    if (res.pending.length && res.status !== "fail") {
      bodyHtml += `
        <div class="eval-modal-section">
          <div class="eval-modal-section-label eval-section-pending">尚待人工查核</div>
          <ul class="eval-modal-list">${res.pending.map((p) => `<li>${p}</li>`).join("")}</ul>
        </div>`
    }

    // ---- 整治資訊 ----
    const stageLabels: Record<string, string> = {
      "1": "第 1 階段：初步評估",
      "2": "第 2 階段：詳細調查",
      "3": "第 3 階段：整治計畫執行中",
      "4": "第 4 階段：驗證/接近解除列管",
    }
    const stageRows: string[] = []
    if (land.remediation_stage) {
      const label = stageLabels[land.remediation_stage] ?? `階段 ${land.remediation_stage}`
      stageRows.push(`<tr><th>整治進度</th><td>${label}</td></tr>`)
    }
    if (land.accelerated === "是") {
      stageRows.push(`<tr><th>加速整治</th><td><span class="eval-tag eval-tag-accel">加速整治中</span>　解除列管時程較一般場址短</td></tr>`)
    }
    if (land.site_category) {
      stageRows.push(`<tr><th>場址類別</th><td>${land.site_category}</td></tr>`)
    }
    if (land.water_protection === "是") {
      stageRows.push(`<tr><th>水源保護區</th><td><span class="eval-tag eval-tag-warn">位於水源保護區內</span>　部分用途有額外限制</td></tr>`)
    } else if (land.water_protection === "否") {
      stageRows.push(`<tr><th>水源保護區</th><td>否</td></tr>`)
    }

    // ---- 污染物 ----
    const pollutRows: string[] = []
    if (land.soil_pollutant) {
      pollutRows.push(`<tr><th>土壤污染物</th><td>${land.soil_pollutant}</td></tr>`)
    }
    if (land.groundwater_pollutant) {
      pollutRows.push(`<tr><th>地下水污染物</th><td>${land.groundwater_pollutant}</td></tr>`)
    }

    if (stageRows.length) {
      bodyHtml += `
        <div class="eval-modal-section">
          <div class="eval-modal-section-label eval-section-site">場址資訊</div>
          <table class="eval-modal-table">${stageRows.join("")}</table>
        </div>`
    }

    if (pollutRows.length) {
      bodyHtml += `
        <div class="eval-modal-section">
          <div class="eval-modal-section-label eval-section-pollut">污染物資訊</div>
          <table class="eval-modal-table">${pollutRows.join("")}</table>
        </div>`
    }

    bodyHtml += `
      <div class="eval-modal-section eval-modal-finance-section">
        <div class="eval-modal-section-label eval-section-finance">財務試算</div>
        <p class="eval-modal-finance-note">${res.finance.note || "無資料"}</p>
        ${res.finance.score != null ? `<p class="eval-modal-finance-score">${Math.round(res.finance.score).toLocaleString()} 元</p>` : ""}
      </div>
      <p class="eval-modal-disclaimer">本評估依使用地類別與污染狀態進行基礎篩選；區位、空間等詳細條件尚未驗證，不代表最終可行性結論。</p>`

    box.innerHTML = `
      <div class="eval-modal-header">
        <div class="eval-modal-title-row">
          <span class="rml-badge ${badgeClass}">${statusLabel}</span>
          <div class="eval-modal-titles">
            <div class="eval-modal-land-name">${land.name || land.id}</div>
            <div class="eval-modal-rule-name">${rule.eval_code}　${rule.use_item}</div>
          </div>
          <button class="eval-modal-close" aria-label="關閉">&times;</button>
        </div>
        ${land.address ? `<div class="eval-modal-addr">${land.address}</div>` : ""}
      </div>
      <div class="eval-modal-body">${bodyHtml}</div>`

    box.querySelector(".eval-modal-close")?.addEventListener("click", closeEvalModal)
  } catch (err) {
    box.innerHTML = `<div class="eval-modal-loading">載入失敗：${err}</div>`
  }
}

// ---- 將「評估資料」table 轉為與「目前符合的場址」相同的卡片列表 ----
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
      if (codeLink) {
        li.dataset.landId = codeLink.dataset.leLand ?? ""
        li.dataset.ruleEvalCode = codeLink.dataset.leRule ?? ""
      }

      const row2 = document.createElement("div")
      row2.className = "rml-item-title rml-item-clickable"

      const badge = document.createElement("span")
      badge.className = isConditional ? "rml-badge rml-badge-cond" : "rml-badge rml-badge-pass"
      badge.textContent = isConditional ? "初步符合" : "通過篩選"

      const codeBadge = document.createElement("span")
      codeBadge.className = "eval-code-badge"
      if (codeLink) {
        const btn = document.createElement("span")
        btn.className = "eval-code-link"
        btn.textContent = codeLink.textContent ?? ""
        codeBadge.appendChild(btn)
      }

      const nameEl = document.createElement("span")
      nameEl.className = "rml-item-name"
      nameEl.textContent = useName

      const chevron = document.createElement("span")
      chevron.className = "rml-item-chevron"
      chevron.textContent = "›"

      row2.appendChild(badge)
      row2.appendChild(codeBadge)
      row2.appendChild(nameEl)
      row2.appendChild(chevron)
      li.appendChild(row2)
      list.appendChild(li)
    })

    table.replaceWith(list)
  })
}

// ---- 統一點擊處理：任何 rml-item 都開啟 modal ----
function handleCardClick(e: MouseEvent) {
  const titleEl = (e.target as HTMLElement).closest(".rml-item-title") as HTMLElement | null
  if (!titleEl) return

  // 只在有 clickable 標記或有 rml-item-chevron 時才接管 (eval-card-list cards)
  // 對 rule-matching-lands 的卡片，也要攔截
  const li = titleEl.closest("li.rml-item") as HTMLElement | null
  if (!li) return

  const landId = li.dataset.landId
  const evalCode = li.dataset.ruleEvalCode
  if (!landId || !evalCode) return

  e.preventDefault()
  e.stopPropagation()
  openEvalModal(landId, evalCode)
}

// ---- ESC 鍵關閉 ----
function handleKeydown(e: KeyboardEvent) {
  if (e.key === "Escape") closeEvalModal()
}

document.addEventListener("nav", () => {
  convertEvalTable()
  ensureModal()
  document.addEventListener("click", handleCardClick)
  document.addEventListener("keydown", handleKeydown)
  window.addCleanup(() => {
    document.removeEventListener("click", handleCardClick)
    document.removeEventListener("keydown", handleKeydown)
  })
})

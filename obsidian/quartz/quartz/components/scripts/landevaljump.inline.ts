// @ts-nocheck
// 場址頁面「評估資料」表格裡的代號連結，因為 Quartz 內部連結解析會把 query string 吃掉，
// 所以改用 data 屬性 + 點擊事件導向，繞過 href 被改寫的問題。
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

document.addEventListener("nav", () => {
  document.addEventListener("click", handleClick)
  window.addCleanup(() => document.removeEventListener("click", handleClick))
})

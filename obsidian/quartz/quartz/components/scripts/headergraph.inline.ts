// @ts-nocheck
// 將 header 上的「關係圖譜」按鈕代理點擊到 Graph 元件內建的
// .global-graph-icon（該按鈕已綁定 Quartz 既有的全螢幕圖譜渲染邏輯，
// 只在被點擊、容器可見時才初始化 D3，避免在 display:none 狀態下量到 0 尺寸）
document.addEventListener("nav", () => {
  const button = document.getElementById("graph-toggle-button")
  if (!button) return

  function onClick() {
    const icon = document.querySelector(".site-header .global-graph-icon") as HTMLElement | null
    icon?.click()
  }

  button.addEventListener("click", onClick)
  window.addCleanup(() => button.removeEventListener("click", onClick))
})

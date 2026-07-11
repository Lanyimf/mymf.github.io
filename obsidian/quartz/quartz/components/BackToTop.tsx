import { QuartzComponent, QuartzComponentConstructor } from "./types"

const BackToTop: QuartzComponent = () => null

const css = `
#back-to-top {
  position: fixed;
  bottom: 1.75rem;
  right: 1.75rem;
  z-index: 1000;
  width: 2.4rem;
  height: 2.4rem;
  border-radius: 50%;
  background: var(--secondary);
  color: var(--light);
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.1rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.18);
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.2s ease, background 0.15s ease;
}
#back-to-top.visible {
  opacity: 1;
  pointer-events: auto;
}
#back-to-top:hover {
  background: var(--tertiary);
}
`

const script = `
(function () {
  function init() {
    let btn = document.getElementById("back-to-top")
    if (!btn) {
      btn = document.createElement("button")
      btn.id = "back-to-top"
      btn.setAttribute("aria-label", "回到頂部")
      btn.innerHTML = "↑"
      document.body.appendChild(btn)
      btn.addEventListener("click", () => window.scrollTo({ top: 0, behavior: "smooth" }))
    }

    const onScroll = () => {
      btn.classList.toggle("visible", window.scrollY > 300)
    }
    window.addEventListener("scroll", onScroll, { passive: true })
    onScroll()
    window.addCleanup(() => window.removeEventListener("scroll", onScroll))
  }

  document.addEventListener("nav", init)
})()
`

BackToTop.css = css
BackToTop.afterDOMLoaded = script

export default (() => BackToTop) satisfies QuartzComponentConstructor

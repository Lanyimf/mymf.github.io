import { QuartzComponent, QuartzComponentConstructor } from "./types"
// @ts-ignore
import script from "./scripts/alllandsmap.inline"

// 這個元件本身不輸出任何畫面，只負責把地圖所需的 CSS／JS 掛進全站資源包；
// 實際顯示用的容器（.all-lands-map-host）直接寫在 content/index.md 裡，
// 這樣地圖才能精確出現在「找地搜尋／用地評估」卡片下方。
const AllLandsMap: QuartzComponent = () => null

AllLandsMap.css = `
.all-lands-map-host {
  width: 100%;
  height: 420px;
  border: 1px solid var(--lightgray);
  border-radius: 8px;
  margin: 1rem 0 1.5rem;
  background: var(--light);
}
`
AllLandsMap.afterDOMLoaded = script

export default (() => AllLandsMap) satisfies QuartzComponentConstructor

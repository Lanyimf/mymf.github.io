import { QuartzComponent, QuartzComponentConstructor } from "./types"
// @ts-ignore
import script from "./scripts/landevaljump.inline"

// 不渲染任何 DOM，純粹掛載全域點擊事件，讓場址頁面「評估資料」表格的
// 代號連結能跳轉到用地評估工具並帶上 land/rule 參數。
const LandEvalJumpLink: QuartzComponent = () => null

LandEvalJumpLink.afterDOMLoaded = script

export default (() => LandEvalJumpLink) satisfies QuartzComponentConstructor

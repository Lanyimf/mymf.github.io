import { QuartzComponent, QuartzComponentConstructor, QuartzComponentProps } from "./types"
import { classNames } from "../util/lang"
// @ts-ignore
import script from "./scripts/landevaluate.inline"
import style from "./styles/landevaluate.scss"

const LandEvaluate: QuartzComponent = ({ displayClass }: QuartzComponentProps) => {
  return (
    <div class={classNames(displayClass, "land-evaluate")}>
      <div class="land-evaluate-controls">
        <div class="land-evaluate-field">
          <label for="le-keyword">搜尋地點</label>
          <input id="le-keyword" type="text" placeholder="輸入名稱、地址或縣市篩選" />
        </div>
        <div class="land-evaluate-field">
          <label for="le-land-select">選擇地點</label>
          <select id="le-land-select"></select>
        </div>
        <button id="le-run" type="button">
          開始評估
        </button>
      </div>
      <div class="land-evaluate-summary"></div>
      <div class="land-evaluate-results"></div>
    </div>
  )
}

LandEvaluate.css = style
LandEvaluate.afterDOMLoaded = script

export default (() => LandEvaluate) satisfies QuartzComponentConstructor

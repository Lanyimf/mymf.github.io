import { QuartzComponent, QuartzComponentConstructor, QuartzComponentProps } from "./types"
import { classNames } from "../util/lang"
// @ts-ignore
import script from "./scripts/landsearch.inline"
import style from "./styles/landsearch.scss"

const LandSearch: QuartzComponent = ({ displayClass }: QuartzComponentProps) => {
  return (
    <div class={classNames(displayClass, "land-search")}>
      <div class="land-search-filters">
        <div class="land-search-field">
          <label for="ls-city">縣市</label>
          <select id="ls-city">
            <option value="">全部縣市</option>
          </select>
        </div>
        <div class="land-search-field">
          <label for="ls-use-class">使用地類別／分區</label>
          <select id="ls-use-class">
            <option value="">全部類別</option>
          </select>
        </div>
        <div class="land-search-field">
          <label for="ls-status">列管狀態</label>
          <select id="ls-status">
            <option value="">全部狀態</option>
          </select>
        </div>
        <div class="land-search-field">
          <label for="ls-area-min">最小面積（m²）</label>
          <input id="ls-area-min" type="number" min="0" placeholder="例如 1000" />
        </div>
        <div class="land-search-field">
          <label for="ls-keyword">關鍵字（地址／名稱）</label>
          <input id="ls-keyword" type="text" placeholder="例如 楠梓、岡山" />
        </div>
        <button id="ls-reset" type="button">
          清除條件
        </button>
      </div>
      <p class="land-search-count"></p>
      <div class="land-search-results"></div>
    </div>
  )
}

LandSearch.css = style
LandSearch.afterDOMLoaded = script

export default (() => LandSearch) satisfies QuartzComponentConstructor

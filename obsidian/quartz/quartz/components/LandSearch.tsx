import { QuartzComponent, QuartzComponentConstructor, QuartzComponentProps } from "./types"
import { classNames } from "../util/lang"
// @ts-ignore
import script from "./scripts/landsearch.inline"
import style from "./styles/landsearch.scss"

const LandSearch: QuartzComponent = ({ displayClass }: QuartzComponentProps) => {
  return (
    <div class={classNames(displayClass, "land-search")}>
      <div class="land-search-bar">
        <input id="ls-keyword" type="text" placeholder="搜尋地址、名稱或關鍵字" />
        <select id="ls-city">
          <option value="">全部縣市</option>
        </select>
      </div>
      <p class="land-search-count"></p>
      <ol class="land-search-list"></ol>
    </div>
  )
}

LandSearch.css = style
LandSearch.afterDOMLoaded = script

export default (() => LandSearch) satisfies QuartzComponentConstructor

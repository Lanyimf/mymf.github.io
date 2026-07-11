import { QuartzComponent, QuartzComponentConstructor, QuartzComponentProps } from "./types"
import { classNames } from "../util/lang"
// @ts-ignore
import script from "./scripts/landsfolderlist.inline"
import style from "./styles/landsfolderlist.scss"

const LandsFolderList: QuartzComponent = ({ displayClass }: QuartzComponentProps) => {
  return (
    <div class={classNames(displayClass, "lands-folder-list")}>
      <div class="lfl-filters">
        <div class="lfl-filter-field">
          <label for="lfl-keyword">關鍵字搜尋</label>
          <input id="lfl-keyword" type="text" placeholder="名稱、地址、縣市（臺/台 通用）" />
        </div>
        <div class="lfl-filter-field">
          <label for="lfl-city">縣市篩選</label>
          <select id="lfl-city">
            <option value="">全部縣市</option>
          </select>
        </div>
      </div>
      <p class="lfl-count"></p>
      <ol class="lfl-list"></ol>
    </div>
  )
}

LandsFolderList.css = style
LandsFolderList.afterDOMLoaded = script

export default (() => LandsFolderList) satisfies QuartzComponentConstructor

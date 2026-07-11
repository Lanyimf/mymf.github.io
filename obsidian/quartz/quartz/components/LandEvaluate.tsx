import { QuartzComponent, QuartzComponentConstructor, QuartzComponentProps } from "./types"
import { classNames } from "../util/lang"
// @ts-ignore
import script from "./scripts/landevaluate.inline"
import style from "./styles/landevaluate.scss"

const LandEvaluate: QuartzComponent = ({ displayClass }: QuartzComponentProps) => {
  return (
    <div class={classNames(displayClass, "land-evaluate")}>
      {/* 模式切換 */}
      <div class="le-tabs">
        <button class="le-tab le-tab-active" data-tab="db">從資料庫查詢</button>
        <button class="le-tab" data-tab="custom">自行輸入土地資料</button>
      </div>

      {/* 模式一：資料庫選擇 */}
      <div class="le-panel" id="le-panel-db">
        <div class="land-evaluate-controls">
          <div class="land-evaluate-field">
            <label for="le-keyword">搜尋地點</label>
            <input id="le-keyword" type="text" placeholder="輸入名稱、地址或縣市篩選" />
          </div>
          <div class="land-evaluate-field">
            <label for="le-land-select">選擇地點</label>
            <select id="le-land-select"></select>
          </div>
          <button id="le-run" class="le-run-btn" type="button">開始評估</button>
        </div>
      </div>

      {/* 模式二：自行輸入 */}
      <div class="le-panel le-panel-hidden" id="le-panel-custom">
        <div class="land-evaluate-controls le-custom-controls">
          <div class="land-evaluate-field le-field-wide">
            <label for="le-custom-address">地址或地號（供顯示用）</label>
            <input id="le-custom-address" type="text" placeholder="例：臺中市大里區仁化路221巷25號" />
          </div>
          <div class="land-evaluate-field">
            <label for="le-custom-type">用地類別</label>
            <select id="le-custom-type">
              <option value="">請選擇</option>
              <option value="EE">EE 農牧用地</option>
              <option value="EB">EB 乙種建築用地</option>
              <option value="ED">ED 丁種建築用地</option>
              <option value="EG">EG 遊憩用地</option>
              <option value="EH">EH 水利用地</option>
              <option value="EN">EN 國土保育用地</option>
              <option value="EP">EP 特定目的事業用地</option>
            </select>
          </div>
          <div class="land-evaluate-field">
            <label for="le-custom-area">面積（m²，可不填）</label>
            <input id="le-custom-area" type="number" min="1" placeholder="例：1200" style="min-width:140px" />
          </div>
          <div class="land-evaluate-field le-field-polluted">
            <label>污染列管狀態</label>
            <label class="le-radio-label">
              <input type="radio" name="le-polluted" value="no" checked /> 非列管場址
            </label>
            <label class="le-radio-label">
              <input type="radio" name="le-polluted" value="yes" /> 列管中（控制或整治場址）
            </label>
          </div>
          <button id="le-run-custom" class="le-run-btn" type="button">開始評估</button>
        </div>
        <p class="le-custom-hint">
          用地類別可查閱地籍謄本或向地政事務所查詢。
        </p>
      </div>

      <div class="land-evaluate-summary"></div>
      <div class="land-evaluate-results"></div>
    </div>
  )
}

LandEvaluate.css = style
LandEvaluate.afterDOMLoaded = script

export default (() => LandEvaluate) satisfies QuartzComponentConstructor

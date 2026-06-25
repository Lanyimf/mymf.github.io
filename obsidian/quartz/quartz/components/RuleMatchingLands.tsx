import { QuartzComponent, QuartzComponentConstructor, QuartzComponentProps } from "./types"
import { classNames } from "../util/lang"
// @ts-ignore
import script from "./scripts/rulematchinglands.inline"
import style from "./styles/rulesfolderlist.scss"

const RuleMatchingLands: QuartzComponent = ({ fileData, displayClass }: QuartzComponentProps) => {
  const evalCode = fileData.frontmatter?.eval_code as string | undefined
  if (!evalCode) return null

  return (
    <div class={classNames(displayClass, "rule-matching-lands")} data-eval-code={evalCode}>
      <h3>目前資料庫中符合基礎篩選的場址</h3>
      <p class="rml-note">
        以下場址的使用地類別與本規則相符，且非污染列管場址，但僅完成基礎篩選——區位、空間條件與加權指標尚未驗證，請勿視為最終結論。
      </p>
      <p class="rml-count"></p>
      <ol class="rml-list rfl-list"></ol>
    </div>
  )
}

const ownCss = `
.rule-matching-lands {
  margin: 1.5rem 0;
  padding-top: 1rem;
  border-top: 1px solid var(--lightgray);
}
.rml-note {
  font-size: 0.82rem;
  color: var(--gray);
  margin: 0.3rem 0 0.6rem;
}
.rml-count {
  font-size: 0.85rem;
  color: var(--gray);
  margin: 0 0 0.5rem;
}
`

function toArray(r: string | string[] | undefined): string[] {
  if (!r) return []
  return Array.isArray(r) ? r : [r]
}

RuleMatchingLands.css = [ownCss, ...toArray(style)]
RuleMatchingLands.afterDOMLoaded = script

export default (() => RuleMatchingLands) satisfies QuartzComponentConstructor

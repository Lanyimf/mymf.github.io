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
      <h3>目前符合的場址</h3>
      <ol class="rml-list"></ol>
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
.rml-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.rml-item {
  padding: 0.6rem 0.8rem;
  border-radius: 5px;
  border-left: 4px solid #2e7d32;
  background: var(--light);
}
.rml-item-title {
  font-size: 0.9rem;
  cursor: pointer;
  user-select: none;
}
.rml-caret {
  display: inline-block;
  width: 1em;
}
.rml-item-detail {
  margin-top: 0.4rem;
  padding-top: 0.4rem;
  border-top: 1px dashed var(--lightgray);
  font-size: 0.8rem;
  color: var(--gray);
}
`

function toArray(r: string | string[] | undefined): string[] {
  if (!r) return []
  return Array.isArray(r) ? r : [r]
}

RuleMatchingLands.css = [ownCss, ...toArray(style)]
RuleMatchingLands.afterDOMLoaded = script

export default (() => RuleMatchingLands) satisfies QuartzComponentConstructor

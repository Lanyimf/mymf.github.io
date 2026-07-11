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
.rml-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}
.rml-item {
  padding: 0.75rem 1rem;
  border-radius: 8px;
  border-left: 4px solid #2e7d32;
  background: var(--light);
  transition: box-shadow 0.15s ease;
}
.rml-item:hover {
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}
.rml-item.rml-conditional {
  border-left-color: #b45309;
}
.rml-item-title {
  font-size: 1rem;
  cursor: pointer;
  user-select: none;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.rml-badge {
  font-size: 0.78rem;
  font-weight: 600;
  padding: 0.15rem 0.5rem;
  border-radius: 999px;
  white-space: nowrap;
  flex-shrink: 0;
}
.rml-badge-pass {
  background: #dcfce7;
  color: #15803d;
}
.rml-badge-cond {
  background: #fef3c7;
  color: #92400e;
}
.rml-item-name {
  font-size: 1rem;
  font-weight: 500;
  flex: 1;
}
`

function toArray(r: string | string[] | undefined): string[] {
  if (!r) return []
  return Array.isArray(r) ? r : [r]
}

RuleMatchingLands.css = [ownCss, ...toArray(style)]
RuleMatchingLands.afterDOMLoaded = script

export default (() => RuleMatchingLands) satisfies QuartzComponentConstructor

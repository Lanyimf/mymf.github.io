import { QuartzComponent, QuartzComponentConstructor, QuartzComponentProps } from "./types"
import { classNames } from "../util/lang"
import { pathToRoot } from "../util/path"
import style from "./styles/rulesfolderlist.scss"
import fs from "fs"
import path from "path"

interface RuleMeta {
  rule_id: string
  eval_code: string
  type_code: string
  type_name: string
  use_item: string
}

function loadRulesMeta(): RuleMeta[] {
  const candidates = [
    path.join(process.cwd(), "quartz/static/rules-meta.json"),
    path.join(process.cwd(), "static/rules-meta.json"),
  ]
  const target = candidates.find((p) => fs.existsSync(p))
  if (!target) throw new Error("rules-meta.json not found")
  return JSON.parse(fs.readFileSync(target, "utf-8"))
}

const RulesCategoryList: QuartzComponent = ({ fileData, displayClass }: QuartzComponentProps) => {
  const baseDir = pathToRoot(fileData.slug!)
  const category = (fileData.frontmatter?.category as string) ?? ""
  const rules = loadRulesMeta().filter((r) => r.type_code === category)

  return (
    <div class={classNames(displayClass, "rules-folder-list")}>
      <p class="rfl-count">此類別下共 {rules.length} 條評估規則。</p>
      <ol class="rfl-list">
        {rules.map((r) => (
          <li class="rfl-item">
            <a href={`${baseDir}/rules/${r.eval_code}`} class="internal">
              {r.eval_code} {r.use_item}
            </a>
          </li>
        ))}
      </ol>
    </div>
  )
}

RulesCategoryList.css = style

export default (() => RulesCategoryList) satisfies QuartzComponentConstructor

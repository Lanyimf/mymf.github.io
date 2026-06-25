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

function getCategories(): { type_code: string; type_name: string }[] {
  const rules = loadRulesMeta()
  const seen = new Map<string, string>()
  for (const r of rules) {
    if (!seen.has(r.type_code)) seen.set(r.type_code, r.type_name)
  }
  return [...seen.entries()].map(([type_code, type_name]) => ({ type_code, type_name }))
}

const RulesFolderList: QuartzComponent = ({ fileData, displayClass }: QuartzComponentProps) => {
  const baseDir = pathToRoot(fileData.slug!)
  const categories = getCategories()

  return (
    <div class={classNames(displayClass, "rules-folder-list")}>
      <p class="rfl-count">此資料夾下共 {categories.length} 個用地類別。</p>
      <ol class="rfl-list">
        {categories.map((c) => (
          <li class="rfl-item">
            <a href={`${baseDir}/rules/${c.type_code}`} class="internal">
              {c.type_code} {c.type_name}
            </a>
          </li>
        ))}
      </ol>
    </div>
  )
}

RulesFolderList.css = style

export default (() => RulesFolderList) satisfies QuartzComponentConstructor

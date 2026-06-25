import { QuartzComponent, QuartzComponentConstructor, QuartzComponentProps } from "./types"
import { classNames } from "../util/lang"
import { resolveRelative } from "../util/path"
import { QuartzPluginData } from "../plugins/vfile"
import style from "./styles/rulesfolderlist.scss"

interface LawsFolderListProps extends QuartzComponentProps {
  pages: QuartzPluginData[]
}

const LawsFolderList: QuartzComponent = ({ fileData, pages, displayClass }: LawsFolderListProps) => {
  const sorted = [...pages].sort((a, b) =>
    (a.frontmatter?.title ?? "").localeCompare(b.frontmatter?.title ?? "", "zh-Hant"),
  )

  return (
    <div class={classNames(displayClass, "rules-folder-list")}>
      <p class="rfl-count">此資料夾下共 {sorted.length} 部法規。</p>
      <ol class="rfl-list">
        {sorted.map((p) => (
          <li class="rfl-item">
            <a href={resolveRelative(fileData.slug!, p.slug!)} class="internal">
              {p.frontmatter?.title}
            </a>
          </li>
        ))}
      </ol>
    </div>
  )
}

LawsFolderList.css = style

export default (() => LawsFolderList) satisfies QuartzComponentConstructor

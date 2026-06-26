import { QuartzComponent, QuartzComponentConstructor, QuartzComponentProps } from "./types"
import { classNames } from "../util/lang"
import { resolveRelative } from "../util/path"
import { QuartzPluginData } from "../plugins/vfile"
import style from "./styles/rulesfolderlist.scss"

interface NumberedPageListProps extends QuartzComponentProps {
  pages: QuartzPluginData[]
}

const NumberedPageList: QuartzComponent = ({
  fileData,
  pages,
  displayClass,
}: NumberedPageListProps) => {
  return (
    <div class={classNames(displayClass, "rules-folder-list")}>
      <ol class="rfl-list">
        {pages.map((p) => (
          <li class="rfl-item">
            <a href={resolveRelative(fileData.slug!, p.slug!)} class="internal">
              {p.frontmatter?.name ?? p.frontmatter?.title}
            </a>
          </li>
        ))}
      </ol>
    </div>
  )
}

NumberedPageList.css = style

export default (() => NumberedPageList) satisfies QuartzComponentConstructor

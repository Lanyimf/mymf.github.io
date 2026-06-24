import { QuartzComponent, QuartzComponentConstructor, QuartzComponentProps } from "./types"
import { classNames } from "../util/lang"
import TableOfContents from "./TableOfContents"

const TocComponent = TableOfContents()

const HorizontalToc: QuartzComponent = (props: QuartzComponentProps) => {
  const { displayClass } = props
  if (!props.fileData.toc) return null
  return (
    <div class={classNames(displayClass, "toc-nav-bar")}>
      <TocComponent {...props} />
    </div>
  )
}

const ownCss = `
.toc-nav-bar {
  margin: 0 0 1.2rem;
  padding-bottom: 0.8rem;
  border-bottom: 1px solid var(--lightgray);
}

.toc-nav-bar .toc-header {
  display: none;
}

.toc-nav-bar .toc {
  flex-direction: row;
  overflow: visible;
}

.toc-nav-bar ul.toc-content {
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin: 0;
  padding: 0;
  max-height: none;
}

.toc-nav-bar ul.toc-content li {
  padding-left: 0 !important;
}

.toc-nav-bar ul.toc-content li a {
  display: inline-block;
  padding: 0.25rem 0.7rem;
  border-radius: 999px;
  background: var(--highlight);
  font-size: 0.8rem;
  opacity: 1 !important;
  text-decoration: none;
  white-space: nowrap;
}

.toc-nav-bar ul.toc-content li a.in-view {
  background: var(--secondary);
  color: var(--light);
}
`

function toArray(r: string | string[] | undefined): string[] {
  if (!r) return []
  return Array.isArray(r) ? r : [r]
}

HorizontalToc.css = [ownCss, ...toArray(TocComponent.css)]
HorizontalToc.beforeDOMLoaded = TocComponent.beforeDOMLoaded
HorizontalToc.afterDOMLoaded = TocComponent.afterDOMLoaded

export default (() => HorizontalToc) satisfies QuartzComponentConstructor

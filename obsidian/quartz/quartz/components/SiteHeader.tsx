import { pathToRoot } from "../util/path"
import { QuartzComponent, QuartzComponentConstructor, QuartzComponentProps } from "./types"
import { classNames } from "../util/lang"
import Search from "./Search"
import Darkmode from "./Darkmode"
import Graph from "./Graph"
// @ts-ignore
import headerGraphScript from "./scripts/headergraph.inline"

interface NavItem {
  label: string
  slug: string
}

const navItems: NavItem[] = [
  { label: "場址資料", slug: "lands" },
  { label: "評估規則", slug: "rules" },
  { label: "法規", slug: "laws" },
  { label: "財務模型", slug: "finance" },
]

const SearchComponent = Search()
const DarkmodeComponent = Darkmode()
const GraphComponent = Graph()

const SiteHeader: QuartzComponent = (props: QuartzComponentProps) => {
  const { fileData, cfg, displayClass } = props
  const title = cfg?.pageTitle ?? "土地開發評估系統"
  const baseDir = pathToRoot(fileData.slug!)

  return (
    <div class={classNames(displayClass, "site-header")}>
      <a href={baseDir} class="site-logo">
        <span class="site-logo-icon">🗺️</span>
        <span class="site-logo-text">{title}</span>
      </a>

      <div class="site-header-search">
        <SearchComponent {...props} />
      </div>

      <nav class="site-header-nav">
        {navItems.map((item) => (
          <a href={`${baseDir}/${item.slug}`} class="site-nav-link">
            {item.label}
          </a>
        ))}
        <button id="graph-toggle-button" type="button" class="site-nav-link site-graph-toggle">
          關係圖譜
        </button>
        <a href={`${baseDir}/找地搜尋`} class="site-nav-cta">
          找地搜尋
        </a>
        <a href={`${baseDir}/用地評估`} class="site-nav-cta">
          用地評估
        </a>
        <span class="site-header-darkmode">
          <DarkmodeComponent {...props} />
        </span>
      </nav>

      <div class="site-graph-host">
        <GraphComponent {...props} />
      </div>
    </div>
  )
}

const ownCss = `
body > header {
  margin: 0;
}

.site-header {
  width: 100%;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  gap: 1.5rem;
  padding: 0.85rem 2.5rem;
  background: var(--light);
  border-bottom: 1px solid var(--lightgray);
  color: var(--dark);
  flex-wrap: wrap;
}

.site-logo {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  text-decoration: none;
  color: var(--dark);
  flex-shrink: 0;
  white-space: nowrap;
}

.site-logo-icon {
  font-size: 1.3rem;
}

.site-logo-text {
  font-size: 1.15rem;
  font-weight: 700;
}

.site-header-search {
  flex: 1 1 auto;
  min-width: 160px;
  max-width: 32rem;
}

.site-header-search .search-button {
  width: 100%;
  border-radius: 999px;
  padding: 0.45rem 1rem;
}

.site-header-nav {
  display: flex;
  align-items: center;
  gap: 1.4rem;
  flex-wrap: wrap;
  margin-left: auto;
}

.site-nav-link {
  color: var(--dark);
  text-decoration: none;
  font-size: 0.92rem;
  font-weight: 600;
  white-space: nowrap;
  background: none;
  border: none;
  cursor: pointer;
  font-family: inherit;
  padding: 0;
}

.site-nav-link:hover {
  color: var(--secondary);
  text-decoration: underline;
}

.site-nav-cta {
  color: var(--light);
  background: var(--secondary);
  font-weight: 600;
  font-size: 0.88rem;
  padding: 0.4rem 0.9rem;
  border-radius: 6px;
  text-decoration: none;
  white-space: nowrap;
  transition: background 0.15s ease;
}

.site-nav-cta:hover {
  background: var(--tertiary);
}

/* 只保留 Graph 元件內建的全螢幕彈窗（.global-graph-outer），
   隱藏小型預覽框本身，header 上只留代理觸發按鈕 */
.site-graph-host {
  position: absolute;
  width: 0;
  height: 0;
  overflow: visible;
}

.site-graph-host .graph > h3,
.site-graph-host .graph-outer {
  display: none;
}

@media all and (max-width: 768px) {
  .site-header {
    padding: 0.75rem 1.2rem;
  }
  .site-header-nav {
    margin-left: 0;
    width: 100%;
    order: 3;
  }
  .site-header-search {
    order: 2;
    flex: 1 1 100%;
  }
}
`

function toArray(r: string | string[] | undefined): string[] {
  if (!r) return []
  return Array.isArray(r) ? r : [r]
}

SiteHeader.css = [
  ownCss,
  ...toArray(SearchComponent.css),
  ...toArray(DarkmodeComponent.css),
  ...toArray(GraphComponent.css),
]
SiteHeader.beforeDOMLoaded = [...toArray(DarkmodeComponent.beforeDOMLoaded)]
SiteHeader.afterDOMLoaded = [
  ...toArray(SearchComponent.afterDOMLoaded),
  ...toArray(GraphComponent.afterDOMLoaded),
  ...toArray(headerGraphScript),
]

export default (() => SiteHeader) satisfies QuartzComponentConstructor

import { PageLayout, SharedLayout } from "./quartz/cfg"
import * as Component from "./quartz/components"

// components shared across all pages
export const sharedPageComponents: SharedLayout = {
  head: Component.Head(),
  header: [Component.SiteHeader()],
  afterBody: [Component.RuleMatchingLands(), Component.LandEvalJumpLink(), Component.Backlinks()],
  footer: Component.Footer({
    links: {
      GitHub: "https://github.com/jackyzha0/quartz",
      "Discord Community": "https://discord.gg/cRFFHYye7t",
    },
  }),
}

// components for pages that display a single page (e.g. a single note)
export const defaultContentPageLayout: PageLayout = {
  beforeBody: [
    Component.ConditionalRender({
      component: Component.Breadcrumbs(),
      condition: (page) => page.fileData.slug !== "index",
    }),
    Component.ConditionalRender({
      component: Component.ArticleTitle(),
      condition: (page) => page.fileData.slug !== "index",
    }),
    Component.ContentMeta(),
    Component.TagList(),
    Component.ConditionalRender({
      component: Component.HorizontalToc(),
      condition: (page) => !page.fileData.slug?.startsWith("lands/"),
    }),
    Component.ConditionalRender({
      component: Component.LandMap(),
      condition: (page) =>
        page.fileData.frontmatter?.lat !== undefined &&
        page.fileData.frontmatter?.lon !== undefined,
    }),
    Component.ConditionalRender({
      component: Component.LandSearch(),
      condition: (page) => page.fileData.frontmatter?.tool === "lands-search",
    }),
    Component.ConditionalRender({
      component: Component.LandEvaluate(),
      condition: (page) => page.fileData.frontmatter?.tool === "land-evaluate",
    }),
    Component.ConditionalRender({
      component: Component.RulesCategoryList(),
      condition: (page) => page.fileData.frontmatter?.tool === "rules-category",
    }),
    Component.ConditionalRender({
      component: Component.AllLandsMap(),
      condition: (page) => page.fileData.slug === "index",
    }),
  ],
  left: [],
  right: [],
}

// components for pages that display lists of pages  (e.g. tags or folders)
export const defaultListPageLayout: PageLayout = {
  beforeBody: [Component.Breadcrumbs(), Component.ArticleTitle(), Component.ContentMeta()],
  left: [],
  right: [],
}

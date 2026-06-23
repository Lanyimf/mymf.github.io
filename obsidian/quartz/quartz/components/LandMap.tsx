import { QuartzComponent, QuartzComponentConstructor, QuartzComponentProps } from "./types"
import { classNames } from "../util/lang"
// @ts-ignore
import script from "./scripts/landmap.inline"
import style from "./styles/landmap.scss"

const LandMap: QuartzComponent = ({ fileData, displayClass }: QuartzComponentProps) => {
  const lat = fileData.frontmatter?.lat
  const lon = fileData.frontmatter?.lon
  if (lat === undefined || lon === undefined) {
    return null
  }

  const latNum = Number(lat)
  const lonNum = Number(lon)
  if (Number.isNaN(latNum) || Number.isNaN(lonNum)) {
    return null
  }

  const openLink = `https://www.openstreetmap.org/?mlat=${latNum}&mlon=${lonNum}#map=17/${latNum}/${lonNum}`

  return (
    <div class={classNames(displayClass, "land-map")}>
      <h3>位置地圖（可疊加地籍圖／正射影像）</h3>
      <div class="land-map-canvas" data-lat={latNum} data-lon={lonNum}></div>
      <p class="land-map-link">
        <a href={openLink} target="_blank" rel="noopener noreferrer">
          在 OpenStreetMap 開啟大圖 ↗
        </a>
      </p>
    </div>
  )
}

LandMap.css = style
LandMap.afterDOMLoaded = script

export default (() => LandMap) satisfies QuartzComponentConstructor

import { QuartzComponent, QuartzComponentConstructor, QuartzComponentProps } from "./types"
import { classNames } from "../util/lang"

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

  const delta = 0.004
  const bbox = `${lonNum - delta},${latNum - delta},${lonNum + delta},${latNum + delta}`
  const embedSrc = `https://www.openstreetmap.org/export/embed.html?bbox=${bbox}&layer=mapnik&marker=${latNum}%2C${lonNum}`
  const openLink = `https://www.openstreetmap.org/?mlat=${latNum}&mlon=${lonNum}#map=17/${latNum}/${lonNum}`

  return (
    <div class={classNames(displayClass, "land-map")}>
      <h3>位置地圖</h3>
      <iframe
        class="land-map-frame"
        src={embedSrc}
        loading="lazy"
        referrerpolicy="no-referrer-when-downgrade"
      ></iframe>
      <p class="land-map-link">
        <a href={openLink} target="_blank" rel="noopener noreferrer">
          在 OpenStreetMap 開啟大圖 ↗
        </a>
      </p>
    </div>
  )
}

LandMap.css = `
.land-map {
  margin: 1rem 0;
}
.land-map-frame {
  width: 100%;
  height: 300px;
  border: 1px solid var(--lightgray);
  border-radius: 5px;
}
.land-map-link {
  margin-top: 0.3rem;
  font-size: 0.85rem;
}
`

export default (() => LandMap) satisfies QuartzComponentConstructor

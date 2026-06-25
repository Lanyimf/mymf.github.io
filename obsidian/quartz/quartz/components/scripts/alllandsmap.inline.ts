// @ts-nocheck
interface LandRecord {
  id: string
  name: string | null
  lat: number | null
  lon: number | null
}

function getBaseDir(): string {
  const script = document.querySelector('script[src$="postscript.js"]') as HTMLScriptElement | null
  if (!script) return "/"
  return script.getAttribute("src")!.replace(/postscript\.js$/, "")
}

document.addEventListener("nav", async () => {
  const container = document.querySelector(".all-lands-map-host") as HTMLElement | null
  if (!container) return
  if ((container as any)._leaflet_id) return // 已初始化過，避免 SPA 導覽重複建立

  if (!document.querySelector('link[data-leaflet]')) {
    const link = document.createElement("link")
    link.rel = "stylesheet"
    link.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
    link.setAttribute("data-leaflet", "true")
    document.head.appendChild(link)
  }

  // @ts-ignore
  const leafletModule = await import("https://esm.sh/leaflet@1.9.4")
  const L = leafletModule.default ?? leafletModule

  const baseDir = getBaseDir()
  const res = await fetch(`${baseDir}static/lands-index.json`)
  const lands: LandRecord[] = await res.json()

  // 台灣中心點，縮放到可看見全島
  const map = L.map(container, {
    center: [23.7, 121.0],
    zoom: 7,
  })

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap contributors",
    maxZoom: 19,
  }).addTo(map)

  for (const l of lands) {
    if (l.lat == null || l.lon == null) continue
    const marker = L.circleMarker([l.lat, l.lon], {
      radius: 5,
      weight: 1,
      color: "#2f5d62",
      fillColor: "#3f8f8a",
      fillOpacity: 0.7,
    }).addTo(map)
    marker.bindPopup(`<a href="${baseDir}lands/${l.id}">${l.name ?? l.id}</a>`)
    marker.on("mouseover", () => marker.setStyle({ radius: 8, fillOpacity: 1 }))
    marker.on("mouseout", () => marker.setStyle({ radius: 5, fillOpacity: 0.7 }))
    marker.on("click", () => {
      window.location.href = `${baseDir}lands/${l.id}`
    })
  }

  window.addCleanup(() => map.remove())
})

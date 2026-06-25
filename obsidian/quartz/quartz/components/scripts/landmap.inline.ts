// @ts-nocheck
document.addEventListener("nav", async () => {
  const containers = document.querySelectorAll<HTMLElement>(".land-map-canvas")
  if (containers.length === 0) return

  // Leaflet (UMD) — load CSS + JS once per page load
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

  for (const container of containers) {
    if ((container as any)._leaflet_id) continue // already initialized

    const lat = parseFloat(container.dataset.lat!)
    const lon = parseFloat(container.dataset.lon!)
    if (Number.isNaN(lat) || Number.isNaN(lon)) continue

    const map = L.map(container, {
      center: [lat, lon],
      zoom: 17,
      scrollWheelZoom: false,
    })

    // 底圖：OpenStreetMap（無需金鑰，全球可用）
    const osm = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "&copy; OpenStreetMap contributors",
      maxZoom: 19,
    }).addTo(map)

    // 底圖：國土測繪中心（NLSC）電子地圖
    const nlscEmap = L.tileLayer(
      "https://wmts.nlsc.gov.tw/wmts/EMAP/default/EPSG:3857/{z}/{y}/{x}",
      { attribution: "內政部國土測繪中心 EMAP", maxZoom: 19 },
    )

    // 底圖：國土測繪中心 正射影像（航空照片）
    const nlscPhoto = L.tileLayer(
      "https://wmts.nlsc.gov.tw/wmts/PHOTO2/default/EPSG:3857/{z}/{y}/{x}",
      { attribution: "內政部國土測繪中心 正射影像", maxZoom: 19 },
    )

    // 疊加圖層：地籍圖（地號邊界）— NLSC WMTS（正式圖層代碼 LANDSECT）
    const cadastral = L.tileLayer(
      "https://wmts.nlsc.gov.tw/wmts/LANDSECT/default/EPSG:3857/{z}/{y}/{x}",
      { attribution: "內政部地政司 地籍圖", maxZoom: 19, opacity: 1, className: "cadastral-tiles" },
    )

    // 標記
    L.marker([lat, lon]).addTo(map)

    const baseLayers = {
      "OpenStreetMap": osm,
      "國土測繪電子地圖": nlscEmap,
      "正射影像（航照）": nlscPhoto,
    }
    const overlays = {
      "地籍圖（地號邊界）": cadastral,
    }
    L.control.layers(baseLayers, overlays, { collapsed: true }).addTo(map)

    window.addCleanup(() => map.remove())
  }
})

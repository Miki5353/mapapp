
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
      const cookies = document.cookie.split(";");
      for (let cookie of cookies) {
        cookie = cookie.trim();
        if (cookie.startsWith(name + "=")) {
          cookieValue = decodeURIComponent(cookie.slice(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

// immediately grab the token:
const CSRF_TOKEN = getCookie("csrftoken");

document.addEventListener("DOMContentLoaded", () => {

  const cfg = window.EditorConfig;

  /* --- Leaflet init -------------------------------------------------- */
  const map = L.map("map", {
    crs: L.CRS.Simple,
    minZoom: -4,
    maxZoom: 2,
    pmIgnore: false
  });
  const bounds = [[0, 0], [cfg.imgH, cfg.imgW]];
  L.imageOverlay(cfg.imgUrl, bounds).addTo(map);
  map.fitBounds(bounds);
  setTimeout(() => map.invalidateSize(), 0);

  let line = null;
  let endArrow = null;

  function redrawLine() {
      if (line) map.removeLayer(line);
      if (endArrow) map.removeLayer(endArrow);

      const latlngs = cfg.points.map(p => [p.y, p.x]);
      line = L.polyline(latlngs, {color: "#2563eb"}).addTo(map);

      if (latlngs.length > 1) {
          const last = latlngs[latlngs.length - 1];
          map.removeLayer(endArrow ?? L.layerGroup());
          endArrow = L.marker(last, {interactive: false}).addTo(map);
      }
  }

  function refreshSidebar() {
    document.getElementById("pt-count").textContent = cfg.points.length;
    const list = document.getElementById("pt-list");
    list.innerHTML = "";
    cfg.points.forEach(pt => {
      const li = document.createElement("li");
      li.textContent = `(${pt.x}, ${pt.y})`;
      list.appendChild(li);
    });
  }

  function addMarker(pt) {
    const marker = L.marker([pt.y, pt.x], {draggable: true, pmIgnore: false}).addTo(map);

    marker.on("dragend", async () => {
      const {lng: x, lat: y} = marker.getLatLng();
      await fetch(`/api/routes/${cfg.routeId}/points/${pt.id}/`, {
        method: "PATCH",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": CSRF_TOKEN
        },
        body: JSON.stringify({x: Math.round(x), y: Math.round(y)})
      });
      Object.assign(pt, {x: Math.round(x), y: Math.round(y)});
      redrawLine();
      refreshSidebar();
    });

    marker.on("click", () => {
      if (confirm("Delete this point?")) deletePoint(pt.id);
    });
  }

  async function savePoint(body) {
    const res = await fetch(`/api/routes/${cfg.routeId}/points/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": CSRF_TOKEN
      },
      body: JSON.stringify(body)
    });
    const pt = await res.json();
    cfg.points.push(pt);
    addMarker(pt);
    redrawLine();
    refreshSidebar();
  }

  async function deletePoint(id) {
    await fetch(`/api/routes/${cfg.routeId}/points/${id}/`, {
        method: "DELETE",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": CSRF_TOKEN
        },
    });
    cfg.points = cfg.points.filter(p => p.id !== id);
    location.reload();
  }

  cfg.points.forEach(addMarker);
  redrawLine();
  refreshSidebar();

  map.on("click", e => {
    const {lng: x, lat: y} = e.latlng;
    savePoint({x: Math.round(x), y: Math.round(y)});
  });


  const form = document.getElementById("add-form");
  form?.addEventListener("submit", e => {
    e.preventDefault();
    const x = parseInt(form.x.value, 10);
    const y = parseInt(form.y.value, 10);
    if (!Number.isNaN(x) && !Number.isNaN(y)) {
      savePoint({x, y});
      form.reset();
    }
  });
});
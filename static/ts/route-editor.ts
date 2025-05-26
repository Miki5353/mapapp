/*--------------------------------------------------------------------
 *  Interaktywny edytor ścieżki na planszy „Połącz Kropki”
 *  ------------------------------------------------------
 *  Zasady UX (wg wymagań):
 *  • Użytkownik może mieć jedną ścieżkę na planszy.
 *  • Klik w kropkę → zaczynamy budować trasę w jej kolorze.
 *  • Podświetlamy tylko kafelki w tym samym wierszu lub kolumnie.
 *  • Podgląd odcinka przy najechaniu myszą.
 *  • Klik akceptuje odcinek jeżeli: ruch ↑↓→←, brak przecinania,
 *    brak innych kolorów na drodze, brak powtórzeń.
 *  • Klik w drugą kropkę tego samego koloru → trasa ukończona (phase ="finished").
 *  • PPM cofa ostatni punkt w fazie "building".
 *  • Klik gotowej ścieżki → okno potwierdzenia kasowania (wracamy do phase ="idle").
 *  • Zapisywać wolno tylko w phase ="finished".
 *-------------------------------------------------------------------*/

import { buildGrid, calcCellSize } from "./grid-renderer.js";

/* ═════════════  Typy  ═════════════ */
interface Dot       { row: number; col: number; color: string }
interface PathPoint { row: number; col: number; order: number }

type Phase = "idle" | "building" | "finished"

interface EditorState {
  phase: Phase
  color: string | null
  points: PathPoint[]
  preview: { row: number; col: number } | null
}

/* ═════════════  Elementy DOM  ═════════════ */
const gridWrapper   = document.getElementById("gridWrapper")!
const gridContainer = document.getElementById("gridContainer")!
const pointList     = document.getElementById("pointList")!
const saveBtn       = document.getElementById("saveRoute")!   as HTMLButtonElement
const clearLastBtn  = document.getElementById("clearLast")!   as HTMLButtonElement
const clearAllBtn   = document.getElementById("clearAll")!    as HTMLButtonElement
const toast         = document.getElementById("saveSuccessToast")!

/* ═════════════  Dane z atrybutów  ═════════════ */
const boardId  = Number(gridContainer.dataset.boardId)
const routeIdAttr = gridContainer.dataset.routeId || null
let   routeId: number | null = routeIdAttr && routeIdAttr.length ? Number(routeIdAttr) : null

/* ═════════════  Globalny stan  ═════════════ */
const state: EditorState = {
  phase: "idle",
  color: null,
  points: [],
  preview: null
}

let stateBoard: { rows: number; cols: number; dots: Dot[] } = { rows: 0, cols: 0, dots: [] }

/* ═════════════  Pobieranie danych  ═════════════ */
async function loadBoard() {
  const res = await fetch(`/api/boards/${boardId}/`)
  if (!res.ok) throw new Error("Board load failed")
  const data = await res.json()
  stateBoard.rows = data.rows
  stateBoard.cols = data.cols
  stateBoard.dots = data.dots as Dot[]
}

async function loadRoute() {
  if (!routeId) return
  const res = await fetch(`/api/routes/${routeId}/`)
  if (!res.ok) throw new Error("Route load failed")
  const data = await res.json()
  if (Array.isArray(data.points) && data.points.length) {
    state.points = data.points
      .sort((a:any,b:any)=>a.order-b.order)
      .map((p:any) => ({ row: p.x, col: p.y, order: p.order }))
    state.phase  = "finished"
    state.color  = findDot(state.points[0].row, state.points[0].col)?.color ?? null
  }
}

/* ═════════════  Pomocnicze  ═════════════ */
function findDot(row: number, col: number): Dot | undefined {
  return stateBoard.dots.find(d => d.row === row && d.col === col)
}

function segmentCells(a: {row:number,col:number}, b: {row:number,col:number}): {row:number,col:number}[] {
  const cells: {row:number,col:number}[] = []
  if (a.row === b.row) {
    const [min,max] = [Math.min(a.col, b.col), Math.max(a.col, b.col)]
    for (let c = min+1; c <= max; c++) cells.push({ row: a.row, col: c })
  } else if (a.col === b.col) {
    const [min,max] = [Math.min(a.row, b.row), Math.max(a.row, b.row)]
    for (let r = min+1; r <= max; r++) cells.push({ row: r, col: a.col })
  }
  return cells
}

function segmentsCross(a:{row:number,col:number}, b:{row:number,col:number}, c:{row:number,col:number}, d:{row:number,col:number}): boolean {
  // wszystkie odcinki są osiowo‑równoległe → sprawdzamy prostą geometrię
  if (a.row === b.row && c.col === d.col) {
    // A poziomy, C pionowy
    const [minAc,maxAc] = [Math.min(a.col,b.col), Math.max(a.col,b.col)]
    const [minCr,maxCr] = [Math.min(c.row,d.row), Math.max(c.row,d.row)]
    return c.col >= minAc && c.col <= maxAc && a.row >= minCr && a.row <= maxCr
  }
  if (a.col === b.col && c.row === d.row) {
    // A pionowy, C poziomy
    const [minAr,maxAr] = [Math.min(a.row,b.row), Math.max(a.row,b.row)]
    const [minCc,maxCc] = [Math.min(c.col,d.col), Math.max(c.col,d.col)]
    return c.row >= minAr && c.row <= maxAr && a.col >= minCc && a.col <= maxCc
  }
  return false // równoległe → brak przecięcia w geometrii siatki
}

function segmentsWeakCross(a:{row:number,col:number}, b:{row:number,col:number}, c:{row:number,col:number}): boolean {
  if(a.row === b.row && b.row === a.row) {
    if(a.col > b.col) {
      return c.col > b.col;
    }
    if(a.col < b.col) {
      return c.col < b.col;
    }
  }

  if(a.col === b.col && b.col === a.col) {
    if(a.row > b.row) {
      return c.row > b.row;
    }
    if(a.row < b.row) {
      return c.row < b.row;
    }
  }

  return true;
}


function isSegmentValid(row: number, col: number): boolean {
  const pts = state.points
  const last = pts[pts.length - 1]!
  const sameRow = last.row === row
  const sameCol = last.col === col
  if (sameRow === sameCol) return false // musi być LUB
  // nie wracamy na ten sam punkt
  if (pts.some(p => p.row === row && p.col === col)) return false
  // przecinanie z istniejącymi krawędziami
  for (let i = 1; i < pts.length - 1; i++) {
    const a = pts[i-1], b = pts[i]
    if (segmentsCross(a,b,last,{row,col})) {
      console.log("Segment crosses existing path:", a, b, last, {row,col})
      return false
    }
  }

  if (pts.length >= 2) {
    const a = pts[pts.length - 2];
    const b = pts[pts.length - 1];
    if (segmentsWeakCross(a, b, { row, col })) {
      console.log("Segment weakly crosses last segment:", a, b, { row, col });
      return false
    }
  }

  // obce kropki na odcinku (bez końca)
  const dir = sameRow ? "col" : "row"
  const [min,max] = sameRow ? [Math.min(last.col,col), Math.max(last.col,col)] : [Math.min(last.row,row), Math.max(last.row,row)]
  for (const dot of stateBoard.dots) {
    if (dot.color === state.color) continue
    if (sameRow && dot.row === row && dot.col > min && dot.col < max) return false
    if (sameCol && dot.col === col && dot.row > min && dot.row < max) return false
  }

  const dot = stateBoard.dots.find(d => d.row === row && d.col === col);
  if (dot && dot.color !== state.color) return false;
  return true
}

function isPathCell(row:number,col:number): boolean {
  return state.points.some(p=>p.row===row&&p.col===col)
}

/* ═════════════  Rysowanie  ═════════════ */
function clearRoutePreview() {
  const oldRect = gridContainer.querySelector<HTMLElement>(".route-rect-preview");
  if (oldRect) oldRect.remove();
}

function hexToRgba(hex: string, alpha: number): string {
  // Remove leading #
  hex = hex.replace(/^#/, "");
  // Support short hex
  if (hex.length === 3) {
    hex = hex.split("").map(x => x + x).join("");
  }
  const num = parseInt(hex, 16);
  const r = (num >> 16) & 255;
  const g = (num >> 8) & 255;
  const b = num & 255;
  return `rgba(${r},${g},${b},${alpha})`;
}

function drawRectangle(
  a: { row: number; col: number },
  b: { row: number; col: number },
  alpha: number,
  withBorder: boolean,
  className: string = "route_rect"
) {
  // Pobierz komórki startową i końcową
  const cellA = gridContainer.querySelector<HTMLElement>(`[data-row='${a.row}'][data-col='${a.col}']`);
  const cellB = gridContainer.querySelector<HTMLElement>(`[data-row='${b.row}'][data-col='${b.col}']`);
  if (!cellA || !cellB) return;

  const rectA = cellA.getBoundingClientRect();
  const rectB = cellB.getBoundingClientRect();
  const parentRect = gridContainer.getBoundingClientRect();

  // Wyznacz środek obu komórek względem gridContainer
  const centerA = {
    x: rectA.left - parentRect.left + rectA.width / 2,
    y: rectA.top - parentRect.top + rectA.height / 2
  };
  const centerB = {
    x: rectB.left - parentRect.left + rectB.width / 2,
    y: rectB.top - parentRect.top + rectB.height / 2
  };

  const rectDiv = document.createElement("div");
  rectDiv.className = className + " pointer-events-none";
  rectDiv.style.position = "absolute";
  rectDiv.style.zIndex = className === "route-rect-preview" ? "10" : "9";
  rectDiv.style.background = state.color ? hexToRgba(state.color, alpha) : `rgba(251,191,36,${alpha})`;
  rectDiv.style.borderRadius = "0.4em"

  // Rozmiary jak w highlightPreview/drawPoint
  const cellSize = rectA.width;
  const rectHeight = cellSize * 0.3;
  const rectWidth = cellSize * 0.3;

  if (a.row === b.row) {
    // poziomy odcinek
    const left = Math.min(centerA.x, centerB.x);
    const width = Math.abs(centerA.x - centerB.x);
    rectDiv.style.left = `${left}px`;
    rectDiv.style.top = `${centerA.y - rectHeight / 2}px`;
    rectDiv.style.width = `${width}px`;
    rectDiv.style.height = `${rectHeight}px`;
  } else if (a.col === b.col) {
    // pionowy odcinek
    const top = Math.min(centerA.y, centerB.y);
    const height = Math.abs(centerA.y - centerB.y);
    rectDiv.style.left = `${centerA.x - rectWidth / 2}px`;
    rectDiv.style.top = `${top}px`;
    rectDiv.style.width = `${rectWidth}px`;
    rectDiv.style.height = `${height}px`;
  } else {
    // fallback na pełny prostokąt
    const minRow = Math.min(a.row, b.row);
    const maxRow = Math.max(a.row, b.row);
    const minCol = Math.min(a.col, b.col);
    const maxCol = Math.max(a.col, b.col);
    rectDiv.style.left = `${minCol * cellSize}px`;
    rectDiv.style.top = `${minRow * cellSize}px`;
    rectDiv.style.width = `${(maxCol - minCol + 1) * cellSize}px`;
    rectDiv.style.height = `${(maxRow - minRow + 1) * cellSize}px`;
  }

  if (withBorder) {
    rectDiv.style.border = `2px solid ${state.color ? hexToRgba(state.color, Math.min(1, alpha * 2.5)) : "rgba(251,191,36,0.7)"}`;
  }

  gridContainer.style.position = "relative";
  gridContainer.appendChild(rectDiv);
}

function highlightPreview() {
  // Usuń stary prostokąt
  clearRoutePreview();
  if (!state.preview || state.points.length === 0) return;

  if (!state.preview || state.points.length === 0) return;

  const last = state.points[state.points.length - 1]!;
  const { row, col } = state.preview;

  drawRectangle(
    last,
    { row, col },
    0.3,
    true,
    "route-rect-preview"
  );
}

function newPoint(point: PathPoint, prevPoint: PathPoint | null) {
  // Usuń stare podświetlenie
  clearRoutePreview();
  // Kropka
  const cell = gridContainer.querySelector<HTMLElement>(`[data-row='${point.row}'][data-col='${point.col}']`);
  if (cell) {

    // Usuń starą kropkę jeśli jest
    let marker = cell.querySelector<HTMLDivElement>(".route_dot");
    if (marker) marker.remove();

    if(point.order !== 1 && (state.phase !== "finished" || point.order !== state.points.length)) {
      const dot = document.createElement("div");
      dot.className = "route_dot";
      dot.style.width = "40%";
      dot.style.height = "40%";
      dot.style.margin = "auto";
      dot.style.borderRadius = "50%";
      dot.style.background = state.color ?? "#fbbf24";
      dot.style.display = "block";
      cell.appendChild(dot);
    }
  }

  // Prostokąt (segment) łączący z poprzednim punktem
  if (prevPoint) {
    drawRectangle(prevPoint, point, 0.5, false, "route_rect");
  }

  // <li> do listy punktów
  if (point.order > pointList.children.length) {
    const li = document.createElement("li");
    li.className = "route_li";
    li.textContent = `(${point.row}, ${point.col})`;
    pointList.appendChild(li);
  }
}

function dropLast() {
  // Usuń ostatni <li>
  const lastLi = pointList.querySelector("li.route_li:last-child");
  if (lastLi) lastLi.remove();


  // Usuń ostatni prostokąt
  const rects = gridContainer.querySelectorAll<HTMLDivElement>(".route_rect");
  if (rects.length > 0) rects[rects.length - 1].remove();

  if( state.phase === "finished") {
    state.phase = "building";
    saveBtn.disabled = true;
  } else {
    // Usuń ostatnią kropkę
    const dots = gridContainer.querySelectorAll<HTMLDivElement>(".route_dot");
    if (dots.length > 0) dots[dots.length - 1].remove();
  }

  if (state.points.length > 0) {
    state.points.pop()
  }
  if (state.points.length === 0) {
    state.phase = "idle"
    state.color = null
  }
  state.preview = null
  clearRoutePreview();
}

function clearAll() {
  // Usuń wszystkie punkty z listy
  pointList.innerHTML = "";
  // Usuń wszystkie kropki
  gridContainer.querySelectorAll<HTMLDivElement>(".route_dot").forEach(el => el.remove());
  // Usuń wszystkie prostokąty
  gridContainer.querySelectorAll<HTMLDivElement>(".route_rect").forEach(el => el.remove());
  // Usuń wszystkie podświetlenia
  clearRoutePreview();
  saveBtn.disabled = true;
}

/* ═════════════  Logika akcji  ═════════════ */
function startBuilding(row:number,col:number,color:string) {
  state.phase = "building"
  state.color = color
  state.points = [{ row, col, order: 1 }]
  state.preview = null
  newPoint({ row, col, order: 1 }, null);
}

function finishRoute() {
  state.phase = "finished"
  state.preview = null
  let last_point = state.points[state.points.length - 1] || null;
  let prev_point = state.points[state.points.length - 2] || null;
  if (last_point && prev_point) {
    newPoint(last_point, prev_point);
  } else if (last_point) {
    newPoint(last_point, null);
  }
  saveBtn.disabled = false;
}

function confirmDeleteRoute() {
  if (!confirm("Skasować tę ścieżkę?")) return
  state.phase = "idle";
  state.color = null;
  state.points = [];
  state.preview = null;
  clearAll();
}

/* ═════════════  Obsługa zdarzeń  ═════════════ */
function handleCellEnter(row: number, col: number) {
  if (state.phase !== "building") return;
  if (!isSegmentValid(row, col)) {
    return;
  }
  state.preview = { row, col };
  highlightPreview();
}

function handleCellClick(row:number,col:number) {
  switch(state.phase) {
    case "idle": {
      const dot = findDot(row,col)
      if (!dot) return
      console.log("Found dot: ", dot)
      startBuilding(row,col,dot.color)
      break
    }
    case "building": {
      if (!isSegmentValid(row,col)) return
      state.points.push({ row, col, order: state.points.length + 1 })
      state.preview = null
      const dot = findDot(row,col)
      if (dot && dot.color === state.color && state.points.length >= 2) {
        finishRoute()
      } else {
        newPoint({ row, col, order: state.points.length }, state.points[state.points.length - 2] || null);
      }
      break
    }
    case "finished": {
      if (isPathCell(row,col)) confirmDeleteRoute()
      break
    }
  }
}

/*  PPM = cofnięcie  */
gridContainer.addEventListener("contextmenu", ev => {
  ev.preventDefault()
  dropLast()
})

/* ═════════════  Budowa siatki i restart przy resize  ═════════════ */
function rebuildGrid() {
  buildGrid(gridContainer, stateBoard.rows, stateBoard.cols, stateBoard.dots, {
    editable: true,
    cellSize: calcCellSize(gridWrapper, stateBoard.rows, stateBoard.cols),
    cellClick: handleCellClick,
    cellEnter: handleCellEnter
  })

  for (let i = 0; i < state.points.length; i++) {
    const point = state.points[i];
    const prevPoint = i > 0 ? state.points[i - 1] : null;
    newPoint(point, prevPoint);
  }
  clearRoutePreview();
}

window.addEventListener("resize", rebuildGrid)

/* ═════════════  Zapis  ═════════════ */
function getCSRFToken(): string {
  return document.cookie.match(/csrftoken=([^;]+)/)?.[1] ?? ""
}

async function saveRoute() {
  if (state.phase !== "finished") {
    alert("Najpierw dokończ ścieżkę (połącz dwie kropki).")
    return
  }
  const headers = { "Content-Type": "application/json", "X-CSRFToken": getCSRFToken() }
  const name = (document.querySelector<HTMLInputElement>("input[name='name']")!.value || "Trasa").trim()

  // 1) utwórz Route, jeśli trzeba
  if (!routeId) {
    const res = await fetch("/api/routes/", {
      method: "POST",
      headers,
      body: JSON.stringify({ name, background: boardId })
    })
    if (!res.ok) { alert("Błąd tworzenia trasy"); return }
    const data = await res.json()
    routeId = data.id
  } else {
    // PATCH nazwy jeśli route już istnieje
    const patchRes = await fetch(`/api/routes/${routeId}/`, {
      method: "PATCH",
      headers,
      body: JSON.stringify({ name })
    })
    if (!patchRes.ok) {
      alert("Błąd aktualizacji nazwy trasy")
      return
    }
  }

  // 2) PUT bulk punktów (preferowane) lub fallback: DELETE+POST
  const bulkRes = await fetch(`/api/routes/${routeId}/points/bulk/`, {
    method: "PUT",
    headers,
    body: JSON.stringify(state.points.map(p => ({ x: p.row, y: p.col })))
  })
  if (!bulkRes.ok) {
    console.log("Bulk failed", bulkRes.status, bulkRes.statusText);
  }
  // wizualny toast
  toast.style.opacity = "1"
  setTimeout(() => toast.style.opacity = "0", 2500)
}

saveBtn.addEventListener("click", saveRoute)

clearLastBtn.addEventListener("click", () => {
  dropLast()
})

clearAllBtn.addEventListener("click", confirmDeleteRoute);

/* ═════════════  INIT  ═════════════ */
(async () => {
  await loadBoard()
  await loadRoute()
  rebuildGrid()
  saveBtn.disabled = state.phase !== "finished"
})();

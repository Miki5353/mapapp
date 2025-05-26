/*--------------------------------------------------------------------
 *  GRID‑RENDERER
 *  ------------------------------------------------------------------
 *  Uniwersalna funkcja budowania siatki z Lab 9 wraz z obsługą kropek
 *  i opcjonalnymi callbackami na klik / hover. Zależności: brak (czysty DOM).
 *-------------------------------------------------------------------*/

export interface Dot {
  row: number;
  col: number;
  color: string;           // dowolny CSS color
}

export interface Options {
  /** Tryb edycji: true → hover‑CSS + nasłuchiwanie click / hover */
  editable?: boolean;
  /** Klik w komórkę.  Wywoływane TYLKO w trybie editable. */
  cellClick?:  (row: number, col: number, cell: HTMLElement) => void;
  /** Najechanie kursorem (mouseenter). Wywoływane w trybie editable. */
  cellEnter?:  (row: number, col: number, cell: HTMLElement) => void;
  /** Odejście kursora (mouseleave).  Wywoływane w trybie editable. */
  cellLeave?:  (row: number, col: number, cell: HTMLElement) => void;

  /** Szerokość / wysokość pojedynczej komórki (px). Domyślnie 40 px. */
  cellSize?: number;
  /** Odstęp między komórkami (grid‑gap) w px. Domyślnie 6 px. */
  gap?: number;
}

/*------------------------------------------------------------------*/
/*  Pomocnik: oblicz optymalny cellSize, aby cała siatka weszła w div */
/*------------------------------------------------------------------*/
export function calcCellSize(container: HTMLElement, rows: number, cols: number): number {
  const rect = container.getBoundingClientRect();
  const size = Math.floor(Math.min(rect.height / rows, rect.width / cols));
  return Math.max(16, 0.9 * size);                     // min 16 px dla mobile
}

/*------------------------------------------------------------------*/
/*  buildGrid – rysuje <div id="grid"> … </div>                     */
/*------------------------------------------------------------------*/
export function buildGrid(
  container: HTMLElement,
  rows: number,
  cols: number,
  dots: Dot[] = [],
  opts: Options = {}
): HTMLElement {
  const size      = opts.cellSize ?? 40;
  const gap       = opts.gap      ?? 6;
  const editable  = !!opts.editable;

  // wyczyść poprzednią zawartość
  container.innerHTML = "";

  // główne <div> siatki
  const grid = document.createElement("div");
  grid.id = "grid";
  grid.style.display = "grid";
  grid.style.height  = "100%";
  grid.style.gridTemplateColumns = `repeat(${cols}, ${size}px)`;
  grid.style.gridTemplateRows    = `repeat(${rows}, ${size}px)`;
  grid.style.gap = `${gap}px`;
  container.appendChild(grid);

  // szybki lookup czy tu leży kropka
  const dotAt = (r: number, c: number) => dots.find(d => d.row === r && d.col === c);

  /*--------------------------------------------------------------*/
  /*  Tworzenie komórek                                            */
  /*--------------------------------------------------------------*/
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const cell = document.createElement("div");
      cell.className = "cell";
      cell.dataset.row = String(r);
      cell.dataset.col = String(c);
      cell.style.cssText = `width:${size}px;height:${size}px;background:#232C33;border-radius:10%;display:flex;align-items:center;justify-content:center;`;
      if (editable) cell.classList.add("transition-transform", "duration-200", "hover:scale-110");

      // kropka?
      const dot = dotAt(r, c);
      if (dot) paintDot(cell, dot.color);

      // callbacki tylko w trybie editable
      if (editable) {
        if (opts.cellClick)
          cell.addEventListener("click",   () => opts.cellClick!(r, c, cell));
        if (opts.cellEnter)
          cell.addEventListener("mouseenter", () => opts.cellEnter!(r, c, cell));
        if (opts.cellLeave)
          cell.addEventListener("mouseleave", () => opts.cellLeave!(r, c, cell));
      }

      grid.appendChild(cell);
    }
  }
  return grid;
}

/*------------------------------------------------------------------*/
/*  paintDot – dekoruje komórkę kolorową kropką                      */
/*------------------------------------------------------------------*/
export function paintDot(cell: HTMLElement, color: string): void {
  cell.classList.add("used");
  const d = document.createElement("div");
  d.style.width  = "60%";
  d.style.height = "60%";
  d.style.margin = "auto";
  d.style.borderRadius = "50%";
  d.style.background   = color;
  cell.appendChild(d);
}

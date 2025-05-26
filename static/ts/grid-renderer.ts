/* grid-renderer.ts
 * uniwersalne budowanie siatki + renderowanie kropek
 */

export interface Dot    { row: number; col: number; color: string }
export interface Options {
  editable?: boolean;           // domyślnie false = read-only
  cellClick?: (row: number, col: number, cell: HTMLElement) => void;
  cellEnter?: (row: number, col: number, cell: HTMLElement) => void; // dodane
  cellExit?: (row: number, col: number, cell: HTMLElement) => void;  // dodane
  cellSize?: number;            // px; domyślnie 40
  gap?: number;                 // px; domyślnie 6
}

export function calcCellSize(container: HTMLElement, rows: number, cols: number): number {
  const rect = container.getBoundingClientRect();
  const h = rect.height;
  const w = rect.width;
  const size = Math.floor(Math.min(h / rows, w / cols));
  return Math.max(16, 0.9 * size);
}

/**
 * Tworzy siatkę i wstawia ją do container'a.
 * Zwraca referencję do <div id="grid">.
 */
export function buildGrid(
  container : HTMLElement,
  rows      : number,
  cols      : number,
  dots      : Dot[],
  opts: Options = {}
): HTMLElement {

  const size   = opts.cellSize ?? 40;
  const gap    = opts.gap      ?? 6;
  const editable = opts.editable ?? false;

  container.innerHTML = "";

  const grid = document.createElement("div");
  grid.id = "grid";
  grid.style.display = "grid";
  grid.style.height = "100%"
  grid.style.gridTemplateColumns = `repeat(${cols}, ${size}px)`;
  grid.style.gridTemplateRows    = `repeat(${rows}, ${size}px)`;
  grid.style.gap = `${gap}px`;
  container.appendChild(grid);

  const isDotHere = (r: number, c: number) =>
    dots.find(d => d.row === r && d.col === c);

  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const cell = document.createElement("div");
      cell.className = "cell";
      cell.dataset.row = String(r);
      cell.dataset.col = String(c);
      cell.style.cssText =
        `width:${size}px;height:${size}px;background:#232C33;border-radius:10%;
         display:flex;align-items:center;justify-content:center;`;
      if (editable) cell.classList.add("transition-transform","duration-200","hover:scale-110");

      const dot = isDotHere(r, c);
      if (dot) {
        paintDot(cell, dot.color);
      }

      if (editable && opts.cellClick)
        cell.addEventListener("click", () => opts.cellClick!(r, c, cell));

      if (editable && opts.cellEnter)
        cell.addEventListener("mouseenter", () => opts.cellEnter!(r, c, cell));
      if (editable && opts.cellExit)
        cell.addEventListener("mouseleave", () => opts.cellExit!(r, c, cell));

      grid.appendChild(cell);
    }
  }
  return grid;
}

export function paintDot(cell: HTMLElement, color: string) {
  cell.classList.add("used");
  const d = document.createElement("div");
  d.className = "dot";
  d.style.width = "60%";
  d.style.height = "60%";
  d.style.margin = "auto";
  d.style.borderRadius = "50%";
  d.style.background = color;
  d.style.display = "block";
  cell.appendChild(d);
}

import { buildGrid, calcCellSize, Dot } from "./grid-renderer.js";

const container = document.getElementById("gridContainer")!;

const boardIdAttr = container.dataset.boardId || null;
let   boardId: string | null = boardIdAttr && boardIdAttr.length ? boardIdAttr : null;

const res = await fetch(`/api/boards/${boardId}`);
if (!res.ok) {
  console.log(res)
  console.error("Nie udało się pobrać planszy:", res.status);
}

const data = await res.json();
console.log("🔹 Załadowano planszę:", data);

const cellSize = calcCellSize(container, data.rows, data.cols);

buildGrid(container, data.rows, data.cols, data.dots, {
  editable: false,
  cellSize: cellSize,
});

function draw() {
  const cellSize = calcCellSize(container, data.rows, data.cols);
  buildGrid(container, data.rows, data.cols, data.dots, {
    editable: false,
    cellSize: cellSize,
  });
}

window.addEventListener("resize", draw);
draw(); // pierwsze wywołanie
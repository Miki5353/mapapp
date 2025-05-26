import { buildGrid, paintDot, calcCellSize, Dot } from "./grid-renderer.js";

interface BoardState {
  rows: number;
  cols: number;
  dots: Dot[];
}

const authToken = (document.querySelector('meta[name="auth-token"]') as HTMLMetaElement)?.content;

const gridWrapper   = document.getElementById("gridWrapper")!;
const gridContainer = document.getElementById("gridContainer")!;
const rowsInput     = document.querySelector<HTMLInputElement>('input[name="rows"]')!;
const colsInput     = document.querySelector<HTMLInputElement>('input[name="cols"]')!;
const colorPicker   = document.getElementById("colorPicker") as HTMLInputElement;
const saveGridBtn   = document.getElementById("saveGrid")!;
const pairList      = document.getElementById("pairList")!;
const paletteBtns   = document.querySelectorAll<HTMLButtonElement>("#colorPalette button");
const deleteToggle  = document.getElementById("deleteToggle") as HTMLButtonElement | null; // opcjonalny


const boardIdAttr = gridContainer.dataset.boardId || null;
let   boardId: string | null = boardIdAttr && boardIdAttr.length ? boardIdAttr : null;

/* ──────────────────────────────────────────────── */
/*  GLOBAL STATE                                   */
let state: BoardState = {
  rows: 5,
  cols: 5,
  dots: [],
};

async function loadBoard(): Promise<void> {
  if (!boardId) return;

  const res = await fetch(`/api/boards/${boardId}`);
  if (!res.ok) {
    console.error("Nie udało się pobrać planszy:", res.status);
    return;
  }

  const data = await res.json();
  console.log("🔹 Załadowano planszę:", data);

  state.rows = data.rows;
  state.cols = data.cols;
  state.dots = data.dots;

  rowsInput.value = String(data.rows);
  colsInput.value = String(data.cols);

  rebuild();
}

let activeColor = colorPicker.value;   // aktualnie wybrany kolor
let deleteMode  = false;               // tryb masowego kasowania

let lastSavedDots: Dot[] = JSON.parse(JSON.stringify(state.dots)); // deep clone

function isDirty(): boolean {
  return JSON.stringify(lastSavedDots) !== JSON.stringify(state.dots);
}                  // flaga, czy nastąpiła zmiana

/* ──────────────────────────────────────────────── */
/*  HELPERS                                         */

/* ─── wybór koloru z listy par ─── */
function pickColor(color: string) {
  activeColor = color;
  colorPicker.value = color;                 // synchronizujemy z pickerem
}

/* ─── usunięcie CAŁEJ pary ─── */
function removePair(color: string) {
  state.dots = state.dots.filter(d => d.color !== color);
  rebuild();                               // przebuduj siatkę i listę
}

function updatePairList() {
  if(!pairList) return;
  pairList.innerHTML = "";
  const grouped: Record<string, Dot[]> = {};
  state.dots.forEach(d => grouped[d.color] = grouped[d.color] ? [...grouped[d.color], d] : [d]);

   Object.entries(grouped).forEach(([color, dots]) => {
    const li = document.createElement("li");
    li.className = "flex items-center gap-2 text-sm";

    /* przycisk wybierający kolor */
    const pickBtn = document.createElement("button");
    pickBtn.className = "w-5 h-5 rounded border border-gray-700";
    pickBtn.style.backgroundColor = color;
    pickBtn.title = "Wybierz";
    pickBtn.addEventListener("click", () => pickColor(color));

    /* tekst współrzędnych */
    const txt = document.createElement("span");
    txt.textContent = dots.map(d => `(${d.row},${d.col})`).join(" – ");

    /* przycisk kasowania pary */
    const delBtn = document.createElement("button");
    delBtn.textContent = "✖";
    delBtn.className = "text-red-500 hover:text-red-400";
    delBtn.title = "Usuń parę";
    delBtn.addEventListener("click", () => removePair(color));

    li.append(pickBtn, txt, delBtn);
    pairList.appendChild(li);
  });
}

function rebuild() {
  buildGrid(
    gridContainer, state.rows, state.cols, state.dots,
    {
      editable: true,
      cellClick: onCellClick,
      cellSize: calcCellSize(gridWrapper, state.rows, state.cols),   // możesz zostawić dynamiczną funkcję
    }
  );
  updatePairList();
}


function showSuccessAnimation() {
  const toast = document.getElementById("saveSuccessToast");
  if (!toast) return;

  toast.style.opacity = "1";
  setTimeout(() => {
    toast.style.opacity = "0";
  }, 2500);
}

/* ──────────────────────────────────────────────── */
/*  CLICK HANDLER                                   */
function onCellClick(row: number, col: number, cell: HTMLElement) {
  const dot = state.dots.find(d => d.row === row && d.col === col);

  /* -- usuwanie pojedyncze, gdy kolor aktywny == kolor kropki -- */
  if (dot && dot.color === activeColor && !deleteMode) {
    state.dots = state.dots.filter(d => d !== dot);
    cell.innerHTML = "";
    cell.classList.remove("used");
    updatePairList();
    return;
  }

  /* -- masowy tryb usuwania -- */
  if (deleteMode && dot) {
    state.dots = state.dots.filter(d => d !== dot);
    cell.innerHTML = "";
    cell.classList.remove("used");
    updatePairList();
    return;
  }

  /* -- komunikat: pole zajęte -- */
  if (cell.classList.contains("used")) {
    alert("To pole jest już zajęte!");
    return;
  }

  /* -- limit 2 kropek tego samego koloru -- */
  const sameColor = state.dots.filter(d => d.color === activeColor);
  if (sameColor.length >= 2) {
    alert("Ten kolor ma już dwie kropki!");
    return;
  }

  /* -- dodaj kropkę -- */
  state.dots.push({ row, col, color: activeColor });
  paintDot(cell, activeColor);
  updatePairList();
}

function validateBeforeSave(): string | null {
  const title = (document.querySelector<HTMLInputElement>('input[name="title"]')?.value || "").trim();
  if (!title) return "Nazwa planszy nie może być pusta.";

  const counts: Record<string, number> = {};
  for (const dot of state.dots) {
    counts[dot.color] = (counts[dot.color] || 0) + 1;
  }

  const unpaired = Object.entries(counts)
    .filter(([_, count]) => count !== 2)
    .map(([color]) => color);

  if (unpaired.length > 0) {
    return `Kolor${unpaired.length > 1 ? "y" : ""} ${unpaired.join(", ")} nie ma${unpaired.length > 1 ? "ją" : ""} pary.`;
  }

  return null; // wszystko OK
}

/* ─── 1. Nowa pomocnicza funkcja buildHeaders() ─── */
function buildHeaders(): HeadersInit {
  const csrftoken =
    document.cookie.match(/csrftoken=([^;]+)/)?.[1] ??
    (document.querySelector('input[name="csrfmiddlewaretoken"]') as HTMLInputElement)?.value ??
    "";

  const authToken =
    (document.querySelector('meta[name="auth-token"]') as HTMLMetaElement)?.content;

  return {
    "Content-Type": "application/json",
    "X-CSRFToken": csrftoken,
    ...(authToken ? { Authorization: `Token ${authToken}` } : {}),
  };
}
/* ─── 2. Poprawione wywołanie fetch() ─── */
saveGridBtn.addEventListener("click", async () => {

  const validationError = validateBeforeSave();
  if (validationError) {
    alert("❌ Błąd: " + validationError);
    return;
  }

  const boardId = boardIdAttr
  const payload = {
    title: (document.querySelector<HTMLInputElement>('input[name="title"]')!).value,
    rows: Number(rowsInput.value),
    cols: Number(colsInput.value),
    dots: state.dots,
  };

  const url    = boardId ? `/api/boards/${boardId}/` : `/api/boards/`;
  const method = boardId ? "PATCH" : "POST";

  const res = await fetch(url, {
    method,
    headers: buildHeaders(),
    credentials: "include",      // ← DOKLEJA sessionid & csrftoken
    body: JSON.stringify(payload),
  });

  if (res.ok) {
    showSuccessAnimation()
    lastSavedDots = JSON.parse(JSON.stringify(state.dots)); // deep clone
    if (!boardId) {
      const data = await res.json();
      window.location.href = `/boards/${data.id}/edit`;
    }
  } else if (res.status === 403) {
    alert("Musisz być zalogowany!");
  } else {
    const err = await res.text();   // .json() może się nie sparsować
    alert("Błąd zapisu: " + err);
  }
});

/* ──────────────────────────────────────────────── */
/*  INPUT CHANGES & RESIZE                          */
[rowsInput, colsInput].forEach(inp =>
  inp.addEventListener("change", () => {
    state.rows = Number(rowsInput.value);
    state.cols = Number(colsInput.value);
    state.dots = state.dots.filter(d => d.row < state.rows && d.col < state.cols);
    rebuild();
}));

window.addEventListener("resize", rebuild);

/* ──────────────────────────────────────────────── */
/*  PALETTE & COLOR PICKER                          */
paletteBtns.forEach(btn =>
  btn.addEventListener("click", () => {
    activeColor = btn.dataset.color!;
    colorPicker.value = activeColor;
  })
);
colorPicker.addEventListener("input", e => {
  activeColor = (e.target as HTMLInputElement).value;
});

/* ──────────────────────────────────────────────── */
/*  DELETE TOGGLE (opcjonalny przycisk)             */
if (deleteToggle) {
  deleteToggle.addEventListener("click", () => {
    deleteMode = !deleteMode;
    deleteToggle.classList.toggle("opacity-50", deleteMode);
  });
}

/* ──────────────────────────────────────────────── */
/*  INIT                                            */
if (boardId) {
  loadBoard();
} else {
  rebuild(); // nowa plansza
}

window.addEventListener("beforeunload", (e) => {
  if (!isDirty()) return;

  e.preventDefault();
  e.returnValue = ""; // konieczne dla zgodności ze specyfikacją
});
// sse-notifications.ts – ver. 3
// Po zmianie: toast jest statyczny w base.html (id="notificationToast")
// i pojawia się w LEWYM dolnym rogu ekranu.
// Nie używamy Tailwinda – tło ustawiamy inline.
// =================================================

interface NotificationPayload {
  board_title?: string;  // alias dla nazwy planszy
  title?: string;        // ewent. inny alias
  board?: string;

  board_id?: number;

  path_name?: string;    // nazwa ścieżki
  path_id?: number;      // ID ścieżki

  owner_username?: string; // wykonawca akcji (alias primary)
}

type EventName =
  | "newBoard" | "boardUpdated" | "boardDeleted"
  | "newPath"  | "pathUpdated"  | "pathDeleted";

const ENDPOINT = "/sse/notifications/";

// ───────── statyczny element toastu ─────────
const toastEl = document.getElementById("notificationToast") as HTMLDivElement;
if (!toastEl) {
  console.error(
    "Nie znaleziono #notificationToast. Dodaj <div id='notificationToast' class='toast'></div> do base.html"
  );
}

function showToast(message: string, color: string, clickUrl: string | null) {
  if (!toastEl) return;
  toastEl.textContent = message;
  toastEl.style.backgroundColor = color;
  toastEl.style.display = "block";

  toastEl.onclick = clickUrl ? () => (window.location.href = clickUrl) : null;

  clearTimeout((toastEl as any)._hideTimer);
  (toastEl as any)._hideTimer = setTimeout(() => {
    toastEl.style.display = "none";
    toastEl.onclick = null;
  }, 3500);
}

function maybePushSystem(body: string) {
  if (!("Notification" in window)) return;
  if (Notification.permission === "granted") {
    new Notification(body);
  } else if (Notification.permission === "default") {
    Notification.requestPermission().then((perm) => {
      if (perm === "granted") new Notification(body);
    });
  }
}

function pick<T>(...vals: (T | undefined)[]): T | undefined {
  return vals.find((v) => v !== undefined);
}

function boardName(d: NotificationPayload) {
  return pick(d.title, d.board_title) ?? "(nieznana plansza)";
}

function userName(d: NotificationPayload) {
  return pick(
    d.owner_username
  ) ?? "Ktoś";
}

function pathName(d: NotificationPayload) {
  return pick(d.path_name) ?? "(ścieżka)";
}

function boardUrl(d: NotificationPayload): string | null {
  const id = pick(d.board_id);
  return id ? `/boards/${id}/` : null;
}

const MAP: Record<EventName, { color: string; msg: (d: NotificationPayload) => string }> = {
  newBoard:      { color: "#27ae60", msg: (d) => `🆕 ${userName(d)} utworzył planszę: ${boardName(d)}` },
  boardUpdated:  { color: "#f39c12", msg: (d) => `✏️ ${userName(d)} edytował planszę: ${boardName(d)}` },
  boardDeleted:  { color: "#e74c3c", msg: (d) => `🗑️ ${userName(d)} usunął planszę: ${boardName(d)}` },
  newPath:       { color: "#3498db", msg: (d) => `➕ ${userName(d)} dodał ścieżkę ${pathName(d)} na ${boardName(d)}` },
  pathUpdated:   { color: "#9b59b6", msg: (d) => `🔄 ${userName(d)} zaktualizował ścieżkę ${pathName(d)}` },
  pathDeleted:   { color: "#c0392b", msg: (d) => `❌ ${userName(d)} usunął ścieżkę ${pathName(d)}` },
};

function connect() {
  const es = new EventSource(ENDPOINT, { withCredentials: true });

  (Object.keys(MAP) as EventName[]).forEach((evtName) => {
    es.addEventListener(evtName, (evt) => {
      const data = JSON.parse((evt as MessageEvent).data) as NotificationPayload;
      const { color, msg } = MAP[evtName];
      const url = boardUrl(data);
      showToast(msg(data), color, url);
      maybePushSystem(msg(data));

     if (
        (evtName === "newBoard" || evtName === "boardDeleted") &&
        window.location.pathname === "/boards/"
      ) {
        setTimeout(() => window.location.reload(), 1800); // 1.8 sekundy
      }
    });
  });

  es.onerror = () => {
    es.close();
    setTimeout(connect, 5000);
  };
}

document.addEventListener("DOMContentLoaded", connect);

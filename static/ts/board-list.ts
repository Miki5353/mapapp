// board-list.ts
/**
 * Usuwanie planszy przez API (DELETE) z potwierdzeniem
 * Obsługuje zarówno wiersze (.js-row) jak i kafelki (.js-card)
 */

function getCSRF(): string {
  return document.cookie.match(/csrftoken=([^;]+)/)?.[1] || "";
}
function getAuthToken(): string | null {
  return (document.querySelector('meta[name="auth-token"]') as HTMLMetaElement)?.content || null;
}

async function deleteBoard(id: string): Promise<boolean> {
  const headers: HeadersInit = { "X-CSRFToken": getCSRF() };
  const token = getAuthToken();
  if (token) headers["Authorization"] = `Token ${token}`;

  const res = await fetch(`/api/boards/${id}/`, {
    method: "DELETE",
    headers,
    credentials: "include",
  });
  return res.ok;
}

/* delegacja zdarzeń */
document.addEventListener("click", async (e) => {
  const btn = (e.target as HTMLElement).closest<HTMLButtonElement>(".js-del");
  if (!btn || btn.disabled) return;

  const id = btn.closest<HTMLElement>(".js-row, .js-card")?.dataset.id;
  if (!id) return;
  if (!confirm("Usunąć tę planszę?")) return;

  if (await deleteBoard(id)) {
    // usuń element z DOM
    btn.closest(".js-row, .js-card")?.remove();
  } else {
    alert("Nie udało się usunąć planszy (błąd serwera).");
  }
});
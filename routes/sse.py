"""Server‑Sent Events (SSE) – **wersja z Redis pub/sub**
=========================================================

Ta wersja *routes/sse.py* publikuje zdarzenia domenowe (GameBoard, Route)
do kanału **Redis**.  Każdy worker Django/ASGI uruchamia własny wątek
listenera, który subskrybuje ten kanał i przekazuje odebrane wiadomości do
lokalnych kolejek klientów SSE.

• *Fan‑out* odbywa się centralnie w Redis, więc **N** procesów może współdzielić
  jeden strumień zdarzeń.
• Kod nadal działa na ``StreamingHttpResponse`` – można go hostować pod
  uvicorn / Daphne.
• W środowisku developerskim, gdy Redis nie jest dostępny, moduł automatycznie
  przełącza się na poprzedni tryb „in‑memory”.
"""
from __future__ import annotations

import json
import os
import queue
import threading
import time
from typing import Generator

import redis  # pip install redis>=5.0
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.http import HttpRequest, HttpResponse, StreamingHttpResponse
from django.utils.timezone import now

from .models import GameBoard, Route

# ---------------------------------------------------------------------------
# 1 – Konfiguracja Redis
# ---------------------------------------------------------------------------
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_CHANNEL = os.getenv("SSE_CHANNEL", "sse:events")

try:
    _redis = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    # Krótki test połączenia; rzuci wyjątek, jeśli brak serwera Redis.
    _redis.ping()
    _redis_available = True
except Exception:  # noqa: BLE001
    _redis_available = False

# ---------------------------------------------------------------------------
# 2 – Lokalne kolejki klientów (per proces)
# ---------------------------------------------------------------------------
_client_queues: list[queue.Queue[str]] = []
_clients_lock = threading.Lock()


def _fan_out_local(payload: str) -> None:
    """Wrzuca *payload* do kolejek klientów utrzymywanych przez ten proces."""
    with _clients_lock:
        for q in list(_client_queues):
            try:
                q.put_nowait(payload)
            except queue.Full:
                # Pomijamy komunikat dla *tego* klienta – jest zasypany.
                pass


# ---------------------------------------------------------------------------
# 3 – Publikowanie zdarzeń (globalne)
# ---------------------------------------------------------------------------

def _publish(payload: str) -> None:
    if _redis_available:
        _redis.publish(REDIS_CHANNEL, payload)
    else:
        # Tryb awaryjny – labowy in‑memory fallback.
        _fan_out_local(payload)


# ---------------------------------------------------------------------------
# 4 – Listener Redis → lokalny fan‑out
# ---------------------------------------------------------------------------

_listener_started = False


def _start_listener_once() -> None:
    global _listener_started  # noqa: PLW0603
    if _listener_started or not _redis_available:
        return

    def _listener() -> None:  # runs forever in background thread
        pubsub = _redis.pubsub()
        pubsub.subscribe(REDIS_CHANNEL)
        for msg in pubsub.listen():
            if msg.get("type") == "message":
                _fan_out_local(str(msg["data"]))

    threading.Thread(target=_listener, daemon=True, name="sse-redis-listener").start()
    _listener_started = True


# Start listener as soon as module is imported
_start_listener_once()

# ---------------------------------------------------------------------------
# 5 – Pomocnik SSE: serializacja + publish
# ---------------------------------------------------------------------------

def _sse(event: str, data: dict) -> None:
    message = f"event: {event}\n" f"data: {json.dumps(data, default=str)}\n\n"
    _publish(message)


# ---------------------------------------------------------------------------
# 6 – Sygnały Django → SSE
# ---------------------------------------------------------------------------
@receiver(post_save, sender=GameBoard)
def _board_saved(sender, instance: GameBoard, created: bool, **_):
    payload = {
        "board_id": instance.pk,
        "title": instance.title,
        "rows": instance.rows,
        "cols": instance.cols,
        "owner_username": instance.owner.username,
    }
    _sse("newBoard" if created else "boardUpdated", payload)


@receiver(post_delete, sender=GameBoard)
def _board_deleted(sender, instance: GameBoard, **_):
    _sse(
        "boardDeleted",
        {
            "board_id": instance.pk,
            "title": instance.title,
            "owner_username": instance.owner.username,
        },
    )


@receiver(post_save, sender=Route)
def _path_saved(sender, instance: Route, created: bool, **_):
    payload = {
        "path_id": instance.pk,
        "board_id": instance.background.pk,
        "board_title": instance.background.title,
        "owner_username": instance.owner.username,
        "path_name": instance.name,
    }
    _sse("newPath" if created else "pathUpdated", payload)


@receiver(post_delete, sender=Route)
def _path_deleted(sender, instance: Route, **_):
    _sse(
        "pathDeleted",
        {
            "path_id": instance.pk,
            "board_id": instance.background.pk,
            "board_title": instance.background.title,
            "owner_username": instance.owner.username,
        },
    )


# ---------------------------------------------------------------------------
# 7 – Django view: /sse/notifications/
# ---------------------------------------------------------------------------

def event_stream(request: HttpRequest) -> HttpResponse:  # pragma: no cover
    """Długotrwałe połączenie SSE."""
    _start_listener_once()  # pewność, że listener działa

    q: queue.Queue[str] = queue.Queue(maxsize=200)
    with _clients_lock:
        _client_queues.append(q)

    def _stream() -> Generator[str, None, None]:
        yield f": connected {now().isoformat()} via redis={'yes' if _redis_available else 'no'}\n\n"
        try:
            while True:
                try:
                    payload = q.get(timeout=15)
                except queue.Empty:
                    yield f": keep-alive {int(time.time())}\n\n"
                else:
                    yield payload
        finally:
            with _clients_lock:
                _client_queues.remove(q)

    resp = StreamingHttpResponse(_stream(), content_type="text/event-stream")
    resp["Cache-Control"] = "no-cache"
    return resp

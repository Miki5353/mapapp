# MapApp

> Kompletny projekt realizujący 3 zadanie z aplikacji WWW korzystając z **Django**.

---

## Spis treści

1. [Wymagania](#wymagania)
2. [Instalacja](#instalacja)
3. [Konfiguracja środowiska](#konfiguracja-środowiska)
4. [Uruchamianie aplikacji](#uruchamianie-aplikacji)
5. [Testy](#testy)
6. [Budowanie zasobów statycznych](#budowanie-zasobów-statycznych)
7. [Korzystanie z aplikacji](#korzystanie-zaplikacji-uiapi)

---

## Wymagania

| Narzędzie         | Wersja              |
| ----------------- | ------------------- |
| Python            | **3.11** lub nowszy |
| Node.js           | **20** lub nowszy   |
| pip / virtualenv  | aktualne            |
| (opc.) PostgreSQL | **14** lub nowszy   |

---

## Instalacja

```bash
# 1. Sklonuj repozytorium
git clone https://github.com/miki5353/mapapp.git
cd mapapp

# 2. Utwórz i aktywuj virtualenv
python3 -m venv venv
source venv/bin/activate            # Windows: venv\Scripts\activate

# 3. Zainstaluj zależności Pythona
pip install -r requirements.txt

# 4. Zainstaluj zależności front‑endowych (Tailwind, bundler itp.)
npm install
```

---

## Konfiguracja środowiska


| Zmienna                   | Opis                                                                                                                                          |
| ------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| `SECRET_KEY`              | Wygenerowany klucz Django (użyj `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`) |
| `DEBUG`                   | `1` (dev) lub `0` (prod)                                                                                                                      |
| `ALLOWED_HOSTS`           | Lista hostów/domen oddzielona przecinkami                                                                                                     |
| `DATABASE_URL`            | URL zgodny z `dj-database-url` (np. `postgres://user:pass@localhost:5432/mydb`)                                                               |

```bash
# wygeneruj nowy klucz (jeżeli nie istnieje, to django wygeneruje automatycznie)
export DJANGO_SECRET_KEY=$(python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")

export DJANGO_DEBUG=1
export DJANGO_ALLOWED_HOSTS="127.0.0.1,localhost"
```
---

## Uruchamianie aplikacji

```bash
# 1. Nałóż migracje bazy danych
python manage.py migrate

# 2. (opcjonalnie) utwórz superużytkownika
python manage.py createsuperuser

# 3. Włącz serwer developerski
python manage.py runserver               # domyślnie 127.0.0.1:8000
# lub na innym porcie
python manage.py runserver 0.0.0.0:9000
```

Aplikacja będzie dostępna pod `http://localhost:8000/` (lub wskazanym porcie). Logi wyświetlą się w terminalu; zamknij serwer klawiszami *Ctrl+C*.

---

## Testy

Projekt korzysta z wbudowanego test‑runnera Django:


```bash
# uruchom wszystkie testy jednostkowe
python manage.py test
```



---

## Budowanie zasobów statycznych

Pliki źródłowe CSS/JS/obrazki trzymamy w `static/`. Tailwind + bundler (np. Parcel, Vite) generują finalne paczki do `dist/`, a potem Django przenosi je do `staticfiles/`.

```bash
# Dev – rebuild przy zapisie
npm run dev

# Prod – minifikacja i hashy w nazwach
npm run build

# Kopiowanie do STATIC_ROOT
python manage.py collectstatic
```
---

## Korzystanie z aplikacji (UI + API)

### 1. Mapa (interfejs graficzny)

| Operacja                    | Jak to zrobić?                                   |
|-----------------------------|--------------------------------------------------|
| **Dodaj punkt**             | kliknij dowolne miejsce na mapie → pojawi się nowy marker |
| **Przesuń punkt**           | złap marker i przeciągnij go (drag & drop)       |
| **Usuń punkt**              | kliknij istniejący marker → potwierdź w oknie dialogowym |

Zmiany zapisują się automatycznie poprzez wywołania REST‑API w tle – nie musisz odświeżać strony.

---

### 2. Admin

Menu admina jest dostępne pod `/admin/` po zalogowaniu na konto administratora. Można tam zarządzać użytkownikami oraz dodawać obrazy tła (zalecam dodać jakiś obraz tła by móc przetestować aplikację).

---

### 3. REST‑API

| End‑point                | Metoda | Opis                                                |
|--------------------------|--------|-----------------------------------------------------|
| `/api/routes/`           | GET    | lista tras                                          |
| `/api/routes/`           | POST   | utwórz nową trasę (`name`, `background`)            |
| `/api/routes/<id>/`      | GET    | szczegóły wybranej trasy                            |
| `/api/routes/<id>/`      | PUT    | aktualizacja całej trasy                            |
| `/api/routes/<id>/`      | PATCH  | aktualizacja części trasy                           |
| `/api/routes/<id>/`      | DELETE | usunięcie trasy                                     |

| End‑point                           | Metoda  | Opis                                    |
|-------------------------------------|---------|-----------------------------------------|
| `/api/routes/<route_pk>/points/`    | GET     | lista punktów dla danej trasy           |
| `/api/routes/<route_pk>/points/`    | POST    | dodaj punkt do trasy                    |
| `/api/routes/<route_pk>/points/<id>`| GET     | szczegóły konkretnego punktu            |
| `/api/routes/<route_pk>/points/<id>`| PATCH   | przesuń punkt                           |
| `/api/routes/<route_pk>/points/<id>`| DELETE  | usuń punkt                              |

> **Autoryzacja:** nagłówek `Authorization: Token <TWÓJ_TOKEN>`
> (patrz poniżej, jak wygenerować token).

---

### 4. Interaktywna dokumentacja

*Swagger UI* dostępny jest pod adresem: **`/api/docs`**
Po prawej stronie wprowadź token (pole „Authorize”), aby wywoływać end‑pointy bezpośrednio z przeglądarki.

---

### 5. Jak nadać token API użytkownikowi

```bash
python manage.py drf_create_token <nazwa_użytkownika>
```

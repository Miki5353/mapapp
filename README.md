# MyDjangoProject

> Kompletny projekt **Django 5 + Tailwind CSS**. Repozytorium zawiera wyłącznie kod źródłowy – wszystkie zależności są pobierane z `requirements.txt` i `package.json`, a pliki generowane (np. `staticfiles/`, `node_modules/`) zostały wyłączone w `.gitignore`. Dzięki temu projekt można odtworzyć w kilku prostych krokach.

---

## Spis treści

1. [Wymagania](#wymagania)
2. [Instalacja](#instalacja)
3. [Konfiguracja środowiska](#konfiguracja-środowiska)
4. [Uruchamianie aplikacji](#uruchamianie-aplikacji)
5. [Testy](#testy)
6. [Budowanie zasobów statycznych](#budowanie-zasobów-statycznych)

---

## Wymagania

| Narzędzie         | Wersja mínima       |
| ----------------- | ------------------- |
| Python            | **3.11** lub nowszy |
| Node.js           | **20** lub nowszy   |
| pip / virtualenv  | aktualne            |
| (opc.) PostgreSQL | **14** lub nowszy   |

---

## Instalacja

```bash
# 1. Sklonuj repozytorium
git clone https://github.com/TwojeKonto/my-django-project.git
cd my-django-project

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

1. **Skopiuj domyślny plik konfiguracyjny** i uzupełnij go:

   ```bash
   cp .env.example .env
   ```
2. **Kluczowe zmienne** do ustawienia:

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

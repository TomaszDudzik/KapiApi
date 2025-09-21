[app]
# Nazwa wyświetlana pod ikonką
title = KPI Dashboard

# Nazwa paczki (bez spacji, małe litery)
package.name = kpi_dashboard

# Odwrócona domena (może być dowolna)
package.domain = org.example

# Główne źródło kodu (tam gdzie jest main.py)
source.dir = .
source.include_exts = py

# Wersja aplikacji
version = 0.1

# Biblioteki potrzebne do działania
requirements = python3,kivy,kivy_garden.graph,requests

# Orientacja ekranu
orientation = portrait

# Ikona (opcjonalnie możesz dodać własną .png)
# icon.filename = %(source.dir)s/icon.png

# Nazwa entrypointa (main.py → app = KpiApp())
entrypoint = main.py

# Jeżeli chcesz ustawić zmienne środowiskowe w apce (np. adres backendu):
android.add_env_vars = API_URL=http://192.168.0.213:8000

android.permissions = INTERNET

[buildozer]
# Poziom logów (2 = normalny, 1 = minimalny, 0 = cisza)
log_level = 2

# Nie pokazuj ostrzeżeń o uruchamianiu jako root
warn_on_root = 0

# API Androida (ustaw na 35 albo najnowsze wspierane przez buildozer)
android.api = 35

# Minimalne API Androida
android.minapi = 21

# Docelowa architektura CPU (możesz zostawić domyślną)
# android.archs = armeabi-v7a, arm64-v8a

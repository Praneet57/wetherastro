# Real-Time Weather Dashboard

A weather app built with FastAPI that pulls live data from the OpenWeatherMap API. Search any city and get current conditions, a 24-hour forecast, and a history of your recent searches stored in MySQL.

---

## What it does

- Search weather for any city in the world
- Shows temperature, feels like, humidity, wind speed, pressure, visibility
- Sunrise and sunset times
- 24-hour forecast with icons
- Last 10 searches saved to the database and shown in the UI
- Quick-access buttons for common cities

---

## Stack

- **Backend** — FastAPI + httpx (async API calls)
- **Database** — MySQL + SQLAlchemy (for search history)
- **External API** — OpenWeatherMap
- **Frontend** — Bootstrap 5, vanilla JS
- **Deployment** — Docker + Docker Compose

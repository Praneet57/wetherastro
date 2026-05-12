from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import engine, get_db
from typing import Optional
import models, httpx, os

import time, sqlalchemy

for attempt in range(10):
    try:
        models.Base.metadata.create_all(bind=engine)
        print("✅ DB connected!")
        break
    except sqlalchemy.exc.OperationalError:
        print(f"⏳ DB not ready, retrying ({attempt+1}/10)...")
        time.sleep(3)

app = FastAPI(title="Real-Time Weather Dashboard", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")

OWM_API_KEY = os.getenv("OWM_API_KEY", "your_openweathermap_api_key_here")
OWM_BASE = "https://api.openweathermap.org/data/2.5"

class WeatherResponse(BaseModel):
    city: str
    country: str
    temperature: float
    feels_like: float
    humidity: int
    wind_speed: float
    description: str
    icon: str
    visibility: Optional[int] = None
    pressure: int
    sunrise: int
    sunset: int

@app.get("/")
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/weather", response_model=WeatherResponse)
async def get_weather(city: str, db: Session = Depends(get_db)):
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                f"{OWM_BASE}/weather",
                params={"q": city, "appid": OWM_API_KEY, "units": "metric"},
                timeout=10
            )
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Weather service unreachable")

    if resp.status_code == 404:
        raise HTTPException(status_code=404, detail=f"City '{city}' not found")
    if resp.status_code == 401:
        raise HTTPException(status_code=401, detail="Invalid API key. Set OWM_API_KEY env variable.")
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail="Failed to fetch weather data")

    data = resp.json()
    result = WeatherResponse(
        city=data["name"],
        country=data["sys"]["country"],
        temperature=round(data["main"]["temp"], 1),
        feels_like=round(data["main"]["feels_like"], 1),
        humidity=data["main"]["humidity"],
        wind_speed=data["wind"]["speed"],
        description=data["weather"][0]["description"].capitalize(),
        icon=data["weather"][0]["icon"],
        visibility=data.get("visibility"),
        pressure=data["main"]["pressure"],
        sunrise=data["sys"]["sunrise"],
        sunset=data["sys"]["sunset"],
    )

    # Save to history
    history = models.SearchHistory(
        city=result.city, country=result.country,
        temperature=result.temperature, description=result.description
    )
    db.add(history)
    db.commit()

    return result

@app.get("/forecast")
async def get_forecast(city: str):
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{OWM_BASE}/forecast",
            params={"q": city, "appid": OWM_API_KEY, "units": "metric", "cnt": 8},
            timeout=10
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Forecast unavailable")
    data = resp.json()
    return [
        {
            "time": item["dt_txt"],
            "temp": round(item["main"]["temp"], 1),
            "description": item["weather"][0]["description"].capitalize(),
            "icon": item["weather"][0]["icon"],
            "humidity": item["main"]["humidity"],
        }
        for item in data["list"]
    ]

@app.get("/history")
def get_history(db: Session = Depends(get_db)):
    records = db.query(models.SearchHistory).order_by(
        models.SearchHistory.searched_at.desc()
    ).limit(10).all()
    return [
        {"city": r.city, "country": r.country, "temperature": r.temperature,
         "description": r.description, "searched_at": r.searched_at}
        for r in records
    ]

@app.get("/health")
def health():
    return {"status": "ok", "app": "WeatherDashboard"}

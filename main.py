from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

app.add_middleware(
CORSMiddleware,
allow_origins=["*"],
allow_methods=["*"],
allow_headers=["*"],
)

if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

@app.api_route("/", methods=["GET", "HEAD"])
def home():
    p = os.path.join("static", "index.html")
    if os.path.exists(p):
        return FileResponse(p)
    return {"status": "live"}

@app.get("/api/products")
def products():
    return [
        {"id":1,"name":"Coca Cola 500ml","price":70,"stock":120,"barcode":"5449000000996"},
        {"id":2,"name":"Bread 400g","price":65,"stock":50,"barcode":"6161100123"},
        {"id":3,"name":"Milk 500ml","price":60,"stock":80,"barcode":"6001234567890"},
        {"id":4,"name":"Soda Fanta 500ml","price":70,"stock":90,"barcode":"5449000000997"},
    ]

@app.get("/api/attendance")
def attendance():
    return [
        {"name":"Marlon Kikuyu","days":26,"balance":14},
        {"name":"Lavinah Boke","days":26,"balance":0},
    ]

@app.api_route("/api/health", methods=["GET","HEAD"])
def health():
    return {"ok":True}

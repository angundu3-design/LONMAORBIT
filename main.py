from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(title="LONMA ORBIT v2.3")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Serve static folder if exists
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# FIX FOR HEAD 405 - Handle both GET and HEAD
@app.api_route("/", methods=["GET", "HEAD"])
def root():
    path = os.path.join("static", "index.html")
    if os.path.exists(path):
        return FileResponse(path)
    return {"status": "LONMA ORBIT API v2.3 LIVE", "docs": "/docs"}

@app.get("/api/health")
@app.head("/api/health")
def health():
    return {"ok": True}

@app.get("/api/products")
def products():
    return [{"id":1,"name":"Coca 500ml","price":70,"barcode":"5449000000996"}]

@app.get("/api/users")
def users():
    return [{"username":"admin"}]

@app.get("/api/attendance")
def att():
    return [{"name":"Marlon","days":26}]


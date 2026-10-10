# main.py - LONMA ORBIT v2.3 - FIXED FOR RENDER
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(title="LONMA ORBIT v2.3", version="2.3.0")

# Allow frontend to call backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- SERVE WEBSITE ---
# This must be BEFORE api routes mount
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def serve_website():
    index_path = os.path.join("static", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {
        "status": "LONMA ORBIT API LIVE",
        "website": "static/index.html not found",
        "docs": "/docs",
        "health": "/api/health"
    }

# --- YOUR API ROUTES ---
@app.get("/api/health")
def health_check():
    return {"ok": True, "service": "LONMA ORBIT", "port": 10000}

@app.get("/api/users")
def get_users():
    # Replace with your real DB logic later
    return [
        {"id": 1, "username": "admin", "role": "admin"},
        {"id": 2, "username": "cashier1", "role": "cashier"}
    ]

@app.get("/api/products")
def get_products():
    return [
        {"id": 1, "name": "Coca 500ml", "price": 70, "stock": 100, "barcode": "5449000000996"},
        {"id": 2, "name": "Bread 400g", "price": 65, "stock": 50, "barcode": "6161100123"},
    ]

@app.get("/api/attendance")
def get_attendance():
    return [
        {"name": "Marlon Kikuyu Ang'undu", "days": 26, "balance": 14},
        {"name": "Lavinah Boke Maroa", "days": 26, "balance": 0},
    ]

# --- IMPORT YOUR EXISTING ROUTES IF YOU HAVE THEM ---
# Uncomment these if you have files in /routes/
try:
    from routes import products as products_route
    app.include_router(products_route.router, prefix="/api/products2", tags=["products"])
except Exception as e:
    print(f"Note: routes/products not loaded: {e}")

try:
    import auth
    app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
except Exception as e:
    print(f"Note: auth not loaded: {e}")

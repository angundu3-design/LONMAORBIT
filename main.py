from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn, os

app = FastAPI(title="LONMA ORBIT v2.3")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory DB (replace with Postgres later)
products = [
    {"id":1, "name":"Soda - Coca 500ml", "price":70, "stock":100, "barcode":"5449000000996"},
    {"id":2, "name":"Bread - 400g", "price":65, "stock":50, "barcode":"6161100123"},
]

users = [{"username":"admin","password":"Lonma@2026","role":"admin"}]

attendance = [
    {"name":"Marlon Kikuyu Ang'undu", "days":26, "taken":7, "balance":14, "status":"Active"},
    {"name":"Lavinah Boke Maroa", "days":26, "taken":21, "balance":0, "status":"Active"},
    {"name":"Sarah Muhia Wanjiku", "days":9, "taken":17, "balance":7, "status":"On Leave"},
]

class ProductIn(BaseModel):
    name: str
    price: float
    stock: int
    barcode: str

@app.get("/")
def home(): return {"status":"LONMA ORBIT v2.3 LIVE","url":"https://app.lonmaorbit.co.ke"}

@app.get("/api/products")
def get_products(): return products

@app.post("/api/products")
def add_product(p: ProductIn):
    products.append({**p.dict(), "id":len(products)+1})
    return {"message":"Added","barcode":p.barcode}

@app.get("/api/products/barcode/{code}")
def get_by_barcode(code: str):
    for prod in products:
        if prod["barcode"] == code: return prod
    raise HTTPException(404, "Product not found")

@app.get("/api/users")
def get_users(): return users

@app.get("/api/attendance")
def get_attendance(): return attendance

@app.get("/api/health")
def health(): return {"ok":True}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)

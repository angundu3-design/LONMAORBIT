from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

app = FastAPI()

USERS = {
 "admin": {"username":"admin","email":"admin@lonmaorbit.co.ke","password":"Lonma@2026","name":"Admin"},
 "Mongelah": {"username":"Mongelah","email":"mongelah@lonmaorbit.co.ke","password":"1234","name":"Mongelah"},
}

PRODUCTS = [
 {"id":1,"name":"Rice 2kg Pishori","price":280,"cat":"Food","stock":100},
 {"id":2,"name":"Cooking Oil 1L","price":220,"cat":"Food","stock":80},
 {"id":3,"name":"Sugar 2kg","price":310,"cat":"Food","stock":90},
 {"id":4,"name":"Bread 400g","price":60,"cat":"Food","stock":50},
 {"id":5,"name":"Milk 500ml","price":60,"cat":"Food","stock":100},
 {"id":6,"name":"Eggs Tray 30pcs","price":650,"cat":"Food","stock":40},
 {"id":11,"name":"Extension 4-Way","price":850,"cat":"Electronics","stock":25},
 {"id":12,"name":"LED Bulb 12W","price":250,"cat":"Electronics","stock":100},
 {"id":13,"name":"Phone Charger Fast","price":650,"cat":"Electronics","stock":40},
 {"id":14,"name":"Power Bank 10000mAh","price":1800,"cat":"Electronics","stock":15},
 {"id":19,"name":"T-Shirt Unisex","price":450,"cat":"Clothes","stock":60},
 {"id":20,"name":"Trouser Jeans","price":1200,"cat":"Clothes","stock":35},
 {"id":21,"name":"Socks Pair","price":100,"cat":"Clothes","stock":150},
 {"id":26,"name":"Soda 500ml","price":60,"cat":"Drinks","stock":200},
 {"id":27,"name":"Water 1L","price":50,"cat":"Drinks","stock":300},
 {"id":28,"name":"Juice 1L","price":150,"cat":"Drinks","stock":80},
 {"id":29,"name":"Energy Drink 500ml","price":120,"cat":"Drinks","stock":60},
]

@app.get("/")
def root():
    return FileResponse("static/index.html")

@app.get("/api/products")
def get_products(cat: str = None):
    if cat and cat!= "All":
        return [p for p in PRODUCTS if p["cat"]==cat]
    return PRODUCTS

@app.post("/api/register")
def register(data: dict):
    u = data.get("username","").strip()
    e = data.get("email","").strip()
    if not u or not e:
        return {"ok":False,"error":"Missing"}
    USERS[u]=data
    USERS[e]=data
    return {"ok":True}

@app.post("/api/login")
def login(data: dict):
    key = data.get("username","").strip()
    pw = data.get("password","").strip()
    for v in USERS.values():
        if (v.get("email")==key or v.get("username")==key) and v.get("password")==pw:
            return {"ok":True,"username":v["username"],"email":v["email"]}
    return {"ok":False}

@app.post("/api/call/offer")
def call_offer(data: dict):
    return {"ok":True}

if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

app = FastAPI()

USERS = {
 "admin": {"username":"admin","email":"admin@lonmaorbit.co.ke","password":"Lonma@2026","name":"Admin","outlet":"Admin"},
 "Mongelah": {"username":"Mongelah","email":"mongelah@lonmaorbit.co.ke","password":"1234","name":"Mongelah","outlet":"Isibania"},
}

# SUPERMARKET PRODUCTS - 4 Categories
PRODUCTS = [
 # 1. FOOD
 {"id":1,"name":"Rice 2kg Pishori","price":280,"cat":"Food","stock":100},
 {"id":2,"name":"Cooking Oil 1L","price":220,"cat":"Food","stock":80},
 {"id":3,"name":"Sugar 2kg Kabras","price":310,"cat":"Food","stock":90},
 {"id":4,"name":"Maize Flour 2kg","price":155,"cat":"Food","stock":120},
 {"id":5,"name":"Bread 400g","price":60,"cat":"Food","stock":50},
 {"id":6,"name":"Milk 500ml Fresh","price":60,"cat":"Food","stock":100},
 {"id":7,"name":"Eggs Tray 30pcs","price":650,"cat":"Food","stock":40},
 {"id":8,"name":"Salt 1kg","price":45,"cat":"Food","stock":200},
 {"id":9,"name":"Tea Leaves 250g","price":180,"cat":"Food","stock":70},
 {"id":10,"name":"Wheat Flour 2kg","price":185,"cat":"Food","stock":60},

 # 2. ELECTRONICS
 {"id":11,"name":"Extension 4-Way","price":850,"cat":"Electronics","stock":25},
 {"id":12,"name":"LED Bulb 12W","price":250,"cat":"Electronics","stock":100},
 {"id":13,"name":"Phone Charger Fast","price":650,"cat":"Electronics","stock":40},
 {"id":14,"name":"Power Bank 10000mAh","price":1800,"cat":"Electronics","stock":15},
 {"id":15,"name":"Torch Rechargeable","price":750,"cat":"Electronics","stock":30},
 {"id":16,"name":"Radio Small","price":1200,"cat":"Electronics","stock":10},
 {"id":17,"name":"Electric Kettle","price":1650,"cat":"Electronics","stock":12},
 {"id":18,"name":"Iron Box","price":1950,"cat":"Electronics","stock":8},

 # 3. CLOTHES
 {"id":19,"name":"T-Shirt Unisex","price":450,"cat":"Clothes","stock":60},
 {"id":20,"name":"Trouser Jeans","price":1200,"cat":"Clothes","stock":35},
 {"id":21,"name":"Socks Pair","price":100,"cat":"Clothes","stock":150},
 {"id":22,"name":"Cap Base","price":350,"cat":"Clothes","stock":40},
 {"id":23,"name":"Leso / Khanga","price":550,"cat":"Clothes","stock":30},
 {"id":24,"name":"School Shirt White","price":600,"cat":"Clothes","stock":25},
 {"id":25,"name":"Belt Leather","price":450,"cat":"Clothes","stock":20},

 # 4. DRINKS
 {"id":26,"name":"Soda 500ml Coke/Fanta","price":60,"cat":"Drinks","stock":200},
 {"id":27,"name":"Water 1L","price":50,"cat":"Drinks","stock":300},
 {"id":28,"name":"Juice 1L Mango","price":150,"cat":"Drinks","stock":80},
 {"id":29,"name":"Energy Drink 500ml","price":120,"cat":"Drinks","stock":60},
 {"id":30,"name":"Yoghurt 500ml","price":90,"cat":"Drinks","stock":70},
 {"id":31,"name":"Beer Tusker 500ml","price":180,"cat":"Drinks","stock":100},
 {"id":32,"name":"Wine 750ml","price":850,"cat":"Drinks","stock":20},
]

OUTLETS = [
 {"id":"isibania","name":"Isibania"},
 {"id":"migori","name":"Migori"},
 {"id":"sirare","name":"Sirare"},
 {"id":"warehouse","name":"Warehouse"},
]

CALLS = {"offers":{},"answers":{},"ices":{}}

@app.get("/")
def root():
    return FileResponse("static/index.html")

@app.get("/api/products")
def get_products(cat: str = None):
    if cat and cat!= "All":
        return [p for p in PRODUCTS if p["cat"]==cat]
    return PRODUCTS

@app.get("/api/outlets")
def get_outlets():
    return OUTLETS

@app.post("/api/register")
def register(data: dict):
    u = data.get("username","").strip()
    e = data.get("email","").strip()
    if not u or not e:
        return {"ok":False,"error":"Missing fields"}
    USERS[u]=data
    USERS[e]=data
    return {"ok":True}

@app.post("/api/login")
def login(data: dict):
    key = data.get("username","").strip()
    pw = data.get("password","").strip()
    user = USERS.get(key)
    if user and user.get("password")==pw:
        return {"ok":True,"username":user["username"],"email":user["email"]}
    for v in USERS.values():
        if (v.get("email")==key or v.get("username")==key) and v.get("password")==pw:
            return {"ok":True,"username":v["username"],"email":v["email"]}
    return {"ok":False,"error":"Invalid"}

@app.post("/api/forgot")
def forgot(data: dict):
    return {"ok":True}

@app.post("/api/call/offer")
def call_offer(data: dict):
    CALLS["offers"][data.get("room","lonma-main")]=data.get("offer")
    return {"ok":True}

@app.get("/api/call/answer")
def call_answer(room: str):
    return {"answer":CALLS["answers"].get(room)}

@app.post("/api/call/answer")
def call_answer_post(data: dict):
    CALLS["answers"][data.get("room","lonma-main")]=data.get("answer")
    return {"ok":True}

if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

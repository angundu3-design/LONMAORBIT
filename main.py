from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

app = FastAPI()

# --- USERS DB with Email ---
USERS = {
 "admin": {"username":"admin","email":"admin@lonmaorbit.co.ke","password":"Lonma@2026","name":"Admin","outlet":"Admin"},
 "Mongelah": {"username":"Mongelah","email":"mongelah@lonmaorbit.co.ke","password":"1234","name":"Mongelah","outlet":"Isibania"},
 "cashier1": {"username":"cashier1","email":"cashier1@lonmaorbit.co.ke","password":"1234","name":"Cashier","outlet":"Isibania"},
 "outlet1": {"username":"outlet1","email":"outlet1@lonmaorbit.co.ke","password":"1234","name":"Outlet","outlet":"Migori"},
}

PRODUCTS = [
 {"id":1,"name":"Print A4 Black","price":10},
 {"id":2,"name":"Photocopy","price":5},
 {"id":3,"name":"Lamination","price":50},
 {"id":4,"name":"Binding","price":100},
 {"id":5,"name":"Passport Photo","price":150},
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
def get_products():
    return PRODUCTS

@app.get("/api/outlets")
def get_outlets():
    return OUTLETS

@app.post("/api/register")
def register(data: dict):
    u = data.get("username","").strip()
    e = data.get("email","").strip()
    if not u or not e:
        return {"ok":False,"error":"Missing username/email"}
    if u in USERS:
        return {"ok":False,"error":"Username exists"}
    USERS[u] = data
    USERS[e] = data
    return {"ok":True}

@app.post("/api/login")
def login(data: dict):
    key = data.get("username","").strip()
    pw = data.get("password","").strip()
    user = USERS.get(key)
    if user and user.get("password")==pw:
        return {"ok":True,"username":user["username"],"email":user["email"]}
    for k,v in USERS.items():
        if (v.get("email")==key or v.get("username")==key) and v.get("password")==pw:
            return {"ok":True,"username":v["username"],"email":v["email"]}
    return {"ok":False,"error":"Invalid credentials"}

@app.post("/api/forgot")
def forgot(data: dict):
    email = data.get("email","")
    return {"ok":True,"msg":f"If {email} exists, reset link sent"}

@app.post("/api/call/offer")
def call_offer(data: dict):
    room = data.get("room","lonma-main")
    CALLS["offers"][room] = data.get("offer")
    return {"ok":True}

@app.get("/api/call/answer")
def call_answer(room: str):
    ans = CALLS["answers"].get(room)
    return {"answer":ans}

@app.post("/api/call/answer")
def call_answer_post(data: dict):
    room = data.get("room","lonma-main")
    CALLS["answers"][room] = data.get("answer")
    return {"ok":True}

@app.post("/api/call/ice")
def call_ice(data: dict):
    room = data.get("room","lonma-main")
    if room not in CALLS["ices"]:
        CALLS["ices"][room]=[]
    CALLS["ices"][room].append(data.get("candidate"))
    return {"ok":True}

@app.get("/api/call/ice")
def call_ice_get(room: str):
    return {"candidates": CALLS["ices"].get(room,[])}

# Static files
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
app = FastAPI()
calls = {"offers":{}, "answers":{}, "ices":{}}
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

@app.api_route("/", methods=["GET","HEAD"])
def home():
    p=os.path.join("static","index.html")
    if os.path.exists(p):
        return FileResponse(p)
    return {"status":"live"}

@app.get("/api/products")
def products():
    return [
        {"id":1,"name":"Coca Cola 500ml","price":70,"stock":120,"barcode":"5449000000996"},
        {"id":2,"name":"Bread 400g","price":65,"stock":50,"barcode":"6161100123"},
        {"id":3,"name":"Milk 500ml","price":60,"stock":80,"barcode":"6001234567890"},
        {"id":4,"name":"Fanta 500ml","price":70,"stock":90,"barcode":"5449000000997"},
    ]

@app.get("/api/outlets")
def outlets():
    return [
        {"id":1,"name":"LONMA Main - Isibania","location":"Isibania Town","staff":5},
        {"id":2,"name":"LONMA Branch - Migori","location":"Migori CBD","staff":3},
        {"id":3,"name":"LONMA Branch - Sirare","location":"Sirare Border","staff":2},
        {"id":4,"name":"LONMA Warehouse","location":"Kehancha","staff":4},
    ]

@app.get("/api/attendance")
def attendance():
    return [{"name":"Marlon Kikuyu","days":26,"balance":14},{"name":"Lavinah Boke","days":26,"balance":0}]

@app.post("/api/call/offer")
def call_offer(data: dict):
    calls["offers"][data["room"]] = data["offer"]
    calls["ices"].setdefault(data["room"], [])
    return {"ok":True}

@app.get("/api/call/offer")
def get_offer(room: str):
    return {"offer": calls["offers"].get(room)}

@app.post("/api/call/answer")
def call_answer(data: dict):
    calls["answers"][data["room"]] = data["answer"]
    return {"ok":True}

@app.get("/api/call/answer")
def get_answer(room: str):
    return {"answer": calls["answers"].get(room)}

@app.post("/api/call/ice")
def post_ice(data: dict):
    calls["ices"].setdefault(data["room"], []).append(data["candidate"])
    return {"ok":True}

@app.get("/api/call/ice")
def get_ice(room: str):
    return calls["ices"].get(room, [])

@app.api_route("/api/health", methods=["GET","HEAD"])
def health():
    return {"ok":True}

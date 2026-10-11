from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
app=FastAPI()
calls={"offers":{},"answers":{},"ices":{}}
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")
@app.api_route("/",methods=["GET","HEAD"])
def home():
    p=os.path.join("static","index.html")
    return FileResponse(p) if os.path.exists(p) else {"status":"live"}
@app.get("/api/products")
def products():
    return [{"id":1,"name":"Coca Cola 500ml","price":70,"stock":120,"barcode":"5449000000996"},{"id":2,"name":"Bread 400g","price":65,"stock":50,"barcode":"6161100123"},{"id":3,"name":"Milk 500ml","price":60,"stock":80,"barcode":"6001234567890"},{"id":4,"name":"Fanta 500ml","price":70,"stock":90,"barcode":"5449000000997"}]
@app.get("/api/outlets")
def outlets():
    return [{"id":1,"name":"Isibania Main","location":"Isibania","staff":5},{"id":2,"name":"Migori","location":"Migori CBD","staff":3},{"id":3,"name":"Sirare","location":"Sirare","staff":2},{"id":4,"name":"Warehouse","location":"Kehancha","staff":4}]
@app.get("/api/attendance")
def attendance():
    return [{"name":"Marlon","days":26,"balance":14}]
@app.post("/api/call/offer")
def co(d:dict):
    calls["offers"][d["room"]]=d["offer"];calls["ices"].setdefault(d["room"],[]);return{"ok":True}
@app.get("/api/call/offer")
def go(room:str):
    return{"offer":calls["offers"].get(room)}
@app.post("/api/call/answer")
def ca(d:dict):
    calls["answers"][d["room"]]=d["answer"];return{"ok":True}
@app.get("/api/call/answer")
def ga(room:str):
    return{"answer":calls["answers"].get(room)}
@app.post("/api/call/ice")
def ci(d:dict):
    calls["ices"].setdefault(d["room"],[]).append(d["candidate"]);return{"ok":True}
@app.get("/api/call/ice")
def gi(room:str):
    return calls["ices"].get(room,[])
@app.api_route("/api/health",methods=["GET","HEAD"])
def h():
    return{"ok":True}

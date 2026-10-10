from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
app = FastAPI()
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
        {"id":5,"name":"Azam Wheat 2kg","price":185,"stock":60,"barcode":"6001001234567"},
        {"id":6,"name":"Cooking Oil 1L","price":320,"stock":40,"barcode":"6002007654321"},
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
    return [
        {"name":"Marlon Kikuyu","days":26,"balance":14},
        {"name":"Lavinah Boke","days":26,"balance":0},
        {"name":"John Cashier","days":24,"balance":2},
        {"name":"Mary Outlet1","days":26,"balance":5},
    ]

@app.api_route("/api/health", methods=["GET","HEAD"])
def health():
    return {"ok":True}

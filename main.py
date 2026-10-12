from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI()

class Login(BaseModel):
 username: str
 password: str

class Pay(BaseModel):
 phone: str
 amount: int

class Chat(BaseModel):
 msg: str

PRODUCTS = [
 {"id":1,"name":"Fresh Fri 5L","price":850,"code":"FF-5L-001","cat":"Cooking Oil","img":"https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=400"},
 {"id":2,"name":"Fresh Fri 2L","price":400,"code":"FF-2L-002","cat":"Cooking Oil","img":"https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=400"},
 {"id":3,"name":"Fresh Fri 1L","price":220,"code":"FF-1L-003","cat":"Cooking Oil","img":"https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=400"},
 {"id":4,"name":"Salt 2kg","price":180,"code":"SLT-2KG-005","cat":"Groceries","img":"https://images.unsplash.com/photo-1584305574586-0a9579496bb7?w=400"},
 {"id":5,"name":"Salt 1kg","price":100,"code":"SLT-1KG-006","cat":"Groceries","img":"https://images.unsplash.com/photo-1584305574586-0a9579496bb7?w=400"},
 {"id":6,"name":"Detox Tea","price":1200,"code":"DTX-001","cat":"Wellness","img":"https://images.unsplash.com/photo-1576092768241-dec231879fc3?w=400"},
 {"id":7,"name":"Green Tea","price":250,"code":"DTX-020","cat":"Wellness","img":"https://images.unsplash.com/photo-1576092768241-dec231879fc3?w=400"},
 {"id":8,"name":"Sawa Men 500ML","price":450,"code":"SWA-MEN-017","cat":"Body Lotion","img":"https://images.unsplash.com/photo-1556228578-0d85b1a4d571?w=400"},
 {"id":9,"name":"Sawa Women","price":450,"code":"SWA-WOM-018","cat":"Body Lotion","img":"https://images.unsplash.com/photo-1556228578-0d85b1a4d571?w=400"},
 {"id":10,"name":"Sawa 250ML","price":250,"code":"SWA-250-019","cat":"Body Lotion","img":"https://images.unsplash.com/photo-1556228578-0d85b1a4d571?w=400"},
 {"id":11,"name":"Sugar 2kg","price":320,"code":"SUG-010","cat":"Groceries","img":"https://images.unsplash.com/photo-1587049352851-8d4e89133924?w=400"},
 {"id":12,"name":"Rice 5kg","price":650,"code":"RIC-011","cat":"Groceries","img":"https://images.unsplash.com/photo-1586201375761-83865001e31c?w=400"},
]

@app.post("/api/login")
def login(d: Login):
 if (d.username=="Mongelah" and d.password=="1234") or (d.username=="admin" and d.password=="Lonma@2026"):
  return {"ok":True}
 return {"ok":False}

@app.get("/api/products")
def products():
 return sorted(PRODUCTS, key=lambda p: 0 if p["code"].startswith(("FF","SLT","DTX")) else 1)

@app.post("/api/stk")
def stk(d: Pay):
 return {"msg":"DEMO","phone":d.phone,"amount":d.amount}

@app.post("/api/chat")
def chat(d: Chat):
 q=d.msg.lower()
 if "code" in q:
  return {"reply":"Codes: FF=Fresh Fri, SLT=Salt, DTX=Detox, SWA=Sawa"}
 if "sale" in q:
  return {"reply":"SALE: Fresh Fri 5L 850, 2L 400, Salt 180, Detox 1200"}
 return {"reply":"Ask about products, prices, codes, delivery."}

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def root():
 return FileResponse("static/index.html")

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
 {"id":1,"name":"Fresh Fri 5L","price":850,"code":"FF-5L-001","comment":"SALE","cat":"Cooking Oil","img":"https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=200"},
 {"id":2,"name":"Fresh Fri 2L","price":400,"code":"FF-2L-002","comment":"SALE","cat":"Cooking Oil","img":"https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=200"},
 {"id":3,"name":"Fresh Fri 1L","price":220,"code":"FF-1L-003","comment":"SALE","cat":"Cooking Oil","img":"https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=200"},
 {"id":4,"name":"Salt 2kg","price":180,"code":"SLT-2KG-005","comment":"SALE","cat":"Groceries","img":"https://images.unsplash.com/photo-1584305574586-0a9579496bb7?w=200"},
 {"id":5,"name":"Salt 1kg","price":100,"code":"SLT-1KG-006","comment":"SALE","cat":"Groceries","img":"https://images.unsplash.com/photo-1584305574586-0a9579496bb7?w=200"},
 {"id":6,"name":"Detox Slim Tea","price":1200,"code":"DTX-001","comment":"SALE","cat":"Wellness","img":"https://images.unsplash.com/photo-1576092768241-dec231879fc3?w=200"},
 {"id":7,"name":"Green Tea","price":250,"code":"DTX-020","comment":"SALE","cat":"Wellness","img":"https://images.unsplash.com/photo-1576092768241-dec231879fc3?w=200"},
 {"id":8,"name":"Sawa Lotion Men 500ML","price":450,"code":"SWA-MEN-017","comment":"Best Seller","cat":"Body Lotion","img":"https://images.unsplash.com/photo-1556228578-0d85b1a4d571?w=200"},
 {"id":9,"name":"Sawa Lotion Women","price":450,"code":"SWA-WOM-018","comment":"Best Seller","cat":"Body Lotion","img":"https://images.unsplash.com/photo-1556228578-0d85b1a4d571?w=200"},
 {"id":10,"name":"Sawa 250ML","price":250,"code":"SWA-250-019","comment":"","cat":"Body Lotion","img":"https://images.unsplash.com/photo-1556228578-0d85b1a4d571?w=200"},
 {"id":11,"name":"Sugar 2kg","price":320,"code":"SUG-010","comment":"","cat":"Groceries","img":"https://images.unsplash.com/photo-1587049352851-8d4e89133924?w=200"},
 {"id":12,"name":"Rice 5kg","price":650,"code":"RIC-011","comment":"","cat":"Groceries","img":"https://images.unsplash.com/photo-1586201375761-83865001e31c?w=200"},
 {"id":13,"name":"Flour 2kg","price":180,"code":"FLR-012","comment":"","cat":"Groceries","img":"https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?w=200"},
 {"id":14,"name":"Milk 500ML","price":70,"code":"MLK-013","comment":"","cat":"Groceries","img":"https://images.unsplash.com/photo-1550583724-b2692b85b150?w=200"},
 {"id":15,"name":"Bread 400g","price":70,"code":"BRD-001","comment":"","cat":"Groceries","img":"https://images.unsplash.com/photo-1549931319-a545dcf3bc73?w=200"},
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
 if "sale" in q:
  return {"reply":"SALE: Fresh Fri 5L 850, 2L 400, Salt 180, Detox 1200"}
 return {"reply":"Bot: Ask about sale or products"}
app.mount("/static", StaticFiles(directory="static"), name="static")
@app.get("/")
def root():
 return FileResponse("static/index.html")

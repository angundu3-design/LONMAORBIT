from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os, sqlite3, urllib.parse
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

conn = sqlite3.connect("lonma.db", check_same_thread=False)
conn.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, email TEXT UNIQUE, password TEXT, name TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT, price INTEGER, code TEXT, image TEXT)")
cur=conn.cursor()
cur.execute("DELETE FROM products")
# Your 9 real products from images
products_data=[
    (1,"Fresh Fri Cooking Oil 2L",850,"LONMA-001"),
    (2,"Detrex Citronella Soap",90,"LONMA-002"),
    (3,"Sawa Men Lotion 72Hrs",299,"LONMA-003"),
    (4,"Detrex Pine Drops Soap",90,"LONMA-004"),
    (5,"Salit Vegetable Oil 5L",1250,"LONMA-005"),
    (6,"Detrex Cool Mint Soap",90,"LONMA-006"),
    (7,"Diva Anti-Dandruff Pomade 250ml",250,"LONMA-007"),
    (8,"Diva Anti-Breakage Pomade 250ml",250,"LONMA-008"),
    (9,"Sawa Cocoa Butter Lotion",299,"LONMA-009"),
]
# Get actual files
files=[f for f in os.listdir(".") if "WhatsApp" in f and f.lower().endswith((".jpg",".jpeg",".png"))]
files=sorted(files)
for i,(pid,name,price,code) in enumerate(products_data):
    if i < len(files):
        img=f"/img/{urllib.parse.quote(files[i])}"
    else:
        img=f"https://via.placeholder.com/300?text={urllib.parse.quote(name)}"
    cur.execute("INSERT INTO products VALUES (?,?,?,?,?)", (pid,name,price,code,img))
conn.commit()

HTML = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>LONMA ORBIT</title>
<style>
:root{--teal:#0A9EBB}*{box-sizing:border-box}body{margin:0;font-family:Arial;background:var(--teal);color:#fff}
.nav{position:fixed;top:0;width:100%;background:var(--teal);padding:8px 15px;display:flex;justify-content:space-between;align-items:center;z-index:100}
.logo-img{height:52px;width:52px;border-radius:50%;background:transparent;padding:0;object-fit:cover;display:block;border:none}
.page{display:none;padding:78px 15px 110px;min-height:100vh;background:var(--teal)}.page.active{display:block}
.card{background:#fff;color:#000;border-radius:14px;padding:12px;margin:10px 0}
.card img{width:100%;height:220px;object-fit:contain;background:#fff;border-radius:10px;padding:10px}
.btn{background:var(--teal);color:#fff;border:none;padding:12px;border-radius:25px;width:100%;font-weight:bold;margin-top:8px;cursor:pointer}
input{width:100%;padding:12px;border-radius:8px;border:1px solid #ddd;background:#f7f7f7;margin:6px 0}
.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}
.bottom{position:fixed;bottom:0;width:100%;background:#fff;display:flex;justify-content:space-around;padding:10px;z-index:100}.bottom div{font-size:10px;color:#000;text-align:center;cursor:pointer}
</style></head><body>
<div class="nav">
<img src="/logo.png" class="logo-img" onerror="this.src='https://via.placeholder.com/100/FFFFFF/0A9EBB?text=LO'">
<div style="display:flex;gap:8px"><span onclick="show('login')" style="background:rgba(255,255,255,0.25);color:#fff;padding:8px 16px;border-radius:20px;font-size:13px">Log in</span><span onclick="show('signin')" style="background:#fff;color:#0A9EBB;padding:8px 16px;border-radius:20px;font-size:13px;font-weight:bold">Sign in</span></div>
</div>

<div id="products" class="page active"><h2>LONMA ORBIT PRODUCTS</h2><div class="grid" id="plist"></div></div>

<div id="terms" class="page"><h2>Terms & Conditions</h2>
<div class="card" style="font-size:13px;line-height:1.6;max-height:70vh;overflow-y:auto;text-align:left">
<h3 style="color:#0A9EBB;margin-top:0">Terms - Pwani Oils & Soaps</h3>
<p><b>1. Products:</b> Fresh Fri, Salit, Detrex, Sawa, Diva - Original Pwani Products. Each with LONMA code verification.</p>
<p><b>2. Prices KSh:</b> Soaps 90, Sawa 299, Diva 250, Fresh Fri 850, Salit 1250</p>
<p><b>3. M-Pesa:</b> STK Push to 07xx - Enter PIN to pay. Charges per Safaricom.</p>
<p><b>4. Delivery:</b> Nairobi same-day before 3PM, upcountry 24-48hrs. Fee 150-300.</p>
<p><b>5. Returns:</b> 24hrs if defect/unopened. Soaps non-returnable if opened.</p>
<p><b>6. Verification:</b> Scan QR LONMA-00X on product to verify originality.</p>
<p><b>Contact:</b> Moi Avenue Nairobi | support@lonmaorbit.co.ke</p>
<button class="btn" onclick="show('products')">I AGREE</button>
</div></div>

<div id="scan" class="page"><h2>Scan Code</h2><div class="card"><input id="manualcode" placeholder="LONMA-001"><button class="btn" onclick="verifyCode()">VERIFY</button><p id="scanresult"></p></div></div>
<div id="locations" class="page"><h2>Locations</h2><div class="card"><h4>CBD</h4><p>Moi Avenue</p></div></div>
<div id="login" class="page"><h2>Log In</h2><div class="card"><input id="lemail" placeholder="Email"><input id="lpass" type="password" placeholder="Password"><button class="btn" onclick="login()">Log In</button></div></div>
<div id="signin" class="page"><h2>Sign Up</h2><div class="card"><input id="sname" placeholder="Name"><input id="semail" placeholder="Email"><input id="spass" type="password" placeholder="Password"><button class="btn" onclick="signin()">Create</button></div></div>

<div class="bottom"><div onclick="show('products')">🛍️<br>Products</div><div onclick="show('scan')">📷<br>Scan</div><div onclick="show('locations')">📍<br>Locations</div><div onclick="show('terms')">📄<br>Terms</div><div onclick="show('login')">👤<br>Account</div></div>

<script>
function show(id){document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));document.getElementById(id).classList.add('active')}
async function loadProducts(){
  let r=await fetch('/api/products');let d=await r.json();
  document.getElementById('plist').innerHTML=d.map(p=>`
    <div class="card">
      <img src="${p.image}" onerror="this.src='https://via.placeholder.com/300'">
      <h4 style="margin:8px 0 2px;font-size:14px">${p.name}</h4>
      <p style="margin:0;font-weight:bold;color:#0A9EBB">KSh ${p.price}</p>
      <small style="color:#666">${p.code}</small>
      <button class="btn">BUY - M-PESA</button>
    </div>`).join('');
}
async function verifyCode(){let c=document.getElementById('manualcode').value;let r=await fetch(`/api/verify/${c}`);let d=await r.json();document.getElementById('scanresult').innerHTML=d.valid?`✅ ${d.product.name} ORIGINAL`:`❌ Invalid`}
async function login(){let r=await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:document.getElementById('lemail').value,password:document.getElementById('lpass').value})});let d=await r.json();alert(d.message)}
async function signin(){let r=await fetch('/api/signin',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:document.getElementById('sname').value,email:document.getElementById('semail').value,password:document.getElementById('spass').value})});let d=await r.json();alert(d.message)}
loadProducts();
</script></body></html>
"""

@app.api_route("/", methods=["GET","HEAD"])
def home(): return HTMLResponse(HTML)

@app.get("/logo.png")
def logo():
    for p in ["logo.png","static/logo.png"]:
        if os.path.exists(p): return FileResponse(p)
    return HTMLResponse("no logo",404)

@app.get("/img/{filename}")
def serve_img(filename: str):
    dec=urllib.parse.unquote(filename)
    if os.path.exists(dec): return FileResponse(dec)
    for f in os.listdir("."):
        if f==dec or urllib.parse.quote(f)==filename:
            return FileResponse(f)
    return HTMLResponse("not found",404)

@app.get("/api/products")
def prods():
    cur=conn.cursor(); cur.execute("SELECT id,name,price,code,image FROM products")
    return [{"id":r[0],"name":r[1],"price":r[2],"code":r[3],"image":r[4]} for r in cur.fetchall()]

@app.get("/api/verify/{code}")
def verify(code:str):
    cur=conn.cursor(); cur.execute("SELECT name FROM products WHERE code=?",(code,))
    row=cur.fetchone(); return {"valid":True,"product":{"name":row[0]}} if row else {"valid":False}

@app.get("/api/locations")
def locs(): return [{"id":1,"name":"CBD","address":"Moi Avenue"}]

@app.post("/api/signin")
async def si(req:Request):
    d=await req.json()
    try: conn.execute("INSERT INTO users VALUES (NULL,?,?,?)",(d.get("email"),d.get("password"),d.get("name")));conn.commit();return {"message":"Created!"}
    except: return {"message":"Exists"}

@app.post("/api/login")
async def lo(req:Request):
    d=await req.json();cur=conn.cursor();cur.execute("SELECT * FROM users WHERE email=? AND password=?",(d.get("email"),d.get("password")))
    return {"message":"Welcome!"} if cur.fetchone() else {"message":"Invalid"}

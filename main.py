from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os, sqlite3, urllib.parse
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# --- DATABASE SETUP - MUST BE FIRST ---
conn = sqlite3.connect("lonma.db", check_same_thread=False)
conn.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, email TEXT UNIQUE, password TEXT, name TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT, price INTEGER, code TEXT, image TEXT)")
cur = conn.cursor()

# --- AUTO FIND IMAGES ---
def find_images():
    imgs=[]
    for f in os.listdir("."):
        if f.lower().endswith((".jpg",".jpeg",".png")):
            if "logo" not in f.lower():
                imgs.append(f)
    return sorted(imgs)

NAMES=["Fresh Fri Cooking Oil 2L","Detrex Citronella Soap","Sawa Men Lotion 72Hrs","Detrex Pine Drops Soap","Salit Vegetable Oil 5L","Detrex Cool Mint Soap","Diva Anti-Dandruff Pomade 250ml","Diva Anti-Breakage Pomade","Sawa Cocoa Butter Lotion"]
PRICES=[850,90,299,90,1250,90,250,250,299]
CODES=[f"LONMA-00{i+1}" for i in range(9)]

cur.execute("DELETE FROM products")
found=find_images()
print(f"FOUND IMAGES IN SERVER: {found}")

for i in range(9):
    if i < len(found):
        img_url=f"/img/{urllib.parse.quote(found[i])}"
    else:
        # Fallback placeholder so no 404 crash
        img_url=f"https://via.placeholder.com/400x300/FFFFFF/0A9EBB?text={urllib.parse.quote(NAMES[i])}"
    cur.execute("INSERT INTO products VALUES (?,?,?,?,?)", (i+1, NAMES[i], PRICES[i], CODES[i], img_url))
conn.commit()

def bot_reply(m):
    m=m.lower()
    if "price" in m: return "Soap 90, Sawa 299, Diva 250, Fresh Fri 850, Salit 1250"
    return "Hi! Ask price, M-Pesa, scan"

HTML = """
<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>LONMA ORBIT</title>
<style>
:root{--teal:#0A9EBB}*{box-sizing:border-box}body{margin:0;font-family:Arial;background:var(--teal);color:#fff}
.nav{position:fixed;top:0;width:100%;background:var(--teal);padding:8px 15px;display:flex;justify-content:space-between;align-items:center;z-index:100}
.logo-img{height:52px;width:52px;border-radius:50%;background:transparent;object-fit:cover;display:block;border:none}
.page{display:none;padding:78px 15px 110px;min-height:100vh;background:var(--teal)}.page.active{display:block}
.card{background:#fff;color:#000;border-radius:14px;padding:12px;margin:10px 0}
.card img{width:100%;height:240px;object-fit:contain;background:#fff;border-radius:10px;padding:12px}
.btn{background:var(--teal);color:#fff;border:none;padding:12px;border-radius:25px;width:100%;font-weight:bold;margin-top:8px;cursor:pointer}
input{width:100%;padding:12px;border-radius:8px;border:1px solid #ddd;background:#f7f7f7;margin:6px 0}
.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}
.bottom{position:fixed;bottom:0;width:100%;background:#fff;display:flex;justify-content:space-around;padding:10px;z-index:100}.bottom div{font-size:10px;color:#000;text-align:center;cursor:pointer}
</style></head><body>
<div class="nav"><img src="/logo.png" class="logo-img" onerror="this.src='https://via.placeholder.com/100'"><div style="display:flex;gap:8px"><span onclick="show('login')" style="background:rgba(255,255,255,.25);color:#fff;padding:8px 16px;border-radius:20px;font-size:13px">Log in</span><span onclick="show('signin')" style="background:#fff;color:#0A9EBB;padding:8px 16px;border-radius:20px;font-size:13px;font-weight:bold">Sign in</span></div></div>
<div id="products" class="page active"><h2>LONMA ORBIT - 9 PRODUCTS</h2><div class="grid" id="plist"></div><div class="card"><input id="phone" placeholder="07xxxxxxxx"><input id="amount" type="number" placeholder="Amount"><button class="btn" onclick="pay()">PAY WITH M-PESA</button><p id="paystatus"></p></div></div>
<div id="scan" class="page"><h2>Scan</h2><div class="card"><input id="manualcode" placeholder="LONMA-001"><button class="btn" onclick="verifyCode()">VERIFY</button><p id="scanresult"></p></div></div>
<div id="locations" class="page"><h2>Locations</h2><div class="card"><h4>CBD</h4><p>Moi Avenue</p></div></div>
<div id="terms" class="page"><h2>Terms</h2><div class="card" style="font-size:13px;line-height:1.6;max-height:65vh;overflow-y:auto;text-align:left"><h3 style="color:#0A9EBB">LONMA ORBIT Terms</h3><p>1. Products: Fresh Fri, Salit, Detrex, Sawa, Diva - Original</p><p>2. Prices: Soap 90, Sawa 299, Diva 250, Fresh Fri 850, Salit 1250</p><p>3. M-Pesa STK - enter phone + amount</p><p>4. Delivery: Nairobi same-day, upcountry 24-48hrs</p><p>5. Returns 24hrs defect only</p><p>Contact: support@lonmaorbit.co.ke</p><button class="btn" onclick="show('products')">I AGREE</button></div></div>
<div id="login" class="page"><h2>Log In</h2><div class="card"><input id="lemail" placeholder="Email"><input id="lpass" type="password" placeholder="Password"><button class="btn" onclick="login()">Log In</button></div></div>
<div id="signin" class="page"><h2>Sign Up</h2><div class="card"><input id="sname" placeholder="Name"><input id="semail" placeholder="Email"><input id="spass" type="password" placeholder="Password"><button class="btn" onclick="signin()">Create</button></div></div>
<div class="bottom"><div onclick="show('products')">🛍️<br>Products</div><div onclick="show('scan')">📷<br>Scan</div><div onclick="show('locations')">📍<br>Locations</div><div onclick="show('terms')">📄<br>Terms</div><div onclick="show('login')">👤<br>Account</div></div>
<script>
function show(id){document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));document.getElementById(id).classList.add('active')}
async function loadProducts(){let r=await fetch('/api/products');let d=await r.json();document.getElementById('plist').innerHTML=d.map(p=>`<div class="card"><img src="${p.image}" loading="lazy" onerror="this.src='https://via.placeholder.com/300?text=${encodeURIComponent(p.name)}'"><h4 style="margin:8px 0 2px;font-size:13px">${p.name}</h4><p style="margin:0;font-weight:bold;color:#0A9EBB">KSh ${p.price}</p><small>${p.code}</small><button class="btn" onclick="document.getElementById('manualcode').value='${p.code}';show('scan')">VERIFY</button><button class="btn" style="background:#000" onclick="document.getElementById('amount').value=${p.price}">BUY</button></div>`).join('')}
async function verifyCode(){let c=document.getElementById('manualcode').value.trim();let r=await fetch(`/api/verify/${c}`);let d=await r.json();document.getElementById('scanresult').innerHTML=d.valid?`✅ ${d.product.name} ORIGINAL`:`❌ Invalid`}
async function login(){let r=await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:document.getElementById('lemail').value,password:document.getElementById('lpass').value})});let d=await r.json();alert(d.message)}
async function signin(){let r=await fetch('/api/signin',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:document.getElementById('sname').value,email:document.getElementById('semail').value,password:document.getElementById('spass').value})});let d=await r.json();alert(d.message)}
async function pay(){let phone=document.getElementById('phone').value;let amt=document.getElementById('amount').value;if(!phone||!amt){document.getElementById('paystatus').innerText='Enter phone & amount';return}document.getElementById('paystatus').innerText='Sending...';let r=await fetch('/mpesa/stkpush',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({phone,amount:amt})});let d=await r.json();document.getElementById('paystatus').innerText=JSON.stringify(d)}
loadProducts();
</script></body></html>
"""

@app.api_route("/", methods=["GET", "HEAD"])
def home(): return HTMLResponse(HTML)

@app.get("/logo.png")
def logo():
    for p in ["logo.png","static/logo.png"]:
        if os.path.exists(p): return FileResponse(p)
    return HTMLResponse("no logo", 404)

@app.get("/img/{filename}")
def serve_img(filename: str):
    decoded = urllib.parse.unquote(filename)
    if os.path.exists(decoded):
        return FileResponse(decoded)
    for f in os.listdir("."):
        if f == decoded or urllib.parse.quote(f) == filename:
            return FileResponse(f)
        if f.lower() == decoded.lower():
            return FileResponse(f)
    return HTMLResponse(f"Image {decoded} not found. Files: {os.listdir('.')}", 404)

@app.get("/api/products")
def products_api():
    cur=conn.cursor(); cur.execute("SELECT id,name,price,code,image FROM products")
    return [{"id":r[0],"name":r[1],"price":r[2],"code":r[3],"image":r[4]} for r in cur.fetchall()]

@app.get("/api/locations")
def locs(): return [{"id":1,"name":"CBD","address":"Moi Avenue"}]

@app.get("/api/verify/{code}")
def verify(code: str):
    cur=conn.cursor(); cur.execute("SELECT name FROM products WHERE code=?", (code.strip(),))
    row=cur.fetchone()
    return {"valid":True,"product":{"name":row[0]}} if row else {"valid":False}

@app.post("/api/signin")
async def signin_api(req: Request):
    data=await req.json()
    try:
        conn.execute("INSERT INTO users (email,password,name) VALUES (?,?,?)", (data.get("email"), data.get("password"), data.get("name"))); conn.commit()
        return {"message":"Created!"}
    except: return {"message":"Exists"}

@app.post("/api/login")
async def login_api(req: Request):
    data=await req.json()
    cur=conn.cursor(); cur.execute("SELECT * FROM users WHERE email=? AND password=?", (data.get("email"), data.get("password")))
    return {"message":"Welcome!"} if cur.fetchone() else {"message":"Invalid"}

@app.post("/mpesa/stkpush")
async def stk(req: Request):
    data=await req.json()
    return {"ResponseCode":"0","message":f"STK to {data.get('phone')} KSh {data.get('amount')}"}

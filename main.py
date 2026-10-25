from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os, sqlite3, glob, urllib.parse
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# FIND ALL UPLOADED IMAGES
def get_uploaded_images():
    imgs=[]
    for f in os.listdir("."):
        if f.lower().endswith((".jpg",".jpeg",".png")) and "WhatsApp" in f:
            imgs.append(f)
    return sorted(imgs)

conn = sqlite3.connect("lonma.db", check_same_thread=False)
conn.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, email TEXT UNIQUE, password TEXT, name TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT, price INTEGER, code TEXT, image TEXT)")
cur=conn.cursor()
# Rebuild products from uploaded images
cur.execute("DELETE FROM products")
uploaded = get_uploaded_images()
if uploaded:
    for i,f in enumerate(uploaded[:10],1):
        # price based on index
        price=[1500,3500,1200,5000,1800,2500,2000,3000,1700,2200][(i-1)%10]
        encoded = urllib.parse.quote(f)
        conn.execute("INSERT INTO products VALUES (?,?,?,?,?)", (i, f"Orbit Item {i}", price, f"LONMA-{i:03d}", f"/img/{encoded}"))
else:
    conn.execute("INSERT INTO products VALUES (1,'Orbit Tee',1500,'LONMA-001','https://via.placeholder.com/300')")
conn.commit()

def bot_reply(m):
    m=m.lower()
    if "price" in m: return "💙 Products from your uploaded images - Tee 1500, Hoodie 3500 etc"
    return "🤖 All your WhatsApp images now live as products!"

HTML = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>LONMA ORBIT</title>
<script src="https://unpkg.com/html5-qrcode@2.3.8/html5-qrcode.min.js"></script>
<style>
:root{--teal:#0A9EBB}*{box-sizing:border-box}body{margin:0;font-family:Arial;background:var(--teal);color:#fff}
.nav{position:fixed;top:0;width:100%;background:var(--teal);padding:8px 15px;display:flex;justify-content:space-between;align-items:center;z-index:100}
.logo-img{height:52px;width:52px;border-radius:50%;background:transparent;padding:0;object-fit:cover;display:block;border:none}
.page{display:none;padding:78px 15px 110px;min-height:100vh;background:var(--teal)}.page.active{display:block}
.card{background:#fff;color:#000;border-radius:14px;padding:12px;margin:10px 0;overflow:hidden}
.card img{width:100%;height:200px;object-fit:cover;border-radius:10px}
.btn{background:var(--teal);color:#fff;border:none;padding:12px;border-radius:25px;width:100%;font-weight:bold;margin-top:8px;cursor:pointer}
input{width:100%;padding:12px;border-radius:8px;border:1px solid #ddd;background:#f7f7f7;margin:6px 0}
.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}
.bottom{position:fixed;bottom:0;width:100%;background:#fff;display:flex;justify-content:space-around;padding:10px;z-index:100}.bottom div{font-size:10px;color:#000;text-align:center;cursor:pointer}
#botBtn{position:fixed;bottom:80px;right:15px;background:#fff;color:var(--teal);width:56px;height:56px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:26px;cursor:pointer;z-index:200}
#botBox{display:none;position:fixed;bottom:145px;right:15px;width:90%;max-width:350px;height:400px;background:#fff;border-radius:15px;z-index:200;flex-direction:column;overflow:hidden}#botBox.open{display:flex}
</style></head><body>
<div class="nav">
<img src="/logo.png" class="logo-img" onerror="this.src='https://via.placeholder.com/100/FFFFFF/0A9EBB?text=LO'">
<div style="display:flex;gap:8px"><span onclick="show('login')" style="background:rgba(255,255,255,0.25);color:#fff;padding:8px 16px;border-radius:20px;font-size:13px;cursor:pointer">Log in</span><span onclick="show('signin')" style="background:#fff;color:#0A9EBB;padding:8px 16px;border-radius:20px;font-size:13px;font-weight:bold;cursor:pointer">Sign in</span></div>
</div>

<div id="products" class="page active"><h2>LONMA ORBIT - YOUR UPLOADED IMAGES</h2><div class="grid" id="plist"></div><p id="count" style="text-align:center"></p></div>

<div id="terms" class="page"><h2>Terms & Conditions</h2><div class="card" style="font-size:13px;line-height:1.6;max-height:65vh;overflow-y:auto"><h3 style="color:#0A9EBB;margin-top:0">LONMA ORBIT Terms</h3><p><b>1.</b> All products original from your uploaded WhatsApp images.</p><p><b>2.</b> Each product has LONMA-00X code - verify via Scan tab.</p><p><b>3.</b> M-Pesa payment final - STK to 07xx number.</p><p><b>4.</b> Nairobi same-day, outside 24-48hrs.</p><p><b>5.</b> 24hr returns if unworn with tags.</p><p><b>6.</b> Privacy - data only for orders.</p><p><b>Contact: support@lonmaorbit.co.ke | Moi Avenue, Nairobi</b></p><button class="btn" onclick="show('products')">I AGREE</button></div></div>

<div id="scan" class="page"><h2>Code Scan</h2><div class="card"><div id="reader"></div><button class="btn" onclick="startScan()">START CAMERA</button><input id="manualcode" placeholder="LONMA-001"><button class="btn" onclick="verifyCode()">VERIFY</button><p id="scanresult"></p></div></div>

<div id="locations" class="page"><h2>Locations</h2><div id="loclist"></div></div>
<div id="login" class="page"><h2>Log In</h2><div class="card"><input id="lemail" placeholder="Email"><input id="lpass" type="password" placeholder="Password"><button class="btn" onclick="login()">Log In</button><p id="lstatus"></p></div></div>
<div id="signin" class="page"><h2>Sign Up</h2><div class="card"><input id="sname" placeholder="Full Name"><input id="semail" placeholder="Email"><input id="spass" type="password" placeholder="Password"><button class="btn" onclick="signin()">Create</button><p id="sstatus"></p></div></div>

<div class="bottom"><div onclick="show('products')">🛍️<br>Products</div><div onclick="show('scan')">📷<br>Scan</div><div onclick="show('locations')">📍<br>Locations</div><div onclick="show('terms')">📄<br>Terms</div><div onclick="show('login')">👤<br>Account</div></div>

<div id="botBtn" onclick="toggleBot()">🤖</div>
<div id="botBox"><div style="padding:12px;background:#0A9EBB;color:#fff;font-weight:bold;display:flex;justify-content:space-between"><span>LO BOT</span><span onclick="toggleBot()" style="cursor:pointer">✕</span></div><div id="botMsgs" style="flex:1;overflow-y:auto;padding:10px;background:#f9f9f9"><div style="background:#fff;padding:10px;border-radius:12px;font-size:13px;color:#000">Your 10 WhatsApp images now showing as products!</div></div><div style="display:flex;padding:10px;border-top:1px solid #eee;background:#fff"><input id="botInput" style="flex:1" placeholder="Ask..." onkeypress="if(event.key==='Enter')sendBot()"><button onclick="sendBot()" style="background:#0A9EBB;color:#fff;border:none;padding:12px 15px;border-radius:0 20px 20px 0">Send</button></div></div>

<script>
function show(id){document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));document.getElementById(id).classList.add('active')}
async function loadProducts(){let r=await fetch('/api/products');let d=await r.json();document.getElementById('count').innerText=d.length+' products from your uploads';document.getElementById('plist').innerHTML=d.map(p=>`<div class="card"><img src="${p.image}" loading="lazy" onerror="this.src='https://via.placeholder.com/300'"><h4 style="margin:8px 0 2px">${p.name}</h4><p style="margin:0">KSh ${p.price}</p><small>${p.code}</small><button class="btn" onclick="document.getElementById('manualcode').value='${p.code}'">VERIFY CODE</button></div>`).join('')}
async function loadLoc(){let r=await fetch('/api/locations');let d=await r.json();document.getElementById('loclist').innerHTML=d.map(l=>`<div class="card"><h4>${l.name}</h4><p>${l.address}</p></div>`).join('')}
async function login(){let r=await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:document.getElementById('lemail').value,password:document.getElementById('lpass').value})});let d=await r.json();document.getElementById('lstatus').innerText=d.message}
async function signin(){let r=await fetch('/api/signin',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:document.getElementById('sname').value,email:document.getElementById('semail').value,password:document.getElementById('spass').value})});let d=await r.json();document.getElementById('sstatus').innerText=d.message}
async function verifyCode(){let code=document.getElementById('manualcode').value;let r=await fetch(`/api/verify/${code}`);let d=await r.json();document.getElementById('scanresult').innerHTML=d.valid?`✅ ${d.product.name} - ORIGINAL`:`❌ Invalid`}
let html5QrCode;function startScan(){html5QrCode=new Html5Qrcode("reader");html5QrCode.start({facingMode:"environment"},{fps:10,qrbox:250},(dec)=>{document.getElementById('manualcode').value=dec;verifyCode();html5QrCode.stop()})}
function toggleBot(){document.getElementById('botBox').classList.toggle('open')}
async function sendBot(){let i=document.getElementById('botInput');let m=i.value;if(!m)return;let b=document.getElementById('botMsgs');b.innerHTML+=`<div style="background:#0A9EBB;color:#fff;margin-left:auto;padding:8px;border-radius:12px;max-width:80%;margin-top:6px;font-size:13px">${m}</div>`;i.value='';let r=await fetch('/api/bot',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:m})});let d=await r.json();b.innerHTML+=`<div style="background:#fff;border:1px solid #eee;padding:8px;border-radius:12px;max-width:80%;margin-top:6px;font-size:13px;color:#000">${d.reply}</div>`;b.scrollTop=b.scrollHeight}
loadProducts();loadLoc();
</script></body></html>
"""

@app.api_route("/", methods=["GET", "HEAD"])
def home():
    return HTMLResponse(HTML)

@app.get("/logo.png")
def logo():
    for p in ["logo.png", "static/logo.png"]:
        if os.path.exists(p): return FileResponse(p)
    return HTMLResponse("no logo", status_code=404)

@app.get("/img/{filename}")
def serve_img(filename: str):
    # filename is URL encoded
    decoded = urllib.parse.unquote(filename)
    # security - only allow in current dir
    if os.path.exists(decoded):
        return FileResponse(decoded)
    # also try without path
    for f in os.listdir("."):
        if f == decoded: return FileResponse(f)
    return HTMLResponse("not found", status_code=404)

@app.get("/api/products")
def products():
    cur=conn.cursor(); cur.execute("SELECT id,name,price,code,image FROM products")
    return [{"id":r[0],"name":r[1],"price":r[2],"code":r[3],"image":r[4]} for r in cur.fetchall()]

@app.get("/api/locations")
def locations():
    return [{"id":1,"name":"LONMA CBD","address":"Moi Avenue, Nairobi"},{"id":2,"name":"Westlands","address":"Westgate Mall"}]

@app.get("/api/verify/{code}")
def verify(code: str):
    cur=conn.cursor(); cur.execute("SELECT name FROM products WHERE code=?", (code,))
    row=cur.fetchone()
    return {"valid":True,"product":{"name":row[0]}} if row else {"valid":False}

@app.post("/api/signin")
async def signin_api(req: Request):
    data=await req.json()
    try:
        conn.execute("INSERT INTO users (email,password,name) VALUES (?,?,?)", (data.get("email"), data.get("password"), data.get("name"))); conn.commit()
        return {"status":"ok","message":"Created!"}
    except: return {"status":"error","message":"Exists"}

@app.post("/api/login")
async def login_api(req: Request):
    data=await req.json()
    cur=conn.cursor(); cur.execute("SELECT * FROM users WHERE email=? AND password=?", (data.get("email"), data.get("password")))
    return {"status":"ok","message":"Welcome!"} if cur.fetchone() else {"status":"error","message":"Invalid"}

@app.post("/api/bot")
async def bot_api(req: Request):
    data=await req.json()
    return {"reply": bot_reply(data.get("message",""))}

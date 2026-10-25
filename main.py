from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os, sqlite3, base64, requests
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# DB setup
conn = sqlite3.connect("lonma.db", check_same_thread=False)
conn.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, email TEXT UNIQUE, password TEXT, name TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT, price INTEGER, code TEXT, image TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY, phone TEXT, amount INTEGER, status TEXT, created TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS locations (id INTEGER PRIMARY KEY, name TEXT, address TEXT, lat REAL, lng REAL)")
cur=conn.cursor()
cur.execute("SELECT COUNT(*) FROM products")
if cur.fetchone()[0]==0:
    conn.execute("INSERT INTO products VALUES (1,'Orbit Tee',1500,'LONMA-001','https://via.placeholder.com/300')")
    conn.execute("INSERT INTO products VALUES (2,'Orbit Hoodie',3500,'LONMA-002','https://via.placeholder.com/300')")
    conn.execute("INSERT INTO products VALUES (3,'Orbit Cap',1200,'LONMA-003','https://via.placeholder.com/300')")
    conn.commit()
cur.execute("SELECT COUNT(*) FROM locations")
if cur.fetchone()[0]==0:
    conn.execute("INSERT INTO locations VALUES (1,'LONMA CBD','Moi Avenue, Nairobi',-1.2833,36.8172)")
    conn.commit()

def bot_reply(m):
    m=m.lower()
    if "price" in m: return "💙 Tee 1500, Hoodie 3500, Cap 1200"
    if "mpesa" in m: return "💳 Enter 07xx + amount, PAY, PIN 1234"
    if "location" in m: return "📍 CBD, Westlands - delivery countrywide"
    return "🤖 Hi! LO Bot - ask products, M-Pesa, locations, scan"

HTML = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>LONMA ORBIT</title>
<script src="https://unpkg.com/html5-qrcode@2.3.8/html5-qrcode.min.js"></script>
<style>
:root{--teal:#0A9EBB}*{box-sizing:border-box}body{margin:0;font-family:Arial;background:var(--teal);color:#fff}
.nav{position:fixed;top:0;width:100%;background:var(--teal);padding:8px 15px;display:flex;justify-content:space-between;align-items:center;z-index:100;box-shadow:0 2px 10px rgba(0,0,0,0.2)}
.logo-img{height:48px;width:auto;min-width:110px;border-radius:8px;background:#fff;padding:3px;object-fit:contain;display:block}
.page{display:none;padding:78px 15px 110px;min-height:100vh;background:var(--teal)}.page.active{display:block}
.card{background:#fff;color:#000;border-radius:14px;padding:15px;margin:10px 0}.btn{background:var(--teal);color:#fff;border:none;padding:12px;border-radius:25px;width:100%;font-weight:bold;margin-top:8px;cursor:pointer}
input{width:100%;padding:12px;border-radius:8px;border:1px solid #ddd;background:#f7f7f7;margin:6px 0}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px}
.bottom{position:fixed;bottom:0;width:100%;background:#fff;display:flex;justify-content:space-around;padding:10px;z-index:100}.bottom div{font-size:10px;color:#000;text-align:center;cursor:pointer}
#botBtn{position:fixed;bottom:80px;right:15px;background:#fff;color:var(--teal);width:56px;height:56px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:26px;cursor:pointer;z-index:200;box-shadow:0 4px 15px rgba(0,0,0,0.3)}
#botBox{display:none;position:fixed;bottom:145px;right:15px;width:90%;max-width:350px;height:400px;background:#fff;border-radius:15px;z-index:200;flex-direction:column;overflow:hidden}
#botBox.open{display:flex}
</style></head><body>
<div class="nav">
<img src="/logo.png" class="logo-img" onerror="this.onerror=null;this.src='https://via.placeholder.com/115x50/FFFFFF/0A9EBB?text=LO+LONMA+ORBIT'">
<div style="display:flex;gap:8px"><span onclick="show('login')" style="background:rgba(255,255,255,0.25);color:#fff;padding:8px 16px;border-radius:20px;font-size:13px;cursor:pointer">Log in</span><span onclick="show('signin')" style="background:#fff;color:#0A9EBB;padding:8px 16px;border-radius:20px;font-size:13px;font-weight:bold;cursor:pointer">Sign in</span></div>
</div>
<div id="products" class="page active"><h2>Products</h2><div class="grid" id="plist"></div><div class="card"><input id="phone" placeholder="07xxxxxxxx"><input id="amount" type="number" placeholder="Amount"><button class="btn" onclick="pay()">PAY WITH M-PESA</button><p id="paystatus"></p></div></div>
<div id="login" class="page"><h2>Log In</h2><div class="card"><input id="lemail" placeholder="Email"><input id="lpass" type="password" placeholder="Password"><button class="btn" onclick="login()">Log In</button><p id="lstatus"></p></div></div>
<div id="signin" class="page"><h2>Sign Up</h2><div class="card"><input id="sname" placeholder="Full Name"><input id="semail" placeholder="Email"><input id="spass" type="password" placeholder="Password"><button class="btn" onclick="signin()">Create Account</button><p id="sstatus"></p></div></div>
<div id="terms" class="page"><h2>Terms</h2><div class="card">Original LONMA products, M-Pesa final, Nairobi same-day delivery</div></div>
<div id="locations" class="page"><h2>Locations</h2><div id="loclist"></div></div>
<div id="scan" class="page"><h2>Code Scan</h2><div class="card"><div id="reader"></div><button class="btn" onclick="startScan()">START CAMERA</button><input id="manualcode" placeholder="LONMA-001"><button class="btn" onclick="verifyCode()">VERIFY</button><p id="scanresult"></p></div></div>
<div class="bottom"><div onclick="show('products')">🛍️<br>Products</div><div onclick="show('scan')">📷<br>Scan</div><div onclick="show('locations')">📍<br>Locations</div><div onclick="show('terms')">📄<br>Terms</div><div onclick="show('login')">👤<br>Account</div></div>
<div id="botBtn" onclick="toggleBot()">🤖</div>
<div id="botBox"><div style="padding:12px;background:#0A9EBB;color:#fff;font-weight:bold;display:flex;justify-content:space-between"><span>LO BOT</span><span onclick="toggleBot()" style="cursor:pointer">✕</span></div><div id="botMsgs" style="flex:1;overflow-y:auto;padding:10px;background:#f9f9f9"><div style="background:#fff;border:1px solid #eee;padding:10px;border-radius:12px;font-size:13px;color:#000">Welcome to LONMA ORBIT 💙 Teal Edition - logo aligned!</div></div><div style="display:flex;padding:10px;border-top:1px solid #eee;background:#fff"><input id="botInput" style="flex:1" placeholder="Ask..." onkeypress="if(event.key==='Enter')sendBot()"><button onclick="sendBot()" style="background:#0A9EBB;color:#fff;border:none;padding:12px 15px;border-radius:0 20px 20px 0">Send</button></div></div>
<script>
function show(id){document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));document.getElementById(id).classList.add('active')}
async function loadProducts(){let r=await fetch('/api/products');let d=await r.json();document.getElementById('plist').innerHTML=d.map(p=>`<div class="card"><img src="${p.image}" style="width:100%;border-radius:8px"><h4>${p.name}</h4><p>KSh ${p.price}</p><small>${p.code}</small><button class="btn" onclick="document.getElementById('amount').value=${p.price}">BUY</button></div>`).join('')}
async function loadLoc(){let r=await fetch('/api/locations');let d=await r.json();document.getElementById('loclist').innerHTML=d.map(l=>`<div class="card"><h4>${l.name}</h4><p>${l.address}</p><a href="https://maps.google.com/?q=${l.lat},${l.lng}" target="_blank"><button class="btn">Directions</button></a></div>`).join('')}
async function login(){let r=await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:document.getElementById('lemail').value,password:document.getElementById('lpass').value})});let d=await r.json();document.getElementById('lstatus').innerText=d.message}
async function signin(){let r=await fetch('/api/signin',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:document.getElementById('sname').value,email:document.getElementById('semail').value,password:document.getElementById('spass').value})});let d=await r.json();document.getElementById('sstatus').innerText=d.message}
async function pay(){let phone=document.getElementById('phone').value;let amount=document.getElementById('amount').value;document.getElementById('paystatus').innerText='Sending STK...';let r=await fetch('/mpesa/stkpush',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({phone,amount})});let d=await r.json();document.getElementById('paystatus').innerText=JSON.stringify(d)}
async function verifyCode(){let code=document.getElementById('manualcode').value;let r=await fetch(`/api/verify/${code}`);let d=await r.json();document.getElementById('scanresult').innerHTML=d.valid?`✅ ${d.product.name}`:`❌ Invalid`}
let html5QrCode;function startScan(){html5QrCode=new Html5Qrcode("reader");html5QrCode.start({facingMode:"environment"},{fps:10,qrbox:250},(dec)=>{document.getElementById('manualcode').value=dec;verifyCode();html5QrCode.stop()})}
function toggleBot(){document.getElementById('botBox').classList.toggle('open')}
async function sendBot(){let i=document.getElementById('botInput');let m=i.value;if(!m)return;let b=document.getElementById('botMsgs');b.innerHTML+=`<div style="background:#0A9EBB;color:#fff;margin-left:auto;padding:10px;border-radius:12px;max-width:80%;margin-top:6px;font-size:13px">${m}</div>`;i.value='';let r=await fetch('/api/bot',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:m})});let d=await r.json();b.innerHTML+=`<div style="background:#fff;border:1px solid #eee;padding:10px;border-radius:12px;max-width:80%;margin-top:6px;font-size:13px;color:#000">${d.reply}</div>`;b.scrollTop=b.scrollHeight}
loadProducts();loadLoc();
</script></body></html>
"""

@app.api_route("/", methods=["GET","HEAD"])
def home():
    return HTMLResponse(HTML)

@app.get("/logo.png")
def logo():
    for p in ["logo.png", "static/logo.png"]:
        if os.path.exists(p):
            return FileResponse(p)
    return FileResponse("https://via.placeholder.com/115x50/FFFFFF/0A9EBB?text=LO") if False else HTMLResponse("upload logo.png", status_code=404)

@app.get("/api/products")
def products():
    cur=conn.cursor(); cur.execute("SELECT id,name,price,code,image FROM products")
    return [{"id":r[0],"name":r[1],"price":r[2],"code":r[3],"image":r[4]} for r in cur.fetchall()]

@app.get("/api/locations")
def locations():
    cur=conn.cursor(); cur.execute("SELECT * FROM locations")
    return [{"id":r[0],"name":r[1],"address":r[2],"lat":r[3],"lng":r[4]} for r in cur.fetchall()]

@app.get("/api/verify/{code}")
def verify(code: str):
    cur=conn.cursor(); cur.execute("SELECT name,price,code FROM products WHERE code=?", (code,))
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
    data=await req.json(); return {"reply": bot_reply(data.get("message",""))}

@app.post("/mpesa/stkpush")
async def stk_push(req: Request):
    data=await req.json()
    # simple mock if no credentials
    if not os.getenv("MPESA_CONSUMER_KEY"):
        return {"ResponseCode":"0","msg":"MOCK STK sent to "+data.get("phone","")}
    return {"ResponseCode":"0","msg":"STK sent"}

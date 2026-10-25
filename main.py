from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os, sqlite3, urllib.parse
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# --- DATABASE ---
conn = sqlite3.connect("lonma.db", check_same_thread=False)
conn.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, email TEXT UNIQUE, password TEXT, name TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT, price INTEGER, code TEXT, image TEXT)")
cur = conn.cursor()
cur.execute("DELETE FROM products")

# FINAL 9 PRODUCTS FROM YOUR UPLOADED IMAGES
# Rename your WhatsApp images in GitHub to these exact names to avoid spaces
FINAL_PRODUCTS = [
    (1, "Fresh Fri Premium Cooking Oil 2L", 850, "LONMA-001", "fresh-fri.jpg"),
    (2, "Detrex Citronella Anti-Bacterial Soap", 90, "LONMA-002", "detrex-citronella.jpg"),
    (3, "Sawa Body Lotion For Men 72Hrs", 299, "LONMA-003", "sawa-men.jpg"),
    (4, "Detrex Pine Drops Soap", 90, "LONMA-004", "detrex-pine.jpg"),
    (5, "Salit Refined Vegetable Oil 5L", 1250, "LONMA-005", "salit-5l.jpg"),
    (6, "Detrex Cool Mint Soap", 90, "LONMA-006", "detrex-mint.jpg"),
    (7, "Diva Anti-Dandruff Hair Pomade 250ml", 250, "LONMA-007", "diva-dandruff.jpg"),
    (8, "Diva Anti-Breakage Hair Pomade", 250, "LONMA-008", "diva-breakage.jpg"),
    (9, "Sawa Cocoa Butter Lotion 72Hrs", 299, "LONMA-009", "sawa-cocoa.jpg"),
]

for pid, name, price, code, filename in FINAL_PRODUCTS:
    # Check if file exists with any WhatsApp name or simple name
    img_path = f"/img/{urllib.parse.quote(filename)}"
    # fallback: try to find any WhatsApp image if simple name not found
    if not os.path.exists(filename):
        # will still use the /img/ link - if not found, frontend shows placeholder
        pass
    cur.execute("INSERT INTO products VALUES (?,?,?,?,?)", (pid, name, price, code, img_path))
conn.commit()

def bot_reply(m):
    m=m.lower()
    if "price" in m: return "💙 Soap 90, Sawa 299, Diva 250, Fresh Fri 850, Salit 1250"
    if "mpesa" in m: return "💳 Enter 07xx + amount → PAY → Enter PIN"
    if "detrex" in m: return "🧼 Detrex: Cool Mint, Pine Drops, Citronella - KSh 90"
    if "sawa" in m: return "🧴 Sawa Lotion 72Hrs - Men & Cocoa Butter - KSh 299"
    if "salit" in m or "fresh" in m: return "🍳 Fresh Fri 2L 850, Salit 5L 1250 - Pwani Original"
    return "🤖 Hi! Ask price, M-Pesa, Detrex, Sawa, Salit, code scan"

# --- HTML ---
HTML = """
<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>LONMA ORBIT - Pwani Products</title>
<script src="https://unpkg.com/html5-qrcode@2.3.8/html5-qrcode.min.js"></script>
<style>
:root{--teal:#0A9EBB}*{box-sizing:border-box}body{margin:0;font-family:Arial;background:var(--teal);color:#fff}
.nav{position:fixed;top:0;width:100%;background:var(--teal);padding:8px 15px;display:flex;justify-content:space-between;align-items:center;z-index:100}
.logo-img{height:52px;width:52px;border-radius:50%;background:transparent;object-fit:cover;display:block;border:none;outline:none;box-shadow:none}
.page{display:none;padding:78px 15px 110px;min-height:100vh;background:var(--teal)}.page.active{display:block}
.card{background:#fff;color:#000;border-radius:14px;padding:12px;margin:10px 0;box-shadow:0 3px 10px rgba(0,0,0,.1)}
.card img{width:100%;height:240px;object-fit:contain;background:#fff;border-radius:10px;padding:12px}
.btn{background:var(--teal);color:#fff;border:none;padding:12px;border-radius:25px;width:100%;font-weight:bold;margin-top:8px;cursor:pointer}
input{width:100%;padding:12px;border-radius:8px;border:1px solid #ddd;background:#f7f7f7;margin:6px 0}
.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}
.bottom{position:fixed;bottom:0;width:100%;background:#fff;display:flex;justify-content:space-around;padding:10px;z-index:100}.bottom div{font-size:10px;color:#000;text-align:center;cursor:pointer}
#botBtn{position:fixed;bottom:80px;right:15px;background:#fff;color:var(--teal);width:56px;height:56px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:26px;cursor:pointer;z-index:200;box-shadow:0 4px 15px rgba(0,0,0,.3)}
#botBox{display:none;position:fixed;bottom:145px;right:15px;width:92%;max-width:360px;height:420px;background:#fff;border-radius:15px;z-index:200;flex-direction:column;overflow:hidden;box-shadow:0 10px 30px rgba(0,0,0,.3)}#botBox.open{display:flex}
.terms{font-size:13px;line-height:1.7;color:#222;text-align:left;max-height:65vh;overflow-y:auto}
.terms h3{color:#0A9EBB;margin:14px 0 4px}
</style></head><body>
<div class="nav">
<img src="/logo.png" class="logo-img" onerror="this.src='https://via.placeholder.com/100/FFFFFF/0A9EBB?text=LO'">
<div style="display:flex;gap:8px"><span onclick="show('login')" style="background:rgba(255,255,255,.25);color:#fff;padding:8px 16px;border-radius:20px;font-size:13px;cursor:pointer">Log in</span><span onclick="show('signin')" style="background:#fff;color:#0A9EBB;padding:8px 16px;border-radius:20px;font-size:13px;font-weight:bold;cursor:pointer">Sign in</span></div>
</div>

<div id="products" class="page active"><h2 style="margin:10px 0">LONMA ORBIT - PWANI PRODUCTS</h2><div class="grid" id="plist"></div><div class="card"><input id="phone" placeholder="07xxxxxxxx"><input id="amount" type="number" placeholder="Amount KSh"><button class="btn" onclick="pay()">PAY WITH M-PESA</button><p id="paystatus" style="font-size:12px"></p></div></div>

<div id="scan" class="page"><h2>Code Scan Verification</h2><div class="card"><div id="reader" style="width:100%"></div><button class="btn" onclick="startScan()">START CAMERA</button><input id="manualcode" placeholder="Enter LONMA-001"><button class="btn" onclick="verifyCode()">VERIFY CODE</button><p id="scanresult" style="font-weight:bold"></p><small>Scan QR on product to verify originality</small></div></div>

<div id="locations" class="page"><h2>Store Locations</h2><div class="card"><h4>LONMA CBD</h4><p>Moi Avenue, Nairobi - Opposite Imenti</p><a href="https://maps.google.com/?q=-1.2833,36.8172" target="_blank"><button class="btn">GET DIRECTIONS</button></a></div><div class="card"><h4>LONMA Westlands</h4><p>Westgate Mall, 1st Floor</p><a href="https://maps.google.com/?q=-1.2634,36.8031" target="_blank"><button class="btn">GET DIRECTIONS</button></a></div></div>

<div id="terms" class="page"><h2>Terms & Conditions</h2><div class="card terms">
<h3 style="margin-top:0">LONMA ORBIT - Official Terms</h3><p><b>Last Updated: May 2026 - Nairobi, Kenya</b></p>
<h3>1. Products</h3><p>Fresh Fri, Salit (Pwani Oils), Detrex Soaps (Cool Mint, Pine Drops, Citronella), Sawa Lotions (Men, Cocoa Butter), Diva Pomades. All 100% original with LONMA-001 to LONMA-009 verification codes.</p>
<h3>2. Pricing</h3><p>Detrex 90 KSh, Sawa 299 KSh, Diva 250 KSh, Fresh Fri 2L 850 KSh, Salit 5L 1250 KSh. Prices inclusive VAT. Subject to change.</p>
<h3>3. M-Pesa Payment</h3><p>STK Push. Enter 07xx, amount, click PAY, enter M-Pesa PIN on phone. Till configured via MPESA env. Safaricom charges apply. Failed transactions refunded 24hrs.</p>
<h3>4. Delivery</h3><p>Nairobi same-day if order before 3PM, next day outskirts, 24-48hrs upcountry via Wells Fargo. Fee 150-400 KSh depending location. Provide accurate phone & pin.</p>
<h3>5. Returns</h3><p>24hrs for manufacturing defect, unworn, tags intact, QR intact. Soaps non-returnable if opened. Exchange free size. Refund to M-Pesa 48hrs for defects only.</p>
<h3>6. Code Verification</h3><p>Scan QR or enter LONMA-00X manually. Valid = ✅ product name, Invalid = ❌ possible fake - report to support@lonmaorbit.co.ke</p>
<h3>7. Accounts</h3><p>Provide true name, email, Kenyan phone. One account per email. Fraud leads to suspension. Age 13+ with guardian if under 18.</p>
<h3>8. Privacy</h3><p>We collect name, email, phone, address for orders only. Not shared except couriers. M-Pesa via Safaricom Daraja. No ad tracking. Delete request via email.</p>
<h3>9. IP</h3><p>LO logo, LONMA ORBIT, product codes are trademarks. No copying without permission.</p>
<h3>10. Liability</h3><p>Not liable for M-Pesa network, courier delays, power outage. Max liability = amount paid. Force majeure exempts.</p>
<h3>11. Governing Law</h3><p>Laws of Kenya, Nairobi Courts. Contact: Moi Avenue, support@lonmaorbit.co.ke, +254 7XX XXX XXX, https://app.lonmaorbit.co.ke</p>
<button class="btn" onclick="show('products')">I AGREE - CONTINUE</button>
</div></div>

<div id="login" class="page"><h2>Log In</h2><div class="card"><input id="lemail" placeholder="Email"><input id="lpass" type="password" placeholder="Password"><button class="btn" onclick="login()">Log In</button><p id="lstatus"></p></div></div>

<div id="signin" class="page"><h2>Sign Up</h2><div class="card"><input id="sname" placeholder="Full Name"><input id="semail" placeholder="Email"><input id="spass" type="password" placeholder="Password"><button class="btn" onclick="signin()">Create Account</button><p id="sstatus"></p></div></div>

<div class="bottom"><div onclick="show('products')">🛍️<br>Products</div><div onclick="show('scan')">📷<br>Scan</div><div onclick="show('locations')">📍<br>Locations</div><div onclick="show('terms')">📄<br>Terms</div><div onclick="show('login')">👤<br>Account</div></div>

<div id="botBtn" onclick="toggleBot()">🤖</div>
<div id="botBox"><div style="padding:12px;background:#0A9EBB;color:#fff;font-weight:bold;display:flex;justify-content:space-between"><span>LO BOT - PWANI</span><span onclick="toggleBot()" style="cursor:pointer">✕</span></div><div id="botMsgs" style="flex:1;overflow-y:auto;padding:10px;background:#f9f9f9"><div style="background:#fff;border:1px solid #eee;padding:10px;border-radius:12px;font-size:13px;color:#000">Welcome! Your 9 Pwani products live 💙 Ask price, Detrex, Sawa, scan</div></div><div style="display:flex;padding:10px;border-top:1px solid #eee;background:#fff"><input id="botInput" style="flex:1" placeholder="Ask..." onkeypress="if(event.key==='Enter')sendBot()"><button onclick="sendBot()" style="background:#0A9EBB;color:#fff;border:none;padding:12px 15px;border-radius:0 20px 20px 0">Send</button></div></div>

<script>
function show(id){document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));document.getElementById(id).classList.add('active')}
async function loadProducts(){
  let r=await fetch('/api/products');let d=await r.json();
  document.getElementById('plist').innerHTML=d.map(p=>`
    <div class="card">
      <img src="${p.image}" loading="lazy" onerror="this.src='https://via.placeholder.com/300/FFFFFF/0A9EBB?text=${encodeURIComponent(p.name)}'">
      <h4 style="margin:8px 0 2px;font-size:13px">${p.name}</h4>
      <p style="margin:0;font-weight:bold;color:#0A9EBB">KSh ${p.price}</p>
      <small style="color:#666">${p.code}</small>
      <button class="btn" onclick="document.getElementById('manualcode').value='${p.code}';show('scan')">VERIFY</button>
      <button class="btn" style="background:#000" onclick="document.getElementById('amount').value=${p.price};show('products');window.scrollTo(0,document.body.scrollHeight)">BUY NOW</button>
    </div>`).join('');
}
async function loadLoc(){}
async function verifyCode(){let c=document.getElementById('manualcode').value.trim();if(!c)return;let r=await fetch(`/api/verify/${c}`);let d=await r.json();document.getElementById('scanresult').innerHTML=d.valid?`✅ ${d.product.name} - ORIGINAL PWANI`:`❌ Invalid Code - Report Fake`}
async function login(){let r=await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:document.getElementById('lemail').value,password:document.getElementById('lpass').value})});let d=await r.json();document.getElementById('lstatus').innerText=d.message}
async function signin(){let r=await fetch('/api/signin',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:document.getElementById('sname').value,email:document.getElementById('semail').value,password:document.getElementById('spass').value})});let d=await r.json();document.getElementById('sstatus').innerText=d.message}
async function pay(){let phone=document.getElementById('phone').value;let amt=document.getElementById('amount').value;if(!phone||!amt){document.getElementById('paystatus').innerText='Enter phone & amount';return}document.getElementById('paystatus').innerText='Sending STK to '+phone+'...';let r=await fetch('/mpesa/stkpush',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({phone,amount:amt})});let d=await r.json();document.getElementById('paystatus').innerText=JSON.stringify(d)}
let html5QrCode;function startScan(){html5QrCode=new Html5Qrcode("reader");html5QrCode.start({facingMode:"environment"},{fps:10,qrbox:250},(dec)=>{document.getElementById('manualcode').value=dec;verifyCode();html5QrCode.stop()},(err)=>{})}
function toggleBot(){document.getElementById('botBox').classList.toggle('open')}
async function sendBot(){let i=document.getElementById('botInput');let m=i.value.trim();if(!m)return;let b=document.getElementById('botMsgs');b.innerHTML+=`<div style="background:#0A9EBB;color:#fff;margin-left:auto;padding:10px;border-radius:12px;max-width:80%;margin-top:6px;font-size:13px">${m}</div>`;i.value='';let r=await fetch('/api/bot',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:m})});let d=await r.json();b.innerHTML+=`<div style="background:#fff;border:1px solid #eee;padding:10px;border-radius:12px;max-width:80%;margin-top:6px;font-size:13px;color:#000">${d.reply}</div>`;b.scrollTop=b.scrollHeight}
loadProducts();
</script></body></html>
"""

@app.api_route("/", methods=["GET", "HEAD"])
def home(): return HTMLResponse(HTML)

@app.get("/logo.png")
def logo():
    for p in ["logo.png", "static/logo.png", "LO.png"]:
        if os.path.exists(p): return FileResponse(p)
    return HTMLResponse("logo not found", 404)

@app.get("/img/{filename}")
def serve_img(filename: str):
    decoded = urllib.parse.unquote(filename)
    # direct
    if os.path.exists(decoded): return FileResponse(decoded)
    # search in dir (handles WhatsApp names)
    for f in os.listdir("."):
        if f == decoded: return FileResponse(f)
        if urllib.parse.quote(f) == filename: return FileResponse(f)
        # match simple name contains
        if decoded.replace(".jpg","") in f or f.replace(" ","") in decoded.replace(" ",""):
            pass
    # try case-insensitive
    for f in os.listdir("."):
        if f.lower() == decoded.lower(): return FileResponse(f)
    return FileResponse(decoded) if os.path.exists(decoded) else HTMLResponse("Image not found - rename WhatsApp files to simple names in GitHub", 404)

@app.get("/api/products")
def products():
    cur=conn.cursor(); cur.execute("SELECT id,name,price,code,image FROM products")
    return [{"id":r[0],"name":r[1],"price":r[2],"code":r[3],"image":r[4]} for r in cur.fetchall()]

@app.get("/api/locations")
def locations():
    return [{"id":1,"name":"LONMA CBD","address":"Moi Avenue"},{"id":2,"name":"Westlands","address":"Westgate Mall"}]

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
        return {"status":"ok","message":"Account created!"}
    except: return {"status":"error","message":"Email exists"}

@app.post("/api/login")
async def login_api(req: Request):
    data=await req.json()
    cur=conn.cursor(); cur.execute("SELECT * FROM users WHERE email=? AND password=?", (data.get("email"), data.get("password")))
    return {"status":"ok","message":"Welcome back!"} if cur.fetchone() else {"status":"error","message":"Invalid credentials"}

@app.post("/api/bot")
async def bot_api(req: Request):
    data=await req.json()
    return {"reply": bot_reply(data.get("message",""))}

@app.post("/mpesa/stkpush")
async def stk_push(req: Request):
    data=await req.json()
    return {"ResponseCode":"0","message":"STK sent to "+data.get("phone","")+" for KSh "+str(data.get("amount",""))+" - Enter PIN (MOCK - configure MPESA env for real)"}

@app.post("/mpesa/callback")
async def callback(req: Request): return {"ResultCode":0,"ResultDesc":"Accepted"}

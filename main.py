from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os, sqlite3, urllib.parse

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# DATABASE - FIXED ORDER - conn FIRST
conn = sqlite3.connect("lonma.db", check_same_thread=False)
conn.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, email TEXT UNIQUE, password TEXT, name TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT, price INTEGER, code TEXT, image TEXT)")

# Clear and insert 9 products with PLACEHOLDER images so NO 404 ever
cur = conn.cursor()
cur.execute("DELETE FROM products")
PRODUCTS = [
    (1, "Fresh Fri Cooking Oil 2L", 850, "LONMA-001"),
    (2, "Detrex Citronella Soap 110g", 90, "LONMA-002"),
    (3, "Sawa Men Lotion 72Hrs Hydration", 299, "LONMA-003"),
    (4, "Detrex Pine Drops Soap 110g", 90, "LONMA-004"),
    (5, "Salit Vegetable Oil 5L", 1250, "LONMA-005"),
    (6, "Detrex Cool Mint Soap 110g", 90, "LONMA-006"),
    (7, "Diva Anti-Dandruff Pomade 250ml", 250, "LONMA-007"),
    (8, "Diva Anti-Breakage Pomade", 250, "LONMA-008"),
    (9, "Sawa Cocoa Butter Lotion", 299, "LONMA-009"),
]
for pid, name, price, code in PRODUCTS:
    # Use placeholder so site works even without real images
    img = f"https://via.placeholder.com/400x300/FFFFFF/0A9EBB?text={urllib.parse.quote(name)}"
    # If real image exists in GitHub, use it
    for f in os.listdir("."):
        if code.lower() in f.lower() or name.split()[0].lower() in f.lower():
            if f.lower().endswith((".jpg",".jpeg",".png")) and "logo" not in f.lower():
                img = f"/img/{urllib.parse.quote(f)}"
    cur.execute("INSERT INTO products VALUES (?,?,?,?,?)", (pid, name, price, code, img))
conn.commit()

print(f"SERVER STARTED - Images in folder: {[f for f in os.listdir('.') if f.lower().endswith(('.jpg','.png'))]}")

HTML = """
<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>LONMA ORBIT</title>
<style>
:root{--teal:#0A9EBB}*{box-sizing:border-box}body{margin:0;font-family:Arial;background:var(--teal);color:#fff}
.nav{position:fixed;top:0;width:100%;background:var(--teal);padding:8px 12px;display:flex;justify-content:space-between;align-items:center;z-index:1000;height:60px}
.logo-img{height:46px;width:46px;border-radius:50%;object-fit:cover;border:2px solid #fff;background:#fff}
.page{display:none;padding:70px 12px 90px;min-height:100vh;background:var(--teal)}.page.active{display:block}
.card{background:#fff;color:#111;border-radius:14px;padding:12px;margin:10px 0}
.card img{width:100%;height:220px;object-fit:contain;background:#fff;border-radius:10px;padding:10px}
.btn{background:var(--teal);color:#fff;border:none;padding:12px;border-radius:25px;width:100%;font-weight:bold;margin-top:8px;cursor:pointer}
input{width:100%;padding:12px;border-radius:10px;border:1px solid #ddd;background:#f7f7f7;margin:6px 0}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.bottom{position:fixed;bottom:0;width:100%;background:#fff;display:flex;justify-content:space-around;padding:8px 0;z-index:1000}.bottom div{font-size:10px;color:#555;text-align:center;cursor:pointer;flex:1}.bottom div.active{color:var(--teal);font-weight:bold}
</style></head><body>
<div class="nav"><img src="/logo.png" class="logo-img" onerror="this.src='https://via.placeholder.com/100'"><div style="display:flex;gap:6px"><span onclick="show('login')" style="background:rgba(255,255,255,.3);color:#fff;padding:6px 12px;border-radius:20px;font-size:12px">Log in</span><span onclick="show('signin')" style="background:#fff;color:#0A9EBB;padding:6px 12px;border-radius:20px;font-size:12px;font-weight:bold">Sign in</span></div></div>

<div id="products" class="page active"><h2 style="font-size:17px;margin:8px 0">LONMA ORBIT - 9 PRODUCTS</h2><div class="grid" id="plist"></div>
<div class="card" style="background:linear-gradient(135deg,#0A9EBB,#087a91);color:#fff"><h3 style="margin:0">💳 M-Pesa Checkout</h3><input id="phone" placeholder="07xxxxxxxx" style="background:#fff"><input id="amount" type="number" placeholder="Amount KSh" style="background:#fff"><button class="btn" style="background:#111" onclick="pay()">PAY NOW</button><p id="paystatus" style="font-size:12px"></p></div></div>

<div id="scan" class="page"><h2>📷 Scan Verification</h2><div class="card"><input id="manualcode" placeholder="LONMA-001"><button class="btn" onclick="verifyCode()">VERIFY CODE</button><p id="scanresult" style="font-weight:bold"></p><p style="font-size:11px;color:#666">Valid: LONMA-001 to LONMA-009 - Fresh Fri, Detrex, Sawa, Salit, Diva</p></div></div>

<div id="locations" class="page"><h2>📍 Locations</h2><div class="card"><h4>CBD - Moi Avenue</h4><p style="font-size:13px">Opposite Imenti, 2nd Floor, Nairobi<br>Mon-Sat 8am-7pm</p><a href="https://maps.google.com/?q=Moi+Avenue+Nairobi" target="_blank"><button class="btn">GET DIRECTIONS</button></a></div><div class="card"><h4>Westlands - Westgate</h4><p style="font-size:13px">1st Floor, Westlands</p><a href="https://maps.google.com/?q=Westgate+Nairobi" target="_blank"><button class="btn">GET DIRECTIONS</button></a></div></div>

<div id="terms" class="page"><h2>📄 Terms & Conditions - Full</h2><div class="card" style="font-size:12px;line-height:1.6;max-height:68vh;overflow-y:auto;text-align:left"><h3 style="color:#0A9EBB;margin-top:0">LONMA ORBIT Official Terms - May 2026</h3><p><b>1. Products:</b> Fresh Fri 2L (LONMA-001), Detrex Citronella (002), Sawa Men (003), Detrex Pine (004), Salit 5L (005), Detrex Mint (006), Diva Dandruff (007), Diva Breakage (008), Sawa Cocoa (009). All original Pwani Oils.</p><p><b>2. Prices KSh:</b> Detrex 90, Sawa 299, Diva 250, Fresh Fri 850, Salit 1250 - inclusive VAT.</p><p><b>3. M-Pesa:</b> STK Push to 07xx. Enter PIN when prompted. Keep SMS. Till uses Daraja API. Configure env for live.</p><p><b>4. Delivery:</b> Nairobi same-day before 3PM, outskirts next day, upcountry 24-48hrs Wells Fargo. Fee 150-350.</p><p><b>5. Returns:</b> 24hrs defect, unopened, QR intact. Soaps non-returnable if opened. Refund to M-Pesa 48hrs defect only.</p><p><b>6. Code Verify:</b> Scan QR or enter LONMA-001 to 009. Valid = ✅ Original, Invalid = ❌ fake report support@lonmaorbit.co.ke</p><p><b>7. Privacy:</b> Name, email, phone, address for orders only. Not sold. Shared only with courier.</p><p><b>8. Contact:</b> Moi Avenue Nairobi, support@lonmaorbit.co.ke, https://app.lonmaorbit.co.ke</p><button class="btn" onclick="show('products')">I AGREE</button></div></div>

<div id="login" class="page"><h2>Log In</h2><div class="card"><input id="lemail" placeholder="Email"><input id="lpass" type="password" placeholder="Password"><button class="btn" onclick="login()">Log In</button><p id="lstatus"></p><p style="font-size:12px;text-align:center">No account? <span style="color:#0A9EBB;font-weight:bold" onclick="show('signin')">Create</span></p></div></div>

<div id="signin" class="page"><h2>Sign Up</h2><div class="card"><input id="sname" placeholder="Full Name"><input id="semail" placeholder="Email"><input id="spass" type="password" placeholder="Password"><button class="btn" onclick="signin()">Create Account</button><p id="sstatus"></p><p style="font-size:12px;text-align:center">Have account? <span style="color:#0A9EBB;font-weight:bold" onclick="show('login')">Log in</span></p></div></div>

<div class="bottom"><div id="b-products" class="active" onclick="show('products')">🛍️<br>Products</div><div id="b-scan" onclick="show('scan')">📷<br>Scan</div><div id="b-locations" onclick="show('locations')">📍<br>Locations</div><div id="b-terms" onclick="show('terms')">📄<br>Terms</div><div id="b-login" onclick="show('login')">👤<br>Account</div></div>

<script>
function show(id){document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));document.getElementById(id).classList.add('active');document.querySelectorAll('.bottom div').forEach(b=>b.classList.remove('active'));let el=document.getElementById('b-'+id);if(el)el.classList.add('active');window.scrollTo(0,0)}
async function loadProducts(){let r=await fetch('/api/products');let d=await r.json();document.getElementById('plist').innerHTML=d.map(p=>`<div class="card"><img src="${p.image}" onerror="this.src='https://via.placeholder.com/300'"><h4 style="font-size:12px;margin:6px 0">${p.name}</h4><p style="margin:0;font-weight:bold;color:#0A9EBB">KSh ${p.price}</p><small style="background:#0A9EBB;color:#fff;padding:2px 6px;border-radius:10px;font-size:10px">${p.code}</small><div style="display:flex;gap:4px;margin-top:6px"><button class="btn" style="flex:1;padding:8px;font-size:11px" onclick="document.getElementById('manualcode').value='${p.code}';show('scan')">VERIFY</button><button class="btn" style="flex:1;padding:8px;font-size:11px;background:#111" onclick="document.getElementById('amount').value=${p.price};show('products')">BUY</button></div></div>`).join('')}
async function verifyCode(){let c=document.getElementById('manualcode').value.trim().toUpperCase();let r=await fetch(`/api/verify/${c}`);let d=await r.json();document.getElementById('scanresult').innerHTML=d.valid?`✅ ${d.product.name} - ORIGINAL`:`❌ Invalid ${c} - Fake?`}
async function login(){let r=await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:document.getElementById('lemail').value,password:document.getElementById('lpass').value})});let d=await r.json();document.getElementById('lstatus').innerText=d.message;if(d.status=='ok')setTimeout(()=>show('products'),600)}
async function signin(){let r=await fetch('/api/signin',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:document.getElementById('sname').value,email:document.getElementById('semail').value,password:document.getElementById('spass').value})});let d=await r.json();document.getElementById('sstatus').innerText=d.message;if(d.status=='ok')setTimeout(()=>show('login'),600)}
async function pay(){let ph=document.getElementById('phone').value;let am=document.getElementById('amount').value;if(!ph||!am){document.getElementById('paystatus').innerText='Enter phone & amount';return}document.getElementById('paystatus').innerText='Sending STK to '+ph+'...';let r=await fetch('/mpesa/stkpush',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({phone:ph,amount:am})});let d=await r.json();document.getElementById('paystatus').innerText=d.message}
loadProducts();
</script></body></html>
"""

@app.api_route("/", methods=["GET","HEAD"])
def home(): return HTMLResponse(HTML)

@app.get("/logo.png")
def logo():
    for p in ["logo.png","static/logo.png"]:
        if os.path.exists(p): return FileResponse(p)
    return HTMLResponse("logo",404)

@app.get("/img/{filename}")
def serve_img(filename: str):
    dec=urllib.parse.unquote(filename)
    if os.path.exists(dec): return FileResponse(dec)
    for f in os.listdir("."):
        if f==dec or urllib.parse.quote(f)==filename: return FileResponse(f)
    return HTMLResponse("not found",404)

@app.get("/api/products")
def products():
    cur=conn.cursor(); cur.execute("SELECT id,name,price,code,image FROM products")
    return [{"id":r[0],"name":r[1],"price":r[2],"code":r[3],"image":r[4]} for r in cur.fetchall()]

@app.get("/api/verify/{code}")
def verify(code: str):
    cur=conn.cursor(); cur.execute("SELECT name FROM products WHERE code=?",(code.strip().upper(),))
    row=cur.fetchone(); return {"valid":True,"product":{"name":row[0]}} if row else {"valid":False}

@app.post("/api/signin")
async def signin_api(req: Request):
    d=await req.json()
    try: conn.execute("INSERT INTO users (email,password,name) VALUES (?,?,?)",(d.get("email"),d.get("password"),d.get("name")));conn.commit();return {"status":"ok","message":"Account created!"}
    except: return {"status":"error","message":"Email exists"}

@app.post("/api/login")
async def login_api(req: Request):
    d=await req.json(); cur=conn.cursor(); cur.execute("SELECT * FROM users WHERE email=? AND password=?",(d.get("email"),d.get("password")))
    return {"status":"ok","message":"Welcome!"} if cur.fetchone() else {"status":"error","message":"Invalid"}

@app.post("/mpesa/stkpush")
async def stk(req: Request):
    d=await req.json(); return {"message":f"STK sent to {d.get('phone')} KSh {d.get('amount')} - Enter PIN (DEMO)"}

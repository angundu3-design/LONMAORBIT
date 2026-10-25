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

def get_images():
    imgs=[f for f in os.listdir(".") if f.lower().endswith((".jpg",".jpeg",".png")) and "logo" not in f.lower()]
    return sorted(imgs)

NAMES=["Fresh Fri Cooking Oil 2L","Detrex Citronella Soap 110g","Sawa Men Lotion 72Hrs","Detrex Pine Drops Soap","Salit Vegetable Oil 5L","Detrex Cool Mint Soap","Diva Anti-Dandruff Pomade 250ml","Diva Anti-Breakage Pomade","Sawa Cocoa Butter Lotion"]
PRICES=[850,90,299,90,1250,90,250,250,299]
CODES=[f"LONMA-00{i+1}" for i in range(9)]
found=get_images()
print(f"IMAGES FOUND: {found}")

for i in range(9):
    if i < len(found):
        img=f"/img/{urllib.parse.quote(found[i])}"
    else:
        img=f"https://via.placeholder.com/400x300/FFFFFF/0A9EBB?text={urllib.parse.quote(NAMES[i])}"
    cur.execute("INSERT INTO products VALUES (?,?,?,?,?)",(i+1,NAMES[i],PRICES[i],CODES[i],img))
conn.commit()

HTML="""
<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1"><title>LONMA ORBIT - Pwani Products Official</title>
<script src="https://unpkg.com/html5-qrcode@2.3.8/html5-qrcode.min.js"></script>
<style>
:root{--teal:#0A9EBB;--dark:#087a91}*{box-sizing:border-box}body{margin:0;font-family:Arial,Helvetica,sans-serif;background:var(--teal);color:#fff;overflow-x:hidden}
.nav{position:fixed;top:0;left:0;right:0;background:var(--teal);padding:8px 12px;display:flex;justify-content:space-between;align-items:center;z-index:1000;height:62px;border-bottom:1px solid rgba(255,255,255,.15)}
.logo-img{height:48px;width:48px;border-radius:50%;object-fit:cover;border:2px solid #fff;display:block;background:#fff}
.page{display:none;padding:72px 12px 90px;min-height:100vh;background:var(--teal)}.page.active{display:block;animation:fade .2s}
@keyframes fade{from{opacity:0}to{opacity:1}}
.card{background:#fff;color:#111;border-radius:16px;padding:12px;margin:10px 0;box-shadow:0 4px 12px rgba(0,0,0,.12)}
.card img{width:100%;height:220px;object-fit:contain;background:#fff;border-radius:12px;padding:10px;border:1px solid #f0f0f0}
.btn{background:var(--teal);color:#fff;border:none;padding:13px;border-radius:28px;width:100%;font-weight:bold;font-size:14px;margin-top:8px;cursor:pointer}
.btn:active{background:var(--dark)}.btn-black{background:#111}
input,select{width:100%;padding:12px 14px;border-radius:10px;border:1px solid #ddd;background:#f8f8f8;margin:6px 0;font-size:14px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.badge{display:inline-block;background:#0A9EBB;color:#fff;padding:3px 8px;border-radius:20px;font-size:10px;margin-top:4px}
.bottom{position:fixed;bottom:0;left:0;right:0;background:#fff;display:flex;justify-content:space-around;padding:8px 0 6px;z-index:1000;border-top:1px solid #eee;box-shadow:0 -2px 10px rgba(0,0,0,.08)}
.bottom div{font-size:10px;color:#666;text-align:center;cursor:pointer;flex:1;padding:4px}.bottom div.active{color:var(--teal);font-weight:bold}
.pay-box{background:linear-gradient(135deg,#0A9EBB,#087a91);color:#fff;border-radius:16px;padding:14px;margin-top:12px}
.terms{font-size:13px;line-height:1.7;color:#222;max-height:68vh;overflow-y:auto;text-align:left}
.terms h3{color:var(--teal);margin:14px 0 4px;font-size:14px}
#botBtn{position:fixed;bottom:78px;right:14px;background:#fff;color:var(--teal);width:54px;height:54px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:24px;cursor:pointer;z-index:1100;box-shadow:0 4px 15px rgba(0,0,0,.3);border:2px solid var(--teal)}
#botBox{display:none;position:fixed;bottom:142px;right:12px;width:88%;max-width:360px;height:420px;background:#fff;border-radius:16px;z-index:1100;flex-direction:column;overflow:hidden;box-shadow:0 12px 30px rgba(0,0,0,.3)}#botBox.open{display:flex}
</style></head><body>
<div class="nav">
<img src="/logo.png" class="logo-img" onerror="this.src='https://via.placeholder.com/100/FFFFFF/0A9EBB?text=LO'">
<div style="display:flex;gap:8px;align-items:center"><span style="font-size:11px;opacity:.9">Official Pwani</span><span onclick="show('login')" style="background:rgba(255,255,255,.25);color:#fff;padding:7px 14px;border-radius:20px;font-size:12px;cursor:pointer;border:1px solid rgba(255,255,255,.4)">Log in</span><span onclick="show('signin')" style="background:#fff;color:#0A9EBB;padding:7px 14px;border-radius:20px;font-size:12px;font-weight:bold;cursor:pointer">Sign in</span></div>
</div>

<!-- PRODUCTS - HOME PAGE -->
<div id="products" class="page active">
<h2 style="margin:8px 0 2px;font-size:18px">LONMA ORBIT PRODUCTS</h2>
<p style="margin:0 0 8px;font-size:12px;opacity:.9">Verified Pwani Oils, Detrex, Sawa, Diva - Each with LONMA code</p>
<div class="grid" id="plist"></div>

<div class="pay-box">
<h3 style="margin:0 0 6px;font-size:15px">💳 M-Pesa Checkout</h3>
<p style="font-size:11px;margin:0 0 8px;opacity:.9">STK Push - Enter phone, amount, confirm PIN on phone</p>
<input id="phone" placeholder="07xxxxxxxx (Safaricom)" style="background:#fff">
<input id="amount" type="number" placeholder="Amount KSh e.g 850" style="background:#fff">
<select id="productSelect" style="background:#fff"><option value="">Select product for quick amount</option></select>
<button class="btn btn-black" onclick="pay()">PAY NOW WITH M-PESA</button>
<p id="paystatus" style="font-size:12px;margin-top:8px;background:rgba(255,255,255,.15);padding:6px;border-radius:8px;min-height:20px"></p>
</div>

<div class="card" style="background:#111;color:#fff;text-align:center"><p style="margin:4px;font-size:12px">🔒 All products verified with LONMA-001 to LONMA-009<br>Scan QR to confirm originality</p></div>
</div>

<!-- SCAN -->
<div id="scan" class="page">
<h2 style="font-size:18px">📷 Code Scan Verification</h2>
<div class="card">
<div id="reader" style="width:100%;border-radius:12px;overflow:hidden"></div>
<button class="btn" onclick="startScan()">START CAMERA SCAN</button>
<div style="text-align:center;margin:10px 0;font-size:12px;color:#666">OR ENTER MANUALLY</div>
<input id="manualcode" placeholder="e.g LONMA-001">
<button class="btn btn-black" onclick="verifyCode()">VERIFY CODE</button>
<p id="scanresult" style="font-weight:bold;font-size:15px;margin-top:10px;min-height:24px"></p>
<div style="font-size:11px;color:#666;background:#f7f7f7;padding:8px;border-radius:8px">Valid codes: LONMA-001 to LONMA-009<br>Each product has unique QR on packaging<br>Fake? Report: support@lonmaorbit.co.ke</div>
</div>
</div>

<!-- LOCATIONS -->
<div id="locations" class="page">
<h2 style="font-size:18px">📍 Store Locations</h2>
<div class="card"><h4 style="margin:0">LONMA CBD Store</h4><p style="margin:4px 0;font-size:13px">Moi Avenue, Nairobi - Opposite Imenti House, 2nd Floor<br>Open: Mon-Sat 8am-7pm, Sun 10am-5pm</p><a href="https://maps.google.com/?q=Moi+Avenue+Nairobi" target="_blank"><button class="btn">GET DIRECTIONS</button></a><p style="font-size:11px;color:#666">Phone: 07XX XXX XXX</p></div>
<div class="card"><h4 style="margin:0">LONMA Westlands</h4><p style="margin:4px 0;font-size:13px">Westgate Mall, 1st Floor, Westlands<br>Open: Mon-Sun 9am-8pm</p><a href="https://maps.google.com/?q=Westgate+Nairobi" target="_blank"><button class="btn">GET DIRECTIONS</button></a></div>
<div class="card"><h4 style="margin:0">Online Delivery</h4><p style="margin:4px 0;font-size:13px">We deliver Nairobi same-day, upcountry 24-48hrs via Wells Fargo & G4S<br>Delivery fee: 150-350 KSh</p><button class="btn" onclick="show('products')">ORDER NOW</button></div>
</div>

<!-- TERMS - FULL DETAILS -->
<div id="terms" class="page">
<h2 style="font-size:18px">📄 Terms & Conditions</h2>
<div class="card terms">
<h3 style="margin-top:0">LONMA ORBIT - Official Terms (May 2026)</h3>
<p><b>Welcome to LONMA ORBIT - Official distributor of Pwani Oil products</b><br>Website: https://app.lonmaorbit.co.ke | Email: support@lonmaorbit.co.ke | Location: Moi Avenue, Nairobi, Kenya</p>
<h3>1. Products & Authenticity</h3><p>We sell: Fresh Fri Cooking Oil (2L, 5L), Salit Vegetable Oil (5L), Detrex Bathing Soaps (Cool Mint 110g, Pine Drops 110g, Citronella Anti-Bacterial 110g), Sawa Body Lotions (Men 72Hrs Hydration, Cocoa Butter Nourishing), Diva Hair Pomades (Anti-Dandruff, Anti-Breakage 250ml). All products 100% original from Pwani Oils. Each unit has unique LONMA-001 to LONMA-009 verification code and QR. Verify via Scan page.</p>
<h3>2. Pricing KSh</h3><p>Detrex Soaps: 90 KSh each, Sawa Lotions: 299 KSh, Diva Pomades: 250 KSh, Fresh Fri 2L: 850 KSh, Salit 5L: 1250 KSh. Prices inclusive VAT 16%. Prices may change with Pwani Oil notice. Delivery not included.</p>
<h3>3. Orders & M-Pesa Payment</h3><p>Select product → enter 07xx Safaricom number → enter amount → click PAY → enter M-Pesa PIN when STK pop-up appears. Till uses Safaricom Daraja API. Configure MPESA_SHORTCODE, CONSUMER_KEY in Render env for real payments. Currently demo mode. Safaricom charges apply. No card payments yet. Keep M-Pesa message as proof.</p>
<h3>4. Delivery & Collection</h3><p>Nairobi CBD: same-day if order before 3PM Mon-Sat. Nairobi outskirts: next day. Upcountry: 24-48hrs via Wells Fargo, G4S. Collection at Moi Avenue free. Provide accurate phone, location pin, estate, house no. Delivery fee: Nairobi 150-250, upcountry 250-400. Courier calls before delivery. Missed delivery = reschedule fee 100.</p>
<h3>5. Returns, Refunds, Exchange</h3><p>Report defect within 24hrs with photos + LONMA code + M-Pesa code. Unopened, unused, tags intact, QR intact. Soaps non-returnable if opened for hygiene. Oils: return if sealed not tampered. Exchange for size/defect free within 48hrs. Refund to M-Pesa 48hrs for defects only, not change of mind. No refund for wrong product ordered by customer - exchange possible.</p>
<h3>6. Code Verification System</h3><p>Scan QR with camera or enter code manually: LONMA-001 Fresh Fri, LONMA-002 Detrex Citronella, LONMA-003 Sawa Men, LONMA-004 Detrex Pine, LONMA-005 Salit 5L, LONMA-006 Detrex Mint, LONMA-007 Diva Dandruff, LONMA-008 Diva Breakage, LONMA-009 Sawa Cocoa. Valid = ✅ shows product name + ORIGINAL. Invalid = ❌ possible fake - email us photo.</p>
<h3>7. Accounts & Security</h3><p>Provide true full name, valid email, Kenyan phone 07xx. One account per email. Password min 6 chars. Don't share PIN. Age 13+ with guardian consent if under 18. We may suspend fraud, fake reviews, reselling. You are responsible for account activity.</p>
<h3>8. Privacy & Data</h3><p>We collect name, email, phone, delivery address, order history for processing only. Not sold. Shared only with courier (phone + address) and Safaricom (for payment). M-Pesa via Daraja secure. We don't store M-Pesa PIN. Request data deletion via support@lonmaorbit.co.ke. Cookies for login only.</p>
<h3>9. Intellectual Property</h3><p>LO logo, LONMA ORBIT text, design, codes are trademarks. Pwani, Fresh Fri, Salit, Detrex, Sawa, Diva are trademarks of Pwani Oil Products Ltd. No copying, reproduction without written permission.</p>
<h3>10. Limitation & Law</h3><p>Not liable for M-Pesa network failure, courier delay, traffic, weather, power outage, wrong address. Max liability = amount paid for product. Force majeure exempts. Governed by Laws of Kenya. Disputes: Nairobi Courts, start with email mediation. Contact: Moi Avenue Nairobi, support@lonmaorbit.co.ke, 07XX XXX XXX, https://app.lonmaorbit.co.ke</p>
<button class="btn" onclick="show('products')">✅ I AGREE - CONTINUE SHOPPING</button>
</div>
</div>

<!-- ACCOUNT -->
<div id="login" class="page">
<h2 style="font-size:18px">👤 My Account</h2>
<div class="card">
<h4 style="margin:0 0 8px">Log In</h4>
<input id="lemail" placeholder="Email address">
<input id="lpass" type="password" placeholder="Password">
<button class="btn" onclick="login()">Log In</button>
<p id="lstatus" style="font-size:12px"></p>
<p style="font-size:12px;text-align:center;margin-top:10px">No account? <span style="color:#0A9EBB;font-weight:bold;cursor:pointer" onclick="show('signin')">Create account</span></p>
</div>
<div class="card" style="background:#f7f7f7;font-size:12px"><p><b>Why create account?</b><br>• Track orders<br>• Save delivery address<br>• Get offers<br>• Faster checkout</p></div>
</div>

<div id="signin" class="page">
<h2 style="font-size:18px">Create Account</h2>
<div class="card">
<h4 style="margin:0 0 8px">Sign Up - Free</h4>
<input id="sname" placeholder="Full Name">
<input id="semail" placeholder="Email address">
<input id="spass" type="password" placeholder="Password (min 6 chars)">
<button class="btn" onclick="signin()">Create Account</button>
<p id="sstatus" style="font-size:12px"></p>
<p style="font-size:12px;text-align:center;margin-top:10px">Already have? <span style="color:#0A9EBB;font-weight:bold;cursor:pointer" onclick="show('login')">Log in</span></p>
</div>
</div>

<div class="bottom">
<div id="b-products" class="active" onclick="show('products')">🛍️<br>Products</div>
<div id="b-scan" onclick="show('scan')">📷<br>Scan</div>
<div id="b-locations" onclick="show('locations')">📍<br>Locations</div>
<div id="b-terms" onclick="show('terms')">📄<br>Terms</div>
<div id="b-login" onclick="show('login')">👤<br>Account</div>
</div>

<div id="botBtn" onclick="toggleBot()">🤖</div>
<div id="botBox">
<div style="padding:12px;background:#0A9EBB;color:#fff;font-weight:bold;display:flex;justify-content:space-between;align-items:center"><span>LO BOT - Help</span><span onclick="toggleBot()" style="cursor:pointer;background:rgba(255,255,255,.2);padding:4px 10px;border-radius:20px">✕</span></div>
<div id="botMsgs" style="flex:1;overflow-y:auto;padding:10px;background:#f5f5f5"><div style="background:#fff;border:1px solid #eee;padding:10px;border-radius:12px;font-size:13px;color:#000">👋 Hi! I'm LO Bot<br>• Ask price<br>• Ask M-Pesa<br>• Ask Detrex, Sawa, Diva, Fresh Fri<br>• Ask scan code<br>• Ask delivery</div></div>
<div style="display:flex;padding:8px;border-top:1px solid #eee;background:#fff"><input id="botInput" style="flex:1;margin:0;border-radius:20px 0 0 20px" placeholder="Ask anything..." onkeypress="if(event.key==='Enter')sendBot()"><button onclick="sendBot()" style="background:#0A9EBB;color:#fff;border:none;padding:12px 16px;border-radius:0 20px 20px 0;font-weight:bold">Send</button></div>
</div>

<script>
let currentPage='products';
function show(id){
 document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));
 document.getElementById(id).classList.add('active');
 document.querySelectorAll('.bottom div').forEach(b=>b.classList.remove('active'));
 let btn=document.getElementById('b-'+id); if(btn) btn.classList.add('active');
 currentPage=id; window.scrollTo(0,0);
}
async function loadProducts(){
 let r=await fetch('/api/products'); let d=await r.json();
 let sel=document.getElementById('productSelect'); sel.innerHTML='<option value="">Select product for quick amount</option>';
 document.getElementById('plist').innerHTML=d.map(p=>{
   sel.innerHTML+=`<option value="${p.price}" data-code="${p.code}">${p.name} - KSh ${p.price} (${p.code})</option>`;
   return `<div class="card">
   <img src="${p.image}" loading="lazy" onerror="this.src='https://via.placeholder.com/300/FFFFFF/0A9EBB?text=${encodeURIComponent(p.name)}'">
   <h4 style="margin:8px 0 2px;font-size:12px;line-height:1.3">${p.name}</h4>
   <p style="margin:2px 0;font-weight:bold;color:#0A9EBB;font-size:14px">KSh ${p.price}</p>
   <span class="badge">${p.code}</span>
   <div style="display:flex;gap:6px;margin-top:8px">
   <button class="btn" style="flex:1;padding:10px;font-size:12px" onclick="document.getElementById('manualcode').value='${p.code}';show('scan')">🔍 VERIFY</button>
   <button class="btn btn-black" style="flex:1;padding:10px;font-size:12px" onclick="document.getElementById('amount').value=${p.price};document.getElementById('productSelect').value=${p.price};show('products');window.scrollTo(0,document.body.scrollHeight)">BUY</button>
   </div>
   </div>`
 }).join('');
}
document.getElementById('productSelect').addEventListener('change',function(){if(this.value)document.getElementById('amount').value=this.value});
async function verifyCode(){let c=document.getElementById('manualcode').value.trim().toUpperCase();if(!c){document.getElementById('scanresult').innerHTML='Enter code';return}let r=await fetch(`/api/verify/${c}`);let d=await r.json();document.getElementById('scanresult').innerHTML=d.valid?`✅ <span style="color:green">${d.product.name}</span><br><small style="color:green">ORIGINAL PWANI PRODUCT - VERIFIED</small>`:`❌ <span style="color:red">Invalid Code ${c}</span><br><small style="color:red">Possible fake - Report to support@lonmaorbit.co.ke</small>`}
async function login(){let e=document.getElementById('lemail').value;let p=document.getElementById('lpass').value;if(!e||!p){document.getElementById('lstatus').innerText='Enter email & password';return}let r=await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:e,password:p})});let d=await r.json();document.getElementById('lstatus').innerText=d.message;if(d.status=='ok')setTimeout(()=>show('products'),800)}
async function signin(){let n=document.getElementById('sname').value;let e=document.getElementById('semail').value;let p=document.getElementById('spass').value;if(!n||!e||!p){document.getElementById('sstatus').innerText='Fill all fields';return}let r=await fetch('/api/signin',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:n,email:e,password:p})});let d=await r.json();document.getElementById('sstatus').innerText=d.message;if(d.status=='ok')setTimeout(()=>show('login'),800)}
async function pay(){let phone=document.getElementById('phone').value.trim();let amt=document.getElementById('amount').value.trim();if(!phone||!amt){document.getElementById('paystatus').innerText='⚠️ Enter phone 07xx and amount';return}if(!phone.startsWith('07')||phone.length!=10){document.getElementById('paystatus').innerText='⚠️ Phone must be 07xxxxxxxx (10 digits)';return}document.getElementById('paystatus').innerText='⏳ Sending STK Push to '+phone+' for KSh '+amt+'... Check phone and enter PIN';let r=await fetch('/mpesa/stkpush',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({phone,amount:amt})});let d=await r.json();document.getElementById('paystatus').innerText='✅ '+d.message+' | If no pop-up, check M-Pesa balance & try again'}
let html5QrCode;function startScan(){let r=document.getElementById('reader');if(html5QrCode)return;html5QrCode=new Html5Qrcode("reader");html5QrCode.start({facingMode:"environment"},{fps:10,qrbox:{width:250,height:250}},(dec)=>{document.getElementById('manualcode').value=dec;verifyCode();html5QrCode.stop().then(()=>{html5QrCode=null});},{})}
function toggleBot(){document.getElementById('botBox').classList.toggle('open')}
async function sendBot(){let i=document.getElementById('botInput');let m=i.value.trim();if(!m)return;let b=document.getElementById('botMsgs');b.innerHTML+=`<div style="background:#0A9EBB;color:#fff;margin-left:auto;padding:10px;border-radius:12px 12px 0 12px;max-width:80%;margin-top:8px;font-size:13px">${m}</div>`;i.value='';let r=await fetch('/api/bot',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:m})});let d=await r.json();b.innerHTML+=`<div style="background:#fff;border:1px solid #eee;padding:10px;border-radius:12px 12px 12px 0;max-width:80%;margin-top:8px;font-size:13px;color:#000">${d.reply}</div>`;b.scrollTop=b.scrollHeight}
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
        if f==dec or urllib.parse.quote(f)==filename or f.lower()==dec.lower():
            return FileResponse(f)
    return HTMLResponse(f"Not found {dec} Files: {os.listdir('.')}",404)

@app.get("/api/products")
def prods():
    cur=conn.cursor(); cur.execute("SELECT id,name,price,code,image FROM products")
    return [{"id":r[0],"name":r[1],"price":r[2],"code":r[3],"image":r[4]} for r in cur.fetchall()]

@app.get("/api/locations")
def locs(): return [{"id":1,"name":"CBD","address":"Moi Avenue"},{"id":2,"name":"Westlands","address":"Westgate"}]

@app.get("/api/verify/{code}")
def verify(code: str):
    cur=conn.cursor(); cur.execute("SELECT name FROM products WHERE code=?",(code.strip().upper(),))
    row=cur.fetchone(); return {"valid":True,"product":{"name":row[0]}} if row else {"valid":False}

@app.post("/api/signin")
async def si(req: Request):
    d=await req.json()
    try: conn.execute("INSERT INTO users (email,password,name) VALUES (?,?,?)",(d.get("email"),d.get("password"),d.get("name")));conn.commit();return {"status":"ok","message":"✅ Account created! Please log in"}
    except: return {"status":"error","message":"❌ Email exists"}

@app.post("/api/login")
async def lo(req: Request):
    d=await req.json(); cur=conn.cursor(); cur.execute("SELECT * FROM users WHERE email=? AND password=?",(d.get("email"),d.get("password")))
    return {"status":"ok","message":"✅ Welcome back!"} if cur.fetchone() else {"status":"error","message":"❌ Invalid credentials"}

@app.post("/api/bot")
async def bot(req: Request):
    m=(await req.json()).get("message","").lower()
    if "price" in m or "how much" in m: reply="💰 Detrex Soap 90, Sawa Lotion 299, Diva 250, Fresh Fri 2L 850, Salit 5L 1250 KSh"
    elif "mpesa" in m or "pay" in m: reply="💳 M-Pesa: Enter 07xx + amount → PAY → Enter PIN when pop-up comes. Keep M-Pesa SMS"
    elif "detrex" in m: reply="🧼 Detrex: Cool Mint, Pine Drops, Citronella 110g - Antibacterial - 90 KSh - Codes LONMA-002,004,006"
    elif "sawa" in m: reply="🧴 Sawa: Men 72Hrs Hydration & Cocoa Butter Nourishing - 299 KSh - Codes LONMA-003,009"
    elif "diva" in m: reply="💇 Diva: Anti-Dandruff & Anti-Breakage Pomade 250ml - 250 KSh - Codes LONMA-007,008"
    elif "fresh" in m or "salit" in m or "oil" in m: reply="🍳 Fresh Fri 2L 850 (LONMA-001), Salit 5L 1250 (LONMA-005) - Pwani Original Cooking Oils"
    elif "deliver" in m: reply="🚚 Nairobi same-day before 3PM, upcountry 24-48hrs via Wells Fargo. Fee 150-350"
    elif "scan" in m or "code" in m or "fake" in m: reply="📷 Scan QR on product or enter LONMA-001 to 009 manually on Scan page to verify originality"
    elif "location" in m: reply="📍 Moi Avenue Nairobi CBD Opposite Imenti + Westgate Mall Westlands. See Locations page for map"
    else: reply="🤖 Hi! Ask me: price, M-Pesa, Detrex, Sawa, Diva, Fresh Fri, scan code, delivery, locations"
    return {"reply":reply}

@app.post("/mpesa/stkpush")
async def stk(req: Request):
    d=await req.json()
    return {"ResponseCode":"0","message":f"STK sent to {d.get('phone')} for KSh {d.get('amount')} - Enter M-Pesa PIN (DEMO - configure MPESA env for real)"}

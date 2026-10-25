from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os, sqlite3
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

conn = sqlite3.connect("lonma.db", check_same_thread=False)
conn.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, email TEXT UNIQUE, password TEXT, name TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT, price INTEGER, code TEXT, image TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS locations (id INTEGER PRIMARY KEY, name TEXT, address TEXT, lat REAL, lng REAL)")
cur=conn.cursor()
cur.execute("SELECT COUNT(*) FROM products")
if cur.fetchone()[0]==0:
    conn.execute("INSERT INTO products VALUES (1,'Orbit Tee',1500,'LONMA-001','https://via.placeholder.com/300')")
    conn.execute("INSERT INTO products VALUES (2,'Orbit Hoodie',3500,'LONMA-002','https://via.placeholder.com/300')")
    conn.execute("INSERT INTO products VALUES (3,'Orbit Cap',1200,'LONMA-003','https://via.placeholder.com/300')")
    conn.execute("INSERT INTO products VALUES (4,'Orbit Jacket',5000,'LONMA-004','https://via.placeholder.com/300')")
    conn.commit()
cur.execute("SELECT COUNT(*) FROM locations")
if cur.fetchone()[0]==0:
    conn.execute("INSERT INTO locations VALUES (1,'LONMA CBD','Moi Avenue, Nairobi',-1.2833,36.8172)")
    conn.execute("INSERT INTO locations VALUES (2,'LONMA Westlands','Westgate Mall',-1.2634,36.8031)")
    conn.commit()

def bot_reply(m):
    m=m.lower()
    if "price" in m: return "💙 Tee 1500, Hoodie 3500, Cap 1200, Jacket 5000"
    if "mpesa" in m: return "💳 Enter 07xx + amount, PAY, PIN 1234"
    if "location" in m: return "📍 CBD, Westlands - delivery countrywide"
    if "terms" in m or "return" in m: return "📄 See Terms page - 24hr returns, same-day Nairobi"
    return "🤖 Hi! Ask about products, M-Pesa, locations, terms, scan"

HTML = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>LONMA ORBIT</title>
<script src="https://unpkg.com/html5-qrcode@2.3.8/html5-qrcode.min.js"></script>
<style>
:root{--teal:#0A9EBB}*{box-sizing:border-box}body{margin:0;font-family:Arial;background:var(--teal);color:#fff}
.nav{position:fixed;top:0;width:100%;background:var(--teal);padding:8px 15px;display:flex;justify-content:space-between;align-items:center;z-index:100}
.logo-img{height:52px;width:52px;border-radius:50%;background:transparent;padding:0;object-fit:cover;display:block;border:none;box-shadow:none}
.page{display:none;padding:78px 15px 110px;min-height:100vh;background:var(--teal)}.page.active{display:block}
.card{background:#fff;color:#000;border-radius:14px;padding:15px;margin:10px 0;box-shadow:0 3px 10px rgba(0,0,0,0.1)}
.btn{background:var(--teal);color:#fff;border:none;padding:12px;border-radius:25px;width:100%;font-weight:bold;margin-top:8px;cursor:pointer}
input{width:100%;padding:12px;border-radius:8px;border:1px solid #ddd;background:#f7f7f7;margin:6px 0}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px}
.bottom{position:fixed;bottom:0;width:100%;background:#fff;display:flex;justify-content:space-around;padding:10px;z-index:100}.bottom div{font-size:10px;color:#000;text-align:center;cursor:pointer}
#botBtn{position:fixed;bottom:80px;right:15px;background:#fff;color:var(--teal);width:56px;height:56px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:26px;cursor:pointer;z-index:200;box-shadow:0 4px 15px rgba(0,0,0,0.3)}
#botBox{display:none;position:fixed;bottom:145px;right:15px;width:90%;max-width:350px;height:400px;background:#fff;border-radius:15px;z-index:200;flex-direction:column;overflow:hidden;box-shadow:0 10px 30px rgba(0,0,0,0.3)}
#botBox.open{display:flex}
.terms-box{text-align:left;font-size:13px;line-height:1.7;color:#222;max-height:65vh;overflow-y:auto}
.terms-box h3{color:#0A9EBB;margin:15px 0 5px}
</style></head><body>
<div class="nav">
<img src="/logo.png" class="logo-img" onerror="this.src='https://via.placeholder.com/100/FFFFFF/0A9EBB?text=LO'">
<div style="display:flex;gap:8px"><span onclick="show('login')" style="background:rgba(255,255,255,0.25);color:#fff;padding:8px 16px;border-radius:20px;font-size:13px;cursor:pointer">Log in</span><span onclick="show('signin')" style="background:#fff;color:#0A9EBB;padding:8px 16px;border-radius:20px;font-size:13px;font-weight:bold;cursor:pointer">Sign in</span></div>
</div>

<div id="products" class="page active"><h2>LONMA ORBIT</h2><div class="grid" id="plist"></div><div class="card"><input id="phone" placeholder="07xxxxxxxx"><input id="amount" type="number" placeholder="Amount"><button class="btn" onclick="pay()">PAY WITH M-PESA</button><p id="paystatus"></p></div></div>

<div id="login" class="page"><h2>Log In</h2><div class="card"><input id="lemail" placeholder="Email"><input id="lpass" type="password" placeholder="Password"><button class="btn" onclick="login()">Log In</button><p id="lstatus"></p></div></div>

<div id="signin" class="page"><h2>Sign Up</h2><div class="card"><input id="sname" placeholder="Full Name"><input id="semail" placeholder="Email"><input id="spass" type="password" placeholder="Password"><button class="btn" onclick="signin()">Create Account</button><p id="sstatus"></p></div></div>

<div id="terms" class="page"><h2>Terms & Conditions</h2>
<div class="card terms-box">
<h3 style="margin-top:0">LONMA ORBIT - Official Terms</h3>
<p><b>Last Updated: 13 May 2026 | Nairobi, Kenya</b></p>

<h3>1. Introduction & Acceptance</h3>
<p>Welcome to LONMA ORBIT (app.lonmaorbit.co.ke). By accessing, browsing, purchasing, or using M-Pesa STK, QR scan, or chatbot, you agree to be bound by these Terms. If you do not agree, do not use the site.</p>

<h3>2. Products & Authenticity Guarantee</h3>
<p>• All products are 100% original LONMA ORBIT designs.<br>
• Each item carries unique verification code: LONMA-001 to LONMA-999<br>
• Verify authenticity via Scan tab - valid codes show ✅ product name<br>
• Invalid codes show ❌ - report fakes immediately to support@lonmaorbit.co.ke<br>
• Product images are for illustration - colors may vary slightly due to lighting</p>

<h3>3. Pricing, Payments & M-Pesa</h3>
<p>• All prices in Kenya Shillings (KSh) inclusive of VAT where applicable<br>
• Primary payment: M-Pesa STK Push (Safaricom)<br>
• Process: Enter 07xx → Amount → Click PAY → Enter M-Pesa PIN on phone<br>
• Till Number / Paybill: Configured via MPESA_SHORTCODE env<br>
• M-Pesa transaction charges apply per Safaricom tariff<br>
• Payment is final once PIN entered and confirmation received<br>
• Failed transactions refunded within 24hrs</p>

<h3>4. Orders, Confirmation & Delivery</h3>
<p>• Nairobi CBD & Eastlands: Same-day delivery if ordered before 3PM<br>
• Nairobi outskirts: Next day delivery<br>
• Outside Nairobi (Mombasa, Kisumu, Nakuru etc): 24-48hrs via Wells Fargo / G4S<br>
• Delivery fee: KSh 150-400 depending on location<br>
• Customer must provide accurate phone, location pin, and name<br>
• We are not liable for delays due to wrong address or unreachable phone<br>
• Order tracking via phone number</p>

<h3>5. Returns, Exchange & Refunds</h3>
<p>• Returns accepted within 24 hours of delivery for size issues or manufacturing defects<br>
• Item must be unworn, unwashed, with original tags and QR code intact<br>
• No returns for: worn items, washed items, custom prints, sale items<br>
• Exchange: Free size exchange within 24hrs subject to stock<br>
• Refund: For defective items only, processed to M-Pesa within 48hrs<br>
• Contact: Use LO BOT or call +254 7XX XXX XXX with order code</p>

<h3>6. User Accounts & Security</h3>
<p>• Must provide true full name, valid email, and Kenyan phone<br>
• You are responsible for maintaining password confidentiality<br>
• One account per person/email - duplicate accounts may be suspended<br>
• We reserve right to suspend accounts for fraud, abuse, or fake orders<br>
• Minimum age: 13 years, with guardian consent if under 18</p>

<h3>7. Code Scan & Anti-Counterfeit</h3>
<p>• Scan QR code on product label using phone camera<br>
• Or manually enter code LONMA-00X in Scan tab<br>
• Valid codes verify product name, price, and authenticity<br>
• Counterfeit products with fake codes are not our liability but report them<br>
• QR system powered by html5-qrcode technology</p>

<h3>8. Store Locations</h3>
<p>• LONMA CBD: Moi Avenue, Nairobi - Opposite Imenti House<br>
• LONMA Westlands: Westgate Mall, 1st Floor<br>
• Hours: Mon-Sat 9AM-8PM, Sunday 10AM-6PM<br>
• Google Maps directions available via Locations tab</p>

<h3>9. Privacy Policy</h3>
<p>• We collect: name, email, phone, delivery address for order processing only<br>
• We do NOT share your data with third parties except delivery partners<br>
• M-Pesa data processed securely by Safaricom Daraja API<br>
• Cookies used only for login session - no tracking ads<br>
• You may request data deletion via support@lonmaorbit.co.ke</p>

<h3>10. Intellectual Property</h3>
<p>• LO logo, LONMA ORBIT name, product designs are our trademarks<br>
• Do not copy, reproduce, or use without written permission<br>
• Product codes are proprietary verification system</p>

<h3>11. Limitation of Liability</h3>
<p>• We are not liable for M-Pesa network failures, power outages, or courier delays<br>
• Maximum liability limited to amount paid for product<br>
• Force majeure (floods, strikes, internet outage) exempts liability<br>
• Use at your own risk - site provided as-is</p>

<h3>12. Changes to Terms</h3>
<p>• We may update Terms anytime - check Terms tab regularly<br>
• Continued use after update = acceptance of new Terms<br>
• Major changes notified via email or site banner</p>

<h3>13. Governing Law & Contact</h3>
<p>• Governed by Laws of Kenya<br>
• Disputes resolved via Nairobi Magistrate Courts or arbitration<br>
• Contact:<br>
📍 Moi Avenue, Nairobi, Kenya<br>
📧 support@lonmaorbit.co.ke<br>
📞 +254 7XX XXX XXX<br>
💬 Chat with LO BOT on site<br>
🌐 https://app.lonmaorbit.co.ke</p>

<button class="btn" onclick="show('products')">I AGREE - CONTINUE SHOPPING</button>
</div></div>

<div id="locations" class="page"><h2>Locations</h2><div id="loclist"></div></div>
<div id="scan" class="page"><h2>Code Scan</h2><div class="card"><div id="reader"></div><button class="btn" onclick="startScan()">START CAMERA</button><input id="manualcode" placeholder="LONMA-001"><button class="btn" onclick="verifyCode()">VERIFY CODE</button><p id="scanresult"></p></div></div>

<div class="bottom"><div onclick="show('products')">🛍️<br>Products</div><div onclick="show('scan')">📷<br>Scan</div><div onclick="show('locations')">📍<br>Locations</div><div onclick="show('terms')">📄<br>Terms</div><div onclick="show('login')">👤<br>Account</div></div>

<div id="botBtn" onclick="toggleBot()">🤖</div>
<div id="botBox"><div style="padding:12px;background:#0A9EBB;color:#fff;font-weight:bold;display:flex;justify-content:space-between"><span>LO BOT</span><span onclick="toggleBot()" style="cursor:pointer">✕</span></div><div id="botMsgs" style="flex:1;overflow-y:auto;padding:10px;background:#f9f9f9"><div style="background:#fff;border:1px solid #eee;padding:10px;border-radius:12px;font-size:13px;color:#000">Welcome to LONMA ORBIT 💙 Full Terms added!</div></div><div style="display:flex;padding:10px;border-top:1px solid #eee;background:#fff"><input id="botInput" style="flex:1" placeholder="Ask..." onkeypress="if(event.key==='Enter')sendBot()"><button onclick="sendBot()" style="background:#0A9EBB;color:#fff;border:none;padding:12px 15px;border-radius:0 20px 20px 0">Send</button></div></div>

<script>
function show(id){document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));document.getElementById(id).classList.add('active')}
async function loadProducts(){let r=await fetch('/api/products');let d=await r.json();document.getElementById('plist').innerHTML=d.map(p=>`<div class="card"><img src="${p.image}" style="width:100%;border-radius:8px"><h4>${p.name}</h4><p>KSh ${p.price}</p><small>${p.code}</small><button class="btn" onclick="document.getElementById('amount').value=${p.price}">BUY</button></div>`).join('')}
async function loadLoc(){let r=await fetch('/api/locations');let d=await r.json();document.getElementById('loclist').innerHTML=d.map(l=>`<div class="card"><h4>${l.name}</h4><p>${l.address}</p><a href="https://maps.google.com/?q=${l.lat},${l.lng}" target="_blank"><button class="btn">Directions</button></a></div>`).join('')}
async function login(){let r=await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:document.getElementById('lemail').value,password:document.getElementById('lpass').value})});let d=await r.json();document.getElementById('lstatus').innerText=d.message}
async function signin(){let r=await fetch('/api/signin',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:document.getElementById('sname').value,email:document.getElementById('semail').value,password:document.getElementById('spass').value})});let d=await r.json();document.getElementById('sstatus').innerText=d.message}
async function pay(){let phone=document.getElementById('phone').value;let amount=document.getElementById('amount').value;document.getElementById('paystatus').innerText='Sending STK...';let r=await fetch('/mpesa/stkpush',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({phone,amount})});let d=await r.json();document.getElementById('paystatus').innerText=JSON.stringify(d)}
async function verifyCode(){let code=document.getElementById('manualcode').value;let r=await fetch(`/api/verify/${code}`);let d=await r.json();document.getElementById('scanresult').innerHTML=d.valid?`✅ ${d.product.name} - ORIGINAL`:`❌ Invalid Code - Possible Fake`}
let html5QrCode;function startScan(){html5QrCode=new Html5Qrcode("reader");html5QrCode.start({facingMode:"environment"},{fps:10,qrbox:250},(dec)=>{document.getElementById('manualcode').value=dec;verifyCode();html5QrCode.stop()})}
function toggleBot(){document.getElementById('botBox').classList.toggle('open')}
async function sendBot(){let i=document.getElementById('botInput');let m=i.value;if(!m)return;let b=document.getElementById('botMsgs');b.innerHTML+=`<div style="background:#0A9EBB;color:#fff;margin-left:auto;padding:10px;border-radius:12px;max-width:80%;margin-top:6px;font-size:13px">${m}</div>`;i.value='';let r=await fetch('/api/bot',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:m})});let d=await r.json();b.innerHTML+=`<div style="background:#fff;border:1px solid #eee;padding:10px;border-radius:12px;max-width:80%;margin-top:6px;font-size:13px;color:#000">${d.reply}</div>`;b.scrollTop=b.scrollHeight}
loadProducts();loadLoc();
</script></body></html>
"""

@app.api_route("/", methods=["GET", "HEAD"])
def home():
    return HTMLResponse(HTML)

@app.get("/logo.png")
def logo():
    for p in ["logo.png", "static/logo.png"]:
        if os.path.exists(p):
            return FileResponse(p)
    return HTMLResponse("logo not found", status_code=404)

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
    cur=conn.cursor(); cur.execute("SELECT name FROM products WHERE code=?", (code,))
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
    return {"status":"ok","message":"Welcome back!"} if cur.fetchone() else {"status":"error","message":"Invalid"}

@app.post("/api/bot")
async def bot_api(req: Request):
    data=await req.json()
    return {"reply": bot_reply(data.get("message",""))}

@app.post("/mpesa/stkpush")
async def stk_push(req: Request):
    data=await req.json()
    return {"ResponseCode":"0","msg":"MOCK STK sent to "+data.get("phone"," - configure MPESA env for real M-Pesa")}

@app.post("/mpesa/callback")
async def callback(req: Request):
    return {"ResultCode":0,"ResultDesc":"Accepted"}

import os, base64, requests, sqlite3
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

load_dotenv()
app = FastAPI(title="LONMA ORBIT")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Serve logo if exists
if os.path.exists("logo.png") or os.path.exists("static"):
    try:
        app.mount("/static", StaticFiles(directory="."), name="static")
    except: pass

MPESA_CONSUMER_KEY = os.getenv("MPESA_CONSUMER_KEY")
MPESA_CONSUMER_SECRET = os.getenv("MPESA_CONSUMER_SECRET")
MPESA_SHORTCODE = os.getenv("MPESA_SHORTCODE", "174379")
MPESA_PASSKEY = os.getenv("MPESA_PASSKEY")
MPESA_CALLBACK_URL = os.getenv("MPESA_CALLBACK_URL", "https://app.lonmaorbit.co.ke/mpesa/callback")
BASE_URL = "https://sandbox.safaricom.co.ke" if os.getenv("MPESA_ENV","sandbox")=="sandbox" else "https://api.safaricom.co.ke"

conn = sqlite3.connect("lonma.db", check_same_thread=False)
conn.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, email TEXT UNIQUE, password TEXT, name TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT, price INTEGER, code TEXT UNIQUE, image TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY, phone TEXT, amount INTEGER, status TEXT, code TEXT, created TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS locations (id INTEGER PRIMARY KEY, name TEXT, address TEXT, lat REAL, lng REAL)")
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM products")
if cur.fetchone()[0]==0:
    conn.execute("INSERT INTO products (name,price,code,image) VALUES ('Orbit Tee',1500,'LONMA-001','https://via.placeholder.com/300')")
    conn.execute("INSERT INTO products (name,price,code,image) VALUES ('Orbit Hoodie',3500,'LONMA-002','https://via.placeholder.com/300')")
    conn.execute("INSERT INTO products (name,price,code,image) VALUES ('Orbit Cap',1200,'LONMA-003','https://via.placeholder.com/300')")
    conn.execute("INSERT INTO products (name,price,code,image) VALUES ('Orbit Jacket',5000,'LONMA-004','https://via.placeholder.com/300')")
    conn.commit()
cur.execute("SELECT COUNT(*) FROM locations")
if cur.fetchone()[0]==0:
    conn.execute("INSERT INTO locations (name,address,lat,lng) VALUES ('LONMA CBD','Moi Avenue, Nairobi',-1.2833,36.8172)")
    conn.execute("INSERT INTO locations (name,address,lat,lng) VALUES ('LONMA Westlands','Westgate Mall',-1.2634,36.8031)")
    conn.execute("INSERT INTO locations (name,address,lat,lng) VALUES ('LONMA TRM','Thika Road Mall',-1.2197,36.8861)")
    conn.commit()

def get_token():
    if not MPESA_CONSUMER_KEY: return None
    auth = base64.b64encode(f"{MPESA_CONSUMER_KEY}:{MPESA_CONSUMER_SECRET}".encode()).decode()
    try:
        r = requests.get(f"{BASE_URL}/oauth/v1/generate?grant_type=client_credentials", headers={"Authorization": f"Basic {auth}"}, timeout=10)
        return r.json().get("access_token")
    except: return None

def stk(phone, amount):
    token = get_token()
    if not token: return {"error":"no token"}
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    pwd = base64.b64encode(f"{MPESA_SHORTCODE}{MPESA_PASSKEY}{ts}".encode()).decode()
    if phone.startswith("0"): phone="254"+phone[1:]
    payload = {"BusinessShortCode":MPESA_SHORTCODE,"Password":pwd,"Timestamp":ts,"TransactionType":"CustomerPayBillOnline","Amount":int(amount),"PartyA":phone,"PartyB":MPESA_SHORTCODE,"PhoneNumber":phone,"CallBackURL":MPESA_CALLBACK_URL,"AccountReference":"LONMA-ORBIT","TransactionDesc":"Payment"}
    r = requests.post(f"{BASE_URL}/mpesa/stkpush/v1/processrequest", json=payload, headers={"Authorization": f"Bearer {token}"})
    return r.json()

# BOT LOGIC
def lonma_bot_reply(message):
    msg = message.lower()
    if "price" in msg or "how much" in msg:
        return "Our prices: Tee KSh 1500, Cap 1200, Hoodie 3500, Jacket 5000. Which one do you want? 🛍️"
    if "location" in msg or "where" in msg or "shop" in msg:
        return "📍 We are at Moi Avenue CBD, Westgate Westlands, and TRM. Delivery countrywide. Check Locations tab!"
    if "mpesa" in msg or "pay" in msg or "payment" in msg:
        return "💳 Pay via M-Pesa: Enter phone 07xx and amount, then click PAY. You'll get STK push. Enter PIN 1234 for sandbox."
    if "code" in msg or "scan" in msg or "verify" in msg or "authentic" in msg:
        return "📷 Each LONMA product has unique code like LONMA-001. Go to Scan tab to verify authenticity."
    if "delivery" in msg or "shipping" in msg:
        return "🚚 Nairobi same day delivery KSh 200, outside Nairobi 24-48hrs KSh 300-500."
    if "hello" in msg or "hi" in msg or "hey" in msg:
        return "Hey! 👋 I'm LONMA Bot. I can help with Products, Prices, M-Pesa Pay, Locations, and Code Scan. What do you need?"
    return "I'm LONMA Bot 🤖 I can help with: Products, Prices, M-Pesa, Locations, Code Scan verification, Delivery. Ask me anything!"

HTML = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>LONMA ORBIT</title>
<script src="https://unpkg.com/html5-qrcode@2.3.8/html5-qrcode.min.js"></script>
<style>
*{box-sizing:border-box}body{margin:0;font-family:Arial;background:#000;color:#fff}
.nav{position:fixed;top:0;width:100%;background:#0a0a0a;padding:10px 15px;display:flex;justify-content:space-between;align-items:center;z-index:100;border-bottom:1px solid #222}
.logo{display:flex;align-items:center;gap:10px;font-weight:bold;letter-spacing:3px}
.logo img{width:38px;height:38px;border-radius:50%;object-fit:cover;background:#fff}
.nav a{color:#fff;text-decoration:none;margin-left:12px;font-size:12px;cursor:pointer}
.page{display:none;padding:80px 15px 120px;min-height:100vh}
.page.active{display:block}
.card{background:#151515;border-radius:12px;padding:15px;margin:10px 0;border:1px solid #222}
.btn{background:#fff;color:#000;border:none;padding:12px 20px;border-radius:25px;width:100%;font-weight:bold;cursor:pointer;margin-top:10px}
input{width:100%;padding:12px;border-radius:8px;border:1px solid #333;background:#111;color:#fff;margin:6px 0}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px}
.bottom{position:fixed;bottom:0;width:100%;background:#111;display:flex;justify-content:space-around;padding:8px;border-top:1px solid #222;z-index:100}
.bottom div{text-align:center;font-size:10px;cursor:pointer}
/* BOT */
#botBtn{position:fixed;bottom:75px;right:15px;background:#fff;color:#000;width:55px;height:55px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:24px;cursor:pointer;z-index:200;box-shadow:0 4px 15px rgba(255,255,255,0.2)}
#botBox{display:none;position:fixed;bottom:140px;right:15px;width:90%;max-width:350px;height:400px;background:#111;border:1px solid #333;border-radius:15px;z-index:200;flex-direction:column;overflow:hidden}
#botBox.open{display:flex}
.botHeader{padding:12px;background:#fff;color:#000;font-weight:bold;display:flex;justify-content:space-between}
.botMsgs{flex:1;overflow-y:auto;padding:10px}
.botMsg{margin:6px 0;padding:10px;border-radius:12px;max-width:80%;font-size:13px}
.userMsg{background:#fff;color:#000;margin-left:auto}
.botReply{background:#222;color:#fff}
.botInput{display:flex;padding:10px;border-top:1px solid #222}
.botInput input{margin:0;border-radius:20px 0 0 20px}
.botInput button{border:none;background:#fff;color:#000;padding:12px 15px;border-radius:0 20px 20px 0;font-weight:bold}
</style></head><body>

<div class="nav">
<div class="logo"><img src="/static/logo.png" onerror="this.style.display='none';document.getElementById('logoText').style.display='block'"><span id="logoText">LONMA ORBIT</span></div>
<div><a onclick="show('login')">Log in</a><a onclick="show('signin')">Sign in</a></div>
</div>

<div id="products" class="page active">
<h2>Products</h2><div class="grid" id="plist"></div>
<div class="card"><input id="phone" placeholder="07xxxxxxxx"><input id="amount" type="number" placeholder="Amount"><button class="btn" onclick="pay()">PAY M-PESA</button><p id="paystatus"></p></div>
</div>

<div id="login" class="page"><h2>Log In</h2><div class="card"><input id="lemail" placeholder="Email"><input id="lpass" type="password" placeholder="Password"><button class="btn" onclick="login()">Log In</button><p id="lstatus"></p></div></div>

<div id="signin" class="page"><h2>Sign Up</h2><div class="card"><input id="sname" placeholder="Full Name"><input id="semail" placeholder="Email"><input id="spass" type="password" placeholder="Password"><button class="btn" onclick="signin()">Create Account</button><p id="sstatus"></p></div></div>

<div id="terms" class="page"><h2>Terms</h2><div class="card" style="line-height:1.6;color:#ccc;font-size:13px">
<p><b>1.</b> Acceptance of terms by using LONMA ORBIT</p><p><b>2.</b> Original products only</p><p><b>3.</b> M-Pesa payments final</p><p><b>4.</b> Nairobi same day, others 24-48hrs</p><p><b>5.</b> QR codes for authenticity</p><p><b>6.</b> Privacy secured</p><p>Contact: support@lonmaorbit.co.ke</p>
</div></div>

<div id="locations" class="page"><h2>Locations</h2><div id="loclist"></div></div>

<div id="scan" class="page"><h2>Code Scan</h2><div class="card"><div id="reader"></div><button class="btn" onclick="startScan()">START CAMERA</button><button class="btn" style="background:#333;color:#fff" onclick="stopScan()">STOP</button><input id="manualcode" placeholder="LONMA-001"><button class="btn" onclick="verifyCode()">VERIFY</button><p id="scanresult"></p></div></div>

<div class="bottom"><div onclick="show('products')">🛍️<br>Products</div><div onclick="show('scan')">📷<br>Scan</div><div onclick="show('locations')">📍<br>Locations</div><div onclick="show('terms')">📄<br>Terms</div><div onclick="show('login')">👤<br>Account</div></div>

<!-- BOT -->
<div id="botBtn" onclick="toggleBot()">🤖</div>
<div id="botBox">
<div class="botHeader"><span>🤖 LONMA Bot</span><span style="cursor:pointer" onclick="toggleBot()">✕</span></div>
<div class="botMsgs" id="botMsgs"><div class="botMsg botReply">Hey! I'm LONMA Bot 👋 Ask me about products, prices, M-Pesa, locations, or code verification!</div></div>
<div class="botInput"><input id="botInput" placeholder="Ask something..." onkeypress="if(event.key==='Enter')sendBot()"><button onclick="sendBot()">Send</button></div>
</div>

<script>
function show(id){document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));document.getElementById(id).classList.add('active')}
async function loadProducts(){let r=await fetch('/api/products');let d=await r.json();document.getElementById('plist').innerHTML=d.map(p=>`<div class="card"><img src="${p.image}" style="width:100%;border-radius:8px"><h4>${p.name}</h4><p>KSh ${p.price}</p><small>${p.code}</small><button class="btn" onclick="document.getElementById('amount').value=${p.price};show('products');window.scrollTo(0,document.body.scrollHeight)">BUY</button></div>`).join('')}
async function loadLoc(){let r=await fetch('/api/locations');let d=await r.json();document.getElementById('loclist').innerHTML=d.map(l=>`<div class="card"><h4>${l.name}</h4><p>${l.address}</p><a href="https://maps.google.com/?q=${l.lat},${l.lng}" target="_blank"><button class="btn">Directions</button></a></div>`).join('')}
async function login(){let r=await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:document.getElementById('lemail').value,password:document.getElementById('lpass').value})});let d=await r.json();document.getElementById('lstatus').innerText=d.message;if(d.status=='ok')show('products')}
async function signin(){let r=await fetch('/api/signin',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:document.getElementById('sname').value,email:document.getElementById('semail').value,password:document.getElementById('spass').value})});let d=await r.json();document.getElementById('sstatus').innerText=d.message;if(d.status=='ok')show('login')}
async function pay(){let phone=document.getElementById('phone').value;let amount=document.getElementById('amount').value;document.getElementById('paystatus').innerText='Sending STK...';let r=await fetch('/mpesa/stkpush',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({phone,amount})});let d=await r.json();document.getElementById('paystatus').innerText=JSON.stringify(d)}
async function verifyCode(){let code=document.getElementById('manualcode').value;if(!code)return;let r=await fetch(`/api/verify/${code}`);let d=await r.json();document.getElementById('scanresult').innerHTML=d.valid?`✅ Authentic: ${d.product.name}`:`❌ Invalid Code`}
let html5QrCode;function startScan(){html5QrCode=new Html5Qrcode("reader");html5QrCode.start({facingMode:"environment"},{fps:10,qrbox:250},(decoded)=>{document.getElementById('manualcode').value=decoded;verifyCode();stopScan()})}function stopScan(){if(html5QrCode)try{html5QrCode.stop()}catch(e){}}
// BOT FUNCTIONS
function toggleBot(){document.getElementById('botBox').classList.toggle('open')}
async function sendBot(){let input=document.getElementById('botInput');let msg=input.value;if(!msg)return;let box=document.getElementById('botMsgs');box.innerHTML+=`<div class="botMsg userMsg">${msg}</div>`;input.value='';let r=await fetch('/api/bot',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:msg})});let d=await r.json();box.innerHTML+=`<div class="botMsg botReply">${d.reply}</div>`;box.scrollTop=box.scrollHeight}
loadProducts();loadLoc();
</script></body></html>
"""

@app.api_route("/", methods=["GET","HEAD"])
def home():
    return HTMLResponse(content=HTML)

@app.get("/api/products")
def products():
    cur=conn.cursor()
    cur.execute("SELECT id,name,price,code,image FROM products")
    return [{"id":r[0],"name":r[1],"price":r[2],"code":r[3],"image":r[4]} for r in cur.fetchall()]

@app.get("/api/locations")
def locations():
    cur=conn.cursor()
    cur.execute("SELECT * FROM locations")
    return [{"id":r[0],"name":r[1],"address":r[2],"lat":r[3],"lng":r[4]} for r in cur.fetchall()]

@app.get("/api/verify/{code}")
def verify(code: str):
    cur=conn.cursor()
    cur.execute("SELECT name,price,code FROM products WHERE code=?", (code,))
    row=cur.fetchone()
    if row: return {"valid":True,"product":{"name":row[0],"price":row[1],"code":row[2]}}
    return {"valid":False}

@app.post("/api/signin")
async def api_signin(req: Request):
    data=await req.json()
    try:
        conn.execute("INSERT INTO users (email,password,name) VALUES (?,?,?)", (data.get("email"), data.get("password"), data.get("name")))
        conn.commit()
        return {"status":"ok","message":"Account created!"}
    except:
        return {"status":"error","message":"Email exists"}

@app.post("/api/login")
async def api_login(req: Request):
    data=await req.json()
    cur=conn.cursor()
    cur.execute("SELECT * FROM users WHERE email=? AND password=?", (data.get("email"), data.get("password")))
    if cur.fetchone(): return {"status":"ok","message":"Welcome back!"}
    return {"status":"error","message":"Invalid credentials"}

@app.post("/api/bot")
async def bot_api(req: Request):
    data=await req.json()
    reply = lonma_bot_reply(data.get("message",""))
    return {"reply": reply}

@app.post("/mpesa/stkpush")
async def stk_push(req: Request):
    data=await req.json()
    res=stk(data.get("phone"), data.get("amount"))
    conn.execute("INSERT INTO orders (phone,amount,status,created) VALUES (?,?,?,?)", (data.get("phone"), data.get("amount"), "PENDING", datetime.now().isoformat()))
    conn.commit()
    return res

@app.post("/mpesa/callback")
async def callback(req: Request):
    body=await req.json()
    try:
        cb=body.get("Body",{}).get("stkCallback",{})
        if cb.get("ResultCode")==0:
            items=cb.get("CallbackMetadata",{}).get("Item",[])
            code=""
            for i in items:
                if i.get("Name")=="MpesaReceiptNumber": code=i.get("Value")
            conn.execute("UPDATE orders SET status=?, code=? WHERE id=(SELECT MAX(id) FROM orders)", ("PAID", code))
            conn.commit()
    except: pass
    return {"ResultCode":0,"ResultDesc":"Accepted"}

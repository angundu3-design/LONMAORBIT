from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os, sqlite3, urllib.parse

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

conn = sqlite3.connect("lonma.db", check_same_thread=False)
conn.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, email TEXT UNIQUE, password TEXT, name TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT, price INTEGER, code TEXT, image TEXT)")
cur = conn.cursor()
cur.execute("DELETE FROM products")
PRODUCTS = [
    (1, "Fresh Fri Cooking Oil 2L", 850, "LONMA-001"),
    (2, "Detrex Citronella Soap 110g", 90, "LONMA-002"),
    (3, "Sawa Men Lotion 72Hrs", 299, "LONMA-003"),
    (4, "Detrex Pine Drops Soap 110g", 90, "LONMA-004"),
    (5, "Salit Vegetable Oil 5L", 1250, "LONMA-005"),
    (6, "Detrex Cool Mint Soap 110g", 90, "LONMA-006"),
    (7, "Diva Anti-Dandruff Pomade 250ml", 250, "LONMA-007"),
    (8, "Diva Anti-Breakage Pomade", 250, "LONMA-008"),
    (9, "Sawa Cocoa Butter Lotion", 299, "LONMA-009"),
]
for pid, name, price, code in PRODUCTS:
    img = f"https://via.placeholder.com/400x300/FFFFFF/0A9EBB?text={urllib.parse.quote(name)}"
    for f in os.listdir("."):
        if f.lower().endswith((".jpg",".jpeg",".png")) and "logo" not in f.lower():
            if code.lower() in f.lower() or name.split()[0].lower() in f.lower():
                img = f"/img/{urllib.parse.quote(f)}"
    cur.execute("INSERT INTO products VALUES (?,?,?,?,?)", (pid, name, price, code, img))
conn.commit()

print(f"SERVER STARTED CART VERSION - Images: {[f for f in os.listdir('.') if f.lower().endswith(('.jpg','.png'))]}")

HTML = """
<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>LONMA ORBIT - Cart</title>
<style>
:root{--teal:#0A9EBB;--dark:#087a91}*{box-sizing:border-box}body{margin:0;font-family:Arial;background:var(--teal);color:#fff}
.nav{position:fixed;top:0;width:100%;background:var(--teal);padding:8px 12px;display:flex;justify-content:space-between;align-items:center;z-index:1000;height:60px;border-bottom:1px solid rgba(255,255,255,.2)}
.logo-img{height:44px;width:44px;border-radius:50%;object-fit:cover;border:2px solid #fff;background:#fff}
.cart-icon{position:relative;background:#fff;color:var(--teal);padding:8px 14px;border-radius:25px;font-weight:bold;cursor:pointer;display:flex;align-items:center;gap:6px}
.cart-count{position:absolute;top:-8px;right:-8px;background:#111;color:#fff;border-radius:50%;width:20px;height:20px;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:bold}
.page{display:none;padding:70px 12px 90px;min-height:100vh;background:var(--teal)}.page.active{display:block}
.card{background:#fff;color:#111;border-radius:14px;padding:12px;margin:10px 0;box-shadow:0 3px 10px rgba(0,0,0,.15)}
.card img{width:100%;height:200px;object-fit:contain;background:#fff;border-radius:10px;padding:10px}
.btn{background:var(--teal);color:#fff;border:none;padding:12px;border-radius:25px;width:100%;font-weight:bold;margin-top:6px;cursor:pointer;font-size:13px}
.btn-black{background:#111}.btn-small{padding:8px 12px;font-size:12px;width:auto;display:inline-block;margin:2px}
input{width:100%;padding:12px;border-radius:10px;border:1px solid #ddd;background:#f7f7f7;margin:6px 0}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.bottom{position:fixed;bottom:0;width:100%;background:#fff;display:flex;justify-content:space-around;padding:8px 0;z-index:1000;box-shadow:0 -2px 10px rgba(0,0,0,.1)}.bottom div{font-size:10px;color:#666;text-align:center;cursor:pointer;flex:1}.bottom div.active{color:var(--teal);font-weight:bold}
.qty-controls{display:flex;align-items:center;justify-content:space-between;background:#f5f5f5;border-radius:25px;padding:4px;margin-top:6px}
.qty-btn{background:var(--teal);color:#fff;border:none;width:28px;height:28px;border-radius:50%;font-weight:bold;cursor:pointer}
.cart-item{display:flex;gap:10px;align-items:center;border-bottom:1px solid #eee;padding:10px 0}
.cart-item img{width:60px;height:60px;object-fit:contain;border-radius:8px;background:#fff;padding:4px;border:1px solid #eee}
</style></head><body>
<div class="nav">
<img src="/logo.png" class="logo-img" onerror="this.src='https://via.placeholder.com/100'">
<div style="display:flex;gap:8px;align-items:center">
<div class="cart-icon" onclick="show('cart')">🛒 CART <span id="cartCount" class="cart-count">0</span></div>
<span onclick="show('login')" style="background:rgba(255,255,255,.3);color:#fff;padding:6px 12px;border-radius:20px;font-size:12px;cursor:pointer">Log in</span>
</div>
</div>

<div id="products" class="page active">
<h2 style="font-size:17px;margin:8px 0">LONMA PRODUCTS - Add to Cart</h2>
<p style="font-size:11px;opacity:.9;margin:0 0 8px">Click ADD TO CART - Same product adds quantity +1</p>
<div class="grid" id="plist"></div>
</div>

<div id="cart" class="page">
<h2 style="font-size:18px">🛒 My Cart</h2>
<div id="cartItems"></div>
<div class="card" id="cartSummary" style="display:none">
<h3 style="margin:0">Order Summary</h3>
<p style="margin:6px 0">Items: <span id="totalItems">0</span></p>
<p style="margin:6px 0;font-weight:bold;font-size:18px;color:#0A9EBB">Total: KSh <span id="totalPrice">0</span></p>
<div style="background:linear-gradient(135deg,#0A9EBB,#087a91);color:#fff;padding:12px;border-radius:12px;margin-top:10px">
<h4 style="margin:0 0 8px">💳 M-Pesa Checkout</h4>
<input id="phone" placeholder="07xxxxxxxx" style="background:#fff">
<button class="btn" style="background:#111" onclick="checkout()">PAY KSh <span id="payTotal">0</span> WITH M-PESA</button>
<p id="paystatus" style="font-size:12px;margin-top:8px;min-height:18px"></p>
</div>
<button class="btn btn-black" style="margin-top:10px;background:#666" onclick="clearCart()">🗑️ CLEAR CART</button>
</div>
<div class="card" id="emptyCart" style="text-align:center;padding:30px"><p style="font-size:40px;margin:0">🛒</p><h3>Cart is Empty</h3><p style="font-size:13px;color:#666">Add products from Products page. Same product increases quantity.</p><button class="btn" onclick="show('products')">GO TO PRODUCTS</button></div>
</div>

<div id="scan" class="page"><h2>📷 Scan Verification</h2><div class="card"><input id="manualcode" placeholder="LONMA-001"><button class="btn" onclick="verifyCode()">VERIFY CODE</button><p id="scanresult" style="font-weight:bold"></p></div></div>
<div id="locations" class="page"><h2>📍 Locations</h2><div class="card"><h4>CBD Moi Avenue</h4><p style="font-size:13px">Opposite Imenti 2nd Floor<br>Mon-Sat 8am-7pm</p><a href="https://maps.google.com/?q=Moi+Avenue+Nairobi" target="_blank"><button class="btn">DIRECTIONS</button></a></div></div>
<div id="terms" class="page"><h2>📄 Terms</h2><div class="card" style="font-size:12px;line-height:1.6;max-height:65vh;overflow-y:auto"><h3 style="color:#0A9EBB;margin-top:0">Terms - LONMA ORBIT</h3><p><b>Cart:</b> Add same product multiple times - quantity increases. You can add Fresh Fri 2 times = qty 2 etc.</p><p><b>Pricing:</b> Detrex 90, Sawa 299, Diva 250, Fresh Fri 850, Salit 1250</p><p><b>M-Pesa:</b> Pay total cart amount via STK Push</p><p><b>Delivery:</b> Nairobi same-day, upcountry 24-48hrs</p><p><b>Verification:</b> LONMA-001 to 009</p><button class="btn" onclick="show('products')">I AGREE</button></div></div>
<div id="login" class="page"><h2>Account</h2><div class="card"><input id="lemail" placeholder="Email"><input id="lpass" type="password" placeholder="Password"><button class="btn" onclick="login()">Log In</button><p id="lstatus"></p><p style="text-align:center;font-size:12px">No account? <span style="color:#0A9EBB;font-weight:bold" onclick="show('signin')">Sign up</span></p></div></div>
<div id="signin" class="page"><h2>Sign Up</h2><div class="card"><input id="sname" placeholder="Name"><input id="semail" placeholder="Email"><input id="spass" type="password" placeholder="Password"><button class="btn" onclick="signin()">Create</button><p id="sstatus"></p></div></div>

<div class="bottom">
<div id="b-products" class="active" onclick="show('products')">🛍️<br>Products</div>
<div id="b-cart" onclick="show('cart')">🛒<br>Cart (<span id="bottomCartCount">0</span>)</div>
<div id="b-scan" onclick="show('scan')">📷<br>Scan</div>
<div id="b-locations" onclick="show('locations')">📍<br>Locations</div>
<div id="b-terms" onclick="show('terms')">📄<br>Terms</div>
</div>

<script>
// CART LOGIC - Same product adds quantity
let cart = JSON.parse(localStorage.getItem('lonma_cart') || '[]');

function saveCart(){
 localStorage.setItem('lonma_cart', JSON.stringify(cart));
 updateCartCount();
}

function updateCartCount(){
 let count = cart.reduce((sum, item) => sum + item.qty, 0);
 document.getElementById('cartCount').innerText = count;
 document.getElementById('bottomCartCount').innerText = count;
 document.getElementById('cartCount').style.display = count > 0 ? 'flex' : 'none';
}

function addToCart(id, name, price, image, code){
 let existing = cart.find(item => item.id === id);
 if(existing){
   existing.qty += 1;
   alert(`✅ Added again! ${name} quantity now ${existing.qty}`);
 } else {
   cart.push({id, name, price, image, code, qty: 1});
   alert(`✅ Added to cart: ${name}`);
 }
 saveCart();
 renderCart();
}

function changeQty(id, delta){
 let item = cart.find(i => i.id === id);
 if(!item) return;
 item.qty += delta;
 if(item.qty <= 0){
   cart = cart.filter(i => i.id !== id);
 } else {
   // Keep in cart
 }
 saveCart();
 renderCart();
}

function clearCart(){
 if(confirm('Clear all cart items?')){
   cart = [];
   saveCart();
   renderCart();
 }
}

function renderCart(){
 let container = document.getElementById('cartItems');
 let summary = document.getElementById('cartSummary');
 let empty = document.getElementById('emptyCart');
 
 if(cart.length === 0){
   container.innerHTML = '';
   summary.style.display = 'none';
   empty.style.display = 'block';
   return;
 }
 empty.style.display = 'none';
 summary.style.display = 'block';
 
 let totalItems = 0;
 let totalPrice = 0;
 
 container.innerHTML = cart.map(item => {
   totalItems += item.qty;
   totalPrice += item.price * item.qty;
   return `<div class="card cart-item">
     <img src="${item.image}" onerror="this.src='https://via.placeholder.com/100'">
     <div style="flex:1">
       <h4 style="margin:0;font-size:13px">${item.name}</h4>
       <p style="margin:2px 0;font-size:12px;color:#0A9EBB;font-weight:bold">KSh ${item.price} x ${item.qty} = KSh ${item.price * item.qty}</p>
       <small style="background:#0A9EBB;color:#fff;padding:2px 6px;border-radius:10px;font-size:10px">${item.code}</small>
       <div class="qty-controls" style="margin-top:8px;max-width:140px">
         <button class="qty-btn" onclick="changeQty(${item.id}, -1)">-</button>
         <span style="font-weight:bold;font-size:14px">${item.qty}</span>
         <button class="qty-btn" onclick="changeQty(${item.id}, 1)">+</button>
         <button class="btn-small btn-black" onclick="changeQty(${item.id}, -${item.qty})" style="margin-left:10px;background:#ff4444">Remove</button>
       </div>
     </div>
   </div>`
 }).join('');
 
 document.getElementById('totalItems').innerText = totalItems;
 document.getElementById('totalPrice').innerText = totalPrice;
 document.getElementById('payTotal').innerText = totalPrice;
}

function show(id){
 document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));
 document.getElementById(id).classList.add('active');
 document.querySelectorAll('.bottom div').forEach(b=>b.classList.remove('active'));
 let btn=document.getElementById('b-'+id); if(btn) btn.classList.add('active');
 if(id === 'cart') renderCart();
 window.scrollTo(0,0);
}

async function loadProducts(){
 let r=await fetch('/api/products'); let d=await r.json();
 document.getElementById('plist').innerHTML=d.map(p=>`<div class="card">
   <img src="${p.image}" loading="lazy" onerror="this.src='https://via.placeholder.com/300'">
   <h4 style="font-size:12px;margin:6px 0;line-height:1.3">${p.name}</h4>
   <p style="margin:0;font-weight:bold;color:#0A9EBB">KSh ${p.price}</p>
   <small style="background:#0A9EBB;color:#fff;padding:2px 6px;border-radius:10px;font-size:10px">${p.code}</small>
   <div style="display:flex;gap:4px;margin-top:8px">
     <button class="btn" style="flex:1;padding:10px;font-size:11px" onclick="addToCart(${p.id}, '${p.name.replace(/'/g,"\\'")}', ${p.price}, '${p.image}', '${p.code}')">🛒 ADD TO CART</button>
     <button class="btn btn-black" style="flex:0 0 60px;padding:10px;font-size:11px" onclick="document.getElementById('manualcode').value='${p.code}';show('scan')">VERIFY</button>
   </div>
   <div id="qty-${p.id}" style="font-size:11px;color:#0A9EBB;margin-top:4px;text-align:center;font-weight:bold"></div>
 </div>`).join('');
 // Show qty if already in cart
 updateQtyDisplays();
}

function updateQtyDisplays(){
 cart.forEach(item => {
   let el=document.getElementById(`qty-${item.id}`);
   if(el) el.innerText = `In cart: ${item.qty} pcs`;
 });
}

async function verifyCode(){let c=document.getElementById('manualcode').value.trim().toUpperCase();let r=await fetch(`/api/verify/${c}`);let d=await r.json();document.getElementById('scanresult').innerHTML=d.valid?`✅ ${d.product.name} - ORIGINAL`:`❌ Invalid ${c}`}
async function login(){let r=await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:document.getElementById('lemail').value,password:document.getElementById('lpass').value})});let d=await r.json();document.getElementById('lstatus').innerText=d.message}
async function signin(){let r=await fetch('/api/signin',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:document.getElementById('sname').value,email:document.getElementById('semail').value,password:document.getElementById('spass').value})});let d=await r.json();document.getElementById('sstatus').innerText=d.message}
async function checkout(){
 let phone=document.getElementById('phone').value.trim();
 if(!phone){document.getElementById('paystatus').innerText='Enter 07xx phone';return}
 let total = cart.reduce((sum, i) => sum + (i.price * i.qty), 0);
 if(total === 0){document.getElementById('paystatus').innerText='Cart empty';return}
 document.getElementById('paystatus').innerText=`Sending STK KSh ${total} to ${phone}...`;
 let r=await fetch('/mpesa/stkpush',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({phone,amount:total,cart:cart})});
 let d=await r.json();
 document.getElementById('paystatus').innerText=`✅ ${d.message} - Items: ${cart.length} types, Total qty: ${cart.reduce((s,i)=>s+i.qty,0)}`;
}

loadProducts();
updateCartCount();
renderCart();
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
    d=await req.json()
    cart_data=d.get('cart',[])
    total_items=sum([i.get('qty',1) for i in cart_data]) if cart_data else 1
    return {"message":f"STK KSh {d.get('amount')} sent to {d.get('phone')} for {total_items} items - Enter PIN (DEMO)"}

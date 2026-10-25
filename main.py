from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import os, sqlite3, urllib.parse

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

conn = sqlite3.connect("lonma.db", check_same_thread=False)
conn.execute("CREATE TABLE IF NOT EXISTS users (email TEXT UNIQUE, password TEXT, name TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT, price INTEGER, code TEXT, image TEXT, category TEXT, stock INTEGER, desc TEXT)")
cur = conn.cursor()
cur.execute("DELETE FROM products")

PRODUCTS = [
    (1, "Fresh Fri Cooking Oil 2L", 850, "LONMA-001", "Cooking Oils", 50),
    (2, "Detrex Citronella Soap 110g", 90, "LONMA-002", "Soaps", 120),
    (3, "Sawa Men Lotion 72Hrs", 299, "LONMA-003", "Lotions", 35),
    (4, "Detrex Pine Drops Soap 110g", 90, "LONMA-004", "Soaps", 100),
    (5, "Salit Vegetable Oil 5L", 1250, "LONMA-005", "Cooking Oils", 25),
    (6, "Detrex Cool Mint Soap 110g", 90, "LONMA-006", "Soaps", 80),
    (7, "Diva Anti-Dandruff Pomade 250ml", 250, "LONMA-007", "Pomades", 40),
    (8, "Diva Anti-Breakage Pomade", 250, "LONMA-008", "Pomades", 45),
    (9, "Sawa Cocoa Butter Lotion", 299, "LONMA-009", "Lotions", 30),
]
for pid, name, price, code, cat, stock in PRODUCTS:
    img = f"https://via.placeholder.com/400x300/FFFFFF/0A9EBB?text={urllib.parse.quote(name)}"
    cur.execute("INSERT INTO products VALUES (?,?,?,?,?,?,?,?)", (pid, name, price, code, img, cat, stock, name))
conn.commit()
print("=== FIXED FINAL VERSION NO UNDEFINED BUG ===")

HTML = """
<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>LONMA ORBIT</title>
<style>
:root{--teal:#0A9EBB}*{box-sizing:border-box}body{margin:0;font-family:Arial;background:#f0f9fb}
.nav{position:fixed;top:0;width:100%;background:var(--teal);padding:8px 12px;display:flex;justify-content:space-between;align-items:center;z-index:1000;height:60px}
.cart-icon{position:relative;background:#fff;color:var(--teal);padding:8px 14px;border-radius:25px;font-weight:bold;cursor:pointer}
.cart-count{position:absolute;top:-8px;right:-8px;background:#ff3b30;color:#fff;border-radius:50%;width:20px;height:20px;display:flex;align-items:center;justify-content:center;font-size:11px}
.page{display:none;padding:66px 10px 90px;min-height:100vh;background:#f0f9fb}.page.active{display:block}
.card{background:#fff;border-radius:16px;padding:12px;margin:8px 0;box-shadow:0 2px 8px rgba(0,0,0,.08);position:relative}
.card img{width:100%;height:190px;object-fit:contain;background:#fff;border-radius:12px;padding:8px}
.btn{background:var(--teal);color:#fff;border:none;padding:12px;border-radius:25px;width:100%;font-weight:bold;cursor:pointer}
input,select,textarea{width:100%;padding:12px;border-radius:10px;border:1px solid #ddd;margin:5px 0}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.bottom{position:fixed;bottom:0;width:100%;background:#fff;display:flex;justify-content:space-around;padding:6px 0;border-top:1px solid #eee;z-index:1000}.bottom div{font-size:10px;color:#777;text-align:center;cursor:pointer;flex:1}.bottom div.active{color:var(--teal);font-weight:bold}
.chips{display:flex;gap:6px;overflow-x:auto;padding:8px 0}.chip{white-space:nowrap;background:#fff;border:1px solid #0A9EBB;color:#0A9EBB;padding:7px 14px;border-radius:20px;font-size:12px;cursor:pointer}.chip.active{background:#0A9EBB;color:#fff}
.qty-controls{display:flex;align-items:center;justify-content:space-between;background:#eef9fb;border-radius:25px;padding:5px 8px;margin-top:8px}
.qty-btn{background:var(--teal);color:#fff;border:none;width:30px;height:30px;border-radius:50%;font-weight:bold;cursor:pointer}
</style></head><body>
<div class="nav"><img src="/logo.png" style="height:44px;width:44px;border-radius:50%;border:2px solid #fff;background:#fff" onerror="this.src='https://via.placeholder.com/100'"><div style="display:flex;gap:8px"><div class="cart-icon" onclick="show('cart')">🛒 CART <span id="cartCount" class="cart-count" style="display:none">0</span></div><span onclick="show('login')" style="background:rgba(255,255,255,.3);color:#fff;padding:6px 12px;border-radius:20px;font-size:12px;cursor:pointer">Account</span></div></div>

<div id="products" class="page active">
<div style="background:linear-gradient(135deg,#ff9a00,#ff6a00);color:#fff;padding:10px;border-radius:12px;margin:8px 0;text-align:center;font-weight:bold;font-size:13px">🎉 FREE DELIVERY over KSh 2000</div>
<div style="position:sticky;top:60px;background:#f0f9fb;padding:8px 0;z-index:900"><input id="searchInput" placeholder="🔍 Search..." oninput="filterProducts()" style="border-radius:25px"><div class="chips"><span class="chip active" onclick="filterCat('All',this)">All</span><span class="chip" onclick="filterCat('Cooking Oils',this)">🍳 Oils</span><span class="chip" onclick="filterCat('Soaps',this)">🧼 Soaps</span><span class="chip" onclick="filterCat('Lotions',this)">🧴 Lotions</span><span class="chip" onclick="filterCat('Pomades',this)">💇 Pomades</span></div></div>
<div class="grid" id="plist"></div>
</div>

<div id="cart" class="page"><h2>🛒 My Cart</h2><div id="cartItems"></div><div class="card" id="cartSummary" style="display:none"><p>Subtotal KSh <span id="subTotal">0</span> (<span id="totalItems">0</span> items)</p><p>Delivery: <span id="deliveryFee">KSh 200</span></p><p style="font-weight:bold;color:#0A9EBB;font-size:18px">Total KSh <span id="totalPrice">0</span></p><p id="freeDeliveryMsg" style="background:#e8f5e9;padding:8px;border-radius:8px;font-size:11px;text-align:center"></p><input id="custName" placeholder="Full Name *"><input id="phone" placeholder="07xxxxxxxx *"><select id="locationArea"><option value="">Select Area *</option><option value="CBD">CBD 150</option><option value="Westlands">Westlands 200</option><option value="Upcountry">Upcountry 350</option></select><textarea id="exactLocation" placeholder="Estate, House No *"></textarea><label style="font-size:12px"><input type="checkbox" id="agreeTerms" style="width:auto"> Agree Terms</label><button class="btn" style="background:#111;margin-top:8px" onclick="checkout()">PAY KSh <span id="payTotal">0</span></button><button class="btn" style="background:#25D366;margin-top:6px" onclick="orderWhatsApp()">💬 WHATSAPP ORDER</button><p id="paystatus" style="font-size:12px;background:#f0f0f0;padding:6px;border-radius:8px"></p><button class="btn" style="background:#666;margin-top:8px" onclick="clearCart()">Clear Cart</button><button class="btn" style="background:#fff;color:#0A9EBB;border:1px solid #0A9EBB" onclick="show('products')">Continue Shopping</button></div><div class="card" id="emptyCart" style="text-align:center;padding:30px"><p style="font-size:50px">🛒</p><h3>Cart empty</h3><button class="btn" onclick="show('products')">Shop Now</button></div></div>

<div id="scan" class="page"><h2>📷 Verify</h2><div class="card"><input id="manualcode" placeholder="LONMA-001"><button class="btn" onclick="verifyCode()">VERIFY</button><p id="scanresult"></p></div></div>
<div id="locations" class="page"><h2>📍 Stores</h2><div class="card"><h4>CBD Moi Ave</h4><a href="https://maps.google.com/?q=Moi+Avenue+Nairobi" target="_blank"><button class="btn">DIRECTIONS</button></a></div></div>
<div id="terms" class="page"><h2>📄 Terms</h2><div class="card"><p>Free delivery over 2000. Cart adds same product qty.</p><button class="btn" onclick="show('products')">OK</button></div></div>
<div id="login" class="page"><h2>Account</h2><div class="card"><input id="lemail" placeholder="Email"><input id="lpass" type="password" placeholder="Password"><button class="btn" onclick="login()">Log In</button><p id="lstatus"></p></div></div>
<div id="signin" class="page"><h2>Sign Up</h2><div class="card"><input id="sname" placeholder="Name"><input id="semail" placeholder="Email"><input id="spass" type="password" placeholder="Password"><button class="btn" onclick="signin()">Create</button><p id="sstatus"></p></div></div>

<div class="bottom"><div id="b-products" class="active" onclick="show('products')">🛍️<br>Products</div><div id="b-cart" onclick="show('cart')">🛒<br>Cart (<span id="bottomCartCount">0</span>)</div><div id="b-scan" onclick="show('scan')">📷<br>Verify</div><div id="b-locations" onclick="show('locations')">📍<br>Stores</div><div id="b-login" onclick="show('login')">👤<br>Account</div></div>

<script>
// FIX: Clear old buggy cart that had undefined images
let raw = localStorage.getItem('lonma_cart');
if(raw && raw.includes('undefined')){ localStorage.removeItem('lonma_cart'); }
let allProducts=[], currentCat='All', searchQuery='', cart=[];
try{let s=localStorage.getItem('lonma_cart'); if(s){cart=JSON.parse(s); cart=cart.filter(c=>c && c.image && !c.image.includes('undefined') && c.name);} if(!Array.isArray(cart))cart=[];}catch(e){cart=[]; localStorage.removeItem('lonma_cart');}

function safeImage(name){
  if(!name) return 'https://via.placeholder.com/400x300/FFFFFF/0A9EBB?text=Product';
  return `https://via.placeholder.com/400x300/FFFFFF/0A9EBB?text=${encodeURIComponent(name)}`;
}
function saveCart(){localStorage.setItem('lonma_cart',JSON.stringify(cart)); updateCartCount();}
function updateCartCount(){let c=0; for(let i of cart)c+=Number(i.qty)||0; document.getElementById('cartCount').innerText=c; document.getElementById('bottomCartCount').innerText=c; document.getElementById('cartCount').style.display=c>0?'flex':'none';}
function filterCat(cat,el){currentCat=cat; document.querySelectorAll('.chip').forEach(ch=>ch.classList.remove('active')); if(el)el.classList.add('active'); renderProducts();}
function filterProducts(){searchQuery=document.getElementById('searchInput').value.toLowerCase(); renderProducts();}
function renderProducts(){
 let list=allProducts.filter(p=>{let mCat=currentCat==='All'||p.category===currentCat; let mSearch=!searchQuery||p.name.toLowerCase().includes(searchQuery); return mCat&&mSearch;});
 let html='';
 for(let p of list){
   let inCart=cart.find(c=>c.id===p.id);
   let qtyText=inCart?`In cart: ${inCart.qty} pcs`:'';
   let img = p.image && !p.image.includes('undefined') ? p.image : safeImage(p.name);
   html+=`<div class="card"><span style="position:absolute;top:8px;left:8px;background:#00c851;color:#fff;padding:3px 8px;border-radius:12px;font-size:10px">In Stock</span><img src="${img}" loading="lazy" onerror="this.src='${safeImage(p.name)}'"><span style="background:#e0f7fa;color:#0A9EBB;padding:2px 8px;border-radius:10px;font-size:10px">${p.category}</span><h4 style="font-size:12px;margin:6px 0">${p.name}</h4><p style="margin:0;font-weight:bold;color:#0A9EBB">KSh ${p.price}</p><small style="background:#0A9EBB;color:#fff;padding:2px 6px;border-radius:10px;font-size:10px">${p.code}</small><button class="btn" onclick="addToCart(${p.id})">🛒 ADD TO CART</button><div style="font-size:11px;color:#0A9EBB;text-align:center;font-weight:bold;min-height:16px;margin-top:4px">${qtyText}</div></div>`;
 }
 document.getElementById('plist').innerHTML=html;
}
function addToCart(id){
 let p=allProducts.find(x=>x.id===id); if(!p)return;
 let found=cart.find(c=>c.id===id);
 if(found){found.qty++; alert('Qty now '+found.qty);} 
 else {cart.push({id:p.id,name:p.name,price:p.price,image:p.image&&!p.image.includes('undefined')?p.image:safeImage(p.name),code:p.code,qty:1,stock:p.stock}); alert('Added: '+p.name);}
 saveCart(); renderCart(); renderProducts();
}
function changeQty(id,delta){for(let i=0;i<cart.length;i++)if(cart[i].id===id){cart[i].qty+=delta; if(cart[i].qty<=0)cart.splice(i,1); break;} saveCart(); renderCart(); renderProducts();}
function clearCart(){if(confirm('Clear?')){cart=[];localStorage.removeItem('lonma_cart');saveCart();renderCart();renderProducts();}}
function renderCart(){
 let cont=document.getElementById('cartItems'), sum=document.getElementById('cartSummary'), empty=document.getElementById('emptyCart');
 if(cart.length===0){cont.innerHTML='';sum.style.display='none';empty.style.display='block';return;}
 empty.style.display='none'; sum.style.display='block';
 let totalItems=0, subTotal=0, html='';
 for(let it of cart){
   totalItems+=it.qty; subTotal+=it.price*it.qty;
   let img = it.image && !it.image.includes('undefined') ? it.image : safeImage(it.name);
   html+=`<div class="card" style="display:flex;gap:10px;align-items:center"><img src="${img}" style="width:60px;height:60px;object-fit:contain;border-radius:8px;border:1px solid #eee;padding:4px" onerror="this.src='${safeImage(it.name)}'"><div style="flex:1"><h4 style="margin:0;font-size:13px">${it.name}</h4><p style="margin:2px 0;font-size:12px;color:#0A9EBB;font-weight:bold">KSh ${it.price} x ${it.qty} = ${it.price*it.qty}</p><div class="qty-controls"><button class="qty-btn" onclick="changeQty(${it.id},-1)">-</button><span>${it.qty} pcs</span><button class="qty-btn" onclick="changeQty(${it.id},1)">+</button><button onclick="changeQty(${it.id},-${it.qty})" style="margin-left:8px;background:#ff4444;color:#fff;border:none;padding:5px 10px;border-radius:12px;font-size:11px">Remove</button></div></div></div>`;
 }
 cont.innerHTML=html;
 let area=document.getElementById('locationArea').value; let delivery=area==='CBD'?150:area==='Upcountry'?350:200; if(subTotal>=2000)delivery=0;
 document.getElementById('subTotal').innerText=subTotal; document.getElementById('totalItems').innerText=totalItems;
 document.getElementById('deliveryFee').innerText=delivery===0?'FREE':'KSh '+delivery;
 let total=subTotal+delivery;
 document.getElementById('totalPrice').innerText=total; document.getElementById('payTotal').innerText=total;
 document.getElementById('freeDeliveryMsg').innerHTML=subTotal>=2000?'🎉 FREE delivery!':`Add KSh ${2000-subTotal} for FREE delivery!`;
}
document.getElementById('locationArea')?.addEventListener('change',renderCart);
function show(id){document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));document.getElementById(id).classList.add('active');document.querySelectorAll('.bottom div').forEach(b=>b.classList.remove('active'));let btn=document.getElementById('b-'+id);if(btn)btn.classList.add('active');if(id==='cart')renderCart();window.scrollTo(0,0);}
async function loadProducts(){let r=await fetch('/api/products');let d=await r.json(); allProducts=d.map(p=>({id:p.id,name:p.name,price:p.price,code:p.code,image:p.image&&!String(p.image).includes('undefined')?p.image:safeImage(p.name),category:p.category||'General',stock:p.stock||50,desc:p.desc||''})); renderProducts();}
async function verifyCode(){let c=document.getElementById('manualcode').value.trim().toUpperCase();let r=await fetch(`/api/verify/${c}`);let d=await r.json();document.getElementById('scanresult').innerHTML=d.valid?`✅ ${d.product.name} ORIGINAL`:`❌ Invalid`;}
async function login(){let r=await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:document.getElementById('lemail').value,password:document.getElementById('lpass').value})});let d=await r.json();document.getElementById('lstatus').innerText=d.message;}
async function signin(){let r=await fetch('/api/signin',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:document.getElementById('sname').value,email:document.getElementById('semail').value,password:document.getElementById('spass').value})});let d=await r.json();document.getElementById('sstatus').innerText=d.message;}
function orderWhatsApp(){if(cart.length===0){alert('Empty');return;}let total=document.getElementById('totalPrice').innerText;let items=cart.map(c=>`${c.name} x${c.qty}`).join(', ');window.open(`https://wa.me/254700000000?text=${encodeURIComponent('Hi LONMA I want: '+items+' Total KSh '+total)}`,'_blank');}
async function checkout(){let name=document.getElementById('custName').value.trim(),phone=document.getElementById('phone').value.trim(),area=document.getElementById('locationArea').value,loc=document.getElementById('exactLocation').value.trim(),agree=document.getElementById('agreeTerms').checked;if(!name||!phone||!area||!loc){document.getElementById('paystatus').innerText='Fill all *';return;}if(!agree){document.getElementById('paystatus').innerText='Agree terms';return;}let total=0;for(let i of cart)total+=i.price*i.qty;let delivery=area==='CBD'?150:area==='Upcountry'?350:200;if(total>=2000)delivery=0;total+=delivery;document.getElementById('paystatus').innerText=`Sending KSh ${total} to ${phone}...`;let r=await fetch('/mpesa/stkpush',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({phone,amount:total,cart})});let d=await r.json();document.getElementById('paystatus').innerText=`✅ ${d.message}`; if(d.message.includes('sent')){cart=[];localStorage.removeItem('lonma_cart');saveCart();setTimeout(()=>{alert('Order success!');show('products');},1000);}}
loadProducts(); updateCartCount(); renderCart();
</script></body></html>
"""

@app.api_route("/", methods=["GET","HEAD"])
def home(): return HTMLResponse(HTML)

@app.get("/logo.png")
def logo():
    for f in ["logo.png","static/logo.png"]:
        if os.path.exists(f): return FileResponse(f)
    return HTMLResponse("logo",404)

@app.get("/undefined")
@app.get("/undefined/")
def handle_undefined():
    return RedirectResponse("https://via.placeholder.com/400x300/FFFFFF/0A9EBB?text=LONMA", status_code=302)

@app.get("/api/products")
def products():
    cur=conn.cursor()
    cur.execute("SELECT id,name,price,code,image,category,stock,desc FROM products")
    result=[]
    for r in cur.fetchall():
        img=r[4]
        if not img or "undefined" in str(img):
            img=f"https://via.placeholder.com/400x300/FFFFFF/0A9EBB?text={urllib.parse.quote(r[1])}"
        result.append({"id":r[0],"name":r[1],"price":r[2],"code":r[3],"image":img,"category":r[5],"stock":r[6],"desc":r[7]})
    return result

@app.get("/api/verify/{code}")
def verify(code: str):
    cur=conn.cursor(); cur.execute("SELECT name FROM products WHERE code=?",(code.strip().upper(),))
    row=cur.fetchone(); return {"valid":True,"product":{"name":row[0]}} if row else {"valid":False}

@app.post("/api/signin")
async def signin_api(req: Request):
    d=await req.json()
    try: conn.execute("INSERT INTO users (email,password,name) VALUES (?,?,?)",(d.get("email"),d.get("password"),d.get("name")));conn.commit();return {"status":"ok","message":"Created!"}
    except: return {"status":"error","message":"Exists"}

@app.post("/api/login")
async def login_api(req: Request):
    d=await req.json(); cur=conn.cursor(); cur.execute("SELECT * FROM users WHERE email=? AND password=?",(d.get("email"),d.get("password")))
    return {"status":"ok","message":"Welcome!"} if cur.fetchone() else {"status":"error","message":"Invalid"}

@app.post("/mpesa/stkpush")
async def stk(req: Request):
    d=await req.json()
    return {"message":f"STK KSh {d.get('amount')} sent to {d.get('phone')} - Enter PIN"}

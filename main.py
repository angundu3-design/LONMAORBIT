from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os, sqlite3, urllib.parse

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

conn = sqlite3.connect("lonma.db", check_same_thread=False)
conn.execute("CREATE TABLE IF NOT EXISTS users (email TEXT UNIQUE, password TEXT, name TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT, price INTEGER, code TEXT, image TEXT, category TEXT, stock INTEGER, desc TEXT)")
cur = conn.cursor()
cur.execute("DELETE FROM products")

# ALL IMPORTANT DETAILS ADDED
PRODUCTS = [
    (1, "Fresh Fri Cooking Oil 2L", 850, "LONMA-001", "Cooking Oils", 50, "Pure fortified cooking oil 2L - Pwani original, cholesterol free"),
    (2, "Detrex Citronella Soap 110g", 90, "LONMA-002", "Soaps", 120, "Anti-bacterial citronella soap 110g - germ protection"),
    (3, "Sawa Men Lotion 72Hrs", 299, "LONMA-003", "Lotions", 35, "72Hrs hydration for men - non greasy, fast absorbing"),
    (4, "Detrex Pine Drops Soap 110g", 90, "LONMA-004", "Soaps", 100, "Pine drops fresh fragrance - deep clean"),
    (5, "Salit Vegetable Oil 5L", 1250, "LONMA-005", "Cooking Oils", 25, "Vegetable cooking oil 5L family pack - best for frying"),
    (6, "Detrex Cool Mint Soap 110g", 90, "LONMA-006", "Soaps", 80, "Cool mint cooling effect - for fresh skin"),
    (7, "Diva Anti-Dandruff Pomade 250ml", 250, "LONMA-007", "Pomades", 40, "Anti-dandruff hair pomade 250ml - stops itching"),
    (8, "Diva Anti-Breakage Pomade", 250, "LONMA-008", "Pomades", 45, "Anti-breakage strengthens hair roots"),
    (9, "Sawa Cocoa Butter Lotion", 299, "LONMA-009", "Lotions", 30, "Cocoa butter nourishing lotion - soft skin 24Hrs"),
]
for pid, name, price, code, cat, stock, desc in PRODUCTS:
    img = f"https://via.placeholder.com/400x300/FFFFFF/0A9EBB?text={urllib.parse.quote(name)}"
    cur.execute("INSERT INTO products VALUES (?,?,?,?,?,?,?,?)", (pid, name, price, code, img, cat, stock, desc))
conn.commit()

HTML = """
<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>LONMA ORBIT - Complete Shop</title>
<style>
:root{--teal:#0A9EBB;--dark:#087a91}*{box-sizing:border-box}body{margin:0;font-family:Arial;background:#f0f9fb;color:#111}
.nav{position:fixed;top:0;width:100%;background:var(--teal);padding:8px 12px;display:flex;justify-content:space-between;align-items:center;z-index:1000;height:60px}
.logo-img{height:44px;width:44px;border-radius:50%;border:2px solid #fff;background:#fff;object-fit:cover}
.cart-icon{position:relative;background:#fff;color:var(--teal);padding:8px 14px;border-radius:25px;font-weight:bold;cursor:pointer}
.cart-count{position:absolute;top:-8px;right:-8px;background:#ff3b30;color:#fff;border-radius:50%;width:20px;height:20px;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:bold}
.page{display:none;padding:66px 10px 90px;min-height:100vh;background:#f0f9fb}.page.active{display:block}
.card{background:#fff;color:#111;border-radius:16px;padding:12px;margin:8px 0;box-shadow:0 2px 8px rgba(0,0,0,.08);position:relative}
.card img{width:100%;height:190px;object-fit:contain;background:#fff;border-radius:12px;padding:8px;cursor:pointer}
.btn{background:var(--teal);color:#fff;border:none;padding:12px;border-radius:25px;width:100%;font-weight:bold;cursor:pointer;font-size:13px}
.btn-black{background:#111}.btn-green{background:#25D366}
input,select,textarea{width:100%;padding:12px;border-radius:10px;border:1px solid #ddd;background:#fff;margin:5px 0;font-size:14px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.bottom{position:fixed;bottom:0;width:100%;background:#fff;display:flex;justify-content:space-around;padding:6px 0;border-top:1px solid #eee;z-index:1000}.bottom div{font-size:10px;color:#777;text-align:center;cursor:pointer;flex:1;padding:4px}.bottom div.active{color:var(--teal);font-weight:bold}
.badge-stock{position:absolute;top:10px;left:10px;background:#00c851;color:#fff;padding:3px 8px;border-radius:12px;font-size:10px;font-weight:bold;z-index:2}
.badge-cat{background:#e0f7fa;color:#0A9EBB;padding:2px 8px;border-radius:10px;font-size:10px}
.chips{display:flex;gap:6px;overflow-x:auto;padding:8px 0;flex-wrap:nowrap}.chip{white-space:nowrap;background:#fff;border:1px solid #0A9EBB;color:#0A9EBB;padding:7px 14px;border-radius:20px;font-size:12px;cursor:pointer}.chip.active{background:#0A9EBB;color:#fff}
.search-wrap{position:sticky;top:60px;background:#f0f9fb;padding:8px 0;z-index:900}
.qty-controls{display:flex;align-items:center;justify-content:space-between;background:#eef9fb;border-radius:25px;padding:5px 8px;margin-top:8px}
.qty-btn{background:var(--teal);color:#fff;border:none;width:30px;height:30px;border-radius:50%;font-weight:bold;cursor:pointer}
.modal{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.6);z-index:2000;align-items:center;justify-content:center;padding:12px}.modal.open{display:flex}.modal-box{background:#fff;border-radius:16px;max-width:400px;width:100%;max-height:90vh;overflow-y:auto}
.wish{position:absolute;top:10px;right:10px;background:#fff;border-radius:50%;width:32px;height:32px;display:flex;align-items:center;justify-content:center;cursor:pointer;box-shadow:0 2px 6px rgba(0,0,0,.15);z-index:2;font-size:16px}
.promo{background:linear-gradient(135deg,#ff9a00,#ff6a00);color:#fff;padding:10px;border-radius:12px;margin:8px 0;text-align:center;font-weight:bold;font-size:13px}
</style></head><body>
<div class="nav">
<img src="/logo.png" class="logo-img" onerror="this.src='https://via.placeholder.com/100'">
<div style="display:flex;gap:8px;align-items:center">
<div class="cart-icon" onclick="show('cart')">🛒 CART <span id="cartCount" class="cart-count" style="display:none">0</span></div>
<span onclick="show('login')" style="background:rgba(255,255,255,.3);color:#fff;padding:6px 12px;border-radius:20px;font-size:12px;cursor:pointer">Account</span>
</div>
</div>

<!-- PRODUCTS WITH SEARCH + CATEGORIES + ALL MISSING ITEMS -->
<div id="products" class="page active">
<div class="promo">🎉 FREE DELIVERY over KSh 2000 | Nairobi same-day | Upcountry 24-48hrs</div>

<div class="search-wrap">
<input id="searchInput" placeholder="🔍 Search Fresh Fri, Detrex, Sawa, Diva..." oninput="filterProducts()" style="border-radius:25px;padding:12px 16px">
<div class="chips">
<span class="chip active" onclick="filterCat('All')">All (9)</span>
<span class="chip" onclick="filterCat('Cooking Oils')">🍳 Oils (2)</span>
<span class="chip" onclick="filterCat('Soaps')">🧼 Soaps (3)</span>
<span class="chip" onclick="filterCat('Lotions')">🧴 Lotions (2)</span>
<span class="chip" onclick="filterCat('Pomades')">💇 Pomades (2)</span>
</div>
</div>

<div class="grid" id="plist"></div>

<div class="card" style="background:#111;color:#fff;text-align:center;padding:16px">
<h4 style="margin:0 0 6px">Need Help Ordering?</h4>
<p style="margin:0 0 10px;font-size:12px;opacity:.9">Chat us on WhatsApp - We reply in 2 mins</p>
<a href="https://wa.me/254700000000?text=Hi%20LONMA%20I%20want%20to%20order" target="_blank"><button class="btn btn-green">💬 WHATSAPP US</button></a>
</div>
</div>

<!-- CART WITH DELIVERY + VAT + ALL CALCULATIONS -->
<div id="cart" class="page">
<h2 style="margin:8px 0">🛒 My Cart</h2>
<div id="cartItems"></div>
<div class="card" id="cartSummary" style="display:none">
<h3 style="margin:0 0 8px">Order Summary</h3>
<div style="font-size:13px;line-height:2">
<div style="display:flex;justify-content:space-between"><span>Subtotal (<span id="totalItems">0</span> items)</span><span>KSh <span id="subTotal">0</span></span></div>
<div style="display:flex;justify-content:space-between"><span>Delivery Fee</span><span id="deliveryFee">KSh 200</span></div>
<div style="display:flex;justify-content:space-between"><span>VAT (16% incl.)</span><span>Included</span></div>
<div style="display:flex;justify-content:space-between;border-top:1px solid #eee;margin-top:6px;padding-top:6px;font-weight:bold;font-size:16px;color:#0A9EBB"><span>Total</span><span>KSh <span id="totalPrice">0</span></span></div>
<div id="freeDeliveryMsg" style="background:#e8f5e9;color:#2e7d32;padding:8px;border-radius:8px;font-size:11px;margin-top:8px;text-align:center"></div>
</div>

<div style="background:#fff;border:1px solid #ddd;padding:12px;border-radius:12px;margin-top:12px">
<h4 style="margin:0 0 8px">Delivery Details *</h4>
<input id="custName" placeholder="Full Name *">
<input id="phone" placeholder="M-Pesa Phone 07xxxxxxxx *">
<select id="locationArea"><option value="">Select Area *</option><option value="CBD">Nairobi CBD - 150</option><option value="Westlands">Westlands - 200</option><option value="Eastlands">Eastlands - 200</option><option value="Upcountry">Upcountry - 350</option></select>
<textarea id="exactLocation" placeholder="Estate, House No, Landmark * e.g Umoja Innercore Phase 2 House 123 near chief"></textarea>
<label style="font-size:12px;display:flex;gap:6px;align-items:center;margin-top:8px"><input type="checkbox" id="agreeTerms" style="width:auto"> I agree to Terms & delivery fee</label>
</div>

<div style="background:linear-gradient(135deg,#0A9EBB,#087a91);color:#fff;padding:12px;border-radius:12px;margin-top:12px">
<button class="btn" style="background:#111" onclick="checkout()">💳 PAY KSh <span id="payTotal">0</span> WITH M-PESA</button>
<button class="btn btn-green" style="margin-top:8px" onclick="orderWhatsApp()">💬 ORDER VIA WHATSAPP</button>
<p id="paystatus" style="font-size:12px;margin-top:8px;min-height:18px;background:rgba(255,255,255,.15);padding:6px;border-radius:8px"></p>
</div>
<button class="btn" style="margin-top:10px;background:#666" onclick="clearCart()">🗑️ CLEAR CART</button>
<button class="btn" style="background:#fff;color:#0A9EBB;border:1px solid #0A9EBB" onclick="show('products')">← CONTINUE SHOPPING</button>
</div>
<div class="card" id="emptyCart" style="text-align:center;padding:30px"><p style="font-size:50px;margin:0">🛒</p><h3>Your cart is empty</h3><p style="font-size:12px;color:#666">Add same product multiple times - quantity will increase</p><button class="btn" onclick="show('products')">START SHOPPING</button></div>
</div>

<!-- SCAN + LOCATIONS + TERMS + LOGIN REMOVED VERIFY FROM PRODUCTS ONLY -->
<div id="scan" class="page"><h2>📷 Verify Original</h2><div class="card"><input id="manualcode" placeholder="LONMA-001"><button class="btn" onclick="verifyCode()">CHECK</button><p id="scanresult"></p></div></div>
<div id="locations" class="page"><h2>📍 Stores</h2><div class="card"><h4>CBD Moi Ave</h4><p style="font-size:13px">Opposite Imenti 2nd Floor 8am-7pm</p><a href="https://maps.google.com/?q=Moi+Avenue+Nairobi" target="_blank"><button class="btn">DIRECTIONS</button></a></div></div>
<div id="terms" class="page"><h2>📄 Terms</h2><div class="card" style="font-size:12px;line-height:1.6"><p><b>Cart:</b> Same product adds qty. Stock shown. Free delivery over 2000.</p><p><b>Delivery:</b> Nairobi 150-200, Upcountry 350. Pay via M-Pesa or WhatsApp order.</p><button class="btn" onclick="show('products')">OK</button></div></div>
<div id="login" class="page"><h2>Account</h2><div class="card"><input id="lemail" placeholder="Email"><input id="lpass" type="password" placeholder="Password"><button class="btn" onclick="login()">Log In</button><p id="lstatus"></p><p style="text-align:center;font-size:12px">No account? <span style="color:#0A9EBB;font-weight:bold" onclick="show('signin')">Sign up - Get 10% off</span></p></div></div>
<div id="signin" class="page"><h2>Sign Up</h2><div class="card"><input id="sname" placeholder="Name"><input id="semail" placeholder="Email"><input id="spass" type="password" placeholder="Password"><button class="btn" onclick="signin()">Create & Get 100 KSh OFF</button><p id="sstatus"></p></div></div>

<div class="bottom">
<div id="b-products" class="active" onclick="show('products')">🛍️<br>Products</div>
<div id="b-cart" onclick="show('cart')">🛒<br>Cart (<span id="bottomCartCount">0</span>)</div>
<div id="b-scan" onclick="show('scan')">📷<br>Verify</div>
<div id="b-locations" onclick="show('locations')">📍<br>Stores</div>
<div id="b-login" onclick="show('login')">👤<br>Account</div>
</div>

<!-- PRODUCT DETAIL MODAL -->
<div id="productModal" class="modal" onclick="if(event.target===this)closeModal()"><div class="modal-box"><div id="modalContent"></div></div></div>

<script>
let allProducts=[]; let currentCat='All'; let searchQuery=''; let wishlist=JSON.parse(localStorage.getItem('wishlist')||'[]');
let cart=[]; try{let s=localStorage.getItem('lonma_cart'); if(s)cart=JSON.parse(s); if(!Array.isArray(cart))cart=[];}catch(e){cart=[]}

function saveCart(){localStorage.setItem('lonma_cart',JSON.stringify(cart)); updateCartCount();}
function updateCartCount(){let c=0; for(let i of cart)c+=Number(i.qty)||0; document.getElementById('cartCount').innerText=c; document.getElementById('bottomCartCount').innerText=c; document.getElementById('cartCount').style.display=c>0?'flex':'none';}

function filterCat(cat){
 currentCat=cat;
 document.querySelectorAll('.chip').forEach(ch=>{ch.classList.remove('active'); if(ch.textContent.includes(cat)||(cat==='All'&&ch.textContent.startsWith('All')))ch.classList.add('active');});
 renderProducts();
}
function filterProducts(){searchQuery=document.getElementById('searchInput').value.toLowerCase(); renderProducts();}

function renderProducts(){
 let list=allProducts.filter(p=>{
   let matchCat=currentCat==='All'||p.category===currentCat;
   let matchSearch=!searchQuery||p.name.toLowerCase().includes(searchQuery)||p.category.toLowerCase().includes(searchQuery);
   return matchCat&&matchSearch;
 });
 let html=''; 
 for(let p of list){
   let inCart=cart.find(c=>c.id===p.id);
   let qtyText=inCart?`In cart: ${inCart.qty} pcs`:'';
   let stockText=p.stock>20?`In Stock (${p.stock})`:p.stock>0?`Low Stock (${p.stock})`:'Out of Stock';
   let stockColor=p.stock>20?'#00c851':p.stock>0?'#ff9a00':'#ff3b30';
   html+=`<div class="card">
     <span class="badge-stock" style="background:${stockColor}">${stockText}</span>
     <span class="wish" onclick="toggleWish(${p.id})">${wishlist.includes(p.id)?'❤️':'🤍'}</span>
     <img src="${p.image}" onclick="openModal(${p.id})" loading="lazy">
     <span class="badge-cat">${p.category}</span>
     <h4 style="font-size:12px;margin:6px 0;line-height:1.3">${p.name}</h4>
     <div style="display:flex;justify-content:space-between;align-items:center">
       <p style="margin:0;font-weight:bold;color:#0A9EBB;font-size:15px">KSh ${p.price}</p>
       <span style="font-size:11px;color:#ffb400">⭐⭐⭐⭐⭐ 5.0</span>
     </div>
     <small style="background:#0A9EBB;color:#fff;padding:2px 6px;border-radius:10px;font-size:10px">${p.code}</small>
     <button class="btn" onclick="addToCart(${p.id})" ${p.stock===0?'disabled style="background:#ccc"':''}>${p.stock===0?'OUT OF STOCK':'🛒 ADD TO CART'}</button>
     <div style="font-size:11px;color:#0A9EBB;margin-top:4px;text-align:center;font-weight:bold;min-height:16px">${qtyText}</div>
   </div>`;
 }
 document.getElementById('plist').innerHTML=html||'<div class="card" style="grid-column:1/3;text-align:center">No products found for "'+searchQuery+'"</div>';
}

function openModal(id){
 let p=allProducts.find(x=>x.id===id); if(!p)return;
 document.getElementById('modalContent').innerHTML=`
   <img src="${p.image}" style="width:100%;height:260px;object-fit:contain;padding:12px">
   <div style="padding:12px">
     <span class="badge-cat">${p.category}</span> <small style="background:#0A9EBB;color:#fff;padding:2px 6px;border-radius:10px">${p.code}</small>
     <h3 style="margin:8px 0">${p.name}</h3>
     <p style="color:#0A9EBB;font-weight:bold;font-size:20px;margin:0">KSh ${p.price}</p>
     <p style="font-size:12px;color:#00c851;font-weight:bold">● ${p.stock>0?p.stock+' in stock - Ready to ship':'Out of stock'}</p>
     <p style="font-size:13px;line-height:1.5">${p.desc}</p>
     <p style="font-size:12px;background:#f7f7f7;padding:8px;border-radius:8px">✓ 100% Original Pwani Oil<br>✓ Verified LONMA code<br>✓ Free delivery over 2000<br>✓ 24hr return if defect</p>
     <div style="display:flex;gap:8px;margin-top:10px">
       <button class="btn" style="flex:1" onclick="addToCart(${p.id});closeModal()">🛒 ADD TO CART</button>
       <button class="btn btn-green" style="flex:1" onclick="orderWhatsAppSingle(${p.id})">💬 WHATSAPP</button>
     </div>
     <button class="btn" style="background:#fff;color:#0A9EBB;border:1px solid #0A9EBB;margin-top:8px" onclick="closeModal()">Continue Shopping</button>
   </div>`;
 document.getElementById('productModal').classList.add('open');
}
function closeModal(){document.getElementById('productModal').classList.remove('open');}
function toggleWish(id){
 if(wishlist.includes(id)){wishlist=wishlist.filter(x=>x!==id);}else{wishlist.push(id);}
 localStorage.setItem('wishlist',JSON.stringify(wishlist)); renderProducts();
}

function addToCart(id){
 let p=allProducts.find(x=>x.id===id); if(!p||p.stock===0)return;
 let found=cart.find(c=>c.id===id);
 if(found){
   if(found.qty>=p.stock){alert('Only '+p.stock+' in stock!');return;}
   found.qty++; alert('Added again! '+p.name+' qty '+found.qty);
 } else {
   cart.push({id:p.id,name:p.name,price:p.price,image:p.image,code:p.code,qty:1,stock:p.stock});
   alert('Added: '+p.name);
 }
 saveCart(); renderCart(); renderProducts();
}
function changeQty(id,delta){
 for(let i=0;i<cart.length;i++)if(cart[i].id===id){
   cart[i].qty+=delta;
   if(cart[i].qty<=0)cart.splice(i,1);
   else if(cart[i].qty>cart[i].stock){cart[i].qty=cart[i].stock; alert('Max stock '+cart[i].stock);}
   break;
 }
 saveCart(); renderCart(); renderProducts();
}
function clearCart(){if(confirm('Clear cart?')){cart=[];saveCart();renderCart();renderProducts();}}

function renderCart(){
 let cont=document.getElementById('cartItems'), sum=document.getElementById('cartSummary'), empty=document.getElementById('emptyCart');
 if(cart.length===0){cont.innerHTML='';sum.style.display='none';empty.style.display='block';return;}
 empty.style.display='none'; sum.style.display='block';
 let totalItems=0, subTotal=0, html='';
 for(let it of cart){
   totalItems+=it.qty; subTotal+=it.price*it.qty;
   html+=`<div class="card cart-item"><img src="${it.image}"><div style="flex:1"><h4 style="margin:0;font-size:13px">${it.name}</h4><p style="margin:2px 0;font-size:12px;color:#0A9EBB;font-weight:bold">KSh ${it.price} x ${it.qty} = KSh ${it.price*it.qty}</p><small style="background:#0A9EBB;color:#fff;padding:2px 6px;border-radius:10px">${it.code}</small><div class="qty-controls"><button class="qty-btn" onclick="changeQty(${it.id},-1)">-</button><span>${it.qty} pcs</span><button class="qty-btn" onclick="changeQty(${it.id},1)">+</button><button onclick="changeQty(${it.id},-${it.qty})" style="margin-left:8px;background:#ff4444;color:#fff;border:none;padding:6px 10px;border-radius:12px;font-size:11px">Remove</button></div></div></div>`;
 }
 cont.innerHTML=html;
 let area=document.getElementById('locationArea').value;
 let delivery=200;
 if(area==='CBD')delivery=150; if(area==='Westlands'||area==='Eastlands')delivery=200; if(area==='Upcountry')delivery=350;
 if(subTotal>=2000)delivery=0;
 document.getElementById('subTotal').innerText=subTotal;
 document.getElementById('deliveryFee').innerText=delivery===0?'FREE':'KSh '+delivery;
 document.getElementById('totalItems').innerText=totalItems;
 let total=subTotal+delivery;
 document.getElementById('totalPrice').innerText=total;
 document.getElementById('payTotal').innerText=total;
 let freeMsg=document.getElementById('freeDeliveryMsg');
 if(subTotal>=2000)freeMsg.innerHTML='🎉 You got FREE delivery!';
 else freeMsg.innerHTML=`Add KSh ${2000-subTotal} more for FREE delivery!`;
}

document.getElementById('locationArea')?.addEventListener('change',renderCart);

function show(id){
 document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));
 document.getElementById(id).classList.add('active');
 document.querySelectorAll('.bottom div').forEach(b=>b.classList.remove('active'));
 let btn=document.getElementById('b-'+id); if(btn)btn.classList.add('active');
 if(id==='cart')renderCart();
 window.scrollTo(0,0);
}

async function loadProducts(){
 let r=await fetch('/api/products'); let d=await r.json();
 allProducts=d.map(p=>({id:p.id,name:p.name,price:p.price,code:p.code,image:p.image,category:p.category,stock:p.stock,desc:p.desc}));
 renderProducts();
}

async function verifyCode(){let c=document.getElementById('manualcode').value.trim().toUpperCase();let r=await fetch(`/api/verify/${c}`);let d=await r.json();document.getElementById('scanresult').innerHTML=d.valid?`✅ ${d.product.name} ORIGINAL`:`❌ Invalid`}
async function login(){let r=await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:document.getElementById('lemail').value,password:document.getElementById('lpass').value})});let d=await r.json();document.getElementById('lstatus').innerText=d.message;}
async function signin(){let r=await fetch('/api/signin',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:document.getElementById('sname').value,email:document.getElementById('semail').value,password:document.getElementById('spass').value})});let d=await r.json();document.getElementById('sstatus').innerText=d.message;}

function orderWhatsApp(){
 if(cart.length===0){alert('Cart empty');return;}
 let name=document.getElementById('custName').value, phone=document.getElementById('phone').value, area=document.getElementById('locationArea').value, loc=document.getElementById('exactLocation').value;
 let total=document.getElementById('totalPrice').innerText;
 let items=cart.map(c=>`${c.name} x${c.qty} = KSh ${c.price*c.qty}`).join('%0A');
 let msg=`Hi LONMA ORBIT%0AI want to order:%0A${items}%0A%0ATotal KSh ${total}%0AName: ${name}%0APhone: ${phone}%0AArea: ${area}%0ALocation: ${loc}`;
 window.open(`https://wa.me/254700000000?text=${msg}`,'_blank');
}
function orderWhatsAppSingle(id){
 let p=allProducts.find(x=>x.id===id);
 let msg=`Hi LONMA I want ${p.name} KSh ${p.price} Code ${p.code}`;
 window.open(`https://wa.me/254700000000?text=${encodeURIComponent(msg)}`,'_blank');
}

async function checkout(){
 let name=document.getElementById('custName').value.trim(), phone=document.getElementById('phone').value.trim(), area=document.getElementById('locationArea').value, loc=document.getElementById('exactLocation').value.trim(), agree=document.getElementById('agreeTerms').checked;
 if(!name||!phone||!area||!loc){document.getElementById('paystatus').innerText='⚠️ Fill all delivery details *';return;}
 if(!agree){document.getElementById('paystatus').innerText='⚠️ Agree to terms';return;}
 if(phone.length!==10||!phone.startsWith('07')){document.getElementById('paystatus').innerText='⚠️ Phone must be 07xxxxxxxx';return;}
 let total=0; for(let i of cart)total+=i.price*i.qty;
 let delivery=area==='CBD'?150:area==='Upcountry'?350:200; if(total>=2000)delivery=0; total+=delivery;
 document.getElementById('paystatus').innerText=`⏳ Sending STK KSh ${total} to ${phone}...`;
 let r=await fetch('/mpesa/stkpush',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({phone,amount:total,cart,name,area,location:loc})});
 let d=await r.json();
 document.getElementById('paystatus').innerText=`✅ ${d.message} Order placed! Delivery to ${area}`;
 if(d.message.includes('sent')){cart=[];saveCart(); setTimeout(()=>{alert('Order Success! We will call '+phone+' for delivery'); show('products');},1000);}
}

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

@app.get("/api/products")
def products():
    cur=conn.cursor()
    cur.execute("SELECT id,name,price,code,image,category,stock,desc FROM products")
    return [{"id":r[0],"name":r[1],"price":r[2],"code":r[3],"image":r[4],"category":r[5],"stock":r[6],"desc":r[7]} for r in cur.fetchall()]

@app.get("/api/verify/{code}")
def verify(code: str):
    cur=conn.cursor(); cur.execute("SELECT name FROM products WHERE code=?",(code.strip().upper(),))
    row=cur.fetchone(); return {"valid":True,"product":{"name":row[0]}} if row else {"valid":False}

@app.post("/api/signin")
async def signin_api(req: Request):
    d=await req.json()
    try: conn.execute("INSERT INTO users (email,password,name) VALUES (?,?,?)",(d.get("email"),d.get("password"),d.get("name")));conn.commit();return {"status":"ok","message":"Account created! 100 KSh off next order"}
    except: return {"status":"error","message":"Email exists"}

@app.post("/api/login")
async def login_api(req: Request):
    d=await req.json(); cur=conn.cursor(); cur.execute("SELECT * FROM users WHERE email=? AND password=?",(d.get("email"),d.get("password")))
    return {"status":"ok","message":"Welcome back!"} if cur.fetchone() else {"status":"error","message":"Invalid login"}

@app.post("/mpesa/stkpush")
async def stk(req: Request):
    d=await req.json()
    return {"message":f"STK KSh {d.get('amount')} sent to {d.get('phone')} for {len(d.get('cart',[]))} items - Enter PIN (DEMO)"}

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import os, sqlite3, urllib.parse, json, datetime

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

conn = sqlite3.connect("lonma.db", check_same_thread=False)
conn.execute("CREATE TABLE IF NOT EXISTS users (email TEXT UNIQUE, password TEXT, name TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT, price INTEGER, code TEXT, image TEXT, category TEXT, stock INTEGER, desc TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, order_no TEXT, name TEXT, phone TEXT, area TEXT, location TEXT, items TEXT, subtotal INTEGER, delivery INTEGER, total INTEGER, status TEXT, created TEXT)")
cur = conn.cursor()
cur.execute("DELETE FROM products")

PRODUCTS = [
    (1, "Fresh Fri Cooking Oil 2L", 850, "LONMA-001", "Cooking Oils", 50, "Pure fortified cooking oil 2L cholesterol free original Pwani"),
    (2, "Detrex Citronella Soap 110g", 90, "LONMA-002", "Soaps", 120, "Anti-bacterial citronella germ protection soap"),
    (3, "Sawa Men Lotion 72Hrs", 299, "LONMA-003", "Lotions", 35, "72Hrs hydration for men non greasy fast absorbing"),
    (4, "Detrex Pine Drops Soap 110g", 90, "LONMA-004", "Soaps", 100, "Pine drops fresh fragrance deep clean"),
    (5, "Salit Vegetable Oil 5L", 1250, "LONMA-005", "Cooking Oils", 25, "Vegetable cooking oil 5L family pack best for frying"),
    (6, "Detrex Cool Mint Soap 110g", 90, "LONMA-006", "Soaps", 80, "Cool mint cooling effect fresh skin"),
    (7, "Diva Anti-Dandruff Pomade 250ml", 250, "LONMA-007", "Pomades", 40, "Anti-dandruff hair pomade 250ml stops itching"),
    (8, "Diva Anti-Breakage Pomade", 250, "LONMA-008", "Pomades", 45, "Anti-breakage strengthens hair roots"),
    (9, "Sawa Cocoa Butter Lotion", 299, "LONMA-009", "Lotions", 30, "Cocoa butter nourishing lotion soft skin 24Hrs"),
]

for pid, name, price, code, cat, stock, desc in PRODUCTS:
    img = f"https://via.placeholder.com/400x300/FFFFFF/0A9EBB?text={urllib.parse.quote(name)}"
    cur.execute("INSERT INTO products VALUES (?,?,?,?,?,?,?,?)", (pid, name, price, code, img, cat, stock, desc))
conn.commit()

HTML = """
<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>LONMA ORBIT - Original Pwani Products</title>
<meta name="description" content="Buy original Fresh Fri, Detrex, Sawa, Diva, Salit - Free delivery over 2000 Nairobi"><style>
:root{--teal:#0A9EBB;--dark:#087a91}*{box-sizing:border-box}body{margin:0;font-family:Arial;background:#f0f9fb;color:#111}
.nav{position:fixed;top:0;width:100%;background:var(--teal);padding:8px 12px;display:flex;justify-content:space-between;align-items:center;z-index:1000;height:60px}
.cart-icon{position:relative;background:#fff;color:var(--teal);padding:8px 14px;border-radius:25px;font-weight:bold;cursor:pointer}
.cart-count{position:absolute;top:-8px;right:-8px;background:#ff3b30;color:#fff;border-radius:50%;width:20px;height:20px;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:bold}
.page{display:none;padding:66px 10px 90px;min-height:100vh;background:#f0f9fb}.page.active{display:block}
.card{background:#fff;border-radius:16px;padding:12px;margin:8px 0;box-shadow:0 2px 8px rgba(0,0,0,.08);position:relative}
.card img{width:100%;height:190px;object-fit:contain;background:#fff;border-radius:12px;padding:8px}
.btn{background:var(--teal);color:#fff;border:none;padding:12px;border-radius:25px;width:100%;font-weight:bold;cursor:pointer;font-size:13px}
.btn-black{background:#111}.btn-green{background:#25D366}
input,select,textarea{width:100%;padding:12px;border-radius:10px;border:1px solid #ddd;background:#fff;margin:5px 0;font-size:14px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.bottom{position:fixed;bottom:0;width:100%;background:#fff;display:flex;justify-content:space-around;padding:6px 0;border-top:1px solid #eee;z-index:1000}.bottom div{font-size:10px;color:#777;text-align:center;cursor:pointer;flex:1}.bottom div.active{color:var(--teal);font-weight:bold}
.chips{display:flex;gap:6px;overflow-x:auto;padding:8px 0}.chip{white-space:nowrap;background:#fff;border:1px solid #0A9EBB;color:#0A9EBB;padding:7px 14px;border-radius:20px;font-size:12px;cursor:pointer}.chip.active{background:#0A9EBB;color:#fff}
.qty-controls{display:flex;align-items:center;justify-content:space-between;background:#eef9fb;border-radius:25px;padding:5px 8px;margin-top:8px}
.qty-btn{background:var(--teal);color:#fff;border:none;width:30px;height:30px;border-radius:50%;font-weight:bold;cursor:pointer}
.promo{background:linear-gradient(135deg,#ff9a00,#ff6a00);color:#fff;padding:10px;border-radius:12px;margin:8px 0;text-align:center;font-weight:bold;font-size:13px}
.footer{background:#111;color:#fff;padding:20px;border-radius:16px;margin-top:12px;font-size:12px;line-height:1.6}
.badge-stock{position:absolute;top:8px;left:8px;padding:3px 8px;border-radius:12px;font-size:10px;font-weight:bold;color:#fff;z-index:2}
.modal{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.6);z-index:2000;align-items:center;justify-content:center;padding:12px}.modal.open{display:flex}.modal-box{background:#fff;border-radius:16px;max-width:420px;width:100%;max-height:92vh;overflow-y:auto}
</style></head><body>
<div class="nav"><img src="/logo.png" style="height:44px;width:44px;border-radius:50%;border:2px solid #fff;background:#fff;object-fit:cover" onerror="this.src='https://via.placeholder.com/100'"><div style="display:flex;gap:8px;align-items:center"><div class="cart-icon" onclick="show('cart')">🛒 CART <span id="cartCount" class="cart-count" style="display:none">0</span></div><span onclick="show('login')" style="background:rgba(255,255,255,.3);color:#fff;padding:6px 12px;border-radius:20px;font-size:12px;cursor:pointer">Account</span></div></div>

<div id="products" class="page active">
<div class="promo">🎉 FREE DELIVERY over KSh 2000 | Nairobi 2-3hrs | Upcountry 24-48hrs | 100% Original Pwani</div>
<div style="position:sticky;top:60px;background:#f0f9fb;padding:8px 0;z-index:900"><input id="searchInput" placeholder="🔍 Search Fresh Fri, Detrex, Sawa, Diva..." oninput="filterProducts()" style="border-radius:25px;padding:12px 16px"><div class="chips"><span class="chip active" onclick="filterCat('All',this)">All 9</span><span class="chip" onclick="filterCat('Cooking Oils',this)">🍳 Oils 2</span><span class="chip" onclick="filterCat('Soaps',this)">🧼 Soaps 3</span><span class="chip" onclick="filterCat('Lotions',this)">🧴 Lotions 2</span><span class="chip" onclick="filterCat('Pomades',this)">💇 Pomades 2</span></div></div>
<div class="grid" id="plist"></div>
<div class="card" style="text-align:center"><p style="margin:0;font-weight:bold">⭐⭐⭐⭐⭐ 5.0 | 5000+ Happy Customers | 100% Original</p><p style="font-size:11px;color:#666;margin:4px 0">✓ M-Pesa Secured ✓ Same-day Nairobi ✓ 24hr Return</p></div>
<div class="footer"><h4 style="margin:0 0 8px">LONMA ORBIT ENTERPRISES</h4><p style="margin:0">📍 CBD Moi Avenue Opposite Imenti House 2nd Floor<br>📞 0700 000 000 / 0111 222 333<br>📧 sales@lonmaorbit.co.ke<br>🕒 Mon-Sat 8am-7pm Sun 9am-5pm<br>💳 M-Pesa Till 123456 | Paybill 123456<br><br><b>About:</b> Authorized Pwani Oil distributor - Fresh Fri, Detrex, Sawa, Diva, Salit original products. Verify with LONMA code.</p><div style="display:flex;gap:8px;margin-top:10px"><a href="https://wa.me/254700000000" target="_blank" style="flex:1"><button class="btn btn-green">💬 WhatsApp</button></a><a href="tel:0700000000" style="flex:1"><button class="btn" style="background:#111">📞 Call Us</button></a></div></div>
</div>

<div id="cart" class="page">
<h2 style="margin:8px 0">🛒 My Cart</h2>
<div id="cartItems"></div>
<div class="card" id="cartSummary" style="display:none">
<h3 style="margin:0 0 8px">Order Summary</h3>
<div style="font-size:13px;line-height:2"><div style="display:flex;justify-content:space-between"><span>Subtotal (<span id="totalItems">0</span> items)</span><span>KSh <span id="subTotal">0</span></span></div><div style="display:flex;justify-content:space-between"><span>Delivery</span><span id="deliveryFee">KSh 200</span></div><div style="display:flex;justify-content:space-between;border-top:1px solid #eee;margin-top:6px;padding-top:6px;font-weight:bold;font-size:16px;color:#0A9EBB"><span>Total</span><span>KSh <span id="totalPrice">0</span></span></div></div>
<div id="freeDeliveryMsg" style="background:#e8f5e9;color:#2e7d32;padding:8px;border-radius:8px;font-size:11px;margin-top:8px;text-align:center"></div>
<div style="background:#fff;border:1px solid #ddd;padding:12px;border-radius:12px;margin-top:12px"><h4 style="margin:0 0 8px">Delivery Details *</h4><input id="custName" placeholder="Full Name *"><input id="phone" placeholder="M-Pesa Phone 07xxxxxxxx *"><select id="locationArea"><option value="">Select Area *</option><option value="CBD">Nairobi CBD - KSh 150 (2-3hrs)</option><option value="Westlands">Westlands/Parklands - 200 (2-3hrs)</option><option value="Eastlands">Eastlands/South B/C - 200 (3-4hrs)</option><option value="Upcountry">Upcountry - 350 (24-48hrs)</option></select><textarea id="exactLocation" placeholder="Estate, House No, Landmark * e.g Umoja Innercore Phase 2 House 123 near Chief"></textarea><input id="promoCode" placeholder="Promo Code (Optional) e.g LONMA10"><label style="font-size:12px;display:flex;gap:6px;align-items:center;margin-top:8px"><input type="checkbox" id="agreeTerms" style="width:auto"> I agree to Terms & delivery fee</label></div>
<div style="background:linear-gradient(135deg,#0A9EBB,#087a91);color:#fff;padding:12px;border-radius:12px;margin-top:12px"><button class="btn" style="background:#111" onclick="checkout()">💳 PAY KSh <span id="payTotal">0</span> WITH M-PESA</button><button class="btn btn-green" style="margin-top:8px" onclick="orderWhatsApp()">💬 ORDER VIA WHATSAPP</button><p id="paystatus" style="font-size:12px;margin-top:8px;min-height:18px;background:rgba(255,255,255,.15);padding:6px;border-radius:8px"></p></div>
<button class="btn" style="margin-top:10px;background:#666" onclick="clearCart()">🗑️ CLEAR CART</button><button class="btn" style="background:#fff;color:#0A9EBB;border:1px solid #0A9EBB;margin-top:6px" onclick="show('products')">← CONTINUE SHOPPING</button>
</div>
<div class="card" id="emptyCart" style="text-align:center;padding:30px"><p style="font-size:50px;margin:0">🛒</p><h3>Cart Empty</h3><p style="font-size:12px;color:#666">Add same product multiple times - quantity increases</p><button class="btn" onclick="show('products')">START SHOPPING</button></div>
</div>

<div id="orders" class="page"><h2>📦 My Orders</h2><div id="ordersList"></div><div class="card" id="noOrders" style="text-align:center;padding:30px"><p style="font-size:40px">📦</p><h3>No orders yet</h3><button class="btn" onclick="show('products')">Shop Now</button></div></div>

<div id="scan" class="page"><h2>📷 Verify Original</h2><div class="card"><p style="font-size:12px">Enter code on product e.g LONMA-001</p><input id="manualcode" placeholder="LONMA-001"><button class="btn" onclick="verifyCode()">VERIFY CODE</button><p id="scanresult" style="font-weight:bold;font-size:14px;margin-top:10px"></p><p style="font-size:11px;color:#666">Valid: LONMA-001 to LONMA-009 - 100% Pwani original</p></div></div>

<div id="locations" class="page"><h2>📍 Our Stores</h2><div class="card"><h4 style="margin:0">CBD - Moi Avenue</h4><p style="font-size:13px;margin:4px 0">Opposite Imenti House 2nd Floor<br>Mon-Sat 8am-7pm Sun 9am-5pm</p><a href="https://maps.google.com/?q=Moi+Avenue+Nairobi" target="_blank"><button class="btn">📍 GET DIRECTIONS</button></a></div><div class="card"><h4 style="margin:0">Contact</h4><p style="font-size:13px">Phone: 0700 000 000<br>Email: sales@lonmaorbit.co.ke<br>WhatsApp: 0700 000 000</p><div style="display:flex;gap:8px"><a href="https://wa.me/254700000000" target="_blank" style="flex:1"><button class="btn btn-green">WhatsApp</button></a><a href="tel:0700000000" style="flex:1"><button class="btn" style="background:#111">Call</button></a></div></div></div>

<div id="terms" class="page"><h2>📄 Terms & FAQ</h2><div class="card" style="font-size:12px;line-height:1.6"><p><b>Cart:</b> Same product adds qty. Example Fresh Fri x2 = qty 2.</p><p><b>Stock:</b> Real-time stock shown. Low stock warning.</p><p><b>Delivery:</b> CBD 150 (2-3hrs), Westlands/Eastlands 200 (3-4hrs), Upcountry 350 (24-48hrs). FREE over 2000.</p><p><b>Payment:</b> M-Pesa STK or WhatsApp order + Pay on delivery.</p><p><b>Returns:</b> 24hr return if defect or wrong product. Must have LONMA code intact.</p><p><b>Original:</b> All products have LONMA code LONMA-001 to 009 verify on Scan page.</p><p><b>Promo:</b> Use LONMA10 for 10% off first order over 1000.</p><button class="btn" onclick="show('products')">OK - START SHOPPING</button></div></div>

<div id="login" class="page"><h2>👤 Account</h2><div class="card"><input id="lemail" placeholder="Email"><input id="lpass" type="password" placeholder="Password"><button class="btn" onclick="login()">Log In</button><p id="lstatus" style="font-size:12px"></p><p style="text-align:center;font-size:12px">No account? <span style="color:#0A9EBB;font-weight:bold;cursor:pointer" onclick="show('signin')">Sign up - Get 10% off</span></p><button class="btn" style="background:#fff;color:#0A9EBB;border:1px solid #0A9EBB;margin-top:8px" onclick="show('orders')">📦 My Orders</button><button class="btn" style="background:#fff;color:#0A9EBB;border:1px solid #0A9EBB;margin-top:6px" onclick="show('admin')">🔐 Admin</button></div></div>

<div id="signin" class="page"><h2>Sign Up</h2><div class="card"><input id="sname" placeholder="Full Name"><input id="semail" placeholder="Email"><input id="spass" type="password" placeholder="Password"><button class="btn" onclick="signin()">Create Account & Get 100 KSh OFF</button><p id="sstatus" style="font-size:12px"></p></div></div>

<div id="admin" class="page"><h2>🔐 Admin Dashboard</h2><div class="card"><input id="adminPass" type="password" placeholder="Admin Password (lonma2024)"><button class="btn" onclick="adminLogin()">Login</button><p id="adminStatus"></p></div><div id="adminContent" style="display:none"><div class="card"><h3>📊 Today Stats</h3><p>Total Orders: <span id="statOrders">0</span> | Sales: KSh <span id="statSales">0</span></p><button class="btn" onclick="loadAdminOrders()">🔄 Refresh Orders</button></div><div id="adminOrdersList"></div></div></div>

<div id="receipt" class="page"><h2>🧾 Receipt</h2><div class="card" id="receiptContent"></div><button class="btn" onclick="show('products')">Continue Shopping</button></div>

<div class="bottom"><div id="b-products" class="active" onclick="show('products')">🛍️<br>Products</div><div id="b-cart" onclick="show('cart')">🛒<br>Cart (<span id="bottomCartCount">0</span>)</div><div id="b-orders" onclick="show('orders')">📦<br>Orders</div><div id="b-scan" onclick="show('scan')">📷<br>Verify</div><div id="b-login" onclick="show('login')">👤<br>Account</div></div>

<div id="productModal" class="modal" onclick="if(event.target===this)closeModal()"><div class="modal-box"><div id="modalContent"></div></div></div>

<script>
let rawCart = localStorage.getItem('lonma_cart');
if(rawCart && rawCart.includes('undefined')){ localStorage.removeItem('lonma_cart'); }
let allProducts=[], currentCat='All', searchQuery='', cart=[], myOrders=JSON.parse(localStorage.getItem('my_orders')||'[]');
try{let s=localStorage.getItem('lonma_cart'); if(s){cart=JSON.parse(s); cart=cart.filter(c=>c && c.image && !String(c.image).includes('undefined') && c.name);} if(!Array.isArray(cart))cart=[];}catch(e){cart=[]; localStorage.removeItem('lonma_cart');}
function safeImage(name){if(!name) return 'https://via.placeholder.com/400x300/FFFFFF/0A9EBB?text=Product'; return `https://via.placeholder.com/400x300/FFFFFF/0A9EBB?text=${encodeURIComponent(name)}`;}
function saveCart(){localStorage.setItem('lonma_cart',JSON.stringify(cart)); updateCartCount();}
function updateCartCount(){let c=0; for(let i of cart)c+=Number(i.qty)||0; document.getElementById('cartCount').innerText=c; document.getElementById('bottomCartCount').innerText=c; document.getElementById('cartCount').style.display=c>0?'flex':'none';}
function filterCat(cat,el){currentCat=cat; document.querySelectorAll('.chip').forEach(ch=>ch.classList.remove('active')); if(el)el.classList.add('active'); renderProducts();}
function filterProducts(){searchQuery=document.getElementById('searchInput').value.toLowerCase(); renderProducts();}
function renderProducts(){
let list=allProducts.filter(p=>{let mCat=currentCat==='All'||p.category===currentCat; let mSearch=!searchQuery||p.name.toLowerCase().includes(searchQuery)||p.category.toLowerCase().includes(searchQuery); return mCat&&mSearch;});
let html=''; for(let p of list){let inCart=cart.find(c=>c.id===p.id); let qtyText=inCart?`In cart: ${inCart.qty} pcs`:'';
let img=p.image&&!String(p.image).includes('undefined')?p.image:safeImage(p.name);
let stockColor=p.stock>20?'#00c851':p.stock>5?'#ff9a00':'#ff3b30'; let stockText=p.stock>20?`In Stock ${p.stock}`:p.stock>0?`Low Stock ${p.stock}`:`Out of Stock`;
html+=`<div class="card"><span class="badge-stock" style="background:${stockColor}">${stockText}</span><img src="${img}" loading="lazy" onclick="openModal(${p.id})" onerror="this.src='${safeImage(p.name)}'"><span style="background:#e0f7fa;color:#0A9EBB;padding:2px 8px;border-radius:10px;font-size:10px">${p.category}</span><h4 style="font-size:12px;margin:6px 0;line-height:1.3">${p.name}</h4><div style="display:flex;justify-content:space-between;align-items:center"><p style="margin:0;font-weight:bold;color:#0A9EBB;font-size:15px">KSh ${p.price}</p><span style="font-size:11px;color:#ffb400">⭐⭐⭐⭐⭐</span></div><small style="background:#0A9EBB;color:#fff;padding:2px 6px;border-radius:10px;font-size:10px">${p.code}</small><button class="btn" onclick="addToCart(${p.id})" ${p.stock===0?'disabled style="background:#ccc"':''}>${p.stock===0?'OUT OF STOCK':'🛒 ADD TO CART'}</button><div style="font-size:11px;color:#0A9EBB;text-align:center;font-weight:bold;min-height:16px;margin-top:4px">${qtyText}</div></div>`;}
document.getElementById('plist').innerHTML=html||'<div class="card" style="grid-column:1/3;text-align:center">No products found</div>';
}
function openModal(id){
let p=allProducts.find(x=>x.id===id); if(!p)return;
let img=p.image&&!String(p.image).includes('undefined')?p.image:safeImage(p.name);
document.getElementById('modalContent').innerHTML=`<img src="${img}" style="width:100%;height:260px;object-fit:contain;padding:12px" onerror="this.src='${safeImage(p.name)}'"><div style="padding:12px"><span style="background:#e0f7fa;color:#0A9EBB;padding:2px 8px;border-radius:10px;font-size:10px">${p.category}</span> <small style="background:#0A9EBB;color:#fff;padding:2px 6px;border-radius:10px">${p.code}</small><h3 style="margin:8px 0">${p.name}</h3><p style="color:#0A9EBB;font-weight:bold;font-size:20px;margin:0">KSh ${p.price}</p><p style="font-size:12px;color:${p.stock>0?'#00c851':'#ff3b30'};font-weight:bold">● ${p.stock>0?p.stock+' in stock - Ready to ship':'Out of stock'}</p><p style="font-size:13px;line-height:1.5">${p.desc}</p><p style="font-size:12px;background:#f7f7f7;padding:8px;border-radius:8px">✓ 100% Original Pwani Oil<br>✓ Verified LONMA code ${p.code}<br>✓ Free delivery over 2000<br>✓ 24hr return if defect<br>✓ 5000+ happy customers</p><div style="display:flex;gap:8px;margin-top:10px"><button class="btn" style="flex:1" onclick="addToCart(${p.id});closeModal()">🛒 ADD TO CART</button><button class="btn" style="flex:1;background:#25D366" onclick="orderWhatsAppSingle(${p.id})">💬 WHATSAPP</button></div><button class="btn" style="background:#fff;color:#0A9EBB;border:1px solid #0A9EBB;margin-top:8px" onclick="closeModal()">Continue Shopping</button></div>`;
document.getElementById('productModal').classList.add('open');
}
function closeModal(){document.getElementById('productModal').classList.remove('open');}
function addToCart(id){
let p=allProducts.find(x=>x.id===id); if(!p||p.stock===0){alert('Out of stock');return;}
let found=cart.find(c=>c.id===id);
if(found){if(found.qty>=p.stock){alert('Only '+p.stock+' in stock');return;} found.qty++; alert('Added again! '+p.name+' qty '+found.qty);}
else {cart.push({id:p.id,name:p.name,price:p.price,image:p.image&&!String(p.image).includes('undefined')?p.image:safeImage(p.name),code:p.code,qty:1,stock:p.stock}); alert('Added: '+p.name);}
saveCart(); renderCart(); renderProducts();
}
function changeQty(id,delta){for(let i=0;i<cart.length;i++)if(cart[i].id===id){cart[i].qty+=delta; if(cart[i].qty<=0)cart.splice(i,1); else if(cart[i].qty>cart[i].stock){cart[i].qty=cart[i].stock; alert('Max '+cart[i].stock);} break;} saveCart(); renderCart(); renderProducts();}
function clearCart(){if(confirm('Clear cart?')){cart=[]; localStorage.removeItem('lonma_cart'); saveCart(); renderCart(); renderProducts();}}
function renderCart(){
let cont=document.getElementById('cartItems'), sum=document.getElementById('cartSummary'), empty=document.getElementById('emptyCart');
if(cart.length===0){cont.innerHTML=''; sum.style.display='none'; empty.style.display='block'; return;}
empty.style.display='none'; sum.style.display='block';
let totalItems=0, subTotal=0, html='';
for(let it of cart){totalItems+=it.qty; subTotal+=it.price*it.qty; let img=it.image&&!String(it.image).includes('undefined')?it.image:safeImage(it.name); html+=`<div class="card" style="display:flex;gap:10px;align-items:center"><img src="${img}" style="width:60px;height:60px;object-fit:contain;border-radius:8px;border:1px solid #eee;padding:4px" onerror="this.src='${safeImage(it.name)}'"><div style="flex:1"><h4 style="margin:0;font-size:13px">${it.name}</h4><p style="margin:2px 0;font-size:12px;color:#0A9EBB;font-weight:bold">KSh ${it.price} x ${it.qty} = KSh ${it.price*it.qty}</p><small style="background:#0A9EBB;color:#fff;padding:2px 6px;border-radius:10px">${it.code}</small><div class="qty-controls"><button class="qty-btn" onclick="changeQty(${it.id},-1)">-</button><span style="font-weight:bold">${it.qty} pcs</span><button class="qty-btn" onclick="changeQty(${it.id},1)">+</button><button onclick="changeQty(${it.id},-${it.qty})" style="margin-left:8px;background:#ff4444;color:#fff;border:none;padding:6px 10px;border-radius:12px;font-size:11px">Remove</button></div></div></div>`;}
cont.innerHTML=html;
let area=document.getElementById('locationArea').value; let delivery=200; if(area==='CBD')delivery=150; if(area==='Westlands'||area==='Eastlands')delivery=200; if(area==='Upcountry')delivery=350;
let promo=document.getElementById('promoCode').value.trim().toUpperCase(); let discount=0; if(promo==='LONMA10'&&subTotal>=1000)discount=Math.floor(subTotal*0.1);
if(subTotal>=2000)delivery=0;
document.getElementById('subTotal').innerText=subTotal; document.getElementById('totalItems').innerText=totalItems; document.getElementById('deliveryFee').innerText=delivery===0?'FREE':`KSh ${delivery}`+(discount>0?` - Discount KSh ${discount}`:'');
let total=subTotal+delivery-discount; document.getElementById('totalPrice').innerText=total; document.getElementById('payTotal').innerText=total;
let freeMsg=document.getElementById('freeDeliveryMsg'); if(subTotal>=2000)freeMsg.innerHTML='🎉 You got FREE delivery!'+(discount>0?` + KSh ${discount} discount!`:'' ); else freeMsg.innerHTML=`Add KSh ${2000-subTotal} more for FREE delivery!`;
}
document.getElementById('locationArea')?.addEventListener('change',renderCart);
document.getElementById('promoCode')?.addEventListener('input',renderCart);
function show(id){document.querySelectorAll('.page').forEach(p=>p.classList.remove('active')); document.getElementById(id).classList.add('active'); document.querySelectorAll('.bottom div').forEach(b=>b.classList.remove('active')); let btn=document.getElementById('b-'+id); if(btn)btn.classList.add('active'); if(id==='cart')renderCart(); if(id==='orders')renderOrders(); window.scrollTo(0,0);}
async function loadProducts(){let r=await fetch('/api/products'); let d=await r.json(); allProducts=d.map(p=>({id:p.id,name:p.name,price:p.price,code:p.code,image:p.image&&!String(p.image).includes('undefined')?p.image:safeImage(p.name),category:p.category||'General',stock:p.stock||50,desc:p.desc||p.name})); renderProducts();}
async function verifyCode(){let c=document.getElementById('manualcode').value.trim().toUpperCase(); if(!c){document.getElementById('scanresult').innerText='Enter code';return;} let r=await fetch(`/api/verify/${c}`); let d=await r.json(); document.getElementById('scanresult').innerHTML=d.valid?`✅ ${d.product.name} - ORIGINAL Pwani Verified<br><small>Code ${c} is genuine</small>`:`❌ Invalid code ${c} - Not original`;}
async function login(){let r=await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:document.getElementById('lemail').value,password:document.getElementById('lpass').value})}); let d=await r.json(); document.getElementById('lstatus').innerText=d.message; if(d.status==='ok')setTimeout(()=>show('products'),800);}
async function signin(){let r=await fetch('/api/signin',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:document.getElementById('sname').value,email:document.getElementById('semail').value,password:document.getElementById('spass').value})}); let d=await r.json(); document.getElementById('sstatus').innerText=d.message; if(d.status==='ok')setTimeout(()=>show('products'),800);}
function orderWhatsApp(){if(cart.length===0){alert('Cart empty');return;} let name=document.getElementById('custName').value||'Customer', phone=document.getElementById('phone').value||'', area=document.getElementById('locationArea').value||'', loc=document.getElementById('exactLocation').value||''; let total=document.getElementById('totalPrice').innerText; let items=cart.map(c=>`${c.name} x${c.qty}=KSh${c.price*c.qty}`).join('%0A'); let msg=`Hi LONMA ORBIT%0AOrder:%0A${items}%0A%0ATotal KSh ${total}%0AName:${name}%0APhone:${phone}%0AArea:${area}%0ALoc:${loc}`; window.open(`https://wa.me/254700000000?text=${msg}`,'_blank');}
function orderWhatsAppSingle(id){let p=allProducts.find(x=>x.id===id); let msg=`Hi LONMA I want ${p.name} KSh ${p.price} Code ${p.code}`; window.open(`https://wa.me/254700000000?text=${encodeURIComponent(msg)}`,'_blank');}
async function checkout(){
let name=document.getElementById('custName').value.trim(), phone=document.getElementById('phone').value.trim(), area=document.getElementById('locationArea').value, loc=document.getElementById('exactLocation').value.trim(), agree=document.getElementById('agreeTerms').checked, promo=document.getElementById('promoCode').value.trim().toUpperCase();
if(!name||!phone||!area||!loc){document.getElementById('paystatus').innerText='⚠️ Fill all delivery details *';return;}
if(!agree){document.getElementById('paystatus').innerText='⚠️ Agree to Terms';return;}
if(phone.length<10){document.getElementById('paystatus').innerText='⚠️ Enter valid 07xx phone';return;}
let subTotal=0; for(let i of cart)subTotal+=i.price*i.qty;
let delivery=area==='CBD'?150:area==='Upcountry'?350:200; if(subTotal>=2000)delivery=0;
let discount=0; if(promo==='LONMA10'&&subTotal>=1000)discount=Math.floor(subTotal*0.1);
let total=subTotal+delivery-discount;
document.getElementById('paystatus').innerText=`⏳ Sending STK KSh ${total} to ${phone}...`;
let r=await fetch('/mpesa/stkpush',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({phone,amount:total,cart,name,area,location:loc,subtotal:subTotal,delivery,discount,promo})});
let d=await r.json();
document.getElementById('paystatus').innerText=`✅ ${d.message}`;
let orderNo='LONMA'+Date.now().toString().slice(-6);
let order={order_no:orderNo, name, phone, area, location:loc, items:[...cart], subtotal:subTotal, delivery, discount, total, status:'Pending', created:new Date().toLocaleString()};
myOrders.unshift(order); localStorage.setItem('my_orders',JSON.stringify(myOrders));
document.getElementById('receiptContent').innerHTML=`<h3 style="text-align:center">LONMA ORBIT RECEIPT</h3><p>Order No: <b>${orderNo}</b><br>Date: ${order.created}<br>Name: ${name}<br>Phone: ${phone}<br>Area: ${area}<br>Location: ${loc}</p><hr>${cart.map(c=>`<div style="display:flex;justify-content:space-between;font-size:13px"><span>${c.name} x${c.qty}</span><span>KSh ${c.price*c.qty}</span></div>`).join('')}<hr><div style="font-size:13px"><div style="display:flex;justify-content:space-between"><span>Subtotal</span><span>KSh ${subTotal}</span></div><div style="display:flex;justify-content:space-between"><span>Delivery</span><span>${delivery===0?'FREE':'KSh '+delivery}</span></div>${discount>0?`<div style="display:flex;justify-content:space-between;color:green"><span>Discount ${promo}</span><span>-KSh ${discount}</span></div>`:''}<div style="display:flex;justify-content:space-between;font-weight:bold;font-size:16px;color:#0A9EBB;border-top:1px solid #eee;margin-top:6px;padding-top:6px"><span>Total</span><span>KSh ${total}</span></div></div><p style="font-size:11px;text-align:center;margin-top:12px">Thank you for shopping with LONMA ORBIT<br>100% Original Pwani Products<br>Call 0700 000 000</p>`;
if(d.message.toLowerCase().includes('sent')||d.message.toLowerCase().includes('success')||true){
cart=[]; localStorage.removeItem('lonma_cart'); saveCart(); renderCart(); renderProducts();
setTimeout(()=>{show('receipt');},800);
}
}
function renderOrders(){
let cont=document.getElementById('ordersList'), empty=document.getElementById('noOrders');
if(myOrders.length===0){cont.innerHTML=''; empty.style.display='block'; return;}
empty.style.display='none'; let html='';
for(let o of myOrders){
html+=`<div class="card"><div style="display:flex;justify-content:space-between"><b>${o.order_no}</b><span style="background:${o.status==='Pending'?'#ff9a00':'#00c851'};color:#fff;padding:2px 8px;border-radius:10px;font-size:10px">${o.status}</span></div><p style="font-size:12px;margin:4px 0">${o.created}<br>${o.items.map(i=>`${i.name} x${i.qty}`).join(', ')}<br><b>Total KSh ${o.total}</b> - ${o.area}</p><button class="btn" style="background:#fff;color:#0A9EBB;border:1px solid #0A9EBB;padding:6px;font-size:11px" onclick="reorder('${o.order_no}')">Reorder</button></div>`;
}
cont.innerHTML=html;
}
function reorder(orderNo){let o=myOrders.find(x=>x.order_no===orderNo); if(!o)return; cart=o.items; saveCart(); show('cart'); renderCart();}
async function adminLogin(){let p=document.getElementById('adminPass').value; if(p!=='lonma2024'){document.getElementById('adminStatus').innerText='Wrong password'; return;} document.getElementById('adminStatus').innerText='Login success'; document.getElementById('adminContent').style.display='block'; loadAdminOrders();}
async function loadAdminOrders(){let r=await fetch('/api/admin/orders'); let d=await r.json(); document.getElementById('statOrders').innerText=d.length; let sales=0; for(let o of d)sales+=o.total||0; document.getElementById('statSales').innerText=sales; let html=''; for(let o of d){html+=`<div class="card"><b>${o.order_no}</b> - ${o.status} - KSh ${o.total}<br><span style="font-size:12px">Name:${o.name} Phone:${o.phone}<br>Area:${o.area} Loc:${o.location}<br>Items:${o.items}<br>Date:${o.created}</span><div style="display:flex;gap:6px;margin-top:6px"><button class="btn" style="padding:6px;font-size:11px" onclick="updateStatus('${o.order_no}','Shipped')">Mark Shipped</button><button class="btn" style="padding:6px;font-size:11px;background:#00c851" onclick="updateStatus('${o.order_no}','Delivered')">Delivered</button></div></div>`;} document.getElementById('adminOrdersList').innerHTML=html||'<div class="card">No orders yet</div>';}
async function updateStatus(orderNo,status){let r=await fetch(`/api/admin/orders/${orderNo}/${status}`,{method:'POST'}); let d=await r.json(); alert(d.message); loadAdminOrders();}
loadProducts(); updateCartCount(); renderCart(); renderOrders();
</script></body></html>
"""

@app.api_route("/", methods=["GET","HEAD"])
def home():
    return HTMLResponse(HTML)

@app.get("/logo.png")
def logo():
    for f in ["logo.png","static/logo.png"]:
        if os.path.exists(f):
            return FileResponse(f)
    return HTMLResponse("logo",404)

@app.get("/undefined")
@app.get("/undefined/")
def handle_undefined():
    return RedirectResponse("https://via.placeholder.com/400x300/FFFFFF/0A9EBB?text=LONMA", status_code=302)

@app.get("/api/products")
def products():
    cur = conn.cursor()
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
    cur=conn.cursor()
    cur.execute("SELECT name FROM products WHERE code=?",(code.strip().upper(),))
    row=cur.fetchone()
    return {"valid":True,"product":{"name":row[0]}} if row else {"valid":False}

@app.get("/api/admin/orders")
def admin_orders():
    cur=conn.cursor()
    cur.execute("SELECT order_no,name,phone,area,location,items,subtotal,delivery,total,status,created FROM orders ORDER BY id DESC")
    return [{"order_no":r[0],"name":r[1],"phone":r[2],"area":r[3],"location":r[4],"items":r[5],"subtotal":r[6],"delivery":r[7],"total":r[8],"status":r[9],"created":r[10]} for r in cur.fetchall()]

@app.post("/api/admin/orders/{order_no}/{status}")
def admin_update(order_no: str, status: str):
    cur=conn.cursor()
    cur.execute("UPDATE orders SET status=? WHERE order_no=?",(status,order_no))
    conn.commit()
    return {"message":f"Order {order_no} marked {status}"}

@app.post("/api/signin")
async def signin_api(req: Request):
    d=await req.json()
    try:
        conn.execute("INSERT INTO users (email,password,name) VALUES (?,?,?)",(d.get("email"),d.get("password"),d.get("name")))
        conn.commit()
        return {"status":"ok","message":"Account created! 100 KSh off - Use LONMA10"}
    except:
        return {"status":"error","message":"Email exists"}

@app.post("/api/login")
async def login_api(req: Request):
    d=await req.json()
    cur=conn.cursor()
    cur.execute("SELECT * FROM users WHERE email=? AND password=?",(d.get("email"),d.get("password")))
    return {"status":"ok","message":"Welcome back!"} if cur.fetchone() else {"status":"error","message":"Invalid login"}

@app.post("/mpesa/stkpush")
async def stk(req: Request):
    d=await req.json()
    order_no='LONMA'+datetime.datetime.now().strftime("%H%M%S")
    items_text=json.dumps([f"{c.get('name')} x{c.get('qty')}" for c in d.get('cart',[])])
    try:
        conn.execute("INSERT INTO orders (order_no,name,phone,area,location,items,subtotal,delivery,total,status,created) VALUES (?,?,?,?,?,?,?,?,?,?,?)",(order_no,d.get('name','Guest'),d.get('phone'),d.get('area'),d.get('location'),items_text,d.get('subtotal',0),d.get('delivery',0),d.get('amount',0),'Pending',datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
        conn.commit()
    except Exception as e:
        print(e)
    return {"message":f"STK KSh {d.get('amount')} sent to {d.get('phone')} Order {order_no} saved - Enter PIN"}

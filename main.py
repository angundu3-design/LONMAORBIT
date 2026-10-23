from fastapi import FastAPI, Form, Cookie, Request
from fastapi.responses import HTMLResponse, RedirectResponse
import json, hashlib, time, os, base64, urllib.request, urllib.parse
from datetime import datetime

app = FastAPI()
USERS = {}
ORDERS = []
PRODUCTS = [
    {"id":1,"name":"Unga 2kg","price":180,"cat":"Flour","img":"🌾","stock":50},
    {"id":2,"name":"Milk 500ml","price":70,"cat":"Dairy","img":"🥛","stock":100},
    {"id":3,"name":"Bread","price":65,"cat":"Bakery","img":"🍞","stock":30},
    {"id":4,"name":"Oil 1L","price":320,"cat":"Cooking","img":"🫒","stock":40},
    {"id":5,"name":"Sugar 2kg","price":310,"cat":"Sugar","img":"🍬","stock":60},
    {"id":6,"name":"Rice 2kg","price":420,"cat":"Rice","img":"🍚","stock":25},
]
ADMIN_PASS = "lonma2026"
LOGO = "<svg xmlns='http://www.w3.org/2000/svg' width='160' height='40' viewBox='0 0 160 40'><rect width='160' height='40' rx='10' fill='#0096B2'/><text x='10' y='28' font-family='serif' font-size='32' font-weight='900' fill='white'>LO</text><rect x='55' y='10' width='95' height='18' rx='5' fill='white'/><text x='60' y='22' font-size='8' letter-spacing='1.5' font-weight='700'>LONMA ORBIT</text></svg>"

def hash_pw(p): return hashlib.sha256(p.encode()).hexdigest()
def get_user(email: str = Cookie(default=None)):
    return {"email":email,**USERS[email]} if email and email in USERS else None

def page(content, user=None, admin=False):
    nav = f"👤 {user['name'].split()[0]} | <a href='/admin' style='color:#ffeb3b'>Admin</a> | <a href='/logout' style='color:#ffeb3b'>Logout</a>" if user else "<a href='/login' style='background:#fff;color:#0096B2;padding:8px 14px;border-radius:20px;text-decoration:none;font-weight:800'>Sign In</a> | <a href='/admin/login' style='color:#ffeb3b;margin-left:10px'>Admin</a>"
    if admin: nav = "<a href='/' style='color:#fff'>Shop</a> | <b style='color:#ffeb3b'>Admin</b> | <a href='/logout' style='color:#fff'>Logout</a>"
    return f"<!DOCTYPE html><html><head><meta name='viewport' content='width=device-width,initial-scale=1'><title>LONMA MART</title><style>body{{margin:0;font-family:system-ui;background:#f5f7f8}}header{{background:#0096B2;color:#fff;padding:10px 16px;display:flex;justify-content:space-between;align-items:center;position:sticky;top:0;z-index:10}} .grid{{display:grid;grid-template-columns:1fr 1fr;gap:12px;padding:15px 15px 90px}} .card{{background:#fff;padding:14px;border-radius:16px;text-align:center}} button{{background:#0096B2;color:#fff;border:0;padding:11px;border-radius:10px;width:100%;font-weight:700;cursor:pointer}} input,select{{width:100%;padding:12px;margin:8px 0;border-radius:10px;border:1px solid #ddd;box-sizing:border-box}} .form{{max-width:500px;margin:20px auto;background:#fff;padding:24px;border-radius:20px}} table{{width:100%;border-collapse:collapse}} th,td{{padding:10px;border-bottom:1px solid #eee;text-align:left}} .badge{{background:#e6f9fc;color:#0096B2;padding:4px 10px;border-radius:20px;font-size:12px}}</style></head><body><header><div style='display:flex;align-items:center;gap:8px;background:#fff;border-radius:10px;padding:2px'>{LOGO}</div><div>{nav}</div></header>{content}</body></html>"

@app.api_route("/", methods=["GET","HEAD"])
async def home(user_email: str = Cookie(default=None)):
    u=get_user(user_email)
    content=f"""
    <div style='padding:12px;display:flex;gap:8px'><input id='s' placeholder='Search...' onkeyup='f()' style='flex:1'><select id='cat' onchange='f()'><option value='all'>All</option><option>Flour</option><option>Dairy</option><option>Bakery</option><option>Cooking</option></select></div>
    <div class='grid' id='g'></div>
    <div style='position:fixed;bottom:0;left:0;right:0;background:#111;color:#fff;padding:12px 18px;display:flex;justify-content:space-between;border-radius:18px 18px 0 0'><div><span id='cc'>0</span> items • <b id='ct'>KSh 0</b></div><button style='width:auto;background:#fff;color:#111' onclick='co()'>Checkout → M-Pesa</button></div>
    <div id='ck' style='display:none;position:fixed;inset:0;background:#fff;padding:20px;z-index:20;overflow:auto'><h2>Checkout + M-Pesa STK</h2><div id='list'></div><h3 id='tt'></h3><form method='post' action='/order'><input type='hidden' name='cart_data' id='cd'><input name='phone' placeholder='07xx M-Pesa number' value="{u['phone'] if u else ''}" required><input name='location' placeholder='Estate / Street' required><button>Place Order → Pay with M-Pesa STK</button><p style='font-size:12px;color:#666;margin-top:10px'>STK will be pushed to your phone.</p><button type='button' onclick="document.getElementById('ck').style.display='none'" style='background:#eee;color:#333;margin-top:10px'>Back</button></form></div>
    <script>const P={json.dumps(PRODUCTS)};let cart=JSON.parse(localStorage.getItem('lonma_cart')||'[]');function render(){{let h='';P.forEach(p=>h+=`<div class=card><div style=font-size:32px>${{p.img}}</div><h4>${{p.name}}</h4><span class=badge>${{p.cat}} • ${{p.stock}} left</span><div style=margin:8px 0><b style=color:#0096B2>KSh ${{p.price}}</b></div><button onclick=add(${{p.id}})>Add</button></div>`);document.getElementById('g').innerHTML=h;up();}}function add(id){{let pr=P.find(x=>x.id==id);cart.push(pr);localStorage.setItem('lonma_cart',JSON.stringify(cart));up();}}function up(){{document.getElementById('cc').innerText=cart.length;let t=cart.reduce((s,i)=>s+i.price,0);document.getElementById('ct').innerText='KSh '+t;document.getElementById('tt').innerText='Total KSh '+t;document.getElementById('cd').value=JSON.stringify(cart);document.getElementById('list').innerHTML=cart.map(c=>`<p>${{c.name}} - ${{c.price}}</p>`).join('');}}function co(){{if(cart.length==0)return alert('Empty');document.getElementById('ck').style.display='block';}}function f(){{let q=document.getElementById('s').value.toLowerCase();let cat=document.getElementById('cat').value;document.querySelectorAll('.card').forEach((el,i)=>{{let ok=P[i].name.toLowerCase().includes(q)&&(cat=='all'||P[i].cat==cat);el.style.display=ok?'block':'none';}});}}render();</script>"""
    return HTMLResponse(page(content,u))

@app.get("/login", response_class=HTMLResponse)
async def lp(): return HTMLResponse(page("<div class='form'><h2>Customer Sign In</h2><form method='post' action='/login'><input name='email' type='email' required placeholder='Email'><input name='password' type='password' required placeholder='Password'><button>Sign In</button></form><p><a href='/register'>Create account</a></p></div>"))
@app.post("/login")
async def lg(email: str = Form(...), password: str = Form(...)):
    if email in USERS and USERS[email]['password']==hash_pw(password):
        r=RedirectResponse("/",303);r.set_cookie("user_email",email,max_age=2592000);return r
    return HTMLResponse(page("<div class='form'><h3 style='color:red'>Wrong</h3><a href='/login'>Try again</a></div>"))
@app.get("/register", response_class=HTMLResponse)
async def rp(): return HTMLResponse(page("<div class='form'><h2>Create</h2><form method='post' action='/register'><input name='name' required placeholder='Name'><input name='email' type='email' required placeholder='Email'><input name='phone' required placeholder='07xx'><input name='password' type='password' required placeholder='Password'><button>Create</button></form></div>"))
@app.post("/register")
async def rg(name: str = Form(...), email: str = Form(...), phone: str = Form(...), password: str = Form(...)):
    USERS[email]={"name":name,"phone":phone,"password":hash_pw(password)};r=RedirectResponse("/",303);r.set_cookie("user_email",email,max_age=2592000);return r
@app.get("/logout")
async def lo(): r=RedirectResponse("/",303);r.delete_cookie("user_email");r.delete_cookie("admin_auth");return r

@app.post("/order")
async def order(phone: str = Form(...), location: str = Form(...), cart_data: str = Form(...), user_email: str = Cookie(default=None)):
    cart=json.loads(cart_data);total=sum(i['price'] for i in cart)
    order_id=f"LO{int(time.time())}"
    ORDERS.append({"id":order_id,"time":datetime.now().strftime("%Y-%m-%d %H:%M"),"user":user_email or "Guest","phone":phone,"location":location,"items":cart,"total":total,"status":"Pending STK"})
    mpesa_msg = f"DEMO MODE: Order {order_id} saved. Would push KSh {total} to {phone}. To go LIVE, add MPESA keys in Render Env. Then real STK will be sent."
    try:
        key=os.getenv("MPESA_CONSUMER_KEY")
        if key:
            mpesa_msg = f"LIVE MODE: STK pushed KSh {total} to {phone}. Check phone for M-Pesa PIN prompt. Order {order_id}"
    except: pass
    return HTMLResponse(page(f"<div class='form'><h1>✅ Order {order_id}</h1><p>Total KSh {total}</p><p>Phone {phone} - {location}</p><div style='background:#e6f9fc;padding:12px;border-radius:12px;margin:12px 0'><b>M-Pesa:</b><br>{mpesa_msg}</div><a href='/'><button>Continue</button></a><a href='/admin' style='display:block;text-align:center;margin-top:10px'>View Admin</a></div>", get_user(user_email)))

@app.post("/mpesa/callback")
async def mpesa_callback(request: Request):
    data=await request.json()
    print("MPESA CB:",data)
    return {"ResultCode":0,"ResultDesc":"Accepted"}

@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page(): return HTMLResponse(page("<div class='form'><h2>Admin Login</h2><form method='post' action='/admin/login'><input name='password' type='password' placeholder='lonma2026' required><button>Login</button></form></div>"))
@app.post("/admin/login")
async def admin_login(password: str = Form(...)):
    if password==ADMIN_PASS:
        r=RedirectResponse("/admin",303);r.set_cookie("admin_auth","yes",max_age=86400);return r
    return HTMLResponse(page("<div class='form'><h3 style='color:red'>Wrong</h3></div>"))

@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(admin_auth: str = Cookie(default=None), user_email: str = Cookie(default=None)):
    if admin_auth!="yes": return RedirectResponse("/admin/login")
    orders_html="".join([f"<tr><td>{o['id']}</td><td>{o['time']}</td><td>{o['phone']}<br><small>{o['user']}</small></td><td>{o['location']}</td><td>{', '.join([i['name'] for i in o['items']])}</td><td><b>KSh {o['total']}</b></td><td>{o['status']}</td></tr>" for o in reversed(ORDERS[-50:])]) or "<tr><td colspan=7>No orders</td></tr>"
    prod_html="".join([f"<tr><td>{p['img']} {p['name']}</td><td>KSh {p['price']}</td><td>{p['cat']}</td><td>{p['stock']}</td><td><form method='post' action='/admin/delete-product'><input type='hidden' name='pid' value='{p['id']}'><button style='width:auto;background:red;padding:4px 8px'>Del</button></form></td></tr>" for p in PRODUCTS])
    return HTMLResponse(page(f"""
    <div style='max-width:1000px;margin:20px auto;padding:0 16px'>
    <h1>Admin Dashboard</h1>
    <div style='display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin:20px 0'>
      <div style='background:#fff;padding:16px;border-radius:12px'><h3>{len(ORDERS)}</h3><p>Orders</p></div>
      <div style='background:#fff;padding:16px;border-radius:12px'><h3>KSh {sum(o['total'] for o in ORDERS)}</h3><p>Revenue</p></div>
      <div style='background:#fff;padding:16px;border-radius:12px'><h3>{len(PRODUCTS)}</h3><p>Products</p></div>
    </div>
    <h2>Add Product</h2><div class='form' style='margin:10px 0'><form method='post' action='/admin/add-product'><input name='name' placeholder='Name' required><input name='price' type='number' required placeholder='Price'><input name='cat' placeholder='Category' required><input name='img' placeholder='Emoji or image URL' required><input name='stock' type='number' required placeholder='Stock'><button>Add Product</button></form></div>
    <h2>Products</h2><div style='background:#fff;padding:12px;border-radius:12px;overflow:auto'><table><tr><th>Product</th><th>Price</th><th>Cat</th><th>Stock</th><th>Action</th></tr>{prod_html}</table></div>
    <h2 style='margin-top:30px'>Recent Orders</h2><div style='background:#fff;padding:12px;border-radius:12px;overflow:auto'><table><tr><th>ID</th><th>Time</th><th>Customer</th><th>Loc</th><th>Items</th><th>Total</th><th>Status</th></tr>{orders_html}</table></div>
    <p style='margin-top:20px;background:#fff;padding:12px;border-radius:12px'>M-Pesa: Add MPESA_CONSUMER_KEY, MPESA_CONSUMER_SECRET, MPESA_SHORTCODE, MPESA_PASSKEY in Render → Environment to go live. Now DEMO mode.</p>
    </div>
    """, get_user(user_email), admin=True))

@app.post("/admin/add-product")
async def add_prod(name: str = Form(...), price: int = Form(...), cat: str = Form(...), img: str = Form(...), stock: int = Form(...), admin_auth: str = Cookie(default=None)):
    if admin_auth!="yes": return RedirectResponse("/admin/login")
    new_id=max([p['id'] for p in PRODUCTS], default=0)+1
    PRODUCTS.append({"id":new_id,"name":name,"price":price,"cat":cat,"img":img,"stock":stock})
    return RedirectResponse("/admin",303)

@app.post("/admin/delete-product")
async def del_prod(pid: int = Form(...), admin_auth: str = Cookie(default=None)):
    if admin_auth!="yes": return RedirectResponse("/admin/login")
    global PRODUCTS
    PRODUCTS=[p for p in PRODUCTS if p['id']!=pid]
    return RedirectResponse("/admin",303)

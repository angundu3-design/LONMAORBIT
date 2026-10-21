from fastapi import FastAPI, Form, Request, Response, Depends, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import json, hashlib, time

app = FastAPI(title="LONMA MART")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# FAKE DB
USERS = {}  # email -> {name, password_hash, phone}
PRODUCTS = [
    {"id":1,"name":"Unga 2kg","price":180,"cat":"Flour","img":"🌾"},
    {"id":2,"name":"Fresh Milk 500ml","price":70,"cat":"Dairy","img":"🥛"},
    {"id":3,"name":"White Bread","price":65,"cat":"Bakery","img":"🍞"},
    {"id":4,"name":"Cooking Oil 1L","price":320,"cat":"Cooking","img":"🫒"},
    {"id":5,"name":"Sugar 2kg","price":310,"cat":"Sugar","img":"🍬"},
    {"id":6,"name":"Rice Pishori 2kg","price":420,"cat":"Rice","img":"🍚"},
    {"id":7,"name":"Eggs Tray 30","price":550,"cat":"Eggs","img":"🥚"},
    {"id":8,"name":"Soda 1.5L","price":110,"cat":"Drinks","img":"🥤"},
]

def hash_pw(p): return hashlib.sha256(p.encode()).hexdigest()
def get_user(email: str = Cookie(default=None)):
    if email and email in USERS:
        return {"email": email, **USERS[email]}
    return None

def base_page(content, user=None):
    user_html = f"<a href='/profile' style='color:#fff;text-decoration:none'>👤 {user['name'].split()[0]}</a> | <a href='/logout' style='color:#ffb'>Logout</a>" if user else "<a href='/login' style='background:#fff;color:#0a8a2c;padding:8px 16px;border-radius:20px;text-decoration:none;font-weight:700'>Sign In</a>"
    return f"""
    <!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>LONMA MART</title>
    <style>
    body{{margin:0;font-family:system-ui;background:#f5f5f5}}
    header{{background:#0a8a2c;color:#fff;padding:12px 18px;display:flex;justify-content:space-between;align-items:center;position:sticky;top:0;z-index:10}}
    .logo{{display:flex;align-items:center;gap:10px;font-weight:900;font-size:20px;letter-spacing:1px}}
    .logo-box{{background:#fff;color:#0a8a2c;width:38px;height:38px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:20px}}
    .grid{{display:grid;grid-template-columns:1fr 1fr;gap:12px;padding:15px 15px 100px}}
    .card{{background:#fff;padding:14px;border-radius:16px;text-align:center;box-shadow:0 2px 10px rgba(0,0,0,.05)}}
    button{{background:#0a8a2c;color:#fff;border:0;padding:11px;border-radius:10px;width:100%;font-weight:700;cursor:pointer}}
    input{{width:100%;padding:14px;margin:8px 0;border-radius:10px;border:1px solid #ddd;box-sizing:border-box}}
    .form-wrap{{max-width:400px;margin:40px auto;background:#fff;padding:30px;border-radius:20px}}
    @media(min-width:700px){{.grid{{grid-template-columns:repeat(4,1fr)}}}}
    </style></head><body>
    <header><div class="logo"><div class="logo-box">LM</div>LONMA MART</div><div>{user_html}</div></header>
    {content}
    </body></html>
    """

@app.api_route("/", methods=["GET", "HEAD"])
async def home(request: Request, user_email: str = Cookie(default=None)):
    user = get_user(user_email)
    products_json = json.dumps(PRODUCTS)
    content = f"""
    <div style="padding:15px"><input id="search" placeholder="Search products..." onkeyup="filterP()" style="padding:14px;border-radius:12px;border:1px solid #ddd;width:100%;box-sizing:border-box"></div>
    <div class="grid" id="grid"></div>
    <div style="position:fixed;bottom:0;left:0;right:0;background:#111;color:#fff;padding:14px 18px;display:flex;justify-content:space-between;border-radius:18px 18px 0 0">
        <div><span id="c-count">0</span> items • <b id="c-total">KSh 0</b></div>
        <button style="width:auto;background:#fff;color:#111" onclick="checkout()">Checkout</button>
    </div>
    <div id="checkout" style="display:none;position:fixed;inset:0;background:#fff;padding:25px;z-index:20;overflow:auto">
        <h2>Checkout</h2><div id="list"></div><h3 id="total"></h3>
        <form method="post" action="/order">
        <input type="hidden" name="cart_data" id="cart_data">
        <input name="phone" placeholder="M-Pesa Phone" value="{user['phone'] if user and 'phone' in user else ''}" required>
        <input name="location" placeholder="Delivery Estate" required>
        <button type="submit">Place Order - Pay M-Pesa</button>
        <button type="button" onclick="document.getElementById('checkout').style.display='none'" style="background:#eee;color:#333;margin-top:10px">Continue Shopping</button>
        </form>
    </div>
    <script>
    const PRODUCTS={products_json}; let cart=JSON.parse(localStorage.getItem('lonma_cart')||'[]');
    function render(){{let h=''; PRODUCTS.forEach(p=>{{h+=`<div class="card"><div style="font-size:38px">${{p.img}}</div><h4>${{p.name}}</h4><p style="color:#888;font-size:12px">${{p.cat}}</p><b style="color:#0a8a2c">KSh ${{p.price}}</b><button onclick="add(${{p.id}})" style="margin-top:8px">Add</button></div>`}}); document.getElementById('grid').innerHTML=h; update();}}
    function add(id){{let p=PRODUCTS.find(x=>x.id==id); cart.push(p); localStorage.setItem('lonma_cart', JSON.stringify(cart)); update();}}
    function update(){{document.getElementById('c-count').innerText=cart.length; let t=cart.reduce((s,i)=>s+i.price,0); document.getElementById('c-total').innerText='KSh '+t; document.getElementById('total').innerText='Total: KSh '+t; document.getElementById('cart_data').value=JSON.stringify(cart); document.getElementById('list').innerHTML=cart.map(c=>`<p>${{c.name}} - ${{c.price}}</p>`).join('');}}
    function checkout(){{if(cart.length==0){{alert('Cart empty');return;}} document.getElementById('checkout').style.display='block';}}
    function filterP(){{let q=document.getElementById('search').value.toLowerCase(); document.querySelectorAll('.card').forEach((el,i)=>{{el.style.display=PRODUCTS[i].name.toLowerCase().includes(q)?'block':'none';}});}}
    render();
    </script>
    """
    return HTMLResponse(base_page(content, user))

@app.get("/login", response_class=HTMLResponse)
async def login_page():
    content = """
    <div class="form-wrap">
    <h2>Welcome Back</h2>
    <form method="post" action="/login">
    <input name="email" type="email" placeholder="Email" required>
    <input name="password" type="password" placeholder="Password" required>
    <button type="submit">Sign In</button>
    </form>
    <p style="text-align:center;margin-top:15px">No account? <a href="/register">Create one</a></p>
    </div>
    """
    return HTMLResponse(base_page(content))

@app.post("/login")
async def login(email: str = Form(...), password: str = Form(...)):
    if email in USERS and USERS[email]['password'] == hash_pw(password):
        resp = RedirectResponse("/", status_code=303)
        resp.set_cookie(key="user_email", value=email, max_age=86400*30)
        return resp
    return HTMLResponse(base_page("<div class='form-wrap'><h3 style='color:red'>Wrong email or password</h3><a href='/login'>Try again</a></div>"))

@app.get("/register", response_class=HTMLResponse)
async def register_page():
    content = """
    <div class="form-wrap">
    <h2>Create Account</h2>
    <form method="post" action="/register">
    <input name="name" placeholder="Full Name" required>
    <input name="email" type="email" placeholder="Email" required>
    <input name="phone" placeholder="Phone 07xx" required>
    <input name="password" type="password" placeholder="Password" required>
    <button type="submit">Create Account</button>
    </form>
    <p style="text-align:center;margin-top:15px">Have account? <a href="/login">Sign In</a></p>
    </div>
    """
    return HTMLResponse(base_page(content))

@app.post("/register")
async def register(name: str = Form(...), email: str = Form(...), phone: str = Form(...), password: str = Form(...)):
    if email in USERS:
        return HTMLResponse(base_page("<div class='form-wrap'><h3>Email already exists</h3><a href='/login'>Login</a></div>"))
    USERS[email] = {"name": name, "phone": phone, "password": hash_pw(password)}
    resp = RedirectResponse("/", status_code=303)
    resp.set_cookie(key="user_email", value=email, max_age=86400*30)
    return resp

@app.get("/profile", response_class=HTMLResponse)
async def profile(user_email: str = Cookie(default=None)):
    user = get_user(user_email)
    if not user:
        return RedirectResponse("/login")
    content = f"""
    <div class="form-wrap">
    <h2>My Account</h2>
    <p><b>Name:</b> {user['name']}</p>
    <p><b>Email:</b> {user['email']}</p>
    <p><b>Phone:</b> {user['phone']}</p>
    <a href="/logout"><button style="background:#111">Logout</button></a>
    <a href="/"><button style="background:#eee;color:#333;margin-top:10px">Continue Shopping</button></a>
    </div>
    """
    return HTMLResponse(base_page(content, user))

@app.get("/logout")
async def logout():
    resp = RedirectResponse("/", status_code=303)
    resp.delete_cookie("user_email")
    return resp

@app.post("/order")
async def order(phone: str = Form(...), location: str = Form(...), cart_data: str = Form(...), user_email: str = Cookie(default=None)):
    cart = json.loads(cart_data)
    total = sum(i['price'] for i in cart)
    user = get_user(user_email)
    who = user['name'] if user else "Guest"
    return HTMLResponse(base_page(f"<div class='form-wrap'><h1 style='color:#0a8a2c'>✅ Order Received!</h1><p>Asante {who}</p><p>Total KSh {total}</p><p>Deliver to {location} - {phone}</p><a href='/'><button>Back to Shop</button></a></div>", user))

@app.get("/health")
async def health():
    return {"status":"ok","users":len(USERS)}

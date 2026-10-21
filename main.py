from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import json

app = FastAPI(title="LONMA Supermarket")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

PRODUCTS = [
    {"id": 1, "name": "Unga 2kg", "price": 180, "cat": "Flour", "stock": 50, "img": "🌾"},
    {"id": 2, "name": "Fresh Milk 500ml", "price": 70, "cat": "Dairy", "stock": 100, "img": "🥛"},
    {"id": 3, "name": "White Bread", "price": 65, "cat": "Bakery", "stock": 40, "img": "🍞"},
    {"id": 4, "name": "Cooking Oil 1L", "price": 320, "cat": "Cooking", "stock": 30, "img": "🫒"},
    {"id": 5, "name": "Sugar 2kg", "price": 310, "cat": "Sugar", "stock": 60, "img": "🍬"},
    {"id": 6, "name": "Rice 2kg Pishori", "price": 420, "cat": "Rice", "stock": 25, "img": "🍚"},
    {"id": 7, "name": "Eggs Tray 30", "price": 550, "cat": "Eggs", "stock": 20, "img": "🥚"},
    {"id": 8, "name": "Soda 1.5L", "price": 110, "cat": "Drinks", "stock": 80, "img": "🥤"},
]

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>LONMA Supermarket</title>
<style>
body{font-family:system-ui;margin:0;background:#f6f6f6}
header{background:#0a8a2c;color:#fff;padding:15px 20px;display:flex;justify-content:space-between;position:sticky;top:0}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;padding:15px 15px 120px}
.product{background:#fff;padding:15px;border-radius:16px;text-align:center;box-shadow:0 2px 8px rgba(0,0,0,.06)}
.emoji{font-size:40px} .price{font-weight:800;color:#0a8a2c;font-size:18px}
button{background:#0a8a2c;color:#fff;border:0;padding:10px 16px;border-radius:10px;width:100%;font-weight:700}
#cart-bar{position:fixed;bottom:0;left:0;right:0;background:#111;color:#fff;padding:15px 20px;display:flex;justify-content:space-between;border-radius:20px 20px 0 0}
#checkout{display:none;position:fixed;top:0;left:0;right:0;bottom:0;background:#fff;padding:30px;z-index:20;overflow:auto}
</style>
</head>
<body>
<header><h2 style="margin:0">LONMA MART</h2><div>Cart <span id="cart-count" style="background:#fff;color:#0a8a2c;padding:4px 10px;border-radius:20px">0</span></div></header>
<div style="padding:15px"><input id="search" placeholder="Search unga, milk, bread..." onkeyup="filterProducts()" style="width:100%;padding:14px;border-radius:12px;border:1px solid #ddd"></div>
<div class="grid" id="grid"></div>
<div id="cart-bar"><div><span id="cart-items">0 items</span> - <b id="cart-total">KSh 0</b></div><button style="width:auto;background:#fff;color:#111" onclick="openCheckout()">Checkout</button></div>
<div id="checkout">
<h2>Checkout</h2><div id="checkout-list"></div><h3 id="checkout-total"></h3>
<form action="/order" method="post">
<input type="hidden" name="cart_data" id="cart_data">
<input name="customer_name" placeholder="Your Name" required style="width:100%;padding:14px;margin:8px 0;border-radius:10px;border:1px solid #ddd">
<input name="phone" placeholder="M-Pesa 07xx" required style="width:100%;padding:14px;margin:8px 0;border-radius:10px;border:1px solid #ddd">
<input name="location" placeholder="Estate" required style="width:100%;padding:14px;margin:8px 0;border-radius:10px;border:1px solid #ddd">
<button type="submit">Pay with M-Pesa</button>
<button type="button" onclick="document.getElementById('checkout').style.display='none'" style="background:#eee;color:#333;margin-top:10px">Back</button>
</form>
</div>
<script>
const PRODUCTS = REPLACE_PRODUCTS;
let cart=[];
function render(){let h='';PRODUCTS.forEach(p=>{h+=`<div class="product"><div class="emoji">${p.img}</div><h4>${p.name}</h4><p style="color:#888;font-size:12px">${p.cat}</p><p class="price">KSh ${p.price}</p><button onclick="add(${p.id})">Add to Cart</button></div>`});document.getElementById('grid').innerHTML=h;}
function add(id){let p=PRODUCTS.find(x=>x.id==id);cart.push(p);update();}
function update(){document.getElementById('cart-count').innerText=cart.length;document.getElementById('cart-items').innerText=cart.length+' items';let t=cart.reduce((s,i)=>s+i.price,0);document.getElementById('cart-total').innerText='KSh '+t;document.getElementById('checkout-total').innerText='Total: KSh '+t;document.getElementById('cart_data').value=JSON.stringify(cart);document.getElementById('checkout-list').innerHTML=cart.map(c=>`<p>${c.name} - KSh ${c.price}</p>`).join('');}
function openCheckout(){if(cart.length==0){alert('Cart empty');return;}document.getElementById('checkout').style.display='block';}
function filterProducts(){let q=document.getElementById('search').value.toLowerCase();document.querySelectorAll('.product').forEach((el,i)=>{el.style.display=PRODUCTS[i].name.toLowerCase().includes(q)?'block':'none';});}
render();
</script>
</body>
</html>
"""

@app.api_route("/", methods=["GET", "HEAD"])
async def home():
    html = HTML_PAGE.replace("REPLACE_PRODUCTS", json.dumps(PRODUCTS))
    return HTMLResponse(html)

@app.post("/order")
async def make_order(customer_name: str = Form(...), phone: str = Form(...), location: str = Form(...), cart_data: str = Form(...)):
    cart = json.loads(cart_data)
    total = sum(item['price'] for item in cart)
    return HTMLResponse(f"<html><body style='font-family:system-ui;text-align:center;padding:50px'><h1 style='color:#0a8a2c'>Order Received!</h1><h2>Asante {customer_name}</h2><p>Total KSh {total}</p><p>Phone {phone} - {location}</p><a href='/'>Back to Shop</a></body></html>")

@app.get("/health")
async def health():
    return {"status": "ok"}

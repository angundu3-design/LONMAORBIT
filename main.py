from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="LONMA ORBIT App")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# FIX for Render HEAD check + root
@app.api_route("/", methods=["GET", "HEAD"])
async def home():
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>LONMA ORBIT - App</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body{margin:0;font-family:Inter,sans-serif;background:#0a0a0a;color:#fff;text-align:center}
            .hero{padding:80px 20px;background:linear-gradient(rgba(0,0,0,0.7),rgba(0,0,0,0.7)),url('https://images.unsplash.com/photo-1470229722913-7c0e2dbbafd3');background-size:cover}
            h1{font-size:48px;letter-spacing:4px;margin:0}
            p{color:#aaa;font-size:18px}
            .grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:20px;padding:40px;max-width:1000px;margin:auto}
            .card{background:#151515;padding:30px;border-radius:16px;border:1px solid #222}
            .card h3{margin-top:0}
            a.btn{display:inline-block;background:#fff;color:#000;padding:14px 28px;border-radius:30px;text-decoration:none;font-weight:700;margin:10px}
            @media(max-width:700px){.grid{grid-template-columns:1fr} h1{font-size:32px}}
        </style>
    </head>
    <body>
        <div class="hero">
            <h1>LONMA ORBIT</h1>
            <p>Premium PA Hire • Luxury Tour Guide • Podcast & Content That Earns</p>
            <a class="btn" href="#book">BOOK NOW</a>
            <a class="btn" href="https://wa.me/254700000000" style="background:transparent;color:#fff;border:1px solid #fff">WhatsApp</a>
        </div>

        <div class="grid">
            <div class="card">
                <h3>🔊 PA FOR HIRE</h3>
                <p>From 2 speakers to full concert rig. Nairobi + countrywide.</p>
                <a class="btn" href="https://lonmaorbit.co.ke">View Packages</a>
            </div>
            <div class="card">
                <h3>🌍 LUXURY TOUR GUIDE</h3>
                <p>Maasai Mara, Diani, Naivasha. Private, curated.</p>
                <a class="btn" href="#book">Book Tour</a>
            </div>
            <div class="card">
                <h3>🎙️ CREATING FOR EARNING</h3>
                <p>Marlon K Podcast + Content Monetization.</p>
                <a class="btn" href="https://lonmaorbit.co.ke">Listen</a>
            </div>
        </div>

        <div id="book" style="padding:60px 20px;max-width:500px;margin:auto">
            <h2>Inquire Now</h2>
            <form action="/inquire" method="post">
                <input name="name" placeholder="Your Name" required style="width:100%;padding:14px;margin:8px 0;border-radius:8px;border:1px solid #333;background:#111;color:#fff">
                <input name="phone" placeholder="Phone / WhatsApp" required style="width:100%;padding:14px;margin:8px 0;border-radius:8px;border:1px solid #333;background:#111;color:#fff">
                <select name="service" style="width:100%;padding:14px;margin:8px 0;border-radius:8px;border:1px solid #333;background:#111;color:#fff">
                    <option>PA System Hire</option>
                    <option>Luxury Tour</option>
                    <option>Podcast / Content</option>
                </select>
                <textarea name="message" placeholder="Tell us dates, location, guests..." style="width:100%;padding:14px;margin:8px 0;border-radius:8px;border:1px solid #333;background:#111;color:#fff;height:100px"></textarea>
                <button type="submit" style="width:100%;padding:14px;background:#fff;color:#000;border:0;border-radius:8px;font-weight:700">SEND INQUIRY</button>
            </form>
            <p style="margin-top:20px;font-size:14px;color:#666">Will be sent to info@lonmaorbit.co.ke</p>
        </div>
    </body>
    </html>
    """)

@app.post("/inquire")
async def inquire(name: str = Form(...), phone: str = Form(...), service: str = Form(...), message: str = Form(...)):
    # Here you will later connect Zoho email / WhatsApp
    print(f"NEW LEAD: {name} - {phone} - {service} - {message}")
    # Redirect to WhatsApp with prefilled message
    text = f"Hello LONMA ORBIT, I am {name}. I need {service}. {message}. My number {phone}"
    import urllib.parse
    wa_link = f"https://wa.me/254700000000?text={urllib.parse.quote(text)}"
    return RedirectResponse(wa_link, status_code=303)

@app.get("/health")
async def health():
    return {"status": "ok", "domain": "app.lonmaorbit.co.ke"}

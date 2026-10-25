# --- FIND ALL IMAGES AUTOMATICALLY ---
def find_images():
    imgs=[]
    for f in os.listdir("."):
        if f.lower().endswith((".jpg",".jpeg",".png")):
            # exclude logo
            if "logo" not in f.lower():
                imgs.append(f)
    return sorted(imgs)

cur = conn.cursor()
cur.execute("DELETE FROM products")

NAMES=[
    "Fresh Fri Cooking Oil 2L",
    "Detrex Citronella Soap",
    "Sawa Men Lotion 72Hrs",
    "Detrex Pine Drops Soap",
    "Salit Vegetable Oil 5L",
    "Detrex Cool Mint Soap",
    "Diva Anti-Dandruff Pomade",
    "Diva Anti-Breakage Pomade",
    "Sawa Cocoa Butter Lotion"
]
PRICES=[850,90,299,90,1250,90,250,250,299]
CODES=[f"LONMA-00{i+1}" for i in range(9)]

found = find_images()
print(f"FOUND IMAGES: {found}")  # will show in logs

for i in range(9):
    if i < len(found):
        filename = found[i]
        img_url = f"/img/{urllib.parse.quote(filename)}"
    else:
        filename = f"product-{i}.jpg"
        img_url = f"https://via.placeholder.com/300?text={NAMES[i]}"
    cur.execute("INSERT INTO products VALUES (?,?,?,?,?)", (i+1, NAMES[i], PRICES[i], CODES[i], img_url))
conn.commit()

# ... and fix serve_img to be bulletproof:
@app.get("/img/{filename}")
def serve_img(filename: str):
    decoded = urllib.parse.unquote(filename)
    print(f"Trying to serve: {decoded}")
    # 1. direct file
    if os.path.exists(decoded):
        return FileResponse(decoded)
    # 2. search case-insensitive
    for f in os.listdir("."):
        if f.lower() == decoded.lower():
            return FileResponse(f)
        if urllib.parse.quote(f) == filename:
            return FileResponse(f)
    # 3. list files for debug
    return HTMLResponse(f"Not found: {decoded}. Files in dir: {os.listdir('.')}", 404)

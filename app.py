import os
import base64
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# ==========================================
# ⚙️ პარამეტრები (შევსებულია შენი მონაცემებით)
# ==========================================
GEMINI_API_KEY = "AIzaSyDCSi3_wpTnBwJxYWvJeKiSreAVf8zre-w" 
FIREBASE_DB_URL = "https://separa-smart-bin-default-rtdb.europe-west1.firebasedatabase.app"
# ==========================================

@app.route('/upload', methods=['POST'])
def upload_image():
    # ვამოწმებთ, მოყვა თუ არა მოთხოვნას სურათი
    if 'image' not in request.files:
        return jsonify({"error": "სურათი არ მოიძებნა"}), 400
    
    image_file = request.files['image']
    base64_image = base64.b64encode(image_file.read()).decode('utf-8')

    print("🧠 ეკო ფიქრობს (Black Board Mode)...")

    # ვაგზავნით მონაცემებს Gemini API-სთან
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key={GEMINI_API_KEY}"
    headers = {'Content-Type': 'application/json'}
    
    prompt = """
    The camera is pointing at a BLACK sorting board.
    
    1. CRITICAL: Check if the surface is EMPTY.
       - If you see MOSTLY the BLACK background/surface and NO distinct object, return 'Empty'.
       - Ignore dust, scratches, glare, or light reflections on the black board.
       
    2. If there IS a distinct object, classify it:
       - 'Plastic' (Bottles, cups, transparent items)
       - 'Paper' (Cardboard, white paper, tissues)
       - 'Metal' (Cans, foil, shiny metallic items)
       - 'Unknown' (Everything else)
       
    Return ONLY the category word.
    """
    
    payload = {
        "contents": [{"parts": [{"text": prompt}, {"inline_data": {"mime_type": "image/jpeg", "data": base64_image}}]}]
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            # ვასუფთავებთ პასუხს зайდმეტი წერტილებისგან
            category = response.json()['candidates'][0]['content']['parts'][0]['text'].strip().replace(".", "")
        else:
            category = "Error"
            print(f"API Error: {response.status_code}")
    except Exception as e:
        category = "Error"
        print(f"Connection Error: {e}")

    # თუ ნაგავი ვიპოვეთ, ვწერთ Firebase-ში
    if category not in ["Empty", "Error", "mt"]:
        firebase_url = f"{FIREBASE_DB_URL}/urna/status.json"
        try:
            requests.put(firebase_url, json=category)
            print(f"✅ Firebase-ში ჩაიწერა: {category}")
        except Exception as e:
            print(f"⚠️ Firebase Error: {e}")
    else:
        print(f"--- {category} (არაფერს ვწერთ ბაზაში, ველოდებით...)")

    return jsonify({"status": "success", "category": category})

# ეს დაგვეხმარება სერვერის მუშაობის შემოწმებაში ბრაუზერიდან
@app.route('/', methods=['GET'])
def home():
    return "🚀 Separa Smart Bin Server is Running perfectly!"

if __name__ == '__main__':
    # Railway ავტომატურად ანიჭებს PORT ცვლადს 8080-ს ან სხვას
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
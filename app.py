from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
from flask_cors import CORS
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from datetime import datetime as dt, timedelta
import certifi

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "asdfpoiu_321") 
CORS(app)

ACCESS_PASSWORD = os.getenv("ACCESS_PASSWORD")
MONGO_URI = os.getenv("MONGO_URI")

try:
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
    db = client["ServiceApp"]
    collection = db["locations"]
    print("Conectado ao MongoDB!")
except Exception as e:
    print(f"Erro no banco: {e}")

# Login HTML
LOGIN_HTML = '''
<div style="text-align:center; margin-top:100px; font-family: sans-serif;">
    <h2>howdy doody!</h2>
    <form method="POST">
        <input type="password" name="pass" placeholder="Pass" required style="padding:10px; border-radius:5px; border:1px solid #ccc;">
        <button type="submit" style="padding:10px 20px; cursor:pointer; background:#222; color:#fff; border:none; border-radius:5px;">Sign In</button>
    </form>
    {% if erro %}<p style="color:red;">{{ erro }}</p>{% endif %}
</div>
'''

# HTML do Dashboard (Com coluna de Imagem)
DASHBOARD_HTML = '''
<div style="font-family: sans-serif; padding: 20px;">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <h2>history</h2>
        <div>
            <a href="https://drive.google.com/file/d/1vrcjqRRqglYPHr85eKtEfy5dcY2fyrPI/view?usp=sharing" target="_blank" style="margin-right:20px; text-decoration:none;">howdy</a>
            <a href="/logout" style="color:red; text-decoration:none; font-weight:bold;">Exit</a>
        </div>
    </div>
    <hr>
    <table border="1" style="width:100%; text-align:left; border-collapse: collapse; margin-top:20px;">
        <tr style="background:#333; color:#fff;">
            <th style="padding:12px;">Device</th>
            <th style="padding:12px;">Data / time</th>
            <th style="padding:12px;">Photo</th>
            <th style="padding:12px;">Coordinates</th>
            <th style="padding:12px;">Map</th>
        </tr>
        {% for loc in dados %}
        <tr style="border-bottom: 1px solid #ddd;">
            <td style="padding:10px;"><strong>{{ loc.dispositivo }}</strong><br><small>{{ loc.ip }}</small></td>
            <td style="padding:10px;">{{ loc.timestamp }}</td>
            <td style="padding:10px;">
                {% if loc.image %}
                    <img src="data:image/jpeg;base64,{{ loc.image }}" style="width:100px; border-radius:5px; cursor:pointer;" onclick="window.open(this.src)">
                {% else %}
                    <span style="color:#ccc;">No photo</span>
                {% endif %}
            </td>
            <td style="padding:10px;">{{ loc.latitude }}, {{ loc.longitude }}</td>
            <td style="padding:10px;">
                <a href="https://www.google.com/maps?q={{ loc.latitude }},{{ loc.longitude }}" target="_blank" style="color:#007bff; text-decoration:none; font-weight:bold;">
                    📍 Open Maps
                </a>
            </td>
        </tr>
        {% endfor %}
    </table>
</div>
'''

@app.route('/')
def home():
    if 'logado' in session:
        dados = list(collection.find().sort("timestamp", -1).limit(100))
        return render_template_string(DASHBOARD_HTML, dados=dados)
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    erro = None
    if request.method == 'POST':
        if request.form['pass'] == ACCESS_PASSWORD:
            session['logado'] = True
            return redirect(url_for('home'))
        erro = "Invalid pass, assitch!"
    return render_template_string(LOGIN_HTML, erro=erro)

@app.route('/logout')
def logout():
    session.pop('logado', None)
    return redirect(url_for('login'))

@app.route('/save', methods=['POST'])
def save():
    try:
        data = request.json or {}
        ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0]
        
        dispositivo = data.get("device", "Unknown")
        
        # Novo: Captura a imagem em Base64 enviada pelo Android
        image_b64 = data.get("image", "")

        record = {
            "dispositivo": dispositivo,
            "ip": ip,
            "timestamp": (dt.utcnow() - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S"),
            "latitude": data.get("latitude"),
            "longitude": data.get("longitude"),
            "image": image_b64  # Salva a string da imagem no MongoDB
        }

        if record["latitude"] and record["longitude"]:
            collection.insert_one(record)
            return jsonify({"status": "ok"}), 201
        
        return jsonify({"status": "error", "message": "missing location data"}), 400
    except Exception as e:
        print(f"Erro ao salvar: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

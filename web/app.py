"""
İtalya Turistik Vize — Web Arayüzü
=====================================
Çalıştır:
    cd C:\\Users\\ASUS\\Desktop\\italya-turistik
    PYTHONUTF8=1 py web/app.py
Ardından: http://127.0.0.1:5000
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask, render_template, request, jsonify
from engine.document_engine import get_document_list, MESLEK_GRUPLARI, KONAKLAMA_TURLERI, ULASIM_ARACLARI, BASVURU_BOLGELERI
from engine.rule_checker import tam_kontrol

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html",
        meslek_gruplari=MESLEK_GRUPLARI,
        konaklama_turleri=KONAKLAMA_TURLERI,
        ulasim_araclari=ULASIM_ARACLARI,
        basvuru_bolgeleri=BASVURU_BOLGELERI,
    )


@app.route("/api/evraklar", methods=["POST"])
def api_evraklar():
    d = request.json
    result = get_document_list(
        meslek=d["meslek"],
        konaklama=d["konaklama"],
        cocuklu=d["cocuklu"],
        ulasim=d["ulasim"],
        bolge=d["bolge"],
    )
    return jsonify({
        "kombinasyon_kodu": result["kombinasyon_kodu"],
        "evrak_listesi": result["evrak_listesi"],
        "uyarilar": result["uyarilar"],
        "bolge_notlari": result["bolge_notlari"],
    })


@app.route("/api/kontrol", methods=["POST"])
def api_kontrol():
    d = request.json
    fields   = d.get("fields", {})
    meslek   = d["meslek"]
    konaklama= d["konaklama"]
    ulasim   = d["ulasim"]
    bolge    = d["bolge"]
    cocuklu  = d["cocuklu"]
    sure     = int(d.get("seyahat_suresi", 7))

    sonuc = tam_kontrol(fields, meslek, konaklama, ulasim, bolge, cocuklu, sure)

    # Serialize dataclasses
    belgeler_json = {}
    for bid, bilgi in sonuc["belgeler"].items():
        belgeler_json[bid] = {
            "etiket":   bilgi["etiket"],
            "skor":     bilgi["skor"],
            "sorunlar": [s.to_dict() for s in bilgi["sorunlar"]],
        }

    return jsonify({"belgeler": belgeler_json, "ozet": sonuc["ozet"]})


if __name__ == "__main__":
    app.run(debug=True, port=5000)

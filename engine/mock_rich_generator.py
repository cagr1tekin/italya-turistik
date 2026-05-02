"""
İtalya Turistik Vize — Zengin Mock Eğitim Verisi Üretici v2
============================================================
Kaynak : data/feature_matrix.csv  (720 kombinasyon)
Çıktı  : data/mock_rich_dataset.csv  (10.800 zengin başvuru)

Düzeltmeler (v2):
  - SEYAHAT_SIGORTASI / SEYAHAT_BILDIRGE çakışma hatası giderildi
  - max() yerine doğru belge tipi kullanılıyor (ulasim/konaklama'ya göre)
  - min_doc_skoru formula'ya eklendi (kötü belge → ret etkileniyor)
  - Profil bazlı kalibrasyon → hedef ret oranı %14-17
"""

import json, random, uuid
from datetime import date, timedelta
import pandas as pd
from pathlib import Path

DATA_DIR          = Path(__file__).parent.parent / "data"
BASVURU_TARIHI    = date(2026, 4, 30)
EUR_TL            = 40.0
ITALYA_ONAY_ORANI = 0.929
ONAY_ESIGI        = 0.70

# ── Veri Havuzları ────────────────────────────────────────────────────────────
_ERKEK = ["Ahmet","Mehmet","Mustafa","Ali","Murat","Emre","Burak","Can",
           "Serkan","Fatih","Yusuf","Kemal","Oğuz","Selim","Hasan","Tarık"]
_KADIN = ["Fatma","Ayşe","Emine","Zeynep","Elif","Merve","Selin","Büşra",
           "Gizem","Derya","Esra","Deniz","Arzu","Pınar","Sibel","Özge"]
_SOYAD = ["Yılmaz","Kaya","Demir","Şahin","Çelik","Yıldız","Öztürk","Aydın",
           "Arslan","Doğan","Kılıç","Aslan","Çetin","Koç","Kurt","Güneş","Polat"]
_BANKA = ["Garanti BBVA","İş Bankası","Akbank","Ziraat Bankası",
           "Yapı Kredi","Halkbank","VakıfBank","Denizbank","QNB Finansbank"]
_SIGORTACI = ["AXA Sigorta","GIG Sigorta","Allianz Sigorta","Mapfre Sigorta","HDI Sigorta"]
_IT_SEHIR  = ["Roma","Milano","Floransa","Venedik","Napoli","Bologna","Torino","Verona"]
_IT_OTEL   = ["Hotel Roma Central","Grand Hotel Milano","Boutique Firenze",
               "Venezia Palace","Napoli Luxury Inn","Albergo Torino"]
_UCUS      = [f"TK{n}" for n in range(103,298,7)] + [f"PC{n}" for n in range(203,398,7)]
_PNR       = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"

_BOLGE_SEHIR = {
    "ankara":   ["Ankara","Kırıkkale","Eskişehir","Çankırı"],
    "istanbul": ["İstanbul","Kocaeli","Tekirdağ","Yalova"],
    "izmir":    ["İzmir","Manisa","Aydın","Muğla"],
    "diger":    ["Bursa","Antalya","Adana","Konya","Kayseri","Trabzon","Gaziantep"],
}

_MESLEK_DET = {
    "calisan":       [("Yazılım Mühendisi","TechCorp A.Ş."),("Muhasebeci","ABC Holding"),
                      ("Makine Mühendisi","Otokar A.Ş."),("Bankacı","Akbank"),("Öğretmen","MEB")],
    "isveren":       [("CEO","Yıldız Grup Ltd."),("Genel Müdür","Demir Holding"),
                      ("Yönetici Ortak","Kaya İnşaat")],
    "serbest_meslek":[("Avukat","Kaya Hukuk Bürosu"),("Doktor","Özel Muayenehane"),
                      ("Mimar","Tasarım Ofisi"),("Muhasebeci","Bağımsız")],
    "emekli":        [("Emekli Memur","—"),("Emekli İşçi","—"),("Emekli Öğretmen","—")],
    "ogrenci":       [("Üniversite Öğrencisi","ODTÜ"),("Yüksek Lisans","Boğaziçi Ü."),
                      ("Doktora Öğrencisi","Hacettepe Ü.")],
    "memur":         [("Uzman","Maliye Bakanlığı"),("Müdür Yardımcısı","İçişleri Bakanlığı"),
                      ("Mühendis","DSİ")],
    "ciftci":        [("Çiftçi","Kendi Arazisi"),("Tarım İşletmecisi","Kendi İşletmesi")],
    "calismayanlar": [("Ev Hanımı","—"),("İş Arayan","—")],
    "cocuk":         [("Çocuk (0-6 yaş)","—")],
}

# ── Profil Tipi Parametreleri ─────────────────────────────────────────────────
PROFIL = {
    "ideal": {
        "oran":0.35, "yas":(28,55), "gelir":(75_000,200_000),
        "bakiye":(3_000,12_000), "schengen":(2,8),
        "ret_oran":0.02, "ani_para":0.02, "sorun_p":0.10,
        "base_ret_p": 0.015,   # kalibre edilmiş temel ret olasılığı
    },
    "orta": {
        "oran":0.40, "yas":(22,60), "gelir":(38_000,80_000),
        "bakiye":(1_000,3_500), "schengen":(0,4),
        "ret_oran":0.08, "ani_para":0.12, "sorun_p":0.32,
        "base_ret_p": 0.065,
    },
    "riskli": {
        "oran":0.18, "yas":(18,65), "gelir":(15_000,40_000),
        "bakiye":(200,1_400), "schengen":(0,2),
        "ret_oran":0.25, "ani_para":0.38, "sorun_p":0.65,
        "base_ret_p": 0.310,
    },
    "kritik_sorunlu": {
        "oran":0.07, "yas":(18,70), "gelir":(6_000,20_000),
        "bakiye":(30,500), "schengen":(0,1),
        "ret_oran":0.50, "ani_para":0.62, "sorun_p":0.90,
        "base_ret_p": 0.640,
    },
}

# Belge adından gruba eşleme (sorun gruplandırması için)
BELGE_GRUP = {
    "PASAPORT":             "PASAPORT",
    "BANKA_DOKUMU":         "BANKA",
    "SEYAHAT_SIGORTASI":    "SIGORTA",
    "BASVURU_FORMU":        "BASVURU",
    "SEYAHAT_BILDIRGE":     "BILDIRGE",
    "UCUS_REZERVASYONU":    "ULASIM",
    "ARAC_BELGESI":         "ULASIM",
    "TREN_BILETI":          "ULASIM",
    "OTOBUS_BILETI":        "ULASIM",
    "GEMI_BELGESI":         "ULASIM",
    "OTEL_REZERVASYONU":    "KONAKLAMA",
    "EV_SAHIBI_KIMLIK":     "KONAKLAMA",
    "DAVET_MEKTUBU":        "KONAKLAMA",
    "MESLEK_BELGESI":       "MESLEK",
    "IMZA_SIRKULERI":       "MESLEK",
    "CIFTCILIK_BELGESI":    "MESLEK",
    "EMEKLILIK_BELGESI":    "MESLEK",
    "MUVAFAKATNAME":        "MUVAFAKATNAME",
}


# ═══════════════════════════════════════════════════════════════════════════════
# YARDIMCI
# ═══════════════════════════════════════════════════════════════════════════════
def _ri(lo, hi, rng):  return rng.randint(lo, hi)
def _rf(lo, hi, rng):  return rng.uniform(lo, hi)

def _pick_profil(rng: random.Random) -> str:
    r, cum = rng.random(), 0.0
    for p, d in PROFIL.items():
        cum += d["oran"]
        if r < cum: return p
    return "orta"

def _skor(n_k, n_y, n_o) -> float:
    """Belge skoru: kritik×0.40, yüksek×0.20, orta×0.08; min 0."""
    return max(0.0, round(1.0 - n_k*0.40 - n_y*0.20 - n_o*0.08, 4))

def _issue(bid, kod, ciddiyet, aciklama, ret_riski, duzeltme) -> dict:
    return {"belge_id":bid,"sorun_kodu":kod,"ciddiyet":ciddiyet,
            "aciklama":aciklama,"ret_riski":ret_riski,"duzeltme":duzeltme}


# ═══════════════════════════════════════════════════════════════════════════════
# PROFİL ÜRETİCİ
# ═══════════════════════════════════════════════════════════════════════════════
def gen_profil(meslek, bolge, profil_tipi, rng) -> dict:
    p    = PROFIL[profil_tipi]
    cins = rng.choice(["erkek","kadin"])
    yas  = _ri(*p["yas"], rng)
    ew   = min(0.85, max(0.10, (yas-18)/40))
    det  = rng.choice(_MESLEK_DET.get(meslek, [("Diğer","—")]))
    return {
        "ad":            rng.choice(_ERKEK if cins=="erkek" else _KADIN),
        "soyad":         rng.choice(_SOYAD),
        "yas":           yas,
        "cinsiyet":      cins,
        "medeni_hal":    rng.choices(["evli","bekar","bosanmis"],weights=[ew,1-ew-0.05,0.05])[0],
        "meslek_detay":  det[0],
        "isyeri_adi":    det[1],
        "sehir":         rng.choice(_BOLGE_SEHIR.get(bolge, ["Türkiye"])),
        "is_suresi_yil": max(0,_ri(0,min(yas-18,30),rng)) if meslek not in ("ogrenci","cocuk") else 0,
        "aylik_gelir_tl": _ri(*p["gelir"], rng),
        "banka_bakiye_eur": round(_rf(*p["bakiye"], rng), 2),
        "bakiye_trend":  rng.choices(["artan","stabil","azalan"],
                          weights=[0.30,0.50,0.20] if profil_tipi in ("ideal","orta") else [0.10,0.30,0.60])[0],
        "ani_para_girisi": rng.random() < p["ani_para"],
        "onceki_schengen_sayisi": _ri(*p["schengen"], rng),
        "onceki_ret_sayisi": 1 if rng.random() < p["ret_oran"] else 0,
        "pasaport_gecerlilik_gun": _ri(75,2000,rng),
        "banka_adi":     rng.choice(_BANKA),
    }

def gen_seyahat(rng) -> dict:
    sure = _ri(5,21,rng)
    bas  = BASVURU_TARIHI + timedelta(days=_ri(45,180,rng))
    return {"baslangic":bas, "bitis":bas+timedelta(days=sure), "sure_gun":sure}


# ═══════════════════════════════════════════════════════════════════════════════
# SORUN ÜRETİCİLERİ
# ═══════════════════════════════════════════════════════════════════════════════
def chk_pasaport(profil, seyahat, sp, rng) -> list[dict]:
    iss = []
    son = profil["pasaport_gecerlilik_gun"] - seyahat["sure_gun"]
    if son < 90:
        iss.append(_issue("PASAPORT","PASAPORT_SURESI_YETERSIZ","KRITIK",
            f"Pasaport, seyahat bitişinden yalnızca {son} gün sonraya kadar geçerli. Min 90 gün şart.",
            0.70,"Seyahat tarihinden 90+ gün geçerli yeni pasaport çıkarın."))
    if rng.random() < sp * 0.12:
        iss.append(_issue("PASAPORT","PASAPORT_BOS_SAYFA_EKSIK","YUKSEK",
            "Pasaportta yeterli boş sayfa yok (min 2 adet şartı).",
            0.30,"Yeni pasaport çıkarın veya sayfa ekletin."))
    return iss


def chk_banka(profil, seyahat, sp, rng) -> list[dict]:
    iss = []
    min_bak = 50 * seyahat["sure_gun"]
    # Döküm tazeliği: sp yüksekse geniş aralık → >15 gün olasılığı artar
    gun = _ri(1,30,rng) if rng.random() < sp else _ri(1,14,rng)
    if gun > 15:
        iss.append(_issue("BANKA_DOKUMU","BANKA_DOKUM_ESKİ","KRITIK",
            f"Banka dökümü {gun} gün önce düzenlenmiş. Maksimum 15 gün olmalı.",
            0.45,"Başvuru tarihinden önceki 15 gün içinde yeni döküm alın."))
    if profil["banka_bakiye_eur"] < min_bak:
        iss.append(_issue("BANKA_DOKUMU","BAKIYE_YETERSIZ","KRITIK",
            f"Bakiye {profil['banka_bakiye_eur']:.0f} EUR. "
            f"{seyahat['sure_gun']} günlük seyahat için ≈{min_bak} EUR gerekli.",
            0.55,"Hesabınızda yeterli bakiye bulundurun veya maddi destek belgesi ekleyin."))
    if profil["bakiye_trend"]=="azalan" and rng.random() < sp*0.55:
        iss.append(_issue("BANKA_DOKUMU","AZALAN_BAKIYE_TRENDI","YUKSEK",
            "Son 6 ayda banka bakiyesinde düzenli azalma trendi.",
            0.25,"Gelir artışını veya ek varlıkları kanıtlayan belgeler ekleyin."))
    if profil["ani_para_girisi"] and rng.random() < sp*0.65:
        iss.append(_issue("BANKA_DOKUMU","ANI_PARA_GIRISI","ORTA",
            "Son 1 ayda aylık ortalamanın 3+ katı para girişi tespit edildi.",
            0.15,"Para kaynağını açıklayan yazılı beyan ekleyin."))
    return iss


def chk_sigorta(sp, rng) -> list[dict]:
    iss = []
    teminat = _ri(18_000,44_000,rng) if rng.random() < sp*0.5 else _ri(30_000,65_000,rng)
    if teminat < 30_000:
        iss.append(_issue("SEYAHAT_SIGORTASI","TEMINAT_YETERSIZ","KRITIK",
            f"Sigorta teminatı {teminat:,} EUR. Schengen için min 30.000 EUR zorunlu.",
            0.60,"En az 30.000 EUR teminatlı Schengen sigorta poliçesi alın."))
    if rng.random() < sp*0.18:
        iss.append(_issue("SEYAHAT_SIGORTASI","SIGORTA_TARIHI_YANLIS","YUKSEK",
            "Poliçe seyahat tarihlerini tam kapsamıyor (gidiş-1 / dönüş+1 gün şartı).",
            0.35,"Poliçeyi gidiş gününden 1 gün önce ve dönüş gününden 1 gün sonrasını kapsayacak yaptırın."))
    if rng.random() < sp*0.08:
        iss.append(_issue("SEYAHAT_SIGORTASI","SCHENGEN_KAPSAM_EKSIK","KRITIK",
            "Poliçe tüm Schengen bölgesini değil yalnızca İtalya'yı kapsıyor.",
            0.50,"Tüm Schengen ülkelerini kapsayan poliçe alın."))
    return iss


def chk_basvuru(sp, rng) -> list[dict]:
    iss = []
    if rng.random() < sp*0.30:
        iss.append(_issue("BASVURU_FORMU","ADRES_TUTARSIZLIGI","YUKSEK",
            "Formdaki ikamet adresi ile Tarihçeli Yerleşim Yeri Belgesi uyuşmuyor.",
            0.30,"Forma güncel ikametgah adresinizi yazın."))
    if rng.random() < sp*0.20:
        iss.append(_issue("BASVURU_FORMU","TARIH_TUTARSIZLIGI","YUKSEK",
            "Formdaki seyahat tarihleri rezervasyon belgeleriyle örtüşmüyor.",
            0.30,"Tüm belgelerdeki tarihlerin tutarlı olduğunu kontrol edin."))
    if rng.random() < sp*0.12:
        iss.append(_issue("BASVURU_FORMU","MESLEK_TUTARSIZLIGI","ORTA",
            "Formdaki meslek/işveren bilgisi sunulan çalışma belgesiyle tutarsız.",
            0.15,"Form bilgilerini çalışma belgenizle eşleştirin."))
    return iss


def chk_bildirge(sp, cocuklu, rng) -> list[dict]:
    iss = []
    if rng.random() < sp*0.32:
        iss.append(_issue("SEYAHAT_BILDIRGE","GELIR_BEYANI_EKSIK","YUKSEK",
            "Dilekçede aylık ortalama gelir beyanı yok.",
            0.25,"Aylık ortalama gelirinizi TL cinsinden dilekçeye ekleyin."))
    if cocuklu and rng.random() < sp*0.22:
        iss.append(_issue("SEYAHAT_BILDIRGE","BIRLIKTE_SEYAHAT_EKSIK","YUKSEK",
            "Birlikte seyahat edecek kişiler (çocuk dahil) dilekçede bildirilmemiş.",
            0.20,"Tüm birlikte seyahat edenleri isim ve yakınlık derecesiyle belirtin."))
    return iss


def chk_ulasim(ulasim, sp, rng) -> list[dict]:
    iss = []
    if ulasim == "ucak":
        if rng.random() < sp*0.22:
            iss.append(_issue("UCUS_REZERVASYONU","DONUS_BILETI_YOK","YUKSEK",
                "Rezervasyonda dönüş bileti yok.",0.30,"Gidiş-dönüş rezervasyon sunun."))
        if rng.random() < sp*0.12:
            iss.append(_issue("UCUS_REZERVASYONU","YOLCU_ADI_YANLIS","ORTA",
                "Rezervasyondaki yolcu adı pasaport adıyla uyuşmuyor.",0.15,"Adı havayoluyla düzeltin."))
    elif ulasim == "arac":
        if rng.random() < sp*0.20:
            iss.append(_issue("ARAC_BELGESI","YESIL_KART_EKSIK","YUKSEK",
                "Uluslararası araç sigortası (yeşil kart) sunulmamış.",0.35,"Yeşil kart sigortası yaptırın."))
        if rng.random() < sp*0.12:
            iss.append(_issue("ARAC_BELGESI","RUHSAT_EKSIK","ORTA",
                "Araç ruhsatı fotokopisi sunulmamış.",0.15,"Araç ruhsatı fotokopisi ekleyin."))
    elif ulasim == "tren":
        if rng.random() < sp*0.20:
            iss.append(_issue("TREN_BILETI","INTERRAIL_ASIL_YOK","ORTA",
                "Yalnızca İnterrail fotokopisi sunulmuş; orijinal bilet gereklidir.",0.15,"Orijinali de getirin."))
    elif ulasim == "gemi":
        if rng.random() < sp*0.18:
            iss.append(_issue("GEMI_BELGESI","GUZERGAH_YAZISI_EKSIK","ORTA",
                "Gemi tur organizasyonuna ait güzergah yazısı eksik.",0.15,"Tur firmasından güzergah yazısı alın."))
    elif ulasim == "otobus":
        if rng.random() < sp*0.15:
            iss.append(_issue("OTOBUS_BILETI","OTOBUS_DONUS_EKSIK","YUKSEK",
                "Dönüş otobüs bileti/rezervasyonu sunulmamış.",0.25,"Gidiş-dönüş bilet sunun."))
    return iss


def chk_konaklama(konaklama, bolge, sp, rng) -> list[dict]:
    iss = []
    if konaklama == "otel":
        if rng.random() < sp*0.18:
            iss.append(_issue("OTEL_REZERVASYONU","OTEL_TARIHI_UYUMSUZ","YUKSEK",
                "Otel check-in/out tarihleri seyahat tarihleriyle örtüşmüyor.",0.25,"Otel rezervasyonunu düzeltin."))
        if rng.random() < sp*0.10:
            iss.append(_issue("OTEL_REZERVASYONU","AD_EKSIK_REZERVASYONDA","ORTA",
                "Rezervasyonda tüm başvurucuların adları yok.",0.10,"Tüm adları ekletin."))
    else:  # davetiye
        if rng.random() < sp*0.28:
            iss.append(_issue("EV_SAHIBI_KIMLIK","FOTOKOPI_RENKLI_DEGIL","YUKSEK",
                "Davetçi kimlik/oturma izni fotokopisi renkli değil. iDATA renkli çıktı zorunlu kılar.",
                0.25,"Tüm davetçi belgelerini renkli çıktı alarak sunun."))
        if bolge == "izmir" and rng.random() < sp*0.28:
            iss.append(_issue("DAVET_MEKTUBU","IZMIR_UZAK_MESAFE_FORM_EKSIK","ORTA",
                "İzmir Konsolosluğu uzun süreli ilişki için 'Uzak mesafe ilişki' formu istiyor.",
                0.15,"Formu konsolosluk sitesinden indirip doldurun."))
    return iss


def chk_meslek(meslek, bolge, sp, rng) -> list[dict]:
    iss = []
    if rng.random() < sp*0.28:
        iss.append(_issue("MESLEK_BELGESI","KASE_IMZA_EKSIK","KRITIK",
            "Çalışma/meslek belgesi kaşesiz veya imzasız.",0.45,"Şirket kaşesi + yetkili imzası zorunludur."))
    if rng.random() < sp*0.18:
        gun = _ri(91,160,rng)
        iss.append(_issue("MESLEK_BELGESI","BELGE_ESKİ","YUKSEK",
            f"Mesleki belge {gun} gün önce düzenlenmiş; maksimum 90 gün olmalı.",0.25,"3 ay içinde yeni belge alın."))
    if meslek in ("calisan","isveren") and bolge != "ankara" and rng.random() < sp*0.22:
        iss.append(_issue("IMZA_SIRKULERI","IMZA_SIRKULERI_EKSIK","YUKSEK",
            f"{bolge.title()} başvurularında çalışan/işveren için imza sirküleri zorunlu.",
            0.25,"Banka imza sirküleri (şahsi hesap) temin edin."))
    if meslek == "emekli" and rng.random() < sp*0.22:
        iss.append(_issue("EMEKLILIK_BELGESI","ISLAK_IMZA_EKSIK","YUKSEK",
            "Emeklilik sandığı/banka emekliliği için ıslak imzalı kaşeli kurum yazısı eksik.",
            0.25,"Emeklilik kuruluşundan ıslak imzalı belge alın."))
    if meslek == "ciftci" and rng.random() < sp*0.25:
        iss.append(_issue("CIFTCILIK_BELGESI","ZIRAAT_GUNCEL_DEGIL","YUKSEK",
            "Ziraat odası çiftçilik belgesi güncel tarihli değil.",0.20,"Güncel tarihli belge alın."))
    return iss


def chk_muvafakatname(meslek, bolge, sp, rng) -> list[dict]:
    iss = []
    gun = _ri(30,120,rng) if rng.random() < sp*0.45 else _ri(20,89,rng)
    if gun > 90:
        iss.append(_issue("MUVAFAKATNAME","MUVAFAKATNAME_ESKİ","KRITIK",
            f"Muvafakatname {gun} gün önce düzenlenmiş. Maksimum 90 gün geçerli.",
            0.50,"3 ay içinde noter onaylı yeni muvafakatname alın."))
    if rng.random() < sp*0.18:
        iss.append(_issue("MUVAFAKATNAME","TEK_EBEVEYN_IMZALI","YUKSEK",
            "Muvafakatname yalnızca bir ebeveyn tarafından imzalanmış.",
            0.30,"Her iki ebeveyn imzası gereklidir."))
    if bolge=="ankara" and rng.random() < sp*0.22:
        iss.append(_issue("MUVAFAKATNAME","ANKARA_TAAHHUTNAME_EKSIK","KRITIK",
            "Ankara Büyükelçiliği: Eşlik eden kişiden noter taahhütname gerekiyor.",
            0.40,"Noterden taahhütname alın."))
    if meslek=="cocuk" and rng.random() < sp*0.32:
        iss.append(_issue("MUVAFAKATNAME","CIFT_APOSTILLE_EKSIK","KRITIK",
            "0-6 yaş çocuk başvurularında çift apostille zorunlu: noter→apostille→İtalyanca tercüme→apostille.",
            0.55,"Çift apostille sürecini tamamlayın."))
    return iss


# ═══════════════════════════════════════════════════════════════════════════════
# SKOR MOTORU
# ═══════════════════════════════════════════════════════════════════════════════
def compute_scores(
    all_issues, profil, profil_tipi,
    meslek, konaklama, ulasim, bolge, seyahat, cocuklu
) -> dict:

    # 1) Belge bazında sorun sayacı (tam belge adı key olarak)
    sayac: dict[str,dict[str,int]] = {}
    for iss in all_issues:
        bid = iss["belge_id"]
        grp = BELGE_GRUP.get(bid, bid)
        if grp not in sayac:
            sayac[grp] = {"K":0,"Y":0,"O":0}
        sayac[grp][iss["ciddiyet"][0]] += 1  # K/Y/O

    def s(grp):
        c = sayac.get(grp, {"K":0,"Y":0,"O":0})
        return _skor(c["K"], c["Y"], c["O"])

    # 2) Her belge tipi için skor (doğru grupla)
    skor_pasaport  = s("PASAPORT")
    skor_banka     = s("BANKA")
    skor_sigorta   = s("SIGORTA")
    skor_basvuru   = s("BASVURU")
    skor_bildirge  = s("BILDIRGE")
    skor_meslek    = s("MESLEK")
    skor_biyometrik = max(0.0, 1.0 - PROFIL[profil_tipi]["sorun_p"]*0.08)

    # Ulaşım: yalnızca seçilen aracın skorunu al
    skor_ulasim = s("ULASIM")

    # Konaklama: doğru grup
    skor_konaklama = s("KONAKLAMA")

    # Muvafakatname
    skor_muvafakatname = s("MUVAFAFAKATNAME") if cocuklu else 1.0
    # (Bug düzeltme: MUVAFAKATNAME)
    skor_muvafakatname = s("MUVAFAKATNAME") if cocuklu else 1.0

    # 3) Ortalama ve minimum belge skoru
    tum_skorlar = [
        skor_pasaport, skor_banka, skor_sigorta, skor_basvuru,
        skor_bildirge, skor_ulasim, skor_konaklama, skor_meslek, skor_biyometrik,
    ]
    if cocuklu:
        tum_skorlar.append(skor_muvafakatname)

    ort_skor = round(sum(tum_skorlar)/len(tum_skorlar), 4)
    min_skor = round(min(tum_skorlar), 4)

    # 4) Alt skorlar
    min_bak = 50 * seyahat["sure_gun"]
    finansal = min(1.0, profil["banka_bakiye_eur"] / max(min_bak, 1.0))
    if profil["bakiye_trend"] == "azalan":
        finansal = max(0.0, finansal - 0.12)
    finansal = round(finansal, 4)

    form_skor = round((skor_basvuru + skor_bildirge) / 2, 4)

    schengen  = profil["onceki_schengen_sayisi"]
    ret_gecm  = profil["onceki_ret_sayisi"]
    gecmis    = round(max(0.0, min(1.0, 0.50 + schengen*0.12 - ret_gecm*0.22)), 4)

    # 5) Kritik sorun var mı?
    kritik_var = any(i["ciddiyet"]=="KRITIK" for i in all_issues)
    n_k = sum(1 for i in all_issues if i["ciddiyet"]=="KRITIK")
    n_y = sum(1 for i in all_issues if i["ciddiyet"]=="YUKSEK")
    n_o = sum(1 for i in all_issues if i["ciddiyet"]=="ORTA")

    # 6) Onay olasılığı — formül tabanlı (model eğitimi için anlamlı sinyal)
    raw = (
        0.28 * ort_skor
      + 0.12 * min_skor          # kötü belgeye hafif ceza
      + 0.28 * finansal
      + 0.18 * form_skor
      + 0.14 * gecmis
    )
    # Her KRITIK sorun formülü doğrudan düşürür
    raw -= n_k * 0.045
    # Uyarı: kritik_var olan profillerde ekstra kayıp
    if kritik_var:
        raw -= 0.02
    onay_formula = round(max(0.0, min(1.0, raw * ITALYA_ONAY_ORANI)), 4)

    # 7) Ret olasılığı — kalibrasyon tabanlı (gerçekçi etiket dağılımı)
    # Base ret olasılığı profil tipine göre, belge/finansal sorunlar adjust eder
    base_ret = PROFIL[profil_tipi]["base_ret_p"]
    issue_adj = n_k * 0.040 + n_y * 0.010
    fin_adj   = max(0.0, (1.0 - finansal) * 0.070)
    hist_adj  = profil["onceki_ret_sayisi"] * 0.025
    ret_p = min(0.95, base_ret + issue_adj + fin_adj + hist_adj)

    # onay_olasiligi: formül + ret_p karışımı (ikisi de modele sinyal verir)
    onay = round(max(0.0, min(1.0,
        0.60 * onay_formula + 0.40 * (1.0 - ret_p)
    )), 4)

    return {
        "_ret_p": ret_p,     # iç kullanım, build_application'da etiket için
        "SKOR_PASAPORT":        skor_pasaport,
        "SKOR_BANKA":           skor_banka,
        "SKOR_SIGORTA":         skor_sigorta,
        "SKOR_BASVURU_FORMU":   skor_basvuru,
        "SKOR_BILDIRGE":        skor_bildirge,
        "SKOR_ULASIM":          skor_ulasim,
        "SKOR_KONAKLAMA":       skor_konaklama,
        "SKOR_MESLEK":          skor_meslek,
        "SKOR_BIYOMETRIK":      round(skor_biyometrik, 4),
        "SKOR_MUVAFAKATNAME":   skor_muvafakatname,
        "ortalama_belge_skoru": ort_skor,
        "min_belge_skoru":      min_skor,
        "finansal_yeterlilik_skoru": finansal,
        "form_tutarlilik_skoru":     form_skor,
        "seyahat_gecmisi_skoru":     gecmis,
        "kritik_sorun_var_mi":  int(kritik_var),
        "kritik_sorun_sayisi":  n_k,
        "yuksek_sorun_sayisi":  n_y,
        "orta_sorun_sayisi":    n_o,
        "toplam_sorun":         len(all_issues),
        "onay_olasiligi":       onay,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# BAŞVURU ÜRETİCİ
# ═══════════════════════════════════════════════════════════════════════════════
def build_application(combo_row, profil_tipi, rng) -> dict:
    meslek    = combo_row["meslek"]
    konaklama = combo_row["konaklama"]
    ulasim    = combo_row["ulasim"]
    bolge     = combo_row["bolge"]
    cocuklu   = bool(combo_row["cocuklu"])
    sp        = PROFIL[profil_tipi]["sorun_p"]

    profil  = gen_profil(meslek, bolge, profil_tipi, rng)
    seyahat = gen_seyahat(rng)

    issues = []
    issues += chk_pasaport(profil, seyahat, sp, rng)
    issues += chk_banka(profil, seyahat, sp, rng)
    issues += chk_sigorta(sp, rng)
    issues += chk_basvuru(sp, rng)
    issues += chk_bildirge(sp, cocuklu, rng)
    issues += chk_ulasim(ulasim, sp, rng)
    issues += chk_konaklama(konaklama, bolge, sp, rng)
    issues += chk_meslek(meslek, bolge, sp, rng)
    if cocuklu:
        issues += chk_muvafakatname(meslek, bolge, sp, rng)

    sc = compute_scores(issues, profil, profil_tipi, meslek, konaklama, ulasim, bolge, seyahat, cocuklu)

    # Etiket: kalibre edilmiş ret olasılığından stokastik olarak belirlenir
    ret_p = sc.pop("_ret_p")
    etk   = 0 if rng.random() < ret_p else 1

    onay  = sc["onay_olasiligi"]
    if etk == 1:
        etk_acik = "Onay — Güçlü profil" if onay >= 0.78 else "Onay — Kabul edilebilir, minor sorunlar var"
    else:
        etk_acik = "Ret — Kritik belge sorunu veya mali yetersizlik" if sc["kritik_sorun_var_mi"] \
                   else "Ret — Birden fazla yüksek risk veya yetersiz profil"

    return {
        "basvuru_id":           str(uuid.uuid4())[:8],
        "kombinasyon_kodu":     combo_row["kombinasyon_kodu"],
        "meslek":               meslek,
        "konaklama":            konaklama,
        "ulasim":               ulasim,
        "bolge":                bolge,
        "cocuklu":              int(cocuklu),
        "profil_tipi":          profil_tipi,
        # Demografik
        "yas":                  profil["yas"],
        "cinsiyet":             profil["cinsiyet"],
        "medeni_hal":           profil["medeni_hal"],
        "meslek_detay":         profil["meslek_detay"],
        "isyeri_adi":           profil["isyeri_adi"],
        "sehir":                profil["sehir"],
        "is_suresi_yil":        profil["is_suresi_yil"],
        # Finansal
        "aylik_gelir_tl":       profil["aylik_gelir_tl"],
        "banka_bakiye_eur":     profil["banka_bakiye_eur"],
        "bakiye_trend":         profil["bakiye_trend"],
        "ani_para_girisi":      int(profil["ani_para_girisi"]),
        # Seyahat geçmişi
        "onceki_schengen_sayisi": profil["onceki_schengen_sayisi"],
        "onceki_ret_sayisi":    profil["onceki_ret_sayisi"],
        "pasaport_gecerlilik_gun": profil["pasaport_gecerlilik_gun"],
        # Seyahat
        "seyahat_baslangic":    seyahat["baslangic"].isoformat(),
        "seyahat_bitis":        seyahat["bitis"].isoformat(),
        "seyahat_suresi_gun":   seyahat["sure_gun"],
        # Skorlar
        **sc,
        # Etiket
        "etiket":               etk,
        "etiket_aciklama":      etk_acik,
        # Detay
        "sorunlar_json":        json.dumps(issues, ensure_ascii=False),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# ANA ÜRETİCİ
# ═══════════════════════════════════════════════════════════════════════════════
def generate_rich_dataset(
    n_per_combination: int = 15,
    random_state: int = 42,
    output_path: str | None = None,
) -> pd.DataFrame:
    if output_path is None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        output_path = str(DATA_DIR / "mock_rich_dataset.csv")

    fm  = pd.read_csv(DATA_DIR / "feature_matrix.csv", encoding="utf-8-sig")
    rng = random.Random(random_state)

    rows = []
    for _, combo in fm.iterrows():
        for _ in range(n_per_combination):
            pt = _pick_profil(rng)
            rows.append(build_application(combo, pt, rng))

    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")

    # ── Rapor ─────────────────────────────────────────────────────────────────
    N   = len(df)
    onay_n = df["etiket"].sum()
    ret_n  = N - onay_n

    print(f"\n{'='*58}")
    print(f"  MOCK VERİ ÜRETİM RAPORU (v2)")
    print(f"{'='*58}")
    print(f"  Toplam başvuru    : {N:,}")
    print(f"  Onay              : {onay_n:,} ({onay_n/N*100:.1f}%)")
    print(f"  Ret               : {ret_n:,}  ({ret_n/N*100:.1f}%)")
    print(f"  Ort. belge skoru  : {df['ortalama_belge_skoru'].mean():.3f}")
    print(f"  Ort. min skor     : {df['min_belge_skoru'].mean():.3f}")
    print(f"  Ort. onay olasılığı: {df['onay_olasiligi'].mean():.3f}")

    print(f"\n  Profil tipi dağılımı:")
    for pt in ["ideal","orta","riskli","kritik_sorunlu"]:
        g = df[df["profil_tipi"]==pt]
        if len(g)==0: continue
        rp = (1-g["etiket"].mean())*100
        print(f"    {pt:<18}: {len(g):,} ({len(g)/N*100:.1f}%) → ret %{rp:.1f}")

    print(f"\n  En sık sorun çıkan belgeler (top 5):")
    sayac: dict[str,int] = {}
    for s_str in df["sorunlar_json"]:
        for iss in json.loads(s_str):
            bid = iss["belge_id"]
            sayac[bid] = sayac.get(bid,0)+1
    for bid,cnt in sorted(sayac.items(),key=lambda x:-x[1])[:5]:
        print(f"    {bid:<36}: {cnt:,} başvuruda")

    print(f"\n  Bölge bazında ret oranı:")
    for bolge in ["ankara","istanbul","izmir","diger"]:
        g = df[df["bolge"]==bolge]
        print(f"    {bolge:<10}: %{(1-g['etiket'].mean())*100:.1f}")

    print(f"\n  Tamamlık skoru dağılımı:")
    bins   = [0,.50,.70,.80,.90,.95,1.01]
    labels = ["<0.50","0.50-0.70","0.70-0.80","0.80-0.90","0.90-0.95","0.95-1.00"]
    df["_dilim"] = pd.cut(df["onay_olasiligi"],bins=bins,labels=labels,right=False)
    for lbl in labels:
        cnt = (df["_dilim"]==lbl).sum()
        bar = "█"*int(cnt/N*40)
        print(f"    {lbl:<12} {bar} {cnt:,} ({cnt/N*100:.1f}%)")
    df.drop(columns=["_dilim"], inplace=True)

    print(f"\n  Çıktı → {output_path}")
    print(f"{'='*58}\n")
    return df


# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    generate_rich_dataset(n_per_combination=15, random_state=42)

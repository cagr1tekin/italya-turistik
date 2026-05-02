"""
İtalya Turistik Vize — Zengin Mock Veri Üretici v3
===================================================
Belge içeriği alanları (OCR simülasyonu) ile üretim.
Kural motoru (rule_checker) ile sorun tespiti yapılır.
Eğitim verisi: ham alan değerleri → onay/ret.

Çıktı: data/mock_rich_v3.csv  (~10.800 satır, ~90 sütun)
"""

import json
import random
import uuid
import pandas as pd
import numpy as np
from pathlib import Path
from engine.rule_checker import tam_kontrol, hesapla_skor

DATA_DIR   = Path(__file__).parent.parent / "data"
ENGINE_DIR = Path(__file__).parent

# ─── Profil Tanımları ─────────────────────────────────────────────────────────
PROFIL = {
    "ideal": {
        "oran": 0.35,
        "base_ret_p": 0.018,
        "yas": (28, 55),
        "bakiye_eur": (3000, 15000),
        "schengen_onceki": (2, 8),
        "sorun_p": 0.08,   # belge sorun üretme olasılığı
    },
    "orta": {
        "oran": 0.40,
        "base_ret_p": 0.075,
        "yas": (22, 62),
        "bakiye_eur": (800, 3500),
        "schengen_onceki": (0, 4),
        "sorun_p": 0.30,
    },
    "riskli": {
        "oran": 0.18,
        "base_ret_p": 0.300,
        "yas": (18, 68),
        "bakiye_eur": (100, 1000),
        "schengen_onceki": (0, 2),
        "sorun_p": 0.65,
    },
    "kritik_sorunlu": {
        "oran": 0.07,
        "base_ret_p": 0.650,
        "yas": (18, 72),
        "bakiye_eur": (20, 400),
        "schengen_onceki": (0, 1),
        "sorun_p": 0.90,
    },
}

MESLEK_DETAY = {
    "calisan":       ["Muhasebeci","Mühendis","Tekniker","Şoför","Hemşire","Öğretmen","Satış Temsilcisi"],
    "isveren":       ["Restoran Sahibi","İnşaat Şirketi","Tekstil İşletmecisi","Market Sahibi"],
    "serbest_meslek":["Avukat","Doktor","Mimar","Mali Müşavir","Eczacı"],
    "emekli":        ["Emekli Memur","Emekli İşçi","Emekli Öğretmen"],
    "ogrenci":       ["Üniversite Öğrencisi","Lise Öğrencisi","Yüksek Lisans Öğrencisi"],
    "memur":         ["Devlet Memuru","Belediye Memuru","Vergi Dairesi Memuru"],
    "ciftci":        ["Çiftçi","Hayvancı","Bahçeci"],
    "calismayanlar": ["Ev Hanımı","İşsiz","Bakıcı"],
    "cocuk":         ["Çocuk (0-6 yaş)"],
}

SEHIRLER = ["İstanbul","Ankara","İzmir","Bursa","Antalya","Adana","Konya","Gaziantep"]


# ─── Profil Seçimi ────────────────────────────────────────────────────────────

def _pick_profil(rng):
    r = rng.random()
    k = 0.0
    for p, cfg in PROFIL.items():
        k += cfg["oran"]
        if r < k:
            return p
    return "orta"


def _sorun_mu(rng, sorun_p):
    return rng.random() < sorun_p


# ─── Belge İçerik Alanları Simülasyonu ───────────────────────────────────────

def _sim_pasaport(rng, cfg, seyahat_suresi):
    sp = cfg["sorun_p"]
    gun = rng.randint(50, 100) if _sorun_mu(rng, sp * 0.3) else rng.randint(90, 600)
    bos = rng.randint(0, 1)    if _sorun_mu(rng, sp * 0.2) else rng.randint(2, 20)
    return {"pas_gecerlilik_gun": gun, "pas_bos_sayfa": bos}


def _sim_sigorta(rng, cfg):
    sp = cfg["sorun_p"]
    teminat = rng.randint(15000, 29000) if _sorun_mu(rng, sp * 0.25) else rng.randint(30000, 60000)
    schengen = not _sorun_mu(rng, sp * 0.15)
    gidis    = not _sorun_mu(rng, sp * 0.20)
    donus    = not _sorun_mu(rng, sp * 0.20)
    eur      = not _sorun_mu(rng, sp * 0.10)
    return {
        "sig_teminat_eur":       teminat,
        "sig_schengen_kapsamli": schengen,
        "sig_gidis_oncesi_var":  gidis,
        "sig_donus_sonrasi_var": donus,
        "sig_eur_belirtilmis":   eur,
    }


def _sim_banka(rng, cfg, seyahat_suresi):
    sp = cfg["sorun_p"]
    bakim = rng.randint(16, 45) if _sorun_mu(rng, sp * 0.40) else rng.randint(1, 15)
    kase  = not _sorun_mu(rng, sp * 0.35)
    min_b = 50 * seyahat_suresi
    bmin, bmax = cfg["bakiye_eur"]
    bakiye = rng.uniform(bmin, bmax)
    duzenli = not _sorun_mu(rng, sp * 0.40)
    trend_r = rng.random()
    trend = "azalan" if trend_r < sp * 0.35 else ("artan" if trend_r < 0.5 else "stabil")
    ani_para = _sorun_mu(rng, sp * 0.20)
    return {
        "banka_son_bakim_gun": bakim,
        "banka_kase_imza_var": kase,
        "banka_bakiye_eur":    round(bakiye, 2),
        "banka_6ay_duzenli":   duzenli,
        "banka_trend":         trend,
        "banka_ani_para":      ani_para,
    }


def _sim_form(rng, cfg):
    sp = cfg["sorun_p"]
    return {
        "form_imzali_tarihli":         not _sorun_mu(rng, sp * 0.30),
        "form_adres_var":              not _sorun_mu(rng, sp * 0.35),
        "form_telefon_sahip":          not _sorun_mu(rng, sp * 0.15),
        "form_seyahat_tarihi_tutarli": not _sorun_mu(rng, sp * 0.25),
    }


def _sim_bildirge(rng, cfg):
    sp = cfg["sorun_p"]
    return {
        "bildirge_gelir_beyan":      not _sorun_mu(rng, sp * 0.40),
        "bildirge_seyahat_arkadasi": not _sorun_mu(rng, sp * 0.20),
    }


def _sim_ulasim(rng, cfg, ulasim):
    sp = cfg["sorun_p"]
    fields = {
        "rez_yolcu_adlari_tam": not _sorun_mu(rng, sp * 0.30),
        "rez_tarih_tutarli":    not _sorun_mu(rng, sp * 0.25),
    }
    if ulasim == "ucak":
        fields["rez_donus_bileti_var"] = not _sorun_mu(rng, sp * 0.35)
    if ulasim == "arac":
        fields["yesil_kart_var"] = not _sorun_mu(rng, sp * 0.30)
    return fields


def _sim_konaklama(rng, cfg, konaklama):
    sp = cfg["sorun_p"]
    fields = {"konal_tum_isimler_var": not _sorun_mu(rng, sp * 0.30)}
    if konaklama == "davetiye":
        fields["davet_renkli_cikti"]    = not _sorun_mu(rng, sp * 0.45)
        fields["davet_oturma_izni_var"] = not _sorun_mu(rng, sp * 0.25)
    return fields


def _sim_meslek(rng, cfg, meslek, bolge):
    sp = cfg["sorun_p"]
    fields = {
        "meslek_antelli_kagit":  not _sorun_mu(rng, sp * 0.35),
        "meslek_kase_imza":      not _sorun_mu(rng, sp * 0.40),
        "meslek_belge_yasi_gun": rng.randint(91, 180) if _sorun_mu(rng, sp * 0.30) else rng.randint(1, 75),
        "faaliyet_yasi_gun":     rng.randint(31, 120) if _sorun_mu(rng, sp * 0.35) else rng.randint(1, 25),
        "faaliyet_kaynak":       "web" if _sorun_mu(rng, 0.3) else "resmi",
        "faaliyet_kase_var":     not _sorun_mu(rng, sp * 0.25),
    }
    if meslek in ("calisan", "isveren"):
        fields["imza_sirkuleri_var"] = not _sorun_mu(rng, sp * 0.35)
    return fields


def _sim_muvafakatname(rng, cfg, meslek):
    sp = cfg["sorun_p"]
    fields = {
        "muv_noter_onayli":    not _sorun_mu(rng, sp * 0.30),
        "muv_her_iki_ebeveyn": not _sorun_mu(rng, sp * 0.25),
        "muv_gecerlilik_gun":  rng.randint(91, 200) if _sorun_mu(rng, sp * 0.35) else rng.randint(1, 85),
    }
    if meslek == "cocuk":
        fields["muv_apostille_var"] = not _sorun_mu(rng, sp * 0.50)
    return fields


# ─── Tek Başvuru Üret ─────────────────────────────────────────────────────────

def _uret_basvuru(rng, meslek, konaklama, ulasim, bolge, cocuklu, kombinasyon_kodu):
    profil_adi = _pick_profil(rng)
    cfg = PROFIL[profil_adi]

    yas = rng.randint(*cfg["yas"])
    cinsiyet = rng.choice(["Erkek", "Kadın"])
    seyahat_suresi = rng.randint(4, 21)
    schengen_onceki = rng.randint(*cfg["schengen_onceki"])
    onceki_ret = rng.randint(0, max(0, schengen_onceki // 3))

    # Belge içerik alanları
    fields = {}
    fields.update(_sim_pasaport(rng, cfg, seyahat_suresi))
    fields.update(_sim_sigorta(rng, cfg))
    fields.update(_sim_banka(rng, cfg, seyahat_suresi))
    fields.update(_sim_form(rng, cfg))
    fields.update(_sim_bildirge(rng, cfg))
    fields.update(_sim_ulasim(rng, cfg, ulasim))
    fields.update(_sim_konaklama(rng, cfg, konaklama))

    if meslek not in ("ogrenci", "calismayanlar", "cocuk"):
        fields.update(_sim_meslek(rng, cfg, meslek, bolge))

    if cocuklu or meslek == "cocuk":
        fields.update(_sim_muvafakatname(rng, cfg, meslek))

    # Kural motoru
    sonuc = tam_kontrol(fields, meslek, konaklama, ulasim, bolge, cocuklu, seyahat_suresi)
    oz    = sonuc["ozet"]
    belge = sonuc["belgeler"]

    # Ret olasılığı
    n_k = oz["n_kritik"]
    n_y = oz["n_yuksek"]
    fin_adj  = -0.05 if fields.get("banka_bakiye_eur", 999) > 50 * seyahat_suresi * 2 else 0.04
    hist_adj = -0.02 * schengen_onceki + 0.05 * onceki_ret
    ret_p = min(0.95, max(0.01,
        cfg["base_ret_p"] + n_k * 0.040 + n_y * 0.012 + fin_adj + hist_adj
    ))

    # Etiket (stokastik)
    etiket = 0 if rng.random() < ret_p else 1

    # Onay olasılığı (karışık: kural + stokastik)
    onay_formula = oz["onay_olasiligi"]
    onay = round(0.60 * onay_formula + 0.40 * (1.0 - ret_p), 3)

    # Açıklama
    en_kotu = min(belge.items(), key=lambda x: x[1]["skor"]) if belge else None
    aciklama = (f"Ret — {en_kotu[1]['etiket']}: skor {en_kotu[1]['skor']:.2f}" if etiket == 0 and en_kotu
                else "Onay")

    # Per-belge skorlar
    skor_row = {}
    for bid in ["PASAPORT","SIGORTA","BANKA","BASVURU_FORMU","BILDIRGE","ULASIM","KONAKLAMA","MESLEK","MUVAFAKATNAME"]:
        skor_row[f"SKOR_{bid}"] = belge[bid]["skor"] if bid in belge else None

    row = {
        "basvuru_id":           str(uuid.uuid4())[:8],
        "kombinasyon_kodu":     kombinasyon_kodu,
        "meslek":               meslek,
        "konaklama":            konaklama,
        "ulasim":               ulasim,
        "bolge":                bolge,
        "cocuklu":              int(cocuklu),
        "profil_tipi":          profil_adi,
        "yas":                  yas,
        "cinsiyet":             cinsiyet,
        "seyahat_suresi_gun":   seyahat_suresi,
        "onceki_schengen":      schengen_onceki,
        "onceki_ret":           onceki_ret,
        # Belge içerik alanları
        **fields,
        # Per-belge skorlar
        **skor_row,
        # Özet
        "ort_skor":             oz["ortalama_skor"],
        "min_skor":             oz["min_skor"],
        "n_kritik":             n_k,
        "n_yuksek":             n_y,
        "n_orta":               oz["n_orta"],
        # Hedef değişkenler
        "onay_olasiligi":       onay,
        "etiket":               etiket,
        "etiket_aciklama":      aciklama,
    }
    return row


# ─── Ana Üretici ──────────────────────────────────────────────────────────────

def generate_mock_v3(
    n_per_combination: int = 15,
    random_state: int = 42,
    output_path: str | None = None,
) -> pd.DataFrame:
    if output_path is None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        output_path = str(DATA_DIR / "mock_rich_v3.csv")

    from engine.document_engine import (
        MESLEK_GRUPLARI, KONAKLAMA_TURLERI,
        ULASIM_ARACLARI, BASVURU_BOLGELERI, get_document_list
    )
    import itertools

    rng = random.Random(random_state)
    rows = []
    total_combo = (len(MESLEK_GRUPLARI) * len(KONAKLAMA_TURLERI) *
                   len(ULASIM_ARACLARI) * len(BASVURU_BOLGELERI) * 2)

    for meslek, konaklama, ulasim, bolge, cocuklu in itertools.product(
        MESLEK_GRUPLARI, KONAKLAMA_TURLERI, ULASIM_ARACLARI, BASVURU_BOLGELERI, [False, True]
    ):
        cocuk_str = "COCUKLU" if cocuklu else "COCUKSUZ"
        kod = f"IT_TUR_{meslek.upper()}_{ulasim.upper()}_{konaklama.upper()}_{bolge.upper()}_{cocuk_str}"
        for _ in range(n_per_combination):
            row = _uret_basvuru(rng, meslek, konaklama, ulasim, bolge, cocuklu, kod)
            rows.append(row)

    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")

    tam = df["etiket"].sum()
    ret = len(df) - tam
    print(f"✅  {len(df):,} başvuru → {output_path}")
    print(f"    Onay : {tam:,} ({tam/len(df)*100:.1f}%)")
    print(f"    Ret  : {ret:,} ({ret/len(df)*100:.1f}%)")
    print()
    print("Profil bazında ret oranı:")
    for p, grp in df.groupby("profil_tipi"):
        r = 1 - grp["etiket"].mean()
        print(f"  {p:<16}: %{r*100:.1f}")
    print()
    print("Kritik sorun → ret ilişkisi:")
    for k in [0,1,2,3]:
        grp = df[df["n_kritik"] == k]
        if len(grp) > 0:
            print(f"  n_kritik={k}: %{(1-grp['etiket'].mean())*100:.1f} ret  ({len(grp)} başvuru)")
    return df


if __name__ == "__main__":
    print("=" * 60)
    print("MOCK BAŞVURU VERİSİ v3 — Belge İçerik Alanları Dahil")
    print("=" * 60)
    df = generate_mock_v3(n_per_combination=15, random_state=42)
    print(f"\nSütun sayısı: {len(df.columns)}")
    print(f"İlk belge içerik sütunları: {[c for c in df.columns if c.startswith('pas_') or c.startswith('sig_') or c.startswith('banka_')][:8]}")

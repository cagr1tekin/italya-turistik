"""
İtalya Turistik Vize — Mock Başvuru Verisi Üretici
===================================================
feature_matrix.csv'den yola çıkarak model eğitimi için sentetik
başvuru verisi üretir. Her kombinasyon için farklı "başvurucu profilleri"
simüle ederek eksik evrak senaryoları oluşturur.

Kullanım:
    py -m engine.mock_data_generator
    # veya
    from engine.mock_data_generator import generate_mock_dataset
    df = generate_mock_dataset(n_per_combination=15, random_state=42)
"""

import json
import random
import uuid
import pandas as pd
import numpy as np
from pathlib import Path

DATA_DIR   = Path(__file__).parent.parent / "data"
ENGINE_DIR = Path(__file__).parent

# ─── Başvurucu Profilleri ────────────────────────────────────────────────────
# Her profil: (isim, oran, eksik_evrak_sayisi_dagilimi)
# eksik_evrak_sayisi_dagilimi: {sayi: olasilik}
PROFILES = {
    "dikkatli":    {"oran": 0.35, "eksik_dagilim": {0: 0.60, 1: 0.30, 2: 0.10}},
    "orta":        {"oran": 0.35, "eksik_dagilim": {0: 0.20, 1: 0.40, 2: 0.25, 3: 0.15}},
    "dikkatsiz":   {"oran": 0.20, "eksik_dagilim": {0: 0.05, 1: 0.20, 2: 0.30, 3: 0.25, 4: 0.20}},
    "cok_dikkatsiz": {"oran": 0.10, "eksik_dagilim": {2: 0.10, 3: 0.20, 4: 0.25, 5: 0.25, 6: 0.20}},
}

# ─── Evrak Kategorileri ve Unutulma Ağırlıkları ──────────────────────────────
# Hangi evrakın unutulma olasılığı yüksek? (yüksek = daha sık atlanır)
EVRAK_UNUTULMA_AGIRLIKLARI = {
    # Temel evraklar — nadiren unutulur
    "DOC_PASAPORT":                1,
    "DOC_KIMLIK_FOTOKOPI":         2,
    "DOC_BASVURU_FORMU":           2,
    "DOC_BIYOMETRIK_FOTOGRAF":     3,
    "DOC_SEYAHAT_SAGLIK_SIGORTASI": 4,
    "DOC_VIZE_HARCI":              1,
    "DOC_TARIHCELI_YERLESIM_YERI": 5,
    "DOC_VUKUATLI_NUFUS":          5,
    "DOC_SEYAHAT_BILDIRGE":        6,

    # Ulaşım evrakları
    "DOC_UCUS_REZERVASYONU":       3,
    "DOC_TREN_BILETI":             4,
    "DOC_OTOBUS_BILETI":           4,
    "DOC_GEMI_BELGESI":            5,
    "DOC_ARAC_RUHSATI":            5,
    "DOC_ARAC_SIGORTASI":          7,
    "DOC_EHLIYET":                 6,

    # Konaklama evrakları
    "DOC_OTEL_REZERVASYONU":       4,
    "DOC_DAVET_MEKTUBU":           6,
    "DOC_EV_SAHIBI_KIMLIK":        8,  # renkli çıktı şartı çok unutuluyor

    # Meslek evrakları — sık unutuluyor
    "DOC_CALISMA_IZIN_BELGESI":    7,
    "DOC_CALISMA_EVRAKLARI":       8,
    "DOC_IMZA_SIRKULERI_CALISAN":  9,
    "DOC_MADDI_GELIR_CALISAN":     6,
    "DOC_CALISMA_IZIN_BELGESI_ISVEREN": 7,
    "DOC_IMZA_SIRKULERI_ISVEREN":  9,
    "DOC_FAALIYET_BELGESI":        7,
    "DOC_TICARET_SICIL_GAZETESI":  8,
    "DOC_VERGI_LEVHASI_ISVEREN":   7,
    "DOC_MADDI_GELIR_ISVEREN":     6,
    "DOC_TICARI_ODA_KAYDI":        7,
    "DOC_VERGI_LEVHASI_SERBEST":   7,
    "DOC_MADDI_GELIR_SERBEST":     6,
    "DOC_EMEKLILIK_BELGESI":       8,  # ıslak imzalı kurum yazısı unutuluyor
    "DOC_MADDI_GELIR_EMEKLI":      6,
    "DOC_OGRENCI_BELGESI":         5,
    "DOC_MADDI_GELIR_OGRENCI":     6,
    "DOC_CALISMA_IZIN_BELGESI_MEMUR": 7,
    "DOC_MADDI_GELIR_MEMUR":       6,
    "DOC_CIFTCILIK_BELGESI":       9,  # ziraat odası belgesi çok unutuluyor
    "DOC_MADDI_GELIR_CIFTCI":      6,
    "DOC_MADDI_GELIR_CALISMAYANLAR": 6,
    "DOC_TEMINAT":                 8,  # tutarlar belirsiz olduğu için atlanıyor

    # Destekçi evrakları — en çok unutulan
    "DOC_MADDI_DESTEKCI_OGRENCI":  10,
    "DOC_MADDI_DESTEKCI_CALISMAYANLAR": 10,
    "DOC_MADDI_DESTEKCI_COCUK":    10,

    # Çocuk evrakları
    "DOC_MUVAFAKATNAME":           7,
    "DOC_MUVAFAKATNAME_COCUK":     9,  # çift apostille şartı karmaşık
    "DOC_COCUK_BASVURU_FORMU":     5,
    "DOC_DOGUM_BELGESI":           6,
}

DEFAULT_AGIRLIK = 6  # listede olmayan evraklar için


def _pick_profile(rng: random.Random) -> str:
    r = rng.random()
    kumulatif = 0.0
    for profil, bilgi in PROFILES.items():
        kumulatif += bilgi["oran"]
        if r < kumulatif:
            return profil
    return "orta"


def _pick_eksik_sayisi(profil: str, rng: random.Random) -> int:
    dagilim = PROFILES[profil]["eksik_dagilim"]
    sayilar = list(dagilim.keys())
    olasiliklar = list(dagilim.values())
    return rng.choices(sayilar, weights=olasiliklar, k=1)[0]


def _pick_eksik_evraklar(
    zorunlu_evraklar: list[str],
    n_eksik: int,
    rng: random.Random,
) -> list[str]:
    """Zorunlu evraklar arasından ağırlıklı rastgele n_eksik tanesini seç."""
    if n_eksik == 0 or not zorunlu_evraklar:
        return []
    n_eksik = min(n_eksik, len(zorunlu_evraklar))
    agirliklar = [EVRAK_UNUTULMA_AGIRLIKLARI.get(e, DEFAULT_AGIRLIK) for e in zorunlu_evraklar]
    secilen = rng.choices(zorunlu_evraklar, weights=agirliklar, k=n_eksik * 3)
    # Tekrarsız n_eksik adet seç
    benzersiz = list(dict.fromkeys(secilen))[:n_eksik]
    return benzersiz


def generate_mock_dataset(
    n_per_combination: int = 15,
    random_state: int = 42,
    output_path: str | None = None,
) -> pd.DataFrame:
    """
    Her kombinasyon için n_per_combination adet sentetik başvuru üretir.

    Toplam satır: 720 × n_per_combination = {720 * n_per_combination}

    Parameters
    ----------
    n_per_combination : int
        Her kombinasyon için üretilecek başvuru sayısı (varsayılan: 15 → 10.800 satır)
    random_state : int
        Tekrarlanabilirlik için seed
    output_path : str | None
        CSV çıktı yolu (None → data/mock_applications.csv)

    Returns
    -------
    pd.DataFrame
        Eğitim için hazır mock başvuru verisi
    """
    if output_path is None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        output_path = str(DATA_DIR / "mock_applications.csv")

    feature_matrix_path = DATA_DIR / "feature_matrix.csv"
    fm = pd.read_csv(feature_matrix_path, encoding="utf-8-sig")
    doc_cols = [c for c in fm.columns if c.startswith("DOC_")]

    rng = random.Random(random_state)
    rows = []

    for _, combo_row in fm.iterrows():
        kombinasyon_kodu = combo_row["kombinasyon_kodu"]
        meta_cols = ["meslek", "konaklama", "ulasim", "bolge", "cocuklu"]
        meta = {k: combo_row[k] for k in meta_cols}

        # Bu kombinasyonda zorunlu olan evraklar
        zorunlu_evraklar = [col for col in doc_cols if combo_row[col] == 1]
        n_zorunlu = len(zorunlu_evraklar)

        for i in range(n_per_combination):
            profil = _pick_profile(rng)
            n_eksik = _pick_eksik_sayisi(profil, rng)
            eksik_evraklar = _pick_eksik_evraklar(zorunlu_evraklar, n_eksik, rng)

            # Başvurucunun sunduğu evraklar (zorunlu - eksik)
            mevcut_set = set(zorunlu_evraklar) - set(eksik_evraklar)
            n_mevcut = len(mevcut_set)
            doc_completeness_score = round(n_mevcut / n_zorunlu, 4) if n_zorunlu > 0 else 1.0

            # Binary evrak vektörü (tüm 49 evrak için)
            evrak_vektor = {}
            for col in doc_cols:
                if combo_row[col] == 1:
                    evrak_vektor[col] = 1 if col in mevcut_set else 0
                else:
                    evrak_vektor[col] = 0  # bu kombinasyonda zaten gerekmiyor

            row = {
                "basvuru_id": str(uuid.uuid4())[:8],
                "kombinasyon_kodu": kombinasyon_kodu,
                **meta,
                "basvurucu_profil": profil,
                "zorunlu_evrak_sayisi": n_zorunlu,
                "mevcut_evrak_sayisi": n_mevcut,
                "eksik_evrak_sayisi": len(eksik_evraklar),
                "doc_completeness_score": doc_completeness_score,
                "eksik_evraklar": "|".join(sorted(eksik_evraklar)),
                "tam_mi": 1 if len(eksik_evraklar) == 0 else 0,
                **evrak_vektor,
            }
            rows.append(row)

    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")

    tam_basvuru = df["tam_mi"].sum()
    eksik_basvuru = len(df) - tam_basvuru
    ort_score = df["doc_completeness_score"].mean()
    ort_eksik = df["eksik_evrak_sayisi"].mean()

    print(f"✅  {len(df):,} mock başvuru → {output_path}")
    print(f"    Tam başvuru     : {tam_basvuru:,} ({tam_basvuru/len(df)*100:.1f}%)")
    print(f"    Eksik başvuru   : {eksik_basvuru:,} ({eksik_basvuru/len(df)*100:.1f}%)")
    print(f"    Ort. tamamlık   : {ort_score:.3f}")
    print(f"    Ort. eksik evrak: {ort_eksik:.2f}")
    print()

    # Profil dağılımı
    print("Profil dağılımı:")
    profil_dagilimi = df["basvurucu_profil"].value_counts()
    for profil, sayi in profil_dagilimi.items():
        print(f"    {profil:<16}: {sayi:,} ({sayi/len(df)*100:.1f}%)")
    print()

    # Meslek bazında ort. tamamlık
    print("Meslek bazında ort. tamamlık skoru:")
    meslek_scores = df.groupby("meslek")["doc_completeness_score"].mean().sort_values()
    for meslek, skor in meslek_scores.items():
        print(f"    {meslek:<20}: {skor:.3f}")
    print()

    # En çok unutulan evraklar
    eksik_evrak_sayaci: dict[str, int] = {}
    for eksik_str in df["eksik_evraklar"].dropna():
        if eksik_str:
            for ev in eksik_str.split("|"):
                if ev:
                    eksik_evrak_sayaci[ev] = eksik_evrak_sayaci.get(ev, 0) + 1
    print("En çok unutulan 10 evrak:")
    for ev, sayi in sorted(eksik_evrak_sayaci.items(), key=lambda x: -x[1])[:10]:
        print(f"    {ev:<40}: {sayi:,} kez")

    return df


if __name__ == "__main__":
    print("=" * 65)
    print("MOCK BAŞVURU VERİSİ ÜRETİCİ")
    print("720 kombinasyon × 15 başvuru = 10.800 satır")
    print("=" * 65)
    print()
    df = generate_mock_dataset(n_per_combination=15, random_state=42)
    print()
    print("Tamamlık skoru dağılımı:")
    bins = [0.0, 0.5, 0.7, 0.8, 0.9, 0.95, 1.01]
    labels = ["<0.50", "0.50-0.70", "0.70-0.80", "0.80-0.90", "0.90-0.95", "0.95-1.00"]
    df["skor_dilimi"] = pd.cut(df["doc_completeness_score"], bins=bins, labels=labels, right=False)
    dagilim = df["skor_dilimi"].value_counts().sort_index()
    for dilim, sayi in dagilim.items():
        bar = "█" * int(sayi / len(df) * 50)
        print(f"  {dilim:<12} {bar} {sayi:,} ({sayi/len(df)*100:.1f}%)")

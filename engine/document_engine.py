"""
İtalya Turistik Vize — Kural Tabanlı Evrak Listesi Motoru v2.0
==============================================================
Kullanım:
    from engine.document_engine import get_document_list, generate_all_combinations

    result = get_document_list(
        meslek="memur",
        konaklama="davetiye",
        cocuklu=True,
        ulasim="tren",
        bolge="istanbul"
    )

v2.0 Değişiklikleri:
    - 9 meslek grubu iDATA PDF'lerinden doğrulandı ve güncellendi
    - Yeni meslek: memur, serbest_meslek, ciftci, calismayanlar, cocuk
    - Güncellenen konaklama: akraba_taniklik → davetiye
    - Yeni ulaşım: tren (Tren/İnterrail)
    - Kaldırılan ulaşım: tur_organizasyonu (ucak içinde not olarak belirtiliyor)
"""

import json
import itertools
import pandas as pd
from pathlib import Path

RULES_PATH = Path(__file__).parent / "italy_tourist_rules.json"
with open(RULES_PATH, encoding="utf-8") as f:
    RULES = json.load(f)

MESLEK_GRUPLARI   = RULES["meta"]["boyutlar"]["meslek_gruplari"]
KONAKLAMA_TURLERI = RULES["meta"]["boyutlar"]["konaklama_turleri"]
ULASIM_ARACLARI   = RULES["meta"]["boyutlar"]["ulasim_araclari"]
BASVURU_BOLGELERI = RULES["meta"]["boyutlar"]["basvuru_bolgeleri"]

DATA_DIR = Path(__file__).parent.parent / "data"


def get_document_list(
    meslek: str,
    konaklama: str,
    cocuklu: bool,
    ulasim: str,
    bolge: str,
) -> dict:
    """
    Verilen parametrelere göre tam evrak listesi ve uyarıları döner.

    Returns
    -------
    {
        "kombinasyon_kodu": str,
        "evrak_listesi": [{"id", "ad", "detay", "zorunlu"}, ...],
        "evrak_sayisi": int,
        "uyarilar": [str, ...],
        "bolge_notlari": [str, ...],
    }
    """
    assert meslek    in MESLEK_GRUPLARI,   f"Geçersiz meslek: {meslek}. Geçerliler: {MESLEK_GRUPLARI}"
    assert konaklama in KONAKLAMA_TURLERI, f"Geçersiz konaklama: {konaklama}. Geçerliler: {KONAKLAMA_TURLERI}"
    assert ulasim    in ULASIM_ARACLARI,   f"Geçersiz ulaşım: {ulasim}. Geçerliler: {ULASIM_ARACLARI}"
    assert bolge     in BASVURU_BOLGELERI, f"Geçersiz bölge: {bolge}. Geçerliler: {BASVURU_BOLGELERI}"

    evraklar: list[dict] = []
    uyarilar: list[str]  = []

    # 1) STANDART EVRAKLAR
    for e in RULES["standart_evraklar"]["evraklar"]:
        evraklar.append(_format_evrak(e))

    # 2) ULAŞIM EVRAKI
    ulasim_kural = RULES["ulasim_kurallari"][ulasim]
    if ulasim == "arac":
        for e in ulasim_kural:
            evraklar.append(_format_evrak(e))
    else:
        evraklar.append(_format_evrak(ulasim_kural))
        if ulasim == "ucak":
            if bolge == "ankara":
                uyarilar.append(
                    "ℹ️  TUR ORGANİZASYONU seçilmişse ANKARA ÖZEL: e-fatura zorunludur; "
                    "banka havalesi → dekont, kredi kartı → hesap ekstresi gerekir."
                )
            else:
                uyarilar.append(
                    "ℹ️  Tur organizasyonu seçilmişse ek evrak: tur kayıt belgesi, "
                    "tur programı ve kaşeli/imzalı tur ödeme makbuzu."
                )

    # 3) KONAKLAMA EVRAKI
    konaklama_kural = RULES["konaklama_kurallari"][konaklama]
    if konaklama == "davetiye":
        for e in konaklama_kural:
            evrak = _format_evrak(e)
            if e.get("izmir_ozel") and bolge == "izmir":
                uyarilar.append(f"ℹ️  İZMİR DAVETİYE ÖZEL: {e['izmir_ozel']}")
            evraklar.append(evrak)
    else:
        evraklar.append(_format_evrak(konaklama_kural))

    # 4) MESLEK EVRAKI
    meslek_kural = RULES["meslek_kurallari"][meslek]
    for e in meslek_kural["evraklar"]:
        evrak = _format_evrak(e)
        if e.get("uyari_ankara") and bolge == "ankara":
            uyarilar.append(f"ℹ️  {e['ad']}: {e['uyari_ankara']}")
        elif e.get("uyari_diger") and bolge != "ankara":
            uyarilar.append(f"ℹ️  {e['ad']}: {e['uyari_diger']}")
        if e.get("bolge_ozel") and e["bolge_ozel"].get(bolge):
            uyarilar.append(f"⚠️  {e['ad']} [{bolge.upper()}]: {e['bolge_ozel'][bolge]}")
        if e.get("ankara_ozel") and bolge == "ankara":
            uyarilar.append(f"🔴  ANKARA ÖZEL ({e['ad']}): {e['ankara_ozel']}")
        evraklar.append(evrak)

    # 5) ÇOCUKLU SEYAHAT
    if cocuklu:
        cocuk_kural = RULES["cocuklu_seyahat_kurallari"]
        for e in cocuk_kural["zorunlu_evraklar"]:
            evraklar.append(_format_evrak(e))

        uyarilar.append(
            "⚠️  ÇOCUKLU SEYAHAT: Muvafakatname her iki ebeveynden noter onaylı alınmalıdır (3 ay geçerli)."
        )
        uyarilar.append(
            "ℹ️  Çocuk ebeveyni dışında biriyle seyahat ediyorsa Refakat Beyanı gereklidir."
        )
        if bolge == "ankara":
            uyarilar.append(
                "🔴  ANKARA ÖZEL: Çocuk ebeveyni dışındaki kişiyle seyahat ediyorsa noterden Taahhütname zorunludur."
            )
        biyometri = cocuk_kural["biyometri_kurali"]
        uyarilar.append(
            f"ℹ️  Biyometri: 12 yaş altı → {biyometri['12_yas_alti']} | "
            f"12 yaş üstü → {biyometri['12_yas_ustu']}"
        )

    # 6) BÖLGE NOTLARI
    bolge_notlari: list[str] = list(RULES["bolge_ozel_kurallari"][bolge]["ozel_kurallar"])
    bolge_data = RULES["bolge_ozel_kurallari"][bolge]
    if "iletisim" in bolge_data:
        bolge_notlari.insert(0, f"📞 İletişim: {bolge_data['iletisim']}")
    if "randevu" in bolge_data:
        bolge_notlari.insert(0, f"📅 Randevu: {bolge_data['randevu']}")

    # 7) KOMBİNASYON KODU
    cocuk_str = "COCUKLU" if cocuklu else "COCUKSUZ"
    kombinasyon_kodu = (
        f"IT_TUR_{meslek.upper()}_{ulasim.upper()}_{konaklama.upper()}_{bolge.upper()}_{cocuk_str}"
    )

    return {
        "kombinasyon_kodu": kombinasyon_kodu,
        "evrak_listesi": evraklar,
        "evrak_sayisi": len(evraklar),
        "uyarilar": uyarilar,
        "bolge_notlari": bolge_notlari,
    }


def _format_evrak(e: dict) -> dict:
    return {
        "id": e.get("id", ""),
        "ad": e.get("ad", ""),
        "detay": e.get("detay", ""),
        "zorunlu": e.get("zorunlu", True),
    }


def generate_all_combinations(output_path: str | None = None) -> pd.DataFrame:
    """180 kombinasyonu üretir ve CSV olarak kaydeder."""
    if output_path is None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        output_path = str(DATA_DIR / "all_combinations.csv")

    rows = []
    for meslek, konaklama, ulasim, bolge, cocuklu in itertools.product(
        MESLEK_GRUPLARI,
        KONAKLAMA_TURLERI,
        ULASIM_ARACLARI,
        BASVURU_BOLGELERI,
        [False, True],
    ):
        result = get_document_list(meslek, konaklama, cocuklu, ulasim, bolge)
        evrak_ids = [e["id"] for e in result["evrak_listesi"]]
        rows.append({
            "kombinasyon_kodu": result["kombinasyon_kodu"],
            "meslek": meslek,
            "konaklama": konaklama,
            "ulasim": ulasim,
            "bolge": bolge,
            "cocuklu": cocuklu,
            "evrak_sayisi": result["evrak_sayisi"],
            "evrak_listesi": "|".join(evrak_ids),
            "uyari_sayisi": len(result["uyarilar"]),
        })

    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"✅  {len(df)} kombinasyon → {output_path}")
    return df


def get_feature_matrix(output_path: str | None = None) -> pd.DataFrame:
    """Model eğitimi için binary özellik matrisi üretir."""
    if output_path is None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        output_path = str(DATA_DIR / "feature_matrix.csv")

    all_evrak_ids: set[str] = set()
    results = []

    for meslek, konaklama, ulasim, bolge, cocuklu in itertools.product(
        MESLEK_GRUPLARI,
        KONAKLAMA_TURLERI,
        ULASIM_ARACLARI,
        BASVURU_BOLGELERI,
        [False, True],
    ):
        result = get_document_list(meslek, konaklama, cocuklu, ulasim, bolge)
        evrak_ids = {e["id"] for e in result["evrak_listesi"]}
        all_evrak_ids.update(evrak_ids)
        results.append((
            result["kombinasyon_kodu"],
            meslek, konaklama, ulasim, bolge, cocuklu,
            evrak_ids
        ))

    sorted_ids = sorted(all_evrak_ids)
    rows = []
    for kod, meslek, konaklama, ulasim, bolge, cocuklu, evrak_ids in results:
        row = {
            "kombinasyon_kodu": kod,
            "meslek": meslek,
            "konaklama": konaklama,
            "ulasim": ulasim,
            "bolge": bolge,
            "cocuklu": int(cocuklu),
        }
        for eid in sorted_ids:
            row[f"DOC_{eid}"] = 1 if eid in evrak_ids else 0
        rows.append(row)

    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"✅  Özellik matrisi: {len(df)} satır × {len(sorted_ids)} evrak sütunu → {output_path}")
    return df


if __name__ == "__main__":
    print("=" * 70)
    print("ÖRNEK: İtalya > Turistik > Memur > Tren > Davetiye > İstanbul > Çocuklu")
    print("=" * 70)
    result = get_document_list(
        meslek="memur",
        konaklama="davetiye",
        cocuklu=True,
        ulasim="tren",
        bolge="istanbul",
    )
    print(f"\nKombinasyon Kodu : {result['kombinasyon_kodu']}")
    print(f"Toplam Evrak     : {result['evrak_sayisi']}\n")
    for i, e in enumerate(result["evrak_listesi"], 1):
        print(f"  {i:2}. [{e['id']}] {e['ad']}")
    if result["uyarilar"]:
        print("\nUYARILAR:")
        for u in result["uyarilar"]:
            print(f"  {u}")
    if result["bolge_notlari"]:
        print(f"\nBÖLGE NOTLARI:")
        for n in result["bolge_notlari"]:
            print(f"  • {n}")

    print("\n" + "=" * 70)
    df = generate_all_combinations()
    print(f"\nMeslek bazında ortalama evrak sayısı:\n{df.groupby('meslek')['evrak_sayisi'].mean().round(1).to_string()}")

    print("\n" + "=" * 70)
    fm = get_feature_matrix()
    print(f"Matris boyutu: {fm.shape}")

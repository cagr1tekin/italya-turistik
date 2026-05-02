"""
İtalya Turistik Vize — Belge İçeriği Kural Kontrolcüsü
=======================================================
iDATA PDF UYARILAR bölümünden çıkarılan kurallar.
OCR'dan gelen belge içeriği alanlarını kontrol eder.

Her belge için döner:
    {"sorunlar": [Sorun(...)], "skor": 0.0-1.0}
"""

from dataclasses import dataclass
from typing import Literal

Seviye = Literal["KRITIK", "YUKSEK", "ORTA"]

@dataclass
class Sorun:
    seviye: Seviye
    kod: str
    mesaj: str

    def to_dict(self):
        return {"seviye": self.seviye, "kod": self.kod, "mesaj": self.mesaj}


# ─── Per-belge Kural Fonksiyonları ────────────────────────────────────────────

def kontrol_pasaport(f: dict) -> list[Sorun]:
    s = []
    gun = f.get("pas_gecerlilik_gun", 999)
    if gun < 90:
        s.append(Sorun("KRITIK", "PAS_GECERLILIK",
            f"Pasaport vize bitiş tarihinden sonra yalnızca {gun} gün geçerli — en az 90 gün gerekli."))
    if f.get("pas_bos_sayfa", 2) < 2:
        s.append(Sorun("KRITIK", "PAS_BOS_SAYFA",
            f"Pasaportda {f.get('pas_bos_sayfa',0)} boş sayfa var — en az 2 boş sayfa gerekli."))
    return s


def kontrol_sigorta(f: dict) -> list[Sorun]:
    s = []
    teminat = f.get("sig_teminat_eur", 30000)
    if teminat < 30000:
        s.append(Sorun("KRITIK", "SIG_TEMINAT",
            f"Sigorta teminatı {teminat:,.0f} EUR — en az 30.000 EUR gerekli."))
    if not f.get("sig_schengen_kapsamli", True):
        s.append(Sorun("KRITIK", "SIG_KAPSAM",
            "Sigorta tüm Schengen bölgesini kapsamamaktadır."))
    if not f.get("sig_gidis_oncesi_var", True):
        s.append(Sorun("KRITIK", "SIG_GIDIS",
            "Sigorta gidiş tarihinden en az 1 gün önce başlamalıdır."))
    if not f.get("sig_donus_sonrasi_var", True):
        s.append(Sorun("KRITIK", "SIG_DONUS",
            "Sigorta dönüş tarihinden en az 1 gün sonra bitmelidir."))
    if not f.get("sig_eur_belirtilmis", True):
        s.append(Sorun("YUKSEK", "SIG_DOVIZ",
            "Teminat bedeli EUR olarak belirtilmemiştir."))
    return s


def kontrol_banka(f: dict, seyahat_suresi: int = 7) -> list[Sorun]:
    s = []
    bakim_gun = f.get("banka_son_bakim_gun", 0)
    if bakim_gun > 15:
        s.append(Sorun("KRITIK", "BANKA_TARIH",
            f"Banka dökümü {bakim_gun} gün önce düzenlenmiş — başvuru tarihinden önceki son 15 gün içinde olmalı."))
    if not f.get("banka_kase_imza_var", True):
        s.append(Sorun("KRITIK", "BANKA_KASE",
            "Banka dökümünde şube kaşesi ve imzası bulunmuyor."))
    min_bakiye = 50 * seyahat_suresi
    bakiye = f.get("banka_bakiye_eur", 9999)
    if bakiye < min_bakiye:
        s.append(Sorun("KRITIK", "BANKA_BAKIYE",
            f"Bakiye {bakiye:.0f} EUR — {seyahat_suresi} günlük seyahat için min {min_bakiye:.0f} EUR gerekli (50 EUR/gün)."))
    if not f.get("banka_6ay_duzenli", True):
        s.append(Sorun("YUKSEK", "BANKA_DUZENLI",
            "Son 6 aylık döküm düzenli gelir yatışı göstermiyor."))
    if f.get("banka_trend", "stabil") == "azalan":
        s.append(Sorun("YUKSEK", "BANKA_TREND",
            "Banka bakiyesi son aylarda düşüş trendi gösteriyor."))
    if f.get("banka_ani_para", False):
        s.append(Sorun("ORTA", "BANKA_ANI_PARA",
            "Hesapta başvuru öncesi ani büyük para girişi tespit edildi."))
    return s


def kontrol_form(f: dict) -> list[Sorun]:
    s = []
    if not f.get("form_imzali_tarihli", True):
        s.append(Sorun("KRITIK", "FORM_IMZA",
            "Başvuru formu imzasız veya tarihe atılmamış."))
    if not f.get("form_adres_var", True):
        s.append(Sorun("YUKSEK", "FORM_ADRES",
            "Başvuru formunda ikamet adresi belirtilmemiş."))
    if not f.get("form_telefon_sahip", True):
        s.append(Sorun("YUKSEK", "FORM_TELEFON",
            "Başvuru formundaki telefon numarası başvuru sahibine ait değil."))
    if not f.get("form_seyahat_tarihi_tutarli", True):
        s.append(Sorun("YUKSEK", "FORM_TARIH",
            "Başvuru formundaki seyahat tarihleri diğer belgelerle tutarsız."))
    return s


def kontrol_bildirge(f: dict) -> list[Sorun]:
    s = []
    if not f.get("bildirge_gelir_beyan", True):
        s.append(Sorun("YUKSEK", "BILDIRGE_GELIR",
            "Seyahat bildirgesinde aylık ortalama gelir beyanı eksik."))
    if not f.get("bildirge_seyahat_arkadasi", True):
        s.append(Sorun("ORTA", "BILDIRGE_ARKADAS",
            "Birlikte seyahat edecek kişiler bildirgede belirtilmemiş."))
    return s


def kontrol_ulasim(f: dict, ulasim: str) -> list[Sorun]:
    s = []
    if ulasim == "ucak" and not f.get("rez_donus_bileti_var", True):
        s.append(Sorun("YUKSEK", "REZ_DONUS",
            "Gidiş-dönüş uçuş rezervasyonu sunulmamış — dönüş bileti gerekli."))
    if ulasim == "arac" and not f.get("yesil_kart_var", True):
        s.append(Sorun("YUKSEK", "ARAC_YESIL_KART",
            "Araç yeşil kartı (uluslararası sigorta) eksik."))
    if not f.get("rez_yolcu_adlari_tam", True):
        s.append(Sorun("YUKSEK", "REZ_YOLCU_ADI",
            "Rezervasyonda tüm başvurucuların isimleri yer almıyor."))
    if not f.get("rez_tarih_tutarli", True):
        s.append(Sorun("YUKSEK", "REZ_TARIH",
            "Rezervasyon tarihleri başvuru formuyla tutarsız."))
    return s


def kontrol_konaklama(f: dict, konaklama: str) -> list[Sorun]:
    s = []
    if not f.get("konal_tum_isimler_var", True):
        s.append(Sorun("YUKSEK", "KONAL_ISIM",
            "Konaklama belgesinde tüm başvurucuların isimleri yer almıyor."))
    if konaklama == "davetiye":
        if not f.get("davet_renkli_cikti", True):
            s.append(Sorun("KRITIK", "DAVET_RENK",
                "Davetiye fotokopileri renkli çıktı olmalıdır — iDATA ofislerinde renkli çıktı hizmeti yoktur."))
        if not f.get("davet_oturma_izni_var", True):
            s.append(Sorun("YUKSEK", "DAVET_OTURMA",
                "Davet eden AB vatandaşı değilse oturma izni fotokopisi gereklidir."))
    return s


def kontrol_meslek(f: dict, meslek: str, bolge: str) -> list[Sorun]:
    s = []
    if not f.get("meslek_antelli_kagit", True):
        s.append(Sorun("KRITIK", "MESLEK_ANTET",
            "Meslek belgesi şirket/kurum antetli kağıda yazılmamış."))
    if not f.get("meslek_kase_imza", True):
        s.append(Sorun("KRITIK", "MESLEK_KASE",
            "Meslek belgesinde yetkili imzası ve kurum kaşesi eksik."))
    belge_yasi = f.get("meslek_belge_yasi_gun", 0)
    if belge_yasi > 90:
        s.append(Sorun("YUKSEK", "MESLEK_ESKI",
            f"Meslek belgesi {belge_yasi} günlük — belgeler 90 günden eski olmamalı."))
    # Faaliyet belgesi
    faaliyet_yasi = f.get("faaliyet_yasi_gun", 0)
    kaynak = f.get("faaliyet_kaynak", "resmi")
    max_gun = 30 if kaynak == "web" else 90
    if faaliyet_yasi > max_gun:
        aciklama = "Ticaret Odası web sitesinden e-imzalı belgeler 1 ay geçerlidir." if kaynak == "web" else "Belgeler 90 günden eski olmamalı."
        s.append(Sorun("YUKSEK", "FAALIYET_ESKI",
            f"Faaliyet belgesi {faaliyet_yasi} günlük — {aciklama}"))
    # İmza sirküleri (ankara hariç)
    if meslek in ("calisan", "isveren") and bolge != "ankara":
        if not f.get("imza_sirkuleri_var", True):
            s.append(Sorun("YUKSEK", "IMZA_SIRKULERI",
                f"İmza sirküleri {bolge.upper()} için zorunludur (Ankara Büyükelçiliği hariç)."))
    return s


def kontrol_muvafakatname(f: dict, meslek: str) -> list[Sorun]:
    s = []
    if not f.get("muv_noter_onayli", True):
        s.append(Sorun("KRITIK", "MUV_NOTER",
            "Muvafakatname noter onaylı değil."))
    if not f.get("muv_her_iki_ebeveyn", True):
        s.append(Sorun("KRITIK", "MUV_EBEVEYN",
            "Her iki ebeveynin muvafakatnamesi gerekli (boşanmış olsalar dahi)."))
    gun = f.get("muv_gecerlilik_gun", 0)
    if gun > 90:
        s.append(Sorun("KRITIK", "MUV_GECERLILIK",
            f"Muvafakatname {gun} günlük — noter onay tarihinden itibaren 3 ay geçerlidir."))
    if meslek == "cocuk" and not f.get("muv_apostille_var", True):
        s.append(Sorun("KRITIK", "MUV_APOSTILLE",
            "0-6 yaş çocuk başvurusunda muvafakatname çift apostille zorunludur."))
    return s


# ─── Skor Hesabı ──────────────────────────────────────────────────────────────

def hesapla_skor(sorunlar: list[Sorun]) -> float:
    skor = 1.0
    for s in sorunlar:
        if s.seviye == "KRITIK":  skor -= 0.40
        elif s.seviye == "YUKSEK": skor -= 0.20
        elif s.seviye == "ORTA":   skor -= 0.08
    return round(max(0.0, skor), 3)


# ─── Ana Kontrol Fonksiyonu ───────────────────────────────────────────────────

BELGE_ETIKETLERI = {
    "PASAPORT":      "Pasaport",
    "SIGORTA":       "Seyahat Sağlık Sigortası",
    "BANKA":         "Maddi Gelir / Banka Dökümü",
    "BASVURU_FORMU": "Başvuru Formu",
    "BILDIRGE":      "Seyahat Bildirgesi",
    "ULASIM":        "Ulaşım Rezervasyonu",
    "KONAKLAMA":     "Konaklama Belgesi",
    "MESLEK":        "Meslek & İş Belgesi",
    "MUVAFAKATNAME": "Muvafakatname",
}

def tam_kontrol(
    fields: dict,
    meslek: str,
    konaklama: str,
    ulasim: str,
    bolge: str,
    cocuklu: bool,
    seyahat_suresi: int = 7,
) -> dict:
    """
    Tüm belge kontrollerini çalıştırır.

    Returns
    -------
    {
      "belgeler": {belge_id: {"etiket", "sorunlar": [Sorun], "skor"}},
      "ozet": {"n_kritik", "n_yuksek", "n_orta", "ort_skor", "min_skor", "onay_olasiligi"}
    }
    """
    belgeler: dict[str, dict] = {}

    def ekle(bid, sorunlar):
        belgeler[bid] = {
            "etiket": BELGE_ETIKETLERI.get(bid, bid),
            "sorunlar": sorunlar,
            "skor": hesapla_skor(sorunlar),
        }

    ekle("PASAPORT",      kontrol_pasaport(fields))
    ekle("SIGORTA",       kontrol_sigorta(fields))
    ekle("BANKA",         kontrol_banka(fields, seyahat_suresi))
    ekle("BASVURU_FORMU", kontrol_form(fields))
    ekle("BILDIRGE",      kontrol_bildirge(fields))
    ekle("ULASIM",        kontrol_ulasim(fields, ulasim))
    ekle("KONAKLAMA",     kontrol_konaklama(fields, konaklama))

    if meslek not in ("ogrenci", "calismayanlar", "cocuk"):
        ekle("MESLEK", kontrol_meslek(fields, meslek, bolge))

    if cocuklu or meslek == "cocuk":
        ekle("MUVAFAKATNAME", kontrol_muvafakatname(fields, meslek))

    # Özet
    tum_sorunlar = [s for b in belgeler.values() for s in b["sorunlar"]]
    n_k = sum(1 for s in tum_sorunlar if s.seviye == "KRITIK")
    n_y = sum(1 for s in tum_sorunlar if s.seviye == "YUKSEK")
    n_o = sum(1 for s in tum_sorunlar if s.seviye == "ORTA")
    skorlar = [b["skor"] for b in belgeler.values()]
    ort = sum(skorlar) / len(skorlar)
    mn  = min(skorlar)

    # Onay olasılığı (kural tabanlı, ML öncesi)
    onay = max(0.02, min(0.97,
        ort * 0.45 + mn * 0.30 - n_k * 0.09 - n_y * 0.03 - n_o * 0.01
    ))

    return {
        "belgeler": belgeler,
        "ozet": {
            "n_kritik":        n_k,
            "n_yuksek":        n_y,
            "n_orta":          n_o,
            "ortalama_skor":   round(ort, 3),
            "min_skor":        round(mn, 3),
            "onay_olasiligi":  round(onay, 3),
        },
    }

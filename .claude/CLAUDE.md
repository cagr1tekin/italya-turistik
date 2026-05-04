# CLAUDE.md — İtalya Turistik Vize Platformu

## Projenin Amacı

İtalya Schengen turistik vize başvurucularına yönelik **kural tabanlı evrak listesi motoru** ve **model eğitim verisi üretim sistemi**. İDATA (it-tr-appointment.idata.com.tr) üzerinden alınan randevular için kişiye özel evrak listesi oluşturur. Uzun vadede AI destekli vize danışmanlık platformunun omurgasını oluşturacak.

**Kapsam:** Şu an yalnızca İtalya + Turistik. Modüler yapı sayesinde ileride diğer ülkeler ve amaçlar eklenecek.

---

## Proje Klasör Yapısı

```
italya-turistik/
├── .claude/
│   └── CLAUDE.md               ← Bu dosya (proje kuralları)
├── docs/
│   ├── idata_pdfs/             ← iDATA'dan indirilen örnek evrak listesi PDF'leri
│   └── references/             ← Strateji dokümanları (algoritma, design thinking, rapor, rehber)
├── engine/
│   ├── italy_tourist_rules.json ← TEK DOĞRULUK KAYNAĞI — kural motoru
│   └── document_engine.py       ← Python motoru (JSON'dan evrak listesi üretir)
└── data/
    ├── all_combinations.csv     ← 720 kombinasyon (generate_all_combinations ile üretilir)
    └── feature_matrix.csv       ← Binary evrak matrisi (model eğitimi için)
```

---

## Kombinasyon Matrisi

| Boyut | Değerler | Sayı |
|-------|----------|------|
| Meslek | calisan, isveren, serbest_meslek, emekli, ogrenci, memur, ciftci, calismayanlar, cocuk | 9 |
| Konaklama | otel, davetiye | 2 |
| Ulaşım | ucak, arac, otobus, gemi, tren | 5 |
| Bölge | ankara, istanbul, izmir, diger | 4 |
| Çocuklu | true, false | 2 |
| **TOPLAM** | | **720 kombinasyon** |

---

## Meslek Grupları (iDATA'nın Resmi 9 Kategorisi)

> **KRİTİK:** Bu listeler iDATA PDF örneklerinden doğrulandı (2026-04-30). Değiştirilmeden önce yeni PDF örnekleri ile karşılaştırılmalıdır.

| Kod | iDATA Adı | Özel Belge |
|-----|-----------|------------|
| `calisan` | Çalışan (SSK/Kadrolu) | 4a/4b Bağ-kur hizmet dökümü, maaş bordrosu |
| `isveren` | İş Veren | Faaliyet belgesi, Ticaret Sicil Gazetesi, 4b Bağ-kur |
| `serbest_meslek` | Serbest Meslek | Ticari/Mesleki Oda Kaydı (Baro, esnaf odası vb.) |
| `emekli` | Emekli | E-devlet/SGK barkodlu hizmet dökümü + kurum ıslak imzalı yazı |
| `ogrenci` | Öğrenci | Öğrenci belgesi (okul kaşeli veya e-devlet barkodlu) + Maddi Destekçi |
| `memur` | Memur | Kurum antetli, imza yetkilisi imzalı + **e-devlet uzun vade hizmet dökümü** |
| `ciftci` | Çiftçi | Ziraat odasından çiftçilik kazanç belgesi + barkodlu hizmet dökümü |
| `calismayanlar` | Çalışmayan Kişiler | Sadece maddi gelir + teminat + maddi destekçi evrakları |
| `cocuk` | Çocuk (0-6 yaş) | Çift apostille muvafakatname + maddi destekçi |

### Memur ≠ Çalışan (Önemli Fark)
- **Çalışan:** 4a Hizmet Dökümü + 4b Bağ-kur + İşe Giriş Bildirgesi
- **Memur:** E-devletten **UZUN VADE** barkodlu hizmet dökümü + kurum antetli maaş/görev belgesi (4a/4b yok)

---

## Ulaşım Araçları

| Kod | iDATA Adı | Özel Evrak |
|-----|-----------|------------|
| `ucak` | Uçak | Gidiş-dönüş uçuş rezervasyonu. Tur organizasyonunda ek: tur belgesi, programı, makbuzu |
| `arac` | Otomobil/Motorsiklet | Araç ruhsatı + yeşil kart + ehliyet |
| `otobus` | Otobüs | Otobüs bileti/rezervasyonu |
| `gemi` | Gemi/Tekne | Gemi turu: güzergah + rezervasyon. Tekne: tonilato, sigorta, kaptanlık belgesi |
| `tren` | Tren/İnterrail | İnterrail orijinal + fotokopi. AB geçişleri rezervasyonla desteklenmeli |

> **NOT:** `tur_organizasyonu` artık bağımsız bir ulaşım tipi değildir. Uçak ile seyahatte tur seçilmişse ek evraklar ucak kuralına dahildir.

---

## Konaklama Türleri

| Kod | iDATA Adı | Özel Evrak |
|-----|-----------|------------|
| `otel` | Otel vb. | Otel rezervasyonu (tüm başvurucuların isimleri dahil) |
| `davetiye` | Davetiye | Davet mektubu + ev sahibi kimlik/oturma izni fotokopisi (**RENKLİ ÇIKTI ZORUNLU**) |

### Davetiye Özel Notları
- Fotokopiler **renkli çıktı** olmalıdır — iDATA ofislerinde renkli çıktı hizmeti yoktur
- İzmir Konsolosluğu: Uzun süreli ilişki (nişan/arkadaşlık) durumunda ek belge + "Uzak mesafe ilişki" formu gereklidir

---

## Bölge Farklılıkları

### Ankara (Büyükelçilik)
- İmza sirküleri **gerekmez** (çalışan, memur, emekli, çiftçi, isveren, serbest meslek için)
- Tur organizasyonunda **e-fatura zorunlu** + ödeme dekontu/ekstresi
- Çocuk üçüncü şahısla seyahatte **noter taahhütname zorunlu**
- Birinci derece dışında akraba **sponsorluğu kabul edilmez**

### İstanbul (Başkonsolosluğu)
- Tel: 0850 460 0849 (TR) / +90 212 970 8493 (yurt dışı)
- Randevu: Çalışma günleri 08:30-13:00 / 13:30-17:30
- İmza sirküleri **gereklidir** (çalışan, isveren)
- Birinci derece dışında akraba sponsorluğu kabul edilmez

### İzmir (Konsolosluk)
- Randevu: Konsolosluk mail adresi ile
- İmza sirküleri **gereklidir**
- Davetiye + uzun süreli ilişki → "Uzak mesafe ilişki" formu
- Ebeveyn sponsor: her iki ebeveyn gelir evrakı gerekli; diğer akraba → noter taahhütname

---

## Maddi Destekçi Evrakları (Önemli Kural)

Şu meslek gruplarında **Maddi Destekçi Evrakları** zorunludur:
- `ogrenci` — ebeveyn sponsor
- `calismayanlar` — eş veya ebeveyn sponsor
- `cocuk` (0-6 yaş) — ebeveyn sponsor

**Kritik:** Masrafları karşılayacak eş/ebeveynler **kendileri başvurmasa bile** tüm çalışma ve gelir evraklarını eksiksiz ibraz etmek durumundadır.

---

## Çocuklu Seyahat Kuralları

- Her çocuk için **ayrı başvuru formu** doldurulmalıdır
- Her iki ebeveyn imzası zorunludur
- Muvafakatname: **noter onaylı**, 3 ay geçerli
- 12 yaş altı: ofise gelme zorunluluğu yok
- 12 yaş üstü: ebeveyn/yetkilendirilmiş kişi eşliğinde ofise gelme zorunlu
- Çocuk (0-6 yaş) kategorisi: muvafakatname **çift apostille** zorunludur

---

## JSON Kural Dosyası (`engine/italy_tourist_rules.json`)

### Güncelleme Kuralları
1. JSON dosyası **tek doğruluk kaynağıdır** — asla document_engine.py içine hardcode evrak eklenmez
2. Yeni evrak eklemeden önce `docs/idata_pdfs/` altındaki PDF ile doğrulanmalıdır
3. Her güncelleme sonrası `meta.versiyon` ve `meta.guncelleme` güncellenmelidir
4. `generate_all_combinations()` ve `get_feature_matrix()` çalıştırılarak `data/` klasörü yenilenmelidir

### Veri Yapısı Hiyerarşisi
```
standart_evraklar       → her kombinasyonda zorunlu (9 evrak)
ulasim_kurallari        → ulaşım tipine göre (1-3 evrak)
konaklama_kurallari     → konaklama tipine göre (1-2 evrak)
meslek_kurallari        → meslek grubuna göre (2-4 evrak)
cocuklu_seyahat_kurallari → cocuklu=True ise (3 evrak)
```

---

## Python Motor Kuralları

### `get_document_list()` Parametreleri
```python
get_document_list(
    meslek: str,     # ['calisan','isveren','serbest_meslek','emekli','ogrenci','memur','ciftci','calismayanlar','cocuk']
    konaklama: str,  # ['otel', 'davetiye']
    cocuklu: bool,   # True/False
    ulasim: str,     # ['ucak', 'arac', 'otobus', 'gemi', 'tren']
    bolge: str,      # ['ankara', 'istanbul', 'izmir', 'diger']
)
```

### Kombinasyon Kodu Formatı
`IT_TUR_{MESLEK}_{ULASIM}_{KONAKLAMA}_{BOLGE}_{COCUKLU/COCUKSUZ}`

Örnek: `IT_TUR_MEMUR_TREN_DAVETIYE_ISTANBUL_COCUKLU`

---

## Model Eğitimi Hedefleri

### feature_matrix.csv Sütunları
- Kimlik sütunları: `kombinasyon_kodu`, `meslek`, `konaklama`, `ulasim`, `bolge`, `cocuklu`
- Evrak sütunları: `DOC_{EVRAK_ID}` → 1 (var) / 0 (yok)

### Kullanım Senaryoları
1. **Eksik Evrak Tespiti:** Başvurucunun beyan ettiği evraklar ile beklenen liste karşılaştırılır
2. **doc_completeness_score:** Kaç evrak tamamlandı / toplam evrak sayısı
3. **Hata Tespiti:** Yanlış kategori seçimi tespiti (örn. memur yerine çalışan seçilmesi)

---

## Hedef Sistem Mimarisi — PDF Tabanlı AI Değerlendirme

### Vizyon
Kullanıcı başvuru bilgilerini girer ve evraklarını PDF olarak yükler. Sistem her evrakı otomatik olarak analiz eder, eksik/hatalı alanları tespit eder ve başvurunun onay olasılığını puanlar. **Her istek için Claude API kullanılmaz** — bunun yerine eğitilmiş bir lokal model kullanılır.

### Neden Claude API Değil?
| Claude API (Her İstekte) | Eğitilmiş Model |
|---|---|
| %70-90 tutarlılık, hallucination riski | Deterministik, kurallar sabit |
| Her istek = maliyet | Tek seferlik eğitim maliyeti |
| API latency (1-3 sn) | Milisaniyeler |
| PDF okuma kabiliyeti değişken | Kontrollü feature extraction |

### Akış

```
Kullanıcı: başvuru bilgileri (meslek, bölge vb.) + PDF'ler
    ↓
[1] PDF Text Extraction
    pdfplumber / PyMuPDF ile metin çıkarımı
    "Pasaport No: TR... Geçerlilik: 2028-03-15 Boş Sayfa: 4"
    ↓
[2] Feature Extraction (regex + NLP)
    Her belge türü için belirlenmiş alanlar çıkarılır
    {pas_gecerlilik_gun: 720, pas_bos_sayfa: 4, sig_teminat_eur: 30000, ...}
    ↓
[3] Eğitilmiş Model (scikit-learn / XGBoost)
    feature_matrix.csv + gerçek etiketlerle eğitilmiş classifier
    → per-belge skor (0.0 - 1.0) + onay_olasiligi
    ↓
[4] rule_checker.py (kural doğrulama katmanı)
    Model çıktısı üzerine deterministic kurallar çalışır
    → KRITIK / YUKSEK / ORTA seviye uyarılar
    ↓
[5] Sonuç Raporu
    Hangi evrak okey, hangi evrakta ne eksik, genel onay skoru
```

### Mevcut Altyapının Bu Mimariyle İlişkisi

`mock_rich_v3.csv`'deki feature sütunları (pas_gecerlilik_gun, sig_teminat_eur vb.) zaten **"PDF'den çıkarılacak alanlar"** olarak tasarlanmıştır. Yani:
- **[1-2] PDF extraction** → mock verideki sütunları gerçek belgeden doldurur
- **[3] Model** → bu sütunları girdi alır, `etiket` (Onay/Ret) tahmin eder
- **[4] rule_checker.py** → şu anki yapısı korunur, girdiyi artık kullanıcı değil extraction katmanı sağlar

### Feature Extraction — Belge Türü Başına Çıkarılacak Alanlar

| Belge | Çıkarılacak Alanlar | Yöntem |
|-------|---------------------|--------|
| Pasaport | geçerlilik tarihi, boş sayfa sayısı | regex (tarih pattern) |
| Sigorta poliçesi | teminat tutarı (EUR), kapsam tarihleri, Schengen ibaresi | regex + keyword |
| Banka dökümü | düzenleme tarihi, kaşe/imza varlığı, bakiye, 6 aylık trend | regex + NLP |
| Faaliyet belgesi | düzenleme tarihi, kurum kaşesi, kaynak türü (web/resmi) | regex + keyword |
| Muvafakatname | noter tarihi, apostille varlığı, her iki ebeveyn imzası | keyword search |

### Geliştirme Aşamaları

**Faz 1 — PDF Extraction Modülü**
- [ ] `engine/pdf_extractor.py` oluştur
- [ ] Her belge türü için ayrı extraction fonksiyonu yaz (pasaport'tan başla)
- [ ] Gerçek PDF'lerle test et, regex pattern'lerini doğrula
- [ ] Çıktı formatı: `mock_rich_v3.csv` ile birebir uyumlu feature dict

**Faz 2 — Model Eğitimi**
- [ ] Gerçek başvuru sonuçlarını topla (onay/ret etiketleri)
- [ ] `mock_rich_v3.csv` şablonunu gerçek veriyle doldur
- [ ] XGBoost / RandomForest classifier eğit
- [ ] Cross-validation ile doğruluk ölç
- [ ] `engine/model/` altına kaydet

**Faz 3 — Entegrasyon**
- [ ] Web arayüzüne PDF upload ekle
- [ ] extraction → model → rule_checker pipeline'ını bağla
- [ ] Per-belge skor + genel onay raporu UI'ına ekle

### Kritik Tasarım Kararları
- **rule_checker.py silinmez:** Model yanlış tahmin etse bile deterministic kurallar arka planda çalışır, çelişki varsa kural kazanır
- **Her belge türü ayrı extraction fonksiyonu:** Pasaport PDF'si ile banka dökümü PDF'si tamamen farklı yapıda — tek genel parser yazmak hata kaynağı olur
- **PDF'ler sunucuda saklanmaz:** Privacy açısından extraction yapıldıktan sonra PDF silinir, yalnızca feature dict tutulur

---

## Geliştirme Öncelikleri

1. [ ] `generate_all_combinations()` çalıştırılarak `data/` güncellenecek
2. [ ] Emeklilik belgesi teminat tutarları iDATA'dan alınacak ve JSON'a eklenecek
3. [ ] `engine/pdf_extractor.py` — pasaport extraction'dan başla (Faz 1)
4. [ ] Test suite: her kombinasyon için beklenen evrak sayısı doğrulama
5. [ ] Gerçek başvuru verisi toplandığında model eğitimi başlat (Faz 2)
6. [ ] Gelecek: Almanya vize modülü (modüler yapıya uygun)

---

## Kritik Uyarılar

- **iDATA sistemi değişebilir:** PDF örnekleri düzenli kontrol edilmelidir (önerilen: aylık)
- **Teminat tutarları eksik:** İtalya İçişleri Bakanlığı tutarları JSON'a eklenmemiştir, harici kaynak gerektirir
- **Çocuk kategorisi farklı:** `cocuk` meslek grubu (0-6 yaş kendi başvurusu) ile `cocuklu=True` parametresi (yetişkinle gelen çocuk) farklı şeylerdir — karıştırılmamalıdır
- **Davetiye fotokopileri:** Mutlaka renkli çıktı olmalıdır, bu iDATA'nın özel koşuludur
- **Memur hizmet dökümü:** 4a/4b Bağ-kur değil, e-devletten "uzun vade" hizmet dökümüdür

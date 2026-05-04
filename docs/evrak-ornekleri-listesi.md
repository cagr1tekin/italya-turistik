# Evrak Örnekleri — PDF Toplama Listesi

Tüm 720 kombinasyondaki benzersiz evrak türleri. PDF extraction modülü geliştirme sürecinde örnek belge bulmak için kullanılır.

Toplam: **38 benzersiz evrak türü** (fiziksel olarak ~25-30 farklı PDF formatı)

---

## 1. Kimlik & Kişisel Belgeler

| # | Evrak | JSON ID | Notlar |
|---|-------|---------|--------|
| 1 | Pasaport | `PASAPORT` | Tüm kombinasyonlarda zorunlu. Kişisel bilgiler + tüm vize/damga sayfaları |
| 2 | TC Nüfus Cüzdanı fotokopisi | `KIMLIK_FOTOKOPI` | Tüm kombinasyonlarda zorunlu. TC kimlik no görünür olmalı |
| 3 | Tarihçeli Yerleşim Yeri Belgesi | `TARIHCELI_YERLESIM_YERI` | e-devlet çıktısı, barkodlu |
| 4 | Tam Vukuatlı Nüfus Kayıt Örneği | `VUKUATLI_NUFUS` | e-devlet çıktısı, barkodlu |

---

## 2. Başvuru Formları & Dilekçeler

| # | Evrak | JSON ID | Notlar |
|---|-------|---------|--------|
| 5 | Vize Başvuru Formu | `BASVURU_FORMU` | Schengen formu (≤90 gün) veya Ulusal form (>90 gün). İmzalı ve tarihli |
| 6 | Seyahat Bildirge / Dilekçe | `SEYAHAT_BILDIRGE` | Aylık gelir beyanı + birlikte seyahat edecekler + vize fotokopisi dahil |
| 7 | Çocuğa Ayrı Başvuru Formu | `COCUK_BASVURU_FORMU` | Sadece cocuklu=True kombinasyonlarında. Her iki ebeveyn imzalı |

---

## 3. Sigorta & Finansal Belgeler

| # | Evrak | JSON ID | Notlar |
|---|-------|---------|--------|
| 8 | Seyahat Sağlık Sigortası Poliçesi | `SEYAHAT_SAGLIK_SIGORTASI` | Min 30.000 EUR, tüm Schengen kapsamlı, gidiş-1 gün / dönüş+1 gün kapsam |
| 9 | Banka Hesap Dökümü + Hesap Cüzdanı | `MADDI_GELIR_CALISAN` `MADDI_GELIR_ISVEREN` `MADDI_GELIR_SERBEST` `MADDI_GELIR_EMEKLI` `MADDI_GELIR_OGRENCI` `MADDI_GELIR_MEMUR` `MADDI_GELIR_CIFTCI` `MADDI_GELIR_CALISMAYANLAR` | 8 farklı ID ama **aynı PDF formatı**. Son 6 aylık, kaşeli/imzalı. Son 15 günde düzenlenmiş hesap cüzdanı aslı |
| 10 | Teminat Belgesi | `TEMINAT` | İtalya İçişleri Bakanlığı tutarlarına göre finansal yeterlilik |

---

## 4. Ulaşım Belgeleri

| # | Evrak | JSON ID | Notlar |
|---|-------|---------|--------|
| 11 | Uçuş Rezervasyonu | `UCUS_REZERVASYONU` | Gidiş-dönüş, tüm yolcu isimleri dahil, tarihler açık |
| 12 | Araç Ruhsatı | `ARAC_RUHSATI` | Sadece arac kombinasyonu. Seyahat güzergah yazısıyla birlikte |
| 13 | Uluslararası Araç Sigortası (Yeşil Kart) | `ARAC_SIGORTASI` | Sadece arac kombinasyonu. Seyahat süresini kapsamalı |
| 14 | Ehliyet | `EHLIYET` | Sadece arac kombinasyonu |
| 15 | Otobüs Bileti / Rezervasyonu | `OTOBUS_BILETI` | Seyahat firması çıktısı, seyahat detaylarını içermeli |
| 16 | Gemi / Tekne Seyahat Belgesi | `GEMI_BELGESI` | Gemi turu: güzergah + rezervasyon. Tekne: tonilato, sigorta, kaptanlık belgesi |
| 17 | Tren / İnterrail Bileti | `TREN_BILETI` | İnterrail orijinal + fotokopi. AB geçişleri rezervasyonla desteklenmeli |

---

## 5. Konaklama Belgeleri

| # | Evrak | JSON ID | Notlar |
|---|-------|---------|--------|
| 18 | Otel Rezervasyonu | `OTEL_REZERVASYONU` | Tüm başvurucu isimleri dahil. İptal edilebilir rezervasyon kabul edilir |
| 19 | Davet Mektubu | `DAVET_MEKTUBU` | İtalya'daki ev sahibinden, adres ve iletişim bilgileri içermeli |
| 20 | Ev Sahibinin Kimlik / Oturma İzni | `EV_SAHIBI_KIMLIK` | AB vatandaşı değilse oturma izni fotokopisi. **RENKLİ ÇIKTI ZORUNLU** |

---

## 6. Meslek Belgeleri

| # | Evrak | JSON ID | Kimin İçin | Notlar |
|---|-------|---------|------------|--------|
| 21 | Çalışma & İzin Belgesi (Çalışan) | `CALISMA_IZIN_BELGESI` | calisan | Şirket antetli + işveren imzalı izin yazısı. Barkodlu 4b Bağ-kur hizmet dökümü |
| 22 | Çalışma Evrakları (Çalışan) | `CALISMA_EVRAKLARI` | calisan | İşe giriş bildirgesi + barkodlu 4a hizmet dökümü + son 3 ay maaş bordrosu |
| 23 | İmza Sirküleri | `IMZA_SIRKULERI_CALISAN` `IMZA_SIRKULERI_ISVEREN` | calisan, isveren | **Aynı belge, 2 ID**. Şahıs şirketinde imza beyannamesi. Ankara'da zorunlu değil |
| 24 | Faaliyet Belgesi | `FAALIYET_BELGESI` | isveren | Son 3 ay içinde alınmış. Web'den e-imzalı ise 1 ay geçerli |
| 25 | Ticaret Sicil Gazetesi | `TICARET_SICIL_GAZETESI` | isveren | Faaliyetin güncel yapısını gösterir fotokopi |
| 26 | Vergi Levhası | `VERGI_LEVHASI_ISVEREN` `VERGI_LEVHASI_SERBEST` | isveren, serbest_meslek | **Aynı belge, 2 ID** |
| 27 | Çalışma & İzin Belgesi (İşveren) | `CALISMA_IZIN_BELGESI_ISVEREN` | isveren | Şirket antetli seyahat dilekçesi + barkodlu 4b Bağ-kur hizmet dökümü |
| 28 | Ticari / Mesleki Oda Kaydı | `TICARI_ODA_KAYDI` | serbest_meslek | Baro kaydı, esnaf odası, ziraat odası vb. Son 3 ay |
| 29 | Emeklilik Belgesi / SGK Hizmet Dökümü | `EMEKLILIK_BELGESI` | emekli | e-devlet/SGK barkodlu hizmet dökümü + kurumdan ıslak imzalı kaşeli yazı |
| 30 | Öğrenci Belgesi | `OGRENCI_BELGESI` | ogrenci | Okul kaşeli/imzalı veya e-devlet barkodlu. Son 3 ay |
| 31 | Çalışma & İzin Belgesi (Memur) | `CALISMA_IZIN_BELGESI_MEMUR` | memur | Kurum antetli, imza yetkilisi imzalı, kaşeli görev belgesi + e-devlet **UZUN VADE** barkodlu hizmet dökümü (4a/4b Bağ-kur değil) |
| 32 | Çiftçilik Belgesi | `CIFTCILIK_BELGESI` | ciftci | Ziraat odasından güncel tarihli çiftçilik kazanç belgesi + barkodlu hizmet dökümü |

---

## 7. Maddi Destekçi Belgeleri

| # | Evrak | JSON ID | Kimin İçin | Notlar |
|---|-------|---------|------------|--------|
| 33 | Maddi Destekçi Evrakları (Öğrenci) | `MADDI_DESTEKCI_OGRENCI` | ogrenci | Ebeveyn gelir evrakları + taahhüt mektubu + nüfus kaydı (ebeveyn-çocuk ilişkisini gösterir) |
| 34 | Maddi Destekçi Evrakları (Çalışmayan) | `MADDI_DESTEKCI_CALISMAYANLAR` | calismayanlar | Eş/ebeveyn tüm çalışma ve gelir evrakları. Bölgeye göre ek kural (İzmir: her iki ebeveyn) |
| 35 | Maddi Destekçi Evrakları (Çocuk) | `MADDI_DESTEKCI_COCUK` | cocuk (meslek grubu) | Ebeveyn gelir evrakları + maddi yükümlülük taahhüt mektubu |

---

## 8. Çocuk Belgeleri

| # | Evrak | JSON ID | Notlar |
|---|-------|---------|--------|
| 36 | Muvafakatname (Çocuklu Yetişkin) | `MUVAFAKATNAME` | cocuklu=True kombinasyonları. Her iki ebeveynden noter onaylı. 3 ay geçerli |
| 37 | Muvafakatname (Çocuk Kategorisi) | `MUVAFAKATNAME_COCUK` | cocuk meslek grubu (0-6 yaş kendi başvurusu). **ÇİFT APOSTİLLE ZORUNLU**: noter → apostille → İtalyanca tercüme → tekrar apostille |
| 38 | Doğum Belgesi / Nüfus Kayıt Belgesi | `DOGUM_BELGESI` | cocuklu=True. Formül A veya ebeveynlik ilişkisini gösteren nüfus kaydı |

---

## Özet Tablosu

| Kategori | Benzersiz Tür | Fiziksel PDF |
|----------|--------------|--------------|
| Kimlik & Kişisel | 4 | 4 |
| Formlar & Dilekçeler | 3 | 3 |
| Sigorta & Finansal | 3 | 2 (banka dökümü tek format) |
| Ulaşım | 7 | 7 |
| Konaklama | 3 | 3 |
| Meslek | 12 | 10 (imza sirküleri ve vergi levhası birer format) |
| Maddi Destekçi | 3 | 1 (aynı format, farklı kişiler) |
| Çocuk | 3 | 3 |
| **Toplam** | **38** | **~33** |

---

## Öncelik Sırası (PDF Extraction Geliştirme İçin)

Tüm kombinasyonlarda geçen ve extraction'da en kritik alanları olan belgeler önce ele alınmalı:

1. **Pasaport** — geçerlilik tarihi, boş sayfa sayısı (regex ile çıkarılabilir)
2. **Seyahat Sağlık Sigortası** — teminat tutarı (EUR), kapsam tarihleri, Schengen ibaresi
3. **Banka Hesap Dökümü** — düzenleme tarihi, bakiye, kaşe/imza varlığı, 6 aylık trend
4. **Faaliyet Belgesi** — düzenleme tarihi, kaynak türü (web/resmi)
5. **Muvafakatname** — noter tarihi, apostille varlığı

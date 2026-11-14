# Rölöve Kroki Uygulaması – Proje Notları

Bu dosya projenin hafızasıdır. Yeni bir sohbette veya Claude Code'da işe bu dosyayı okutarak başlanır.

## 1. Amaç

Bina içi rölöve için telefonda çalışan bir kroki uygulaması:
- Bosch lazer metreden ölçüyü Bluetooth ile alıp seçili çizgiye yazmak
- Gönyesizliği çapraz ölçülerle dengelemek
- Total/GPS noktalarıyla birleştirip ülke koordinatına oturtmak
- NetCAD/AutoCAD'e ölçekli DXF vermek

## 2. Donanım

- **Lazer metre:** Bosch GLM 50-27 CG Professional (Li-ion, sipariş kodu 0 601 072 U01)
- **Telefon:** iPhone (iOS). Android'de de çalışmalı.
- **Uyarı:** Bosch MeasureOn'un önerdiği firmware güncellemelerini yükleme. Protokol değişebilir.

## 3. Bosch BLE protokolü (14.11.2026'da nRF Connect ile doğrulandı)

- **Servis:** `02A6C0D0-0451-4000-B000-FB3210111989`
- **Karakteristik:** `02A6C0D1-0451-4000-B000-FB3210111989` (Write, Indicate)

**Bağlantı adımları**
1. Cihaza bağlan.
2. 02A6C0D1 için indication aboneliğini aç.
3. 02A6C0D1'e şu komutu yaz: `C0 55 02 01 00 1A` (otomatik ölçüm gönderimini açar).
4. Lazerde her ölçümde bir indication paketi gelir.

**Ölçüm paketi örneği** (lazer ekranı 0.951 m):
```
C0 55 10 06 00 0A 00 4A 7B 73 3F 00 00 00 00 00 00 00 00 00 66
```
- `C0 55`: ölçüm paketi başlığı
- `10`: veri uzunluğu (16 bayt)
- `06 00 0A 00`: anlamı henüz bilinmiyor (mod veya referans olabilir)
- **Bayt 7–10:** `4A 7B 73 3F`. float32, little-endian, birim metre → 0.9511
- Son bayt `66`: CRC

**Diğer paketler**
- `C0 11 00 3A`: durum veya onay mesajı. Görmezden gel.

**İkinci servis:** `02A6C0F0-…` (F1, F2: write/notify, F3: write, F4: read/notify). Amacı bilinmiyor.

**Açık soru:** Eğim açısı Bluetooth ile geliyor mu? Bilinmeyen baytları farklı modlarda ölçüm yaparak incele.

## 4. Platform kararları

- Tek sayfalık web uygulaması (PWA): HTML + JavaScript, sunucu yok. Veriler telefonda (IndexedDB) tutulur, JSON olarak yedeklenir.
- Çevrimdışı çalışır (service worker).
- Yayın: GitHub Pages. Web Bluetooth HTTPS gerektiriyor.
- **iPhone:** Bluefy tarayıcısı (Safari'de Web Bluetooth yok). **Android:** Chrome.
- **İleride:** ESP32 köprüsü. Bosch'a BLE ile bağlanır, telefona Bluetooth klavye (HID) gibi değer yazar. Böylece düz Safari'de de çalışır.

## 5. Koordinat dosyası formatı (NCN)

- Boşlukla ayrılmış, ondalık ayırıcı nokta, 3 ondalık hane
- Sütun sırası: **Ad Y X Z** (Y = sağa değer ~5xxxxx, X = yukarı değer ~4xxxxxx)
- Nokta adları harf ve numara: `B1`, `B2`… Ayrı kod sütunu yok, kod adın içinde.
- Aynı köşe 2–3 kez ölçülebiliyor (birbirine 2–4 cm yakın noktalar). Ortalama alma seçeneği olmalı.

Örnek (uydurma değerler):
```
B1 500100.000 4100200.000 6.100
B2 500106.200 4100193.400 6.120
```

**Koordinat sistemi:** ITRF96, 3° TM. Dilim: **(kullanıcıdan öğrenilecek)**

## 6. DXF kuralları

- 1:1 çizim, model alanı, birim metre
- Format R12 veya 2000, Türkçe karakterler için kod sayfası ANSI_1254
- Ölçek (1/50, 1/100) yalnızca yazı ve ölçü boyunu belirler
- Katmanlar (kesinleşmedi): DUVAR, KOLON, KAPI, PENCERE, OLCU, NOKTA, NOKTA_ADI, KOT, YAZI

## 7. Aşamalı plan

**Aşama 1 – Çekirdek**
- Bosch bağlantısı, otomatik yeniden bağlanma, ölçü gelince ses ve titreşim
- Duvar takip modu: lazerle uzunluk, ±90° veya elle açı girerek dönme
- Çizgi seç → ölç → değer yazılır → sonraki çizgiye geçilir
- Büyüteç, snap, geri al/yinele, yakınlaştırma ve kaydırma, elle ölçü girişi
- Projeyi kaydetme, JSON yedek, DXF çıktısı
- Test: bir oda çizilir, DXF NetCAD'de doğru açılır.

**Aşama 2 – Gönyesizlik ve dengeleme**
- Nokta adları, çapraz ölçüler
- En küçük kareler dengelemesi, kapanma hatası, tolerans uyarısı
- Gerçek açıların yazılması, eksik çaprazın bildirilmesi
- Birden fazla oda, ortak duvarlar, duvar kalınlığı

**Aşama 2 – Ölçü kuralları (14.11.2026 kroki testinden)**
- n köşeli kapalı şekil için **2n − 3 ölçü** gerekir. n kenar ölçülünce **n − 3 çapraz zorunlu**, +1 çapraz kontrol için.
- Kapı sövesi, niş köşesi ve kolon köşesi de **köşe sayılır**.
- **Kenar ölçüleri gönyeyi asla göstermez.** Test: kenarları doğru olan bir oda aslında 1,49 m kayık bir paralelkenardı (açılar 73,4° ve 106,6°).
- **Kenar boyu, duvardaki kırığa duyarsızdır.** 8 m'lik duvarda 10 cm kırık, boyu sadece 0,6 mm uzatır. Söve gibi ara noktalar ancak karşı köşeden çaprazla sabitlenir.
- Yay ya da eğri duvar: kiriş + sehim (kirişin ortasından yaya dik mesafe) veya yay üstünde bir nokta.
- Odalar arası bağlantı: söve derinliği (duvar kalınlığı), iki taraftan kapı genişliği ve kapıdan geçen en az bir çapraz.

**Aşama 2 – Sihirbaz akışı**
1. **Kroki girişi:** Köşelere sırayla dokunulur. Program noktaları adlandırır (S1, S2…) ve "N köşe, 2N−3 ölçü gerekli" yazar.
2. **Kenar sırası:** Ölçülecek kenarı vurgular. Lazer ölçüsü gelince sonrakine geçer. Parçalı duvarlarda (kapı, pencere) köşeden köşeye toplam boyu da kontrol olarak ister.
3. **Durum çubuğu:** "Kenarlar tamam. Şekil belirsiz, K çapraz zorunlu."
4. **Çapraz önerisi:** En sağlam üçgeni verecek çaprazı yanıp sönerek gösterir (sivri üçgenlerden kaçınır). Sövelere karşı köşeden çapraz önerir.
5. **Gönye kontrolü (ilk çaprazdan sonra):** Köşe açılarını hesaplar, dik varsayımla beklenen çaprazı ölçülenle karşılaştırır.
   - "✅ Gönyeli. En büyük sapma 0,05° (4 mm). Kontrol çaprazı isteğe bağlı."
   - "⚠️ Gönyesiz. S1 köşesi 106,6° (+16,6°). İkinci çaprazı ölç."
6. **Kontrol çaprazından sonra:** En küçük kareler dengelemesi.
   - "✅ Kapanma 2 mm, kabul."
   - "❌ Kapanma 4 cm. En şüpheli ölçü S2–S3 (en büyük artık), tekrar ölç."
7. **Ara nokta uyarısı:** "K1 sövesi sabitlenmedi. S4 → K1 çaprazını ölç." Kullanıcı "düz duvar varsay" diyebilir. Bu durumda nokta kırmızı "varsayım" olarak işaretlenir.
8. **Oda bağlantısı:** "Salon ile yatak odası bağlı değil. Kapı derinliğini ve kapıdan geçen bir çaprazı ölç."
9. **Son rapor:** Ölçülmemiş veya varsayılmış her şey listelenir ve DXF'te VARSAYIM katmanına yazılır. İstenirse eski kroki ESKI_CIZIM katmanında karşılaştırma için durur.

**Aşama 2 – İstasyon modu (alternatif ölçü yöntemi)**

A) Köşe istasyonu: bir köşeden diğer tüm köşelere mesafe ölçülür, ayrıca tüm kenarlar.
- Bilinmeyen 2n−3, ölçü n kenar + (n−3) radyal = 2n−3. **Kontrol yok**, istasyon dışından 1 ek çapraz zorunlu.
- İstasyonun bulunduğu duvardaki ara noktalar (söve vb.) zayıf belirlenir, çünkü mesafe duvar boyunca gider. Program bunlar için başka köşeden ölçü ister.
- Tüm köşeler görünmüyorsa (L oda) ikinci istasyon kurulur. İki istasyon en az 2 ortak köşe görmeli.

B) Serbest istasyon (önerilen): lazer sehpada, referans sehpa vidası (diş merkezi), oda ortasında.
- Tüm köşelere radyal ölçü ve tüm kenarlar. Bilinmeyen 2n−1, ölçü 2n → **kendiliğinden 1 kontrol**.
- Cihazı köşeye oturtma sorunu yok. Ortadan iyi geometri, sivri üçgen yok.

Programda:
- Başlarken istasyon tipi seçilir: köşe veya sehpa.
- Her ölçüde krokide hedef köşeye dokunulur, ölçü o noktaya bağlanır.
- Çözüm trilaterasyon + kenarlar ile, en küçük kareler. Raporlar: gönye, kapanma, zayıf noktalar ("K1 istasyon duvarında, S3'ten ölç").
- Ayna (simetrik) çözüm belirsizliği kaba krokiden çözülür.
- İleride ESP32 açı istasyonu ile radyallere yatay açı da eklenir.

**Ölçü tipi ve referans düzeltmeleri**
- Her ölçü bir tiple kaydedilir: yüzeyden, köşe ucuyla (+sabit uç boyu), sehpadan (vida merkezi). Program gereken sabiti ekler.
- Kenar ölçümü: cihazı iç köşeye sokma. Sırtını dik duvara düz dayayıp köşeden 2–3 cm içeride, duvara paralel ölç. 1° gönyesizlikte hata yaklaşık 0,4 mm.
- İç köşe iyi bir hedeftir. **Dış köşe (kolon, çıkıntı) tehlikeli bir hedeftir**, nokta kayarsa arkadaki duvara gider. Dış köşeye kart veya gönye tutularak nişan alınır. Program dış köşe hedeflerinde uyarı verir.
- İç köşeden ölçmek şartsa: Bosch'un referans ayarı (arka kenar, ön kenar, sehpa vidası; kılavuzdan doğrulanacak) veya 3D baskı sivri köşe ucu (sabit uzunluk, uygulamada ayarlanır).

**Dairede saha prosedürü**
1. Kaba kroki: odalar, kapılar, pencereler, kolonlar, nişler. Oda harfleri ve saat yönünde köşe numaraları.
2. Başlangıç odası: diğer odalara kapısı açılan yer (koridor veya salon).
3. Her odada kenarlar: köşeden köşeye. Parçalı duvarlar parça parça ve toplam boy olarak.
4. Her odada çaprazlar: n−3 zorunlu + 1 kontrol, ayrıca sövelere çaprazlar.
5. Özel elemanlar: kolon (2 kenar + iki köşeden 2 mesafe), yay (kiriş + sehim), niş.
6. Yükseklikler: net tavan, kapı, pencere parapeti ve lentosu.
7. Odaları bağla: söve derinliği, kapı genişliği, kapıdan geçen çapraz. Dış duvar kalınlığı pencere sövesinden.
8. Genel kontrol: daire boyunca uzun bir ölçü.
9. Koordinat (gerekirse): total veya GPS ile 3–4 bina köşesi, sonra Helmert.
10. Her duvarın fotoğrafı.

**Aşama 3 – Detaylar**
- Kapı, pencere, niş ve kolon şablonları (köşeden mesafe, genişlik, parapet, lento)
- Kat yüksekliği, kotlar, oda adı ve alanı, otomatik ölçü çizgileri
- Fotoğraf ve not ekleme

**Aşama 4 – Koordinat entegrasyonu**
- NCN/CSV içe aktarma, tekrarlı noktaların ortalanması
- Helmert dönüşümü (en az 2–3 ortak nokta) ve artık hata raporu
- Kodlu noktalardan otomatik çizim ("acil iş" akışı)
- Ülke koordinatında DXF ve NCN çıktısı

**Aşama 5 – Üçgenleme ve dolaylı ölçüm**
- Trilaterasyon, eğimle dolaylı yükseklik, uzatma ve ofset ölçüleri

**Aşama 6 – Altlık ve cephe**
- Fotoğraf veya LiDAR kesiti altlığı (2 noktayla ölçekleme)
- Cephe fotoğrafını 4 noktayla düzleme

**Aşama 7 – Opsiyonel donanım**
- ESP32 açı istasyonu: AS5048A enkoder ve DFRobot SEN0366 lazer modülü, klavye köprüsü, kalibrasyon

## 8. Açık sorular

- [ ] 3° TM dilimi
- [ ] Katman adları ve renkleri, yazı boyları
- [ ] Nokta kodlama listesi (B = bina, …)
- [ ] Kapanma toleransı (öneri: 2 cm)
- [ ] GitHub hesabı ve depo adı
- [ ] GLM 50-27 CG'nin referans düzlemi seçenekleri (kılavuzdan) ve Bluetooth paketinde referansın görünüp görünmediği
- [ ] Köşe ucu adaptörü: tasarım ve uzunluk

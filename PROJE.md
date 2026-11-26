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

## 8. Durum (14.11.2026)

**Yayın:** https://aknergn09-maker.github.io/rolove/ (depo: aknergn09-maker/rolove)

**v1 – Aşama 1 tamam:** Bosch BLE, takip modu, DXF, JSON, geri al.

**v2 – Aşama 2 başladı**
- Veri modeli: noktalar (kullanıcı adlı), kenarlar (duvar / detay / çapraz), şekiller (oda / detay), kısıtlar (çizgi üstünde, dik).
- Dengeleme: en küçük kareler. σ mesafe 2 mm, tahmini kenar 0,5 m, 90° varsayım 2°, çizgi üstünde 1 mm.
- Belirlilik analizi: ölçüyle bağlı bileşen başına RREF ve sıfır uzayı → sabitlenmemiş noktalar, eksik ölçü, kontrol sayısı.
- Gönye raporu: köşe iç açısı, varsayım, durum (gönyeli / gönyesiz / varsayım). Çelişen ölçü > 5 mm.
- Çapraz önerisi: eksikse "gerekli", belirliyse "kontrol". Mor çizgi, lazer ölçüsü doğrudan ona yazılır.
- Araçlar:
  - Takip: büyük yön diskleri
  - El çizimi: RDP sadeleştirme, 22° içindeki açılar 90°'ye
  - Çizgi: yakalama (köşe, kesişim, orta, dik, üzerinde, 90°)
  - Çapraz: iki nokta arası mesafe
  - Seç: ad değiştirme, köşe varsayımı
- Nokta adlandırma: ön ek + sıradaki numara (menüden). Her nokta elle yeniden adlandırılabilir.

**v3 – Arayüz ve saha düzeltmeleri**
- Sekmeler:
  - Kroki: Serbest / Takip
  - Ölç: ◀ ▶, elle giriş, son ölçüyü kullan, iki noktaya dokunarak çapraz
  - Nokta No: tuş takımı, ABC ile harf, otomatik artış, aynı ad varsa yer değiştirme
- Dokunma kayması düzeltildi: panel yüksekliği değişince tuval yeniden boyutlanıyor (ResizeObserver).
- BLE filtresi: `C0 55 .. MOD` paketinde mod ≠ 06 ise ayar/mod değişikliği sayılıyor ve sonraki 3 sn'de gelen ölçü yok sayılıyor. Örnek: referans değiştirince cihaz `C0 55 10 02 01 ..` ve ardından son ölçüyü yeniden (`06`) gönderiyor.
- Serbest çizim:
  - Sürükle = el çizimi (90° sınırı 35°, ana yön 15° içindeyse eksenlere oturur, kısa parçalar birleşir)
  - Basılı tut (420 ms) = yakalamalı nokta, büyüteçle çizgi başlatma
  - Dokun = seç ya da zincire nokta ekle
  - Bir köşeden başlayan çizim o köşeye bağlanır.
- Daire algılama: yarıçap sapması < %13, sivri köşe yok, en/boy 0,7–1,43. Lazerle çap (ayardan yarıçap) ölçülür. DXF'te CIRCLE.
- Daha sade etiketler. Düğmeye basılı tutunca ne işe yaradığı gösteriliyor.

**v4 – CAD araçları**
- Kroki araç çubuğu: ✎ serbest, ╱ çizgi, ⌒ fillet, ◯ daire, 🚪 kapı, ∥ ofset, ⟲ takip, ⊥ eksen kilidi.
- Çizgi: cm tuş takımı ile doğrudan mesafe (200 → 2,00 m), sonra yöne dokunulur. Eksen kilidi açıksa 90°, ana yön ilk duvardan alınır. Yazılan değerler **tahmini**dir (est), lazer ölçüsü gerçek değerdir.
- Ölçek: oda başına, ölçülen kenarların ölçü/tahmin oranının medyanı. Ölçülmemiş kenarlar bu katsayıyla büyür/küçülür.
- Fillet: köşeye yarıçap. Köşe sanal kesişim olarak kalır, duvarlar teğet noktalarda kesilir.
- Kapı: duvar üstünde konum t ve genişlik w; menteşe ve yön değiştirilebilir. Ölç'te genişlik ya da köşeden uzaklık ölçülür. DXF'te duvar kapı boşluğunda bölünür.
- Ofset: tek duvar ya da odanın tamamı (dışa, köşeler kesişimle), kalınlık ölçülebilir.
- DXF: ölçülmemiş her şey **TAHMINI** katmanında (renk 30, kesikli) ve ~ ile. Ayrıca KAPI ve OFSET katmanları, açıklama yazısı.

**v5 – Pline ve düzenleme araçları**
- Pline: Bitir ile açık kalır. Açık bir pline'ın ucuna dokununca o pline'a devam edilir, başka bir pline'ın ucuna değince ikisi birleşir.
- Çizgi aracında yön okları (ilk segmentte 4 yön, sonra Sol/Düz/Sağ) ve ✓ (yazılan cm'yi seçili yönde çiz). Yön okuna cm yazılıyken dokunmak doğrudan çizer.
- Aks yakalama: eksen kilidiyle giderken noktaların (öncelikle başlangıcın) hizası yakalanır. Başlangıç noktasında yakalama yarıçapı 34 px.
- Düzenle ✥: noktayı sürükle (ölçülmemiş kenar tahminleri güncellenir, açı varsayımları yeniden belirlenir), çizgiye dokun = kırık noktası ekle, noktayı sil = komşu kenarları birleştir.
- Trim ✂ / Extend ⇥: kesişim noktaları "çizgi üstünde" kısıtıyla bağlanır.
- Kapı: duvarı üçe böler (duvar – kapı açıklığı – duvar). Söveler köşe noktası olur, adlandırılır ve ölçülür. Kapı açıklığı ayrı kenar türüdür, ölçek katsayısından etkilenmez.
- Duvar ▥: pline'ın tamamına kalınlık bandı (köşeler kesişimle), tarama, kapıda kesilir. DXF'te DUVAR_DIS ve TARAMA katmanları.
- Daire + kapalı pline kesişirse birleşir: yay kenarı (merkez noktası + yarıçap kısıtı) oluşur. Alan yayla hesaplanır. Ölç'te yay seçilip yarıçap (ya da çap) ölçülür.
- Nokta No: hattın üstüne basılı tutunca hat bölünür, sıradaki adla nokta konur.
- Ölçülen bir kenar bölünürse toplam ölçüsü gizli bir kenar olarak korunur.

**v6 – Ofset ve duvar gerçek çizgi**
- Ofset ve duvar dış yüzü artık gerçek nokta + kenar + pline (şekilde `gen` = ofset kimliği). Yakalanır, adlandırılır, ölçülür, trim/extend edilir.
- Kalınlık bağı kısıtlarla tutulur: `offd` (noktanın kaynak çizgiye işaretli dik uzaklığı = kalınlık), düz ve uç noktalarda `perp`, yaylarda yarıçap = iç yarıçap ± kalınlık. Kaynak oda ölçüyle değişince dış yüz paralel kalır.
- Kaynak pline değişince (kapı, kırık) dış yüz kendiliğinden yeniden kurulur. Kapıda dış yüz de kesilir, söve çizgileri (kalınlık boyunda) oluşur.
- Dış yüzün yapısı elle değiştirilirse (trim, kırık, pline devamı) ofset kaydı çözülür, çizgiler bağımsız pline olur. Kalınlık kısıtı son değerle kalır, duvar taraması kalkar.
- Kalınlık: araçta cm + ✓, ya da Ölç'te dış yüz kenarı seç → "kalınlık" → lazer.
- Pline devamı: Çizgi aracında açık uçlar yeşil halkayla gösterilir (30 px yakalama). Serbest/Düzenle'de açık pline'ın kenarı ya da noktası seçilince "╱ Devam" düğmesi.

### v7 notları (16 istek)

- Hizalama kılavuzları: basılı tutunca ya da çizgi aracında imleç, ekrandaki noktaların x/y hizasına (çizimin eksen açısında) 9 px içinde oturur, pembe kesikli kılavuz çizilir. Zincirde aks izi (track) başlangıç noktasına öncelik verir, kapanış köşesi tam yakalanır.
- Seçim: daire içine dokununca seçilir; fillet yayı kenar olarak seçilir; ofset/duvar dış çizgisi seçilince "∥ Grup", "⇅", "Ayır" düğmeleri.
- Ofset/duvar önizleme: dokununca önizleme olur; cm yazınca canlı değişir, ✓ uygular, ✕ / araç / sekme değişimi iptal eder ve iz bırakmaz. Araç değişince seçim, tampon, yerleştirme izleri temizlenir.
- Gerçek fillet: köşe silinir, iki teğet nokta gerçek (adlandırılabilir, yakalanır) olur, yay kenarı (`arc`) ve yardımcı merkez noktası (`aux`, adsız, DXF'e yazılmaz) eklenir. Kısıtlar: yarıçap (`radius`), teğetlik (`perp` + `tan`, 0.2°). Köşeden ölçülmüş kenar varsa sanal köşe `aux` olarak kalır ve iki çizgi üzerinde tutulur. Eski `P.fillets` açılışta dönüştürülür.
- Pencere: `window` kenar türü, duvarı kapı gibi böler, söveler gerçek köşe. `P.windows [{id,e,sill,h,sillM,hM}]`. Kroki'de cm + "Parapet"/"Yükseklik" düğmeleri; Ölç'te Genişlik → Parapet → Yükseklik lazerle sırayla. Ayar: "Pencere parapet/yükseklik sor". DXF katmanı PENCERE.
- Kapı açılışı: yerleştirince 4 seçenek (İçe/Dışa × menteşe noktası adı), son seçim yeni kapılara uygulanır (`SET.doorSide/doorHinge`).
- Join: açık pline'ların uçları aynı nokta ya da 2 cm içindeyse Bitir'de ve ofset/duvar öncesinde birleşir; uç uca kapanırsa oda olur. Ofset bir kenara dokununca tüm pline'a uygulanır; açık ofsetin uçları kapatılır.
- Çıkıntı: zincir bir oda duvarının üstünden başlayıp aynı düz duvara dönerse (en az 2 parça) uç noktalar duvara eklenir, aradaki duvar parçası silinir, zincir odanın halkasına katılır.
- İki eksen kilidi (v7b): ⊥ objeye göre, ✛ X-Y (ekran ekseni, açı 0). Aktif olana tekrar basınca kilit kapanır. `SET.orthoMode` = 'obj' | 'xy'. X-Y'de el çizimi de 0/90'a oturur.
- Eksen kilidi (obje): zincirin ilk noktası bir kenarın üstündeyse o kenarın açısı; boşta başlıyorsa ilk parça serbest, sonraki parçalar ilk parçaya göre kilitli.
- Lazer: seçim yoksa ölçü odaklı şeklin sıradaki ölçülmemiş kenarına otomatik yazılır (↶ ile geri). Çizgi/araç modunda ölçü cm tamponuna gider.
- Bosch paketleri: bayt 3 = mod. 0x04 (ön referans), 0x06 (arka), 0x08 → uzaklık. Değer 0 olan paket = ayar (yok sayma penceresi 1.5 sn). Diğer modlar (0x0A min/max, eğim vb.) @7/@11/@15 float olarak çözülür, ilk değer yazılır, Ölç panelinde diğerleri düğme olur. Eğim modunun gerçek paketi henüz görülmedi; günlük ekranından alınacak.
- Çapraz önerisi: sadece gönye belirsizse ve (oda için hiç çapraz yoksa ya da gönyesizlik/sapma > tolerans görüldüyse). Aday çapraz oda içinden görünmeli (duvar kesmez, köşeye sürtmez, orta noktası içeride), ≤ 30 m, en uzunu. Kontrol çaprazı ayara bağlı (varsayılan kapalı). Kalan köşeler "90° kabul" olarak raporlanır.
- İlk ölçü ölçeği: bir bağlı grupta ilk kenar ölçülünce grup (oda içindeki ölçülmemiş detaylar dahil) o kenarın ilk ucuna göre orantılı ölçeklenir; yazılan kapı/pencere genişliği, yazılmış yarıçaplar ve duvar kalınlığı korunur. Ekran ölçeği de aynı oranda değişir, köşe ekranda yerinde kalır.
- Grup taşıma: Düzenle'de kenar/daire/oda içinden sürükleme, birbirine bağlı (kenar, kısıt, ofset) her şeyi birlikte taşır.
- v7c — Daire/yay kesme: Trim'de daireye dokununca dokunulan parça silinir, kalan yay kenar olur (uçlar çizgi üstünde gerçek nokta). Yay da çizgilerle kırpılır; çizgi de daire/yayla kırpılır. Yakalama: çizgi–daire kesişimi (`cint`), daire üstü (`cnear`); nokta `oncirc` kısıtıyla (merkeze uzaklık = yarıçap) daire/yay üstünde kalır. Yaylar artık düz çizgi gibi yakalanmıyor.
- v7c — Nokta adı: yeni noktalara otomatik ad verilmez (ayar: "Yeni noktalara otomatik ad ver"). Nokta No ile ad verilen nokta total noktası sayılır (`p.tot`, mor üçgen): analizde koordinatı bilinir; iki total noktası arasındaki kenar ölçü istemez, çapraz önerisine girmez. Boş tamponla noktaya dokunmak adı ve total işaretini siler. Nokta No hat, yay ve daire üstüne basılı tutarak da konur.
- v7d — Tuşla yazılan uzunluk (`e.typed` = zincir kimliği) gerçek kabul edilir: σ 1 cm, oda ölçek oranıyla çarpılmaz, ilk ölçü ölçeklemesinde korunur. Yazılı kenar ölçülünce %15'ten fazla farklıysa o zincirin yazılı değerleri eskiz sayılır ve ölçeklenir. Düzenle'de sürüklenen kenarın yazılı işareti kalkar. (Odaya eklenen 180x30 iç çıkıntının oda ölçeğiyle bozulması düzeltildi.)
- v7e — Ofset/duvar noktaları artık çözüme girmiyor, kaynak çizgiden her commit'te türetiliyor (dar çıkıntıda kalınlık kısıtları odayı büküyordu). Yakalamada oda çizgisi duvar dış yüzüne tercih edilir. Çözüm sonrası serbest dönme/öteleme, kenar açı değişimlerinin ağırlıklı medyanı ve nokta kaymalarının medyanıyla geri alınır (oda ölçüyle dönmüyor). Yazılı kenar bölününce toplam uzunluk gizli kenarla korunur; yazılı ağırlıklı şekilde ölçek oranı uygulanmaz; eskiz tahmin σ = max(0.5, 0.3·uzunluk).
- Test: work/t8.py 40 kontrol, t9 (eksen kilidi) 6, t10 (daire kesme/total) 13, t11 (çıkıntı geometrisi) 4, t12 (bantlı L oda + iç duvar + ölçü) 4 (16 maddenin hepsi) + t4–t7 güncellendi.

## 9. Açık sorular

- [ ] 3° TM dilimi
- [ ] Katman adları ve renkleri, yazı boyları
- [ ] Nokta kodlama listesi (B = bina, …)
- [ ] Kapanma toleransı (öneri: 2 cm)
- [ ] GitHub hesabı ve depo adı
- [ ] Bosch eğim modu paketi (günlük ekran görüntüsü bekleniyor). Bilinen: 04 ön, 06 arka referans, 0A üç değer, değer 0 = ayar.
- [ ] Köşe ucu adaptörü: tasarım ve uzunluk

## 10. YENİDEN BAŞLANGIÇ — kullanıcının istemedikleri ve istekleri (15.11.2026)

Eski sürüm (v7e) yedek kalacak. Kullanıcı "başla" demeden kod yazılmayacak; önce öneriler konuşulacak.

1. Çizgiye yama/kırık eklemek zor; düz çizgideki kırık silinemiyor. → Seçim aracı: noktayı seç → kaydır / sil.
2. Arayüz kullanışlı değil.
3. Önce ofset atılsın, tarama sonradan eklensin. Tıklanan aralığa (kapalı alana) tarama. Kapı/pencere alanı ikiye bölüyorsa kapı/pencere ağzı kapansın, tarama karışmasın.
4. Tek oda değil, birden çok oda: bir odadan başlayıp yanına birleştirerek gidiyor. Eski programda çok zordu.
5. Lazer ölçüsü verince o çizgi gerçek değere gelsin; diğer odalar dahil HER ŞEY ölçeklensin. Her yeni cephe uymadığında çizgiler yine en az düzeyde ölçeklenebilir.
6. Çoğu obje algılanmıyor (daireye tarama atılamadı). Daireye dinamik (canlı) önizleme; 3 noktadan daire.
7. Serbest çizim uzun çizgilerde 20–30 cm duvar kalınlıklarını algılamıyor, çizgileri üst üste koyuyor; daire algılamıyor. Köşe seçip devam edilemiyor; olmazsa en azından köşe seç-kaydır, bir köşe diğer köşeye otursun.
8. Çizgiyle çizerken kapı/pencere koyma tuşu olsun, sonra çizgi devam etsin. Ofset atılınca kapı otomatik kayıp uysun.
9. Kapı/pencere yükseklikleri ayrı sekmede, sonradan. Tavan arası ölçülemediği için yer–tavan istesin; pencere yüksekliği ve yerden yüksekliği (parapet) girilsin, tavan arasını program hesaplasın; 0 girilebilsin (yere sıfır pencere).
10. Geometri hesabı önce yazıyla: gerekli çaprazları söylesin, alındıktan sonra "yeterli" desin; "Geometriyi hesapla" tuşu (ayrı sekme olabilir). Duvar içinden geçen çapraz istemesin.
11. AutoCAD gibi bir program: arayüz ve plan görüntüsü çok iyi olsun.

## 11. v8 — Yeni çekirdek, Aşama 1 (15.11.2026)
- Sıfırdan yazıldı. Eski sürüm: eski.html (veri anahtarları rk2_*, yeni: rk3_*; projeler ayrı).
- Model: nodes {id,x,y}, lines {id,a,b,kind: sketch|typed|laser|total}, rooms {id,name,ax,ay}. Geometri = gerçek; hiçbir hesap kendiliğinden noktayı oynatmaz.
- Odalar: çizgilerden düzlemsel graf (kesişimler ve T bağlantılar bölünerek), yarım-kenar yüz taraması; oda = çapa noktasını içeren en küçük yüz; ayrı parçalar (kolon) ada olarak alandan düşer. Kapanan yeni alana otomatik oda (ada içindekiler hariç).
- Arayüz: siyah tema; üstte komut satırı; sağda ⊥ (obje kilidi), ✛ (X-Y), ⌖ (yakalama), ⤢; altta Çiz/Düzenle/Ekle sekmeleri; alttan açılan panel (tuş takımı, özellikler).
- Çizgi: dokun/basılı tut + büyüteç, yakalama (uç, orta, kesişim, dik, üzerinde), eksen hizası, cm yaz + ok tuşu ya da parmakla yön; köşeden köşeye çizince oda kapanır.
- Seç: dokun = çizgi/köşe/oda; mavi kare (grip) sürükle; köşeyi köşeye bırak = birleştir; çizgi ortasındaki elmas = çizgiyi kaydır; kutu seçim; Uzunluk (A/B sabit), Taşı (baz → hedef, mesafe yazılabilir), Sil, Kırığı sil, Buradan devam.
- Test: work/v8/t1.py 19 kontrol.
- v8.1: Duvar aracı (çizgi gibi çizilir; kalınlık 10–30 cm çipleri; ⇄ Yön; kapalıda varsayılan dışa; kalınlık türetilir, köşe taşınınca uyar; bant içine dokun = duvar seç). Serbest çizim geri geldi: ekran pikseliyle RDP (5 px), 8 px altı parçalar atılır, 20° içinde eksene oturtma, çizgi konumu ham noktaların ortalaması, iki paralel parça arasında kısa geçiş = dik kademe (25 cm duvar kalınlığı tanınır), uçlar köşeye/çizgiye bağlanır, kapanınca oda. Test: work/v8/t2.py 11 kontrol.
- v8.2: Dokunma düzeltmeleri — düğmeler pointerup ile tetiklenir (tarayıcının yuttuğu click'e güvenilmez); panel kompakt (tuş takımı "⌨ cm"e dokununca açılır); ⇄ Yön ve kalınlık düğmeleri çizim bitince az önce çizilen duvara uygulanır; Uzunluk ✓ sonrası panel kapanır; çizgi seçilince duvarı varsa kalınlık/⇄ satırı; Serbest'te "▥ Son çizime duvar ekle"; Seç → "▥ Duvar" (bağlı zincir ya da oda sınırı). Testler artık iPhone 13 öykünmesi + gerçek dokunma olaylarıyla: work/v8/t3.py 20 kontrol (+ t1 19, t2 11).
- v8.3: Duvarın diğer yüzü ve uç kapakları seçilebilir (panel: uzunluk, kalınlık, ⇄, "Çizgilere çevir", kalınlığı kaldır) ve yakalanır (uç, orta, üzerinde). t3.py 25 kontrol.

- v8.4: Duvar aksı yakalama (aks, aks ucu, aks orta), duvar yüzüne/aksa dik; orto yönündeki ışın çizgiye/duvar yüzüne/aksa çarpınca tam üstüne oturur (gerçek çizgide T bağlantı). t4.py 7 kontrol.

- v8.5: Kesişim yakalama birleşik: gerçek çizgiler + duvar yüzleri + (uçları uzatılmış) duvar aksları; yakın parçalarla sınırlı (40 px). Türetilmiş noktalar (aks/yüz) gerçek çizginin üstüne düşerse çizgi bölünür ve bağlanır. t5.py 5 kontrol.
- v8.6: Aks–aks kesişimi ve kapalı köşedeki aks ucu verilmez; aks yalnızca çizgi ve duvar yüzleriyle (kendi duvarı hariç) kesiştirilir; aks ucu sadece açık uçlarda.
- v8.7: "Uzantı kesişimi": çizgi ve duvar yüzlerinin 1 m uzantısı başka çizgi/yüzle kesişince yakalanır (oda çizgisinin uzantısı × komşu duvarın dış yüzü); yeşil noktalı kılavuz çizilir. Aks artık uzatılmıyor. t6.py 5 kontrol.
- v8.8: Seç → açık duvar ya da açık çizgi zinciri → "Kapat" (uçları birleştirir, kalınlık aynı tarafta kalır, oda oluşur). t7.py 5 kontrol.

### Aşama planı (v8) — kullanıcı isteğiyle sıra değişti: önce çizim, sonra ölçme
1. Arayüz, çizgi/dikdörtgen/duvar/serbest, yakalama (aks, dik), seç-taşı-sil, çok oda — TAMAM (onay bekliyor)
2. Ofset, kapı/pencere (çizerken ve sonradan), tarama (tıklanan alana; kapı/pencere ağzı kapanır), duvar birleşim yerleri
3. Daire (merkez, 2 nokta, 3 nokta, canlı önizleme), kes/uzat/birleştir
4. Lazer ölçü ve ortak ölçek
5. Kontrol sekmesi: yazılı rapor, oda içinden çapraz önerisi, "Geometriyi hesapla" (önizleme + onay)
6. Yükseklikler sekmesi
7. Nokta adı / total noktaları, DXF

- v8.9: Oda düzenle
  - Ötele (Seç → çizgi → Ötele → cm → yön oku): duvarın düz devamı (aynı doğrultudaki bitişik parçalar) paralel kayar; uçlara bağlı çizgiler kendi doğrultusunda uzar/kısalır; 60 cm içinde paralel ve arası oda olmayan karşı yüz (komşu odanın duvarı) aynı miktarda kayar, kalınlık korunur. Karşı yüzün düğümü kaymayan paralel bir çizgiye de bağlıysa (C odası) düğüm ayrılır, yeni köşe bağlı duvarın üstüne oturur; C'ye dokunulmaz. Kural (kullanıcı onayı): başka hiçbir şey kaymaz.
  - Çıkıntı/Girinti (Düzenle → Çıkıntı; v8.10: Ekle sekmesinden kaldırıldı, varsayılan "Çizerek"): Ölçüyle (başlangıca dokun → bitişe dokun ya da en yaz + ok → derinlik yaz + yön oku) ve Elle çiz (duvardan başla, aynı düz duvara dön). Aradaki duvar parçası silinir, duvar bandı zinciri yeni yolu izler, oda alanı güncellenir. Komşuya dokunulmaz; aradaki parçaya bağlı boşta kalan çizgiler kendi doğrultusunda yeni hatta uzatılır/kısaltılır ve bağlanır.
  - Çizerken nokta kendi son noktasına yakalanmaz.
  - t8.py 11 kontrol.
- v8.11: Çıkıntı "Çizerek" = parmakla serbest çizim (duvardan başla, aynı düz duvarda bitir). Sonra komşu dış yüz varsa soru: "Evet, kalınlık korunsun" (komşu duvar çizgisi aynı kalınlıkla yeni şekli izler) / "Hayır, sabit kalsın". Yeni oda, komşu duvarın dış yüzünden başlayıp yine o dış yüzde bitince dış yüz boyunca kapanır (ortak duvar; çizgiler l.face ile işaretli). Serbest çizimde de geçerli. t9.py 10 kontrol.

- v8.12: Çıkıntı "Çizerek" yeniden çizgi gibi (nokta koy / cm + ok); her noktada aynı düz duvara dönüp dönmediği kontrol edilir. Çıkıntı aracında duvar yüzü/aks yakalanmaz (son nokta oda çizgisine oturur — önceki hata: dışa çıkıntıda dönüş duvarın dış yüzüne yakalanıyordu). Tam çizgi üstüne düşen her nokta çizgiyi böler. Serbest çizimde aynı duvarda başlayıp biten çizim için soru: "Çıkıntı mı? Evet / Hayır" (Hayır = yeni oda/çizgi, bitişik oda çizimi bozulmasın). Karşı yüz aranırken yeni çizilen çizgiler hariç.

- v8.13: Köşe dönen çıkıntı/girinti: bir cepheden başlayıp başka cepheye (aynı odanın sınırı) dönünce aradaki köşe parçası (en kısa sınır yolu, ≤6 parça) silinir. İki odayı ayıran bölme silinmez; kapanan alanda başka çizgi varsa yapılmaz. Serbest çizimde soru "Çıkıntı / girinti mi?" (Evet'te serbest çizimin açtığı oda silinir). t10.py 8 kontrol.

- v8.14: Köşe dönen çıkıntı/girintide de "dış yüz değişsin mi?" sorusu (taban parçalarından birinin 60 cm içinde karşı yüzü varsa). Evet: yeni yol aynı kalınlıkla ötelenir, komşu odanın çizgileriyle (gerekirse kendi doğrultusunda uzatılarak) kesiştirilir, aradaki komşu parçası silinir. t10.py 13 kontrol.

- v8.15: Duvarın diğer yüzü (iç/dış fark etmez) oda tespitinde sınır sayılır (sanal çizgi). Duvar bandının içindeki parçalar (halka) oda olmaz. Sanal yüz, kendi duvarı olmayan başka bir odanın alanına giriyorsa sayılmaz. Sonuç: dıştan iskelet çiz, içten (iç yüzden) oda doldur → oda oluşur, alan iç yüzden. Serbest çizim uçları duvar yüzüne de yakalanır. Not: komşu odaya taşan duvar bandı (ötele/çıkıntı "Hayır") o odanın alanından düşer (t8 C 8.95, t9 B 8.3). t11.py 6 kontrol.

- v8.16: Sanal yüzün atılma kuralı değişti: yalnızca duvar bandı (referans çizgi → yüz) başka bir gerçek çizgiyi aşıyorsa yüz sayılmaz (komşu odaya taşma). Başka odanın duvarının dış yüzü, iskeletin içinde olsa da sınırdır. Çizgi/duvar zinciri bir duvar yüzüne düşünce oda kontrolü yapılır (önceden sadece mevcut düğüm/çizgiye düşünce). Yön fark etmez. t12.py 6 kontrol.

- v8.17: Hata: dışarıya eklenen odanın duvar ucu (kapak) iskeletin çizgisiyle üst üste biniyordu; kolinear çakışan parçalar bölünmediği için yüz grafiği bozuluyor, komşu oda "açık" görünüyordu. computeFaces artık her parçayı sanal yüz uçlarında da böler. Duvar halkası tespiti: odanın içinde (farklı derinliklerde) bantsız bir nokta varsa duvar değil. t13.py 4 kontrol (kullanıcının senaryosu UI ile).

- v9.0 (2. aşama başladı): Ekle → Eleman (Kolon/Şömine/Baca/Şaft/Diğer; çiz ya da alana dokun; taralı; alanı yazar, odadan DÜŞÜLMEZ) ve Merdiven (çerçeve çizgi gibi çizilir ya da alana dokun; "Merdiven" + m² yazar, odadan DÜŞÜLÜR; Basamak: karşılıklı iki kenar seç + rıh sayısı N → N çizgi başlangıç ve bitiş dahil; v9.1: KISA kenar esas, N-1 eşit aralık, kısa kenara dik çıkılıp uzun kenarın doğrultusunda biter (uzun kenarın fazlası önemsiz), var olan kenar tekrar çizilmez; basamak çizgileri l.step, yüz grafiğine girmez; Yön: başlangıç/dönüş/bitiş noktaları → ok, P.arrows). Odalar P.rooms içinde kind:'eleman'|'merdiven'. rA(r) = görünen alan. Kararlar: yelpaze basamaklar elle çizgi; dairesel merdiven 3. aşamada (3 nokta: başlangıç-ara-bitiş, genişlik → ofset yay, rıh sayısı, ışınsal basamak; "esas cephe" sorusu gereksiz çünkü eş merkezli yaylarda eşit açı iki yayda aynı). Bekleyen: kapı/pencere gösterimi soruları. t14.py 11 kontrol.

- v9.2 (inceleme sonrası sağlamlaştırma):
  - Basamaklar P.stepSets {stair, a,b (kısa kenar düğümleri), c,d (uzun kenar), N}; her commit'te regenSteps ile yeniden üretilir (çerçeve taşınır/ötelenirse izler, merdiven işareti silinirse gider; bir basamak çizgisi silinirse seti gider). Oklar {stair, ref düğüm} ile merdiveni izler. Basamak uçları seçilemez.
  - Kayıt başarısızsa (hafıza dolu) "KAYDEDİLEMEDİ" uyarısı.
  - Aynı adlı proje üstüne yazmaz (uniqName: "ad (2)"); Adlandır var olan adı reddeder; JSON yükle aynı adı değiştirir.
  - Kural (kullanıcı): ötelemede başka odanın m²'si değişmez. Duvar bandının sanal yüzü bir gerçek alanın içindeyse, o duvarın referans çizgisi o alanın sınırında ya da içinde değilse sınır sayılmaz (t8 C = 9.00).
  - Basamak modunda en yakın gerçek çizgi seçilir (köşeye yakın dokunuş da olur).
  - Sürüm (VER) menüde; yedek hatırlatma: son değişiklikten 30 dk sonra yedek yoksa ☰ kırmızı nokta, menüde "son yedek" bilgisi, açılışta uyarı; JSON yedek alınca P.backupAt.
  - HATA bulundu ve düzeltildi: ☰ menüsü dokunuşla açılıp aynı dokunuşun tıklamasıyla hemen kapanıyordu (600 ms koruma).
  - Testler depoda: test/t1..t15.py, `python3 test/run_all.py` (CHROME ortam değişkeni ya da playwright chromium).

- v9.3 Kapı/Pencere (Ekle → 🚪 Kapı/Pen.): duvar çizgisine (ya da dış yüzüne) dokun (köşeye yakınsa köşe) → isteğe bağlı "Köşeden" cm + "Genişlik" cm → yön oku; ya da bitiş noktasına dokun. Duvar çizerken alt satırda 🚪Kapı / ▤Pen.: sonraki parça açıklık olur. Kapı: söveler + kanat + kesik çeyrek daire yay (kullanıcı onayı); varsayılan oda tarafına açılır. Pencere: duvar içinde 3 çizgi (iki yüz + orta). Etiket K90 / P120. Seç → açıklığa dokun: ⇄ Menteşe, ⇅ Açılış yönü, Genişlik, tür değiştir, Sil. Veri P.openings {type, ha, hb (aynı doğrultudaki duvarın uç düğümleri), s, w, hinge, sw}; düğümler birlikte kayarsa açıklık gider, duvar tek ucundan uzarsa açıklık yerinde kalır; ev sahibi çizgi silinirse açıklık silinir. Alanı etkilemez. Ayrıca: araç değişince tuş takımı kapanır (çizim alanını kapatıyordu). t16.py 18 kontrol.

- v9.4 Kapı eli: Sağ/Sol (tanım: kapının açıldığı taraftan, kanadı kendine çektiğin taraftan duvara bakınca menteşe sağdaysa Sağ — DIN ile aynı). Etiket "K90 Sağ". Panelde El [Sağ][Sol] + "⇅ <oda> tarafına açılır" (el korunur, menteşe uyarlanır). Kapı ekledikten sonra Kapı/Pen. aracında da son kapının satırı görünür. HATA düzeltildi: düğmeye dokunuşun ikinci tıklaması panel yeniden çizilince başlığa düşüp tuş takımını açıyordu (tıklama koruması artık her hedefte).

- v9.5 Açıklık duvarı böler (kullanıcı isteği; kroki ve lazer için): kapı/pencere kenarları gerçek düğüm (köşe), çizgi köşe→kenar, açıklık, kenar→köşe parçalarına bölünür; ölçü zinciri bu parçaları yazar (etiket artık sadece "K Sağ/Sol", "P"). Açıklık = kendi iki düğümü arası (o.nb=1); eski kayıtlar açılınca dönüştürülür. Genişlik değişince bitiş kenarı duvar boyunca kayar, komşu parça kısalır. Açıklık silinince kenar düğümleri birleşir (kırık silinir). Kısa parça ölçü yazısı sınırı 42→26 px. t16.py 27 kontrol.

- v9.6: çıkıntı/girintide silinen duvar parçasındaki kapı/pencere yeni yolun paralel yüzüne taşınır; sığmazsa kaldırılır ve uyarı. t17.py.
- v10.0 4. AŞAMA (ana uygulamada): Ölç sekmesi → 📏 Lazer / Ölçü.
  - Bosch GLM (50 C ailesi, 50-27 CG dahil varsayıldı) Web Bluetooth: servis 02a6c0d0-0451-4000-b000-fb3210111989, karakteristik 02a6c0d1-…; bağlanınca C0 55 02 01 00 1A yazılır; bildirim C0 55 10 06 … bayt 7–10 float32 LE metre. iPhone'da Bluefy gerekir. Gerçek cihazla DENENMEDİ (sahte cihazla test).
  - Akış: çizgiye dokun → lazer ölçümü gelir (ya da önce ölç sonra dokun) ya da cm yaz (virgüllü, mm) → Uygula. Çizgi kind 'laser', l.m (m).
  - Dengeleme (adjustGeometry): ağırlıklı en küçük kareler (CGLS, Gauss-Newton). Her çizgi yönü güçlü (300) korunur; lazer boyu 3000, yazılan 30, eskiz boyu ortak ölçek k ile 1. Sonuç: ilk ölçümde her şey aynı oranla ölçeklenir, sonrakiler yalnızca gerekeni değiştirir, açılar korunur. Çelişkili ölçüde (>2 mm kalıntı) uyarı.
  - Lazer etiketleri 3 hane; çizgi sonradan bozulursa kırmızı "≠ gerçek"; "Yeniden hesapla". Ölçülü çizgi bölünürse (kapı) parça ölçüleri oranla dağıtılır, toplam korunur. t18.py 17 kontrol.

- ÖNİZLEME (onizleme.html, ana uygulamaya ALINMADI, onay bekliyor; kayıt alanı ayrı: rk3p_*, ilk açılışta ana projeler kopyalanır):
  - Üstte 3 sekme: Çizim (Çiz/Düzenle/Ekle) · Ölçüm (Lazer/Elle, Kontrol, Yükseklik) · Kroki (Nokta adı, DXF/Dışa).
  - Kroki nokta adları: ilk dokunuşta başlangıç sorulur (ör. 101), her dokunuş sıradaki adı alır (sondaki sayı artar, sıfır dolgusu korunur). Köşe, kapı kenarı, duvar dış köşesi (en yakın düğüme ofsetle bağlı; ölçeklemede kalınlık korunur). Seç: adını değiştir / buradan devam / sil. Otomatik ad YOK.
  - DXF (R12, metre, ezdxf ile doğrulandı): katmanlar CIZGI_ESKIZ/YAZILAN/LAZER, DUVAR, KAPI (yay ARC), PENCERE, ODA (ad+alan), ELEMAN, MERDIVEN, NOKTA (POINT+ad), OLCU. Türkçe harfler \U+XXXX. ☰ menüde ve Kroki → DXF/Dışa.
  - 5. aşama Kontrol: köşegen yalnız oda içinden (iki köşe), lazer/elle; "Geometriyi hesapla" yeşil kesik önizleme → Onayla/Vazgeç; köşegenler dengelemeye girer. Ölçü raporu (oda, alan, çevre, kenarlar, köşegenler, açıklıklar, yükseklikler, nokta adları) paylaş/kaydet.
  - 6. aşama Yükseklik: oda taban–tavan; pencere denizlik (0 olur) + yükseklik; kapı yükseklik; üstten tavana = H − denizlik − yükseklik (negatifse kırmızı). Lazer ölçüsü seçili alana yazılır.
  - Duvar birleşimleri: tüm bantlar tek parça çizilir (iç kesişim çizgileri yok, tarama ekrana sabit desen).
  - 3. aşama: Daire (merkez+r, 2 nokta, 3 nokta; canlı önizleme; ≤4 mm kirişle çokgen), Buda/Uzat/Birleştir (Düzenle → ✂), Dairesel merdiven (3 nokta başlangıç-ara-bitiş + genişlik içe/dışa + rıh; ışınsal basamaklar, merdiven alanı).
  - Testler: test/p1..p4.py (PAGE=onizleme.html ile t1..t18 de geçiyor).

- v10.1 (ana) + önizleme: yazı yerleşimi (LB): her karede yazılar sırayla yerleşir, çakışan yazı aday konumlara kayar (ölçü: dışa uzak/içe/boyunca; oda adı: alt/üst/yana, gerekirse oda dışına; açıklık etiketi iki yan). Menüde ana ↔ önizleme ↔ eski sürüm düğmeleri (data-m=go). t19.py.
- Önizleme ek: nokta adları 12 aday konum (uzaksa ince bağlantı çizgisi), köşegen yazısı çizgi boyunca kayar. P.arcs {ids, closed}: daire ve dairesel merdiven yayları; ekranda ara düğümler gizli, yay başına tek "R" yazısı; DXF'te CIRCLE/ARC (düğümler 5 mm içinde daireye uyuyorsa, yoksa çizgi). Dairesel merdiven basamakları iç/dış yay düğümlerinden yeniden üretilir (gerçek daireyse açıyla tam yay üstünde, değilse zincir boyunca oranla) → ölçeklemeye uyar. Yön oku merdiven konturunun 3 köşesine ağırlık koordinatıyla bağlı (afin, ölçeğe uyar); dairesel merdivende ok otomatik orta yay boyunca. DXF'te ok başları.

- v10.2 (ana + önizleme): ORTO obje yedeği düzeltildi — bağlı çizgi yoksa eksen projedeki İLK çizgiden değil, binanın baskın yönünden (düz çizgilerin boyla ağırlıklı açı histogramı, yay/basamak hariç) alınır.
- Önizleme ek: Daire aracında "▥ Duvar" (kapalı duvar bandı, SET.wallT). Çizgi/Duvar zincirinde "◠ Yay" (yay üstünde bir nokta → bitiş; ilk noktaya dokununca kapanır, oda ve duvar bandı yayı izler). Düzenle → Çıkıntı → "◠ Yay" (duvarda başlangıç → tepe → duvarda bitiş; aradaki düz duvar kesilir, içe ya da dışa; applyDetour). Ekle → Eleman: [╱ Çizgi] [◯ Daire] [Alana dokun] (daire kolon/şömine). Yaylı alanlar tam: kiriş–yay dilimleri alana eklenir/çıkarılır (arcFix). t-p5.py 11 kontrol.

- Önizleme: daire duvarlarla KESİLİR (circleCut): Daire aracında 3 nokta serbest (boşlukta olabilir); daire çizgileri kestiği yerlerden bölünür, odaların DIŞINDA kalan yaylar applyDetour ile oda sınırına katılır (düz parça silinir, duvar/oda/açıklık izler), içerde kalan yay çizilmez; değmezse normal daire. Çıkıntı-Yay: 3 nokta serbest, dokunulan tarafın yayı tutulur (içe/dışa). Yay araçlarında duvar yüzüne yakalama ve ORTO kapalı; yay parçalarının uzantı kesişimleri yakalanmaz (hata: dokunuş 18 cm kayıyordu). Yeni daire oda adının üstüne düşerse ad odanın kalan kısmına taşınır. Yay alan düzeltmesi adalarda da. t-p6.py 8 kontrol.

- Önizleme: daire/yay önizlemesi sonucu birebir gösterir (circlePlan ortak): kalacak yay kalın yeşil, atılacak yay soluk kesik, silinecek duvar parçası kırmızı kesik. Düzenle → Buda/Yuvarla → ◜ Yuvarla (fillet): yarıçap (cm) → köşeye dokun (iki çizgili köşe) → teğet yay önizlemesi → Uygula (applyDetour, duvar/oda izler); sığmazsa "en çok … cm". t-p7.py 14 kontrol (önizleme pikselleri parmak ekrandayken ölçülür).

### Konuşulan öneriler (uygulandı, v8.9)
- Oda düzenle: Çıkıntı/Girinti aracı — duvara dokun, genişlik + derinlik (+dış / −iç) yaz, aradaki duvar parçası otomatik silinir, duvar kalınlığı yeni sınırı izler. Alternatif: serbestçe çiz, aradaki parça otomatik kırpılsın.
- Duvar ötele: çizgiyi seç → cm yaz → İçe/Dışa. Uçlara bağlı komşu çizgiler kendi doğrultusunda uzar/kısalır (açılar korunur); kalınlık bantları izler. Komşu odanın aynı duvardaki çizgisi de birlikte ötelensin mi (bağlı duvar)?

## v10.3 / önizleme (16.11)
- Açık bina + daire: daire açık uçları birleştiriyorsa dış yay kalır, duvar zinciri yay boyunca devam edip kapanır, tek oda oluşur (circlePlan close grubu, linePath, wallJoinArc).
- Buda: yay, sadece içinden geçen değil, dokunan çizgilerden de kesilir (arcBuda). Buda sonrası yüzü kaybolan oda silinir.
- ORTO ekseni yay kirişinden alınmıyor (frameBase, index + önizleme) → v10.3.
- Test: p8.
- (16.11 öğleden sonra) Açık hat kapatma genelleştirildi (openPlan/trimStub): daire uçlardan tam geçmese de olur — 3 nokta basık yay (daire yan duvarları ikinci kez keser), merkez+r ile uçları aşan/uçlara varmayan daire. Uçları birleştiren dış yay kalır, daire içine/dışına taşan uç parçaları budanır, diğer yay parçaları atılır; duvar yay boyunca kapanır. Önizleme budanacak uçları kırmızı gösterir. p8: 14 kontrol (Duvar aracıyla elle çizim dahil).
- v10.4: Ölç'te duvarın diğer yüzüne dokunulunca yüz seçilir (yeşil, panelde yüz boyu); yazılan/lazer ölçü YÜZE uygulanır: çizgi = ölçü − köşe uzantıları (dış bantta −2t, iç bantta +2t). Önceden ölçü referans çizgisine yazılıyordu (dıştan 4.40 ölçülen duvar çizgiyi 4.40 yapıyordu). index + önizleme. t20.py 9 kontrol.
- v10.5: Çıkıntıda duvarın diğer yüzüne dokunuş kabul edilir: nokta referans çizgisindeki karşılığına oturur (zincirden geliyorsa orto ışınının çizgiyle kesişimi, yoksa dik iz düşüm; köşeye 14 px yakınsa köşe). Ölçüler yüzden alınmış olur, yüz kalınlıkla paralel taşınır. Önceden yakın zoomda yüz çizgiden uzak kalınca dokunuş boşa düşüyordu (v8.12'de yüz yakalama çıkıntıda kapatılmıştı). Yay modunda yok. t21.py 8 kontrol.
- v10.6: Çıkıntı "Çizerek" duvarın diğer yüzünde (beyaz çizgi) çizilir: dokunuş yüzde kalır ("Duvar yüzü"), yol aynı yüze dönünce çizilen yol YENİ YÜZ olur; referans çizgisi yolun kalınlık kadar (bant tarafının tersine) ötelenmişi, uçları eski referans çizgisine oturur (cikFaceCheck). Dış bantta çıkıntı, iç bantta girinti test edildi. "Ölçü yazarak" modunda yüz dokunuşu referans çizgisine iz düşer (v10.5). t21.py 8 kontrol.
- v10.7: Çıkıntı (Çizerek): dokunuş beyaz çizgiye turuncudan yakınsa beyaz çizgi seçilir (cikFaceCloser) — önceden normal zoomda dönüş dokunuşu turuncuya oturup başlangıç beyazda kalınca hiçbir kontrol tutmuyor, sadece çizgi kalıyordu. Uçlardan biri turuncu çizgide kalırsa son parçanın doğrultusunda beyaz çizgiye taşınır. t21.py 13 kontrol (zoom 60/66/90, özensiz dokunuş, turuncu→beyaz).
- v10.8: Köşe kolonu: beyaz çizgiden çizilen çıkıntı köşeyle bağlı iki duvar parçasının yüzlerinde başlayıp bitebilir (quadAt; yön duvar sırasına göre, kapalı duvarda baş/son geçişi dahil). Yüzden çizilen çıkıntıdan sonra soru: "Diğer yüz (turuncu çizgi) ne olsun? Kayar, kalınlık korunsun / Sabit kalsın". Sabit: turuncu çizgi ve duvar aynen kalır, çizilen yol gerçek çizgi olarak oda sınırı olur (oda kolon kadar küçülür). t21.py 19 kontrol.
- v10.9: Beyaz çizgiden çıkıntıda iki durum hazırlanır (S.faceAsk {kayar, sabit, cur}); düğmeler arasında geçiş yapılır. "Sabit kalsın (duvar kalınlaşır)": turuncu çizgi/duvar aynen, çizilen yol gerçek çizgi, yol ile beyaz çizgi arası P.fills (düğüm kimlikleri; köşede beyaz çizgi köşeleri wallGeom'dan) taralı duvar olarak çizilir, odadan düşer. İçeri (oda tarafına) çizimde varsayılan Sabit (kolon), dışarıda Kayar. t21.py 24 kontrol.
- Önizleme (16.11 akşam): lazer ölçeklemede oda içindeki obje grupları (birbirine değen çizgiler: eleman, merdiven, kolon, iç detay) odanın üçgeninden (triOf/baryOf) odayla birlikte kayar, kendi ölçeği korunur; oda adları (çapa) da odasıyla kayar (çapa düzeltmesi ana uygulamada da). Seç: ortadaki tutamaktan sürükleme objeyi (binaya bağlı olmayan grup) bütün taşır, köşeden sadece köşe; en yakın tutamak seçilir. Duvar kalınlığı ölçüden: çizgi + diğer yüz ölçülü duvarlardan köşedeki komşu duvarların kalınlığı en küçük kareler ile (l.wt parça kalınlığı, aynı doğrultudaki parçalara; elle kalınlık seçilince silinir). p9, p10, p11.
- v11.0 (ana + önizleme): Kolon iki ayrı duvarın beyaz çizgileri arasında (T bağlantı) → sabit, dolgu kapanışı iki yüz doğrusunun kesişimi. Kolonun altında kalan eski beyaz çizgi çizilmez (faceVisible). Ölç: beyaz çizgi ona değen noktalardan (başka duvarın ucu ve yüzü, kolon köşesi, çizgi ucu) kırılır, dokunulan parça seçilir; ölçü P.dims (iki düğüm arası duvar doğrultusundaki mesafe, uç düzeltmeleri ea/eb) olarak adjustGeometry'ye girer, yeşil etiketle gösterilir. adjustGeometry: başka duvarın beyaz çizgisindeki düğümler (iç duvar ucu, kolon köşesi) o yüzde kalır. Ölçeklemede oda adları odasıyla kayar. t22.py 10 kontrol.
- v11.1: Kolon altında kalan gerçek çizgiler (Çizgi ile yüz boyunca kapatılmış odanın çizgileri) silinir (killUnderFill: kolon köşelerinden ve kapanış köşesinden bölünür, kapanış kenarındaki duvar dışı çizgiler gider; açılışta eski kolonlara da uygulanır). Kolon uçları yerinde düğüm varsa onu kullanır (çift düğüm yok). Ölç: beyaz çizgiyle çakışan gerçek çizgiye dokununca da yüz seçilir ve kırılma noktaları uygulanır. adjustGeometry sonrası yüzdeki düğümler gerçek yüze tam iz düşer (köşedekiler iki yüze). t22.py 11 kontrol.
- v11.2 (kullanıcı kararı: hatanın kökü): Oda duvarın beyaz çizgisinde kapanınca o çizginin üstüne gerçek çizgi EKLENMEZ (closeAlongFace boş döner; beyaz çizgi sanal sınır). Açılışta/geri almada beyaz çizgiyle tam üst üste olan eski l.face çizgileri silinir (l.keep olanlar kalır). Komşu oda artık duvarın yeni yüzünü kendiliğinden izler; çıkıntıdan sonra soru yine çıkar: Evet = olduğu gibi, Hayır = komşu odanın eski sınırına çizgi eklenir (l.keep). Komşu, tabanın beyaz çizgisinin dışında 2 cm örneklenerek bulunur (neighborEdges). Ayrı duvarlı komşu (eski gerçek çizgi) için eski davranış. Kapı/pencere boşluğunda çizgi çizilmez (çizgi silinmez, oda kapalı kalır); kapı daralınca görünen çizgi kendiliğinden uzar. Geri alma soruları kapatır. t9 güncellendi, t23.py 7 kontrol.
- v11.3: Önizlemedeki temiz duvar birleşimi ana uygulamaya alındı (drawWalls): bir duvar başka duvara bağlanınca (T), bağlandığı yerde beyaz çizgi kesilir, bantlar birleşir. Kullanıcının temsili çizimi: iki oda arasında iç duvar, dış duvarın iç çizgisi birleşimde yok.

## v12 önizleme (16.11 gece) — DUVAR = İKİ BAĞIMSIZ ÇİZGİ + TARALI ALAN (kullanıcı kararı)
- Veri: P.wq taralı dörtgenler {g, n:[a,b,c,d]} (a-b bir yüz, d-c karşı yüz), P.offs kalınlık bağı {n,a,b,d} (lazer ölçeklemede w=1000; ölçülürse esner), P.fills kalınlaşan duvar (kolon). P.walls sadece çizim anında; commit'te solidifyWalls: karşı yüz gerçek çizgi, uç kapakları; başka çizgiye bağlanan uçta (T) aradaki çizgi silinir. S.lastSolid: ⇄ Yön / kalınlık son duvarı yeniden kurar.
- Odalar: duvar alanında oda oluşmaz (isWallFace); bantlı halka yüzü ada kontrolünü engellemez. Katılaştırmadan sonra yeni çizgilerle autoRooms.
- Çıkıntı (Çizerek): bir çizgiden başlayıp bir çizgide biten zincir (cikLineCheck) → kapanış = en kısa çizgi yolu (closingWalk). Seçenekler: "Duvar kalınlaşsın" (kapanış çizgileri silinir, dolgu) / "Ofset korunsun" (kayarApply: yol tabanın yerine, karşı yüz her parçada aynı yana kalınlık kadar ötelenmiş yol, dörtgenler bölünür/yenilenir; köşede de). Varsayılan: oda tarafına → kalınlaşsın, dışa → ofset.
- Kapı/pencere: opGeom kalınlığı dörtgenden; iki yüzde de boşluk çizilmez, tarama kapıda açılır.
- Eski projeler: ilk katılaştırmada "(yedek v11)" kopyası saklanır. DXF: dörtgen kenarındaki çizgiler DUVAR katmanı. Daire ▥ Duvar: halka dörtgenler, karşı yay da P.arcs.
- Testler: q1.py 18 kontrol; önizlemede eski duvar testleri (V11 listesi run_all'da) atlanır, ana uygulamada çalışır.
- Eksik (sıradaki): daire/yayın duvarı kesmesi ve Çıkıntı-Yay iki çizgili duvarda; "Ölçü yazarak" çıkıntı ve serbest çizim çıkıntısı karşı yüzü kaydırmıyor; duvar aksı yakalama yok; kroki yazı kalabalığı.
- v12 önizleme (23:xx): kapı/pencere duvarın karşı çizgisini de kenarlarından böler (splitOppOpenings, commit'te). Ekle → ▨ Duvar alanı: taralı yere dokun = o dörtgen/dolgunun taraması kalkar (P.wqOff'ta saklanır, tekrar dokun = geri gelir); kapalı alana dokun = taralı duvar alanı (oda silinir), tekrar dokun = kalkar, oda geri gelir. Sağdaki ▾/▴ düğmesi alttaki araç çubuğunu gizler/açar. q1.py 25 kontrol.

### v12 tamamlama + v11.4 lazer (16.11 gece, son tur)
- Duvar alanı (tarama) aracı artık GRUP bazında: duvarın bir yerine dokununca o duvarın taramasının tamamı kalkar / geri gelir (P.wqOff).
- cikApplyPath ortak: zincir, Ölçü yazarak, serbest çizim ve yay çıkıntısı hepsi aynı yoldan; duvarsız çizgide klasik çıkıntı (soru yok).
- Daire ile açık duvarı kapatma: wallCapOf + arcWallJoin — iki uç kapağı silinir, iç yay + ofset dış yay, tarama yay boyunca (test q2/6: oda 45.343).
- Lazer (her iki sayfa): laserParse gevşetildi (C0 55 10 + değer>0.01), otomatik gönderim için 3 yazma yöntemi denenir, bağlantı koparsa 1 kez yeniden bağlanır, Ölç panelinde "Gelen veri: N paket · son hex" teşhis satırı; iPhone Safari/Chrome'da Web Bluetooth YOK → Bluefy uyarısı. Test t24.
- Ana: v11.4 (yalnız lazer). v12 ana uygulamaya kullanıcı onayı ile geçecek.
- (16.11 23:40) Kullanıcı: "tarama program yapmasın, en son ben yapayım". Duvar bilgisi (P.wq, kalınlık bağı, çıkıntı sorusu) aynen duruyor; sadece GÖRÜNÜM: P.hatchOn = taralı duvar grupları, dolgularda f.hatch. Program kendiliğinden taramaz; Duvar alanı aracı grup grup açar/kapar. Taralı duvarda "kalınlaşsın" dolgusu taralı gelir.
- (16.11 23:50) Hata: "ölçü uzun gelince nokta dış duvarın dışına atıyor". Sebep (v12): T bağlantı düğümü iç yüz çizgisini ikiye böler ama dış çizgi tek parça; çelişen uzun ölçüde iç yüz kırılıp düğüm dış çizginin dışına çıkıyordu. Düzeltme: adjustGeometry'de onQ — wq kenarı üstündeki ara düğümler o kenarın doğrusunda (ağırlık 3000), sonunda tam yüze oturtulur. Çelişki kırmızı "≠" ve "UYARI ölçüler çelişiyor" ile gösterilir. Test q3. Ana uygulamada (v11) duvar o düğümde kırılır, dışarı taşmaz.

### v11.5 ana (17.11 gece) — kullanıcı: "v11 güzeldi, çıkıntıyı v12 gibi çöz, alt çubuğu gizleme olsun"
- Kullanıcı v12 (bağımsız iki yüz) modelini bıraktı: gönye/ölçü uyarlamasında saçma genişlemeler. Ana uygulama v11 modelinde kalıyor; önizleme v12 olarak duruyor (kullanılmıyor).
- ▾ (fBar) ana uygulamaya eklendi.
- refKolon: turuncu (oda) çizgisinden içeri çizilen çıkıntıda da soru: "Ofset korunsun (o da kayar)" / "Duvar kalınlaşsın (o sabit)". Kalınlaşsın = beyaz yüz düz kalır, çizilen yol ile eski turuncu çizgi arası duvar dolgusu (fills), oda küçülür. Varsayılan: kalınlaşsın; ama derinlik > 60 cm (gerçek girinti), duvarda kapı/pencere varsa ya da çizilen yer odaya katıldıysa (dışa) ofset korunsun. Zincir, Ölçü yazarak, serbest ve yay yollarının hepsinde.
- underFillSet: dolgunun altında kalan eski turuncu çizgiler, ölçü yazısı ve yalnız onlara ait nokta çizilmez; Ölç/kapı seçiminde de seçilmez.
- Test t25 (11). t17 SETUP soru durumunu sıfırlar.

### Önizleme = v11.5 + aşamalar (17.11 gece; kullanıcı: "üstteki sekme olsun, sıralama iyi, hepsini yap, sabah bakarım")
- v12 önizleme bırakıldı (git geçmişinde, testleri test/v12_arsiv). Yeni önizleme: 190c15a'daki önizleme (v11.2 + sekmeler, daire, kontrol, yükseklik, kroki, DXF, objeler, lazerden kalınlık) ile ana uygulamanın v11.3–v11.5 değişiklikleri 3 yollu birleştirildi (git merge-file), 6 çakışma elle çözüldü.
- Kayıt alanı rk4p_* (ilk açılışta ana uygulamanın projeleri kopyalanır; eski v12 önizleme projeleri rk3p_* içinde, dokunulmadı).
- DXF: kolon altındaki gizli turuncu çizgiler yazılmaz, kapı/pencere boşluğunda oda çizgisi bölünür (ekranla aynı).
- run_all: PAGE=onizleme.html → tüm t* + p* (q* arşivde). Yeni p12: uçtan uca (duvar, kapı, köşe kolonu, ölçü, köşegen+hesapla, yükseklik, nokta adı, DXF).
- Bilinen küçük: kolon dolgusu ile duvar taraması birleşim yerinde çok ince desen dikişi görünüyor.
- v11.6 (ana + önizleme): kolon dolgusu duvarla aynı ekran deseniyle taranır (birleşimde dikiş yok).
- v11.7 (17.11 sabah): Ölçü yazarak çıkıntı beyaz yüzden başlatılınca genişlik/derinlik turuncuya uygulanıyordu (beyaz yüz 1.40 geniş, yanlış yerde, soru yok). Artık dokunuş yüze yakınsa (cikFaceCloser her modda) candidate.fc ile yüz saklanır, yol yüzde kurulur ve cikFaceCheck ile beyazdan çizer gibi uygulanır (ofset korunsun / kalınlaşsın sorusu). t25 +2.
- v11.8 (17.11 11:00): Kullanıcı ekranı: bölme duvarın turuncu tarafından başlayan kolon, ucu duvarın öbür (beyaz) yüzüne atlıyordu (cikFaceCheck end(): segX uzatılmış kesişimi de kabul ediyordu) → çizgi bölmeyi kesiyor, dolgu iki tarafa taşıyordu. Artık uç sadece son parça duvarı gerçekten geçiyorsa (t 0..1) beyaza taşınır, yoksa turuncuda kalır (ref). Aynı duvarda ref uçlu durum cikFaceCheck'te ele alınmaz. t25 +1.
- v11.9 (17.11 11:15): Kullanıcının GLM 50-27 CG'si bağlı, 36 paket geliyor ama hepsi 'C0 11 00 3A' (her ~2 sn canlılık sinyali; matom-642/Bosch-GLM-BLE README). Ölçüm paketi (C0 55 10 06 ...) gelmiyor → otomatik gönderme komutu kabul edilmemiş. Değişiklik: yazma sırası yanıtlı önce (gatttool char-write-req gibi), 250 ms bekleme, lazer C0 55 ile yanıt vermezse komut 2.5 sn arayla 6 kez yinelenir; canlılık sinyali ayrı sayılır; '📏 Uzaktan ölç' düğmesi C0 56 01 00 1E komutunu iki kez yazar (CaveSurvey#150). Gerçek cihazla DOĞRULANMADI.
- v11.10 (17.11 23:00): Kullanıcı kararları: lazer ölçüsü Uygula ile oturur; gönye sadece o oda; (çapraz oda içinden — benim önerim).
  - Lazer (ana + önizleme): laserParse yalnız 4. bayt 06 (ölçüm sonucu) — ölçüm yeri değişince gelen durum paketi "rasgele 1 m" yapıyordu. laserValue artık uygulamaz: Ölç'te kutuya cm yazar (Uygula), Gönye'de/Yükseklik'te kutuya yazar (Kaydet). Çizgi seçili değilse bekler, dokununca kutuya gelir.
  - Önizleme Gönye (eski Kontrol aracı, 📐): çapraz kaydı odaya bağlı (d.room); "📐 Gönyele: Oda" → adjustGeometry({only: oda sınırındaki düğümler}): dışarıdaki düğümler sabit (1e6), ölçek sabit, uzun çizgilerin yönü serbest (0.3), kısa (<0.6 m) kırıklar yönünü korur (300), ölçülmemiş boy kendi uzunluğuyla 300/L² (kısa = sert), düz duvar ara düğümleri doğruda (COL). Önizlemede köşe açıları (°) yazar, Onayla/Vazgeç. Eski "Geometriyi hesapla" (tüm çizim, kırıkları eziyordu) kaldırıldı. Test p13 (+p2, p12 güncellendi).
- v11.11 (18.11 01:00): Kullanıcı JSON'u (Oda 5, Oda 4'ün beyaz yüzüne dayanan oda). (1) Ölç yüz parçası komşu duvarın dış (turuncu) hizasına kadar uzuyordu: faceDim'de dayanan duvarın öbür yüzü, dayandığı yüz eğikse kesişimle bulunur (ana+önizleme). (2) Gönye bu odada çalışmıyordu: köşeler düğüm değil (yüz kesişimi). Çapraz uçları artık düğüm + yerel ofset (cornerAnchor: en yakın duvar düğümü, en uzun çizgisinin yönünde al/be) — dengelemede duvar dönünce birlikte döner. Gönyede oynayan düğümler: sınır düğümleri + yüz köşelerinin düğümleri (başka odanın sınırında değilse). Uyumsuzluk sadece o odanın ölçülerinden. Açılarda duvar ucu sivrisi atılır. roomOfSeg'deki yorum satırı kodu yutuyordu (düzeltildi). Test p14.
- v11.12-önizleme (18.11 01:30): Kullanıcı: Oda 5'te Oda 4'ün 6.85 duvarının diğer yüzüne 4.405 girince Oda 4 bozuluyordu. Artık: tamamı lazerle ölçülmüş (bitmiş) odaların düğümleri başka yerde ölçü alınınca sabit (doneRoomNodes → adjustGeometry opts.fix, 1e9). Yüz parçası ölçüsünde (applyDim) ayrıca ortak ölçek K sabit (opts.fixK) — dayanılan duvar değil karşıdaki (Oda 5'in sağ) duvar kayar. Uyarı sadece sabit olmayan ölçülerden. Çizgi ölçüsünde (applyMeasure) de bitmiş odalar sabit. Test p14 +1.
- v11.12 / v11.13-önizleme (18.11 11:40): Kullanıcı JSON (mslm, Oda 4): 5,6 cm kırıklar parmakla 23°/69° eğik çizilmiş, program yönü çizimden aldığı için kırık kayboluyordu.
  - Önizleme Gönye aracı: "Kırık sınırı" 10/20/30/50 cm (SET.jog, varsayılan 30, kayıtlı); sınır altı kısa parça (iki yanı uzun) "🔧 Kırıkları düzelt: Oda (n)" → adjustGeometry({only: oda düğümleri, keepAngles, jogs}): kırık önceki duvara dik (açı, 3000), sonraki duvar öncekine paralel (3000), kırığın çizim yönü yok sayılır; önizleme + onay. roomCycle: oda köşeleri düğümse onlar, değilse odayı içine alan kapalı duvarın düğümleri. Test p15.
  - Lazer (ana+önizleme): "ölçüm yeri değişince ölçü almıyor" → 4. bayt ölçüm yerine göre değişiyormuş; laserParse yine C0 55 10 hepsini kabul ediyor (değer kutuya gelir, Uygula ile oturur; tek başına gelen yanlış değer çizimi bozmaz).
- v11.13 / v11.14-önizleme (18.11 12:30): Yüzden (beyaz) ölçülen duvar: beyaz yüz yeşil çizilir + ölçüsü yüzün yanında (drawFaceMeas); turuncu çizgi hesaplanan olarak turuncu kalır (yeşil değil). Öbür yüz (turuncu) de ölçülünce ikisi de yeşil, ikisi de tutulur, köşedeki komşu duvarların kalınlığı hesaplanır (A, zaten çalışıyordu — denendi: 3.700 yüz + 4.150 çizgi → komşu duvarlar 22.5 cm).
- v11.14 / v11.15-önizleme (26.11): Kullanıcı: "ölçü alınca tüm odalar ölçeklensin, çizim bozuluyor" → "bağlantıları korusun ama bana sorsun". neighborAsk (ana+önizleme): ölçüden sonra ölçülen çizginin odası dışındaki bir odanın ŞEKLİ bozulduysa (çizgi oranları/açıları farklı değiştiyse; bütün halinde ölçekleme/öteleme sayılmaz) Ölç panelinde soru: "🔗 Bağlantı korunsun" (varsayılan, eski davranış) / "Komşular yerinde kalsın" (ölçülen odanın sınırındaki, başka odaya ait olmayan düğümler dışında her şey sabit). Ana adjustGeometry'ye opts.fix eklendi. Lazer boy ağırlığı 3000 → 1e4 (ölçü eskiz yönlerine daha baskın; çelişki yine uyarılır). neighborAsk'ta afterLoad kullanılmaz (yüz boyunca çizgileri siliyordu). Test t26.

## v11.15 / v11.16-önizleme — Duvar köşe düzenleme + Kırığı sil
- Seç: duvar (taralı alan) seçilince tüm duvar köşelerinde tutamak çıkar; köşeden tutup sürükleyince duvar ve oda birlikte gelir. Panelde "Köşeden tutup sürükle" ipucu.
- Seç: kırık çizgisi seçilince (iki ucunda tek komşu, komşular ±25° paralel, kırık komşulardan kısa) "Kırığı sil" düğmesi. Basınca kırık silinir, uç düğüm iki komşunun düz hattına (p–q) taşınıp birleşir; duvar/oda korunur. Duvar yüzü seçiliyken o parça kırıksa aynı düğme orada da çıkar. Geri al ile döner.
- jogInfo / jogDelete / faceJog fonksiyonları. Test: t27 (her iki sayfa).

## YENİ PROGRAM: cad.html (cad-1.0) — sıfırdan, duvarsız, AutoCAD mantığı (aşama 1+2)
Adres: https://aknergn09-maker.github.io/rolove/cad.html — v11 (index.html) ve önizleme dokunulmadan duruyor.
Kaynak: cad_src/ (shell.html, icons.json, cad_geo.js = geometri çekirdeği DOM'suz, cad_app.js = arayüz). `python3 cad_src/build.py` → cad.html. Kayıt anahtarı rcad1_doc.
Kararlar (kullanıcıyla netleşti):
- Duvar/oda/m² yok. Sadece objeler: line, pl (pline, kapalı/açık), cir, arc. Koordinat obje içinde (paylaşımlı düğüm yok).
- Arayüz: sadece sağda tek kaydırmalı sütun, sadece simge. Sıra: geri, ileri | Seç, Çiz, Düzenle | Yakalama | Sığdır. Çiz/Düzenle/Yakalama'ya basınca yanında aynı genişlikte pencere açılır, seçince kapanır.
- Çiz: Line, Pline, Circle (merkez+yarıçap), Arc (3 nokta). İlk noktaya dokununca kapanır; son noktaya tekrar dokununca veya ✓ ile biter. Geri al çizim sırasında son noktayı siler.
- Hızlı uzunluk (line/pline): 10/50/100 cm basıldıkça toplar, ⌫ son basışı siler. Oklar ekran yönünde: yatay giderken ↑↓, dikey giderken ←→, ilk noktada 4 ok. Oka basınca çizgi atılır. Kroki ölçeği.
- Yakalama (aç/kapa): köşe(+kesişim), orta, obje üstü, Ortho (önceki çizgiye/başlanan objeye göre 90°), XY (ekrana göre 90°), aks takibi (çizgi uzantısı, 10 px). Dokunurken büyüteç.
- Kapalı alanlar hafif mavi dolgu (düzlem grafı, faces()).
- Seç: dokun = seç/bırak, boşa dokun = temizle, boşta sürükle = kaydır. Mavi köşe tutamağı = köşeyi taşı (aynı noktadaki diğer objelerin uçları da gelir). Turuncu orta tutamak = kenarı paralel kaydır; komşu kenarlar kendi doğrultusunda uzar/kısalır, kenar üstünde T ile biten çizgiler kenarda kalır. Aynı doğrultudaki ardışık pline parçaları tek kenar (ileride kapı noktaları için).
- Düzenle: Offset (cm tuş takımı; obje sonra taraf), Trim (tüm objeler kesici), Extend, Fillet (r=0 köşe birleştir), Taşı/Kopyala (temel noktadan hedefe sürükle; seçim yoksa dokunulan obje), Explode, Join (seçim ya da dokunulan zincir), Sil. Offset grup YOK (kullanıcı kararı).
- Düğmeler click değil pointerup ile (sürükleme sonrası ilk dokunuş kaybolmasın).
Sonraki aşamalar (konuşuldu, yapılmadı): kapı/pencere (2 dokunuş, pline'a aynı doğrultuda kırık noktası ekler, DXF'te çizgi kesintisiz + ayrı katman), lazer ölçü notları (nokta-nokta, noktadan dik, çizgiden dik, dik ayak/dik boy; çizimi değiştirmez), nokta adları export'ta (kullanıcınınkiler kalır, diğerleri X1..), total CSV/NCN içe alma (sabit), DXF import (ayrı katman) ve export, PC'de gönye/ölçek programı.
Testler: test/c1.py, test/c2.py (`PAGE=cad.html python3 test/run_all.py`).

### cad-1.1
- Aks takibi: çizilen zincirin noktalarından (başlangıç dahil) ve parmağın üzerinden geçtiği son 2 köşe/orta noktadan 90° hiza çizgileri (zincirin ilk kenar doğrultusu ve dik; XY açıksa eksenler). Ortho ışınıyla kesişince yakalar → dikdörtgenin 4. köşesi başlangıç hizasına oturur.
- Kapalı alan hesabına yay ve daireler girdi (faces() yayları 64'te bir parçalara böler).
- Explode/Join sonucu 1 sn yeşil/sarı yanıp söner, uç noktalar görünür. Join: zincir otomatik birleşmezse dokunulan obje seçili kalır, sonraki dokunulan ona eklenir (devam edilebilir), boşa dokununca bırakır.
- Sütundaki Çiz/Düzenle: basınca son kullanılan araç direkt aktif + pencere açılır; pencerede başkası seçilebilir; tuvale dokununca pencere kapanır ve dokunuş işlenir. Bu yolla açılınca Sil/Explode/Join seçime hemen uygulanmaz (sadece pencereden seçilince).
- Pencere açıkken hızlı uzunluk ve offset tuş takımı gizlenir (pencereyi örtüyordu).
- Test: c3.py.

### cad-1.2
- Hızlı uzunluk paneli tek sütun (toplam, 10, 50, 100, ⌫, oklar, ✓ alt alta). Panel uzunsa kendi içinde kayar.
- Katman sırası kesin: açılan pencere (z 30) > sağ sütun (z 20) > alt paneller (z 10); pencere açıkken alt paneller zaten gizli.

### cad-1.3
- Offset tuş takımı küçüldü (36 px) ve varsayılan kapalı: sadece değeri gösteren küçük düğme (örn. 15). Basınca tuş takımı açılır, yeni değer baştan yazılır, ✓ ile kapanır.
- Bekleyen öneri (onay bekliyor): çizim modunda sağ sütun yerine sadece ≡ (menüye dön), geri, ileri + hızlı uzunluk; A = tek şerit, B = üstte mini sütun + altta ayrı panel, parmak tuvaldeyken soluk.

### cad-1.4 — çizim modu (öneri B, onaylandı)
- Çizim sürerken (line/pline zinciri, daire merkezi, yay noktaları varken) sağ sütun küçülür: ≡ (normal sütun), geri, ileri, sığdır. 10/50/100 paneli sağ altta, sütunla aynı kenarda, 40 px düğmeler.
- Parmak tuvaldeyken ikisi %30 soluk. ✓ / kapanma / geri al ile çizim bitince normal sütun kendiliğinden döner. ≡ çizimi bozmadan normal sütunu açar; tuvale dokununca küçük sütuna dönüp çizime devam eder.
- Test: c4.py (c3 güncellendi: çizim sırasında araç değiştirmek için önce ≡).

### cad-1.5 — aşama 3 (kapı/pencere) + aşama 4'ün netleşen kısmı (DXF)
- Kaynak: cad_src/cad_ops.js (build: GEO + OPS + APP). Kapı/pencere D.ops: {id, t:'door'|'win', a, b, hinge, sw}.
- Sütun: Kapı/Pencere grubu (son kullanılan direkt), Dosya grubu (DXF dışa, DXF içe, yeni çizim — yeni çizim 3 sn içinde ikinci dokunuşla).
- Yerleştirme: çizgiye 2 dokunuş (yakalamalı, çizgi üstüne izdüşüm). Pline'a aynı doğrultuda 2 kırık noktası eklenir (pline ve kapalı alan bozulmaz). 3–60 cm içinde paralel çizgi (offset ikizi) varsa kapı/pencere iki yüze yayılır, ikiz pline'a da kırık noktası eklenir; kapı ikizden uzağa (odaya) açılır. İkiz yoksa tek çizgide ±5 cm sembol.
- Kapı aracıyla kapıya dokununca 4 durum döner (menteşe sağ/sol × açılış tarafı). Seç ile kapı seçilir: panel (menteşe ↔, taraf ↕, kapı⇄pencere, sil) + iki uç tutamağı (çizgi boyunca, pline köşeleri ve ikiz köşeleri birlikte). Kenar orta tutamağıyla kayan kenardaki kapılar birlikte gelir; köşe taşınınca o köşedeki kapı ucu gelir; Taşı/Kopyala kapıları da taşır/kopyalar. Sil aracı kapıyı siler ve eklenen kırık noktalarını kaldırır.
- Ekranda kapı/pencere yerinde çizgi boşluk gibi boyanır (geometri kesintisiz). Şablon v11 ile aynı (söveler, kanat + kesik yay; pencere 3 çizgi).
- DXF dışa (R12, AC1009, ANSI_1254): CIZIM (LINE, kapalı/açık POLYLINE, CIRCLE, ARC), KAPI, PENCERE, NOKTA (POINT + TEXT X1.. — tüm köşe/uçlar ve kapı uçları; kullanıcı adı verme henüz yok), IMPORT (altlık). Dosya adı cizim_YYYYMMDD_HHMM.dxf, iPhone'da paylaş menüsü.
- DXF içe: LINE, LWPOLYLINE, POLYLINE/VERTEX, CIRCLE, ARC, POINT (TEXT/INSERT/blok yok). Altlık gri, seçilemez/düzenlenemez, yakalanır, kapalı alan dolgusu yapmaz, trim/extend sınırı olur.
- Test: c5.py.
Aşama 4'ün KALANI onay bekliyor: lazer ölçü notları, ölçü türleri, nokta adı verme, total CSV/NCN, ölçü/koordinat listesi.

### cad-1.6 — kalınlık sınırı ayarı
- Sütunda ⚙ Ayarlar: kapı/pencere kalınlık arama sınırı (cm, varsayılan 60, 5–300). Kaydedilir (rcad1_doc.thMax).
- opCands: sınır içindeki paralel çizgiler yakından uzağa. Kapı/pencere o.th: yerleştirirken en yakın; 0 = tek çizgi; sonradan duvar kaysa da hatırlanan değere en yakın aday seçilir (başka çizgiye atlamaz).
- Kapı/pencere panelinde kalınlık düğmesi: en yakın → sonraki … → tek çizgi → en yakın; eski ikizdeki kırık noktaları kalkar, yenisine eklenir.
- Tutamaklar üst üste gelirse orta (kenar) tutamağı öncelikli.
- Test: c6.py.

### cad-1.7 — Düzleştir
- Düzenle → Düzleştir (flat): pline'da girinti/çıkıntının herhangi bir parçasına dokun. İki yandaki duvar aynı hizadaysa aradaki köşeler silinir (düz geçer). Paralel ama kayıksa (kademe) uzun duvarın hizası esas alınır, kısa taraf applyEdge ile o hizaya çekilir (komşusu kendi doğrultusunda uzar), artık köşeler temizlenir.
- Aynı doğrultudaki parçalar tek kenar sayılır (kapı kırık noktaları bozulmaz); kaldırılacak bölgede kapı noktası varsa işlem yapılmaz (kırmızı uyarı).
- Pencere: 1 parçalık (kademe) ve 3 parçalık (girinti) desenler, dokunulan parçanın etrafında aranır. Sadece pline (ayrı çizgiler önce Join).
- Test: c7.py.
- Bekleyen öneri: komşu alanlarda offset'in diğer alana giren / üst üste binen / araya düşen kısmını otomatik kesme (sadece yeni offset kesilir).

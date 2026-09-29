ROULETTE PRO AI V2.9.42 • LOBİ BİTTİ DÜZELTME

SORUN
- Masalar gezilip veri alındıktan sonra program bazen hâlâ masa açıkmış gibi davranıyordu.
- Ekran aslında Pragmatic Rulet lobisine dönmüş olmasına rağmen durum satırı şurada kalabiliyordu:
  SEKMELİ TOPLA: oyun içi Lobi düğmesi tıklandı • Pragmatic Rulet lobisi bekleniyor
- Bunun nedeni bazı Pragmatic iframe'lerinin masa kapanınca hemen temizlenmemesi; eski oyun iframe'i arkada SON500/Lobi kontrolü raporlamaya devam edebiliyordu.

DÜZELTME
1. Lobiye dönüş koruma süresi eklendi.
   - Program oyun içi Lobi düğmesine bastıktan sonra kısa süre eski oyun iframe raporlarını yok sayar.
   - Bu sırada gerçek görünen lobby kartları öncelik kazanır.

2. Lobby görünürse masa bekleme kilidi temizlenir.
   - Gerçek kartlar görünüyorsa program artık "hâlâ masadayım" diye düşünmez.
   - Eski oyun verisi/iframe'i bekleme durumunu yeniden başlatamaz.

3. Tur sonu algısı hızlandırıldı.
   - Program lobby sonunu bir kez gördüyse ve tıklanacak yeni kart kalmadıysa taramayı bitirir.
   - Durum artık otomatik tekrar beklemesine geçer.

4. Önceki düzeltmeler korundu.
   - SON500 paneli görünüyorsa masa kilitlenip 500/500 okunur.
   - PowerUp Rulet / Sıcak & Soğuk-only masalar atlanır.
   - SON500 olmayan masalar hata değil, atla sayılır.

BEKLENEN DURUM
- Masa verisi alınca:
  SEKMELİ TOPLA: sağ-alt SON500 paneli kaydedildi • ... • 500/500
- Lobiye dönünce:
  SEKMELİ TOPLA: Pragmatic Rulet lobisine dönüldü • ... kart • sıradaki masa seçiliyor
- Tüm görülen/liste sonu masalar bitince:
  SEKMELİ TOPLA: lobi sonuna ulaşıldı • ... • 5 dk sonra otomatik tekrar

NOT
- Bu sürüm özellikle ekran lobbydeyken programın eski masa iframe'ine takılı kalması sorununu düzeltir.

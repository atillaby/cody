# Proje Kuralları

1. Test ortamı kullanılmayacak - direkt production odaklı geliştirme
2. .env dosyası sadece proje sahibinin kontrolünde
3. Sadece OKX borsası entegrasyonu kullanılacak
4. OKX'teki tüm çiftler ve USDT yönetimi:
   - OKX borsasındaki tüm çiftler analiz edilecek
   - Ana bakiye her zaman USDT olarak tutulacak
[... 23 kuralın tamamı ...]

Not: Yeni kurallar eklendikçe güncellenecektir.

# 🚨 Trading Bot Kuralları

## 📊 Risk Yönetimi
- [x] Maksimum pozisyon büyüklüğü: Portföyün %5'i  (risk_manager.py içinde eklendi)
- [x] Stop-loss zorunluluğu: Her işlemde -%1 (risk_manager.py'de calculate_stop_levels)
- [x] Kaldıraç kullanımı: Sadece spot işlemler (trade_manager.py spot işlemler)
- [x] Risk/Ödül oranı: 1:2 (risk_manager.py'de risk_reward_ratio)

## 💰 İşlem Kuralları
- [x] Minimum işlem tutarı: 10 USDT (trade_manager.py'de min_trade_amount)
- [x] Maksimum işlem tutarı: Portföyün %5'i (risk_manager.py'de max_position_size)
- [x] USDT rezervi: Her zaman toplam portföyün %20'si (risk_manager.py'de usdt_reserve_ratio)
- [x] Açık pozisyon limiti: Maksimum 5 adet (risk_manager.py'de max_open_positions)

## ⏱️ Zaman Yönetimi
- [x] İşlem kontrolü: Her 5 dakikada bir (trade_manager.py'de asyncio.sleep(300))
- [x] Portföy optimizasyonu: Her 15 dakikada bir (portfolio_manager.py'de implement edildi)
- [x] Stop-loss kontrolleri: Her 1 dakikada bir (trade_manager.py'de monitor_positions)
- [x] Kar realizasyonu: Hedef fiyata ulaşıldığında (trade_manager.py'de take_profit)

## 🔄 Strateji Kuralları
- [x] Trend takibi zorunluluğu (moving_average.py'de implement edildi)
- [x] Hacim kontrolü şartı (trade_validator.py'de min_volume kontrolü)
- [x] Minimum 3 gösterge onayı (strategy_manager.py'de multiple_strategy_check)
- [x] RSI aşırı alım/satım kontrolü (rsi_strategy.py'de implement edildi)

## 🚫 Yasaklı İşlemler
- [x] Kaldıraçlı işlemler (sadece spot işlemler yapılıyor)
- [x] Market emirleri (sadece limit emirler kullanılıyor)
- [x] Yüksek spread olan çiftler (trade_validator.py'de spread kontrolü)
- [x] Düşük hacimli coinler (trade_validator.py'de min_volume kontrolü)

# Kod Yazım Kuralları v1.1

## ✅ Temel Kurallar
- [x] Her modül/sınıf tek bir sorumluluk almalı
- [x] Bir sınıf/modül 300 satırı geçmemeli
- [x] Fonksiyonlar 50 satırı geçmemeli
- [x] Doc string kullanımı zorunlu
- [x] Type hint kullanımı zorunlu
- [x] İsimlendirmeler açıklayıcı olmalı

## ✅ Loglama
- [x] Her önemli işlem loglanmalı
- [x] Hata durumları detaylı loglanmalı
- [x] Log seviyeleri doğru kullanılmalı
- [x] Her modül kendi logger'ını oluşturmalı

## ✅ Hata Yönetimi
- [x] Try-except blokları kullanılmalı
- [x] Hatalar üst katmanlara uygun şekilde iletilmeli
- [x] Custom exception sınıfları kullanılmalı
- [x] Recovery mekanizmaları eklenmelı

## ✅ Asenkron Programlama
- [x] Async/await kullanımı
- [x] Rate limiting uygulanmalı
- [x] Task yönetimi düzgün yapılmalı
- [x] Kaynak temizliği için finally blokları

## ✅ Konfigürasyon
- [x] .env dosyası kullanımı
- [x] Config doğrulama
- [x] Hassas bilgiler environment'ta tutulmalı
- [x] Default değerler tanımlanmalı

## ✅ Veritabanı/Cache
- [x] Redis connection pooling
- [x] Bağlantı yönetimi
- [x] Timeout mekanizmaları
- [x] Veri serializasyonu

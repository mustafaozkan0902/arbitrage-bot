import requests
import time
from tabulate import tabulate

# === API URL'leri ===
URL_BINANCE = "https://api.binance.com/api/v3/ticker/bookTicker"
URL_PARIBU = "https://www.paribu.com/ticker"

# === Binance coin listesi çek
def get_binance_coins():
    try:
        data = requests.get(URL_BINANCE, timeout=10).json()
        coins = set()
        for item in data:
            symbol = item["symbol"]
            if symbol.endswith("USDT"):
                coins.add(symbol.replace("USDT", ""))
        return coins
    except Exception as e:
        print("Binance verisi alınamadı:", e)
        return set()

# === Paribu coin listesi çek
def get_paribu_coins():
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        data = requests.get(URL_PARIBU, headers=headers, timeout=10).json()
        return {key.replace("_TL", "") for key in data.keys() if key.endswith("_TL")}
    except Exception as e:
        print("Paribu verisi alınamadı:", e)
        return set()

# === Ortak coin listesini oluştur ===
paribu_coins = get_paribu_coins()
binance_coins = get_binance_coins()

# Hariç tutulacak coinler
EXCLUDED_COINS = {"bal", "gal", "het", "beam", "clv", "omg", "pda", "reef", "waves", "hnt", "enj"}

COINS = sorted([
    coin for coin in (paribu_coins & binance_coins)
    if coin.lower() not in EXCLUDED_COINS
])

print(f"Toplam kontrol edilecek coin sayısı: {len(COINS)}")

# === Kullanıcıdan arbitraj eşiği al ===
while True:
    try:
        min_fark_normal = 1.0
        min_fark_ters = 1.0
        break
    except ValueError:
        print("Lütfen geçerli bir sayı girin.")

# === Binance verisi al
def get_binance_data():
    try:
        data = requests.get(URL_BINANCE, timeout=10).json()
        return {item["symbol"]: item for item in data}
    except:
        return {}

# === Paribu verisi al
def get_paribu_data():
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        return requests.get(URL_PARIBU, headers=headers, timeout=10).json()
    except:
        return {}

# === Arbitraj hesapla
def calculate_arbitrage(binance_data, paribu_data, min_fark_normal, min_fark_ters):
    normal_results = []
    ters_results = []

    try:
        usdt_tl = float(paribu_data['USDT_TL']['lowestAsk'])
    except:
        print("USDT_TL verisi alınamadı.")
        return normal_results, ters_results

    for coin in COINS:
        try:
            b_symbol = coin + "USDT"
            p_symbol = coin + "_TL"

            if b_symbol not in binance_data or p_symbol not in paribu_data:
                continue

            b_ask = float(binance_data[b_symbol]["askPrice"])
            b_bid = float(binance_data[b_symbol]["bidPrice"])
            p_ask = float(paribu_data[p_symbol]["lowestAsk"])
            p_bid = float(paribu_data[p_symbol]["highestBid"])

            fiyat_binance_tl_ask = b_ask * usdt_tl  # Binance satış fiyatı
            fiyat_binance_tl_bid = b_bid * usdt_tl  # Binance alış fiyatı

            # Normal arbitraj: Paribu'da sat > Binance'ten al
            fark_normal = 100 * (1 - fiyat_binance_tl_ask / p_bid)
            if fark_normal >= min_fark_normal:
                normal_results.append([
                    coin,
                    round(fark_normal, 2),
                    round(p_bid, 4),
                    round(b_ask, 4),
                    round(fiyat_binance_tl_ask, 2)
                ])

            # Ters arbitraj: Binance'te sat > Paribu'dan al
            fark_ters = 100 * (1 - p_ask / fiyat_binance_tl_bid)
            if fark_ters >= min_fark_ters:
                ters_results.append([
                    coin,
                    round(fark_ters, 2),
                    round(b_bid, 4),
                    round(p_ask, 4),
                    round(fiyat_binance_tl_bid, 2)
                ])

        except:
            continue

    return normal_results, ters_results

# === Ana döngü ===
if __name__ == "__main__":
    while True:
        binance_data = get_binance_data()
        paribu_data = get_paribu_data()
        normal_results, ters_results = calculate_arbitrage(binance_data, paribu_data, min_fark_normal, min_fark_ters)

        if normal_results:
            print("\n➡️  --- Normal Arbitraj (Paribu > Binance) ---")
            print(tabulate(normal_results, headers=["Coin", "Fark %", "Paribu Bid (TL)", "Binance Ask (USDT)", "Binance TL"], tablefmt="pretty"))
        else:
            print("\n➡️  Uygun normal arbitraj fırsatı yok.")

        if ters_results:
            print("\n⬅️  --- Ters Arbitraj (Binance > Paribu) ---")
            print(tabulate(ters_results, headers=["Coin", "Fark %", "Binance Bid (USDT)", "Paribu Ask (TL)", "Binance TL"], tablefmt="pretty"))
        else:
            print("\n⬅️  Uygun ters arbitraj fırsatı yok.")

        time.sleep(5)

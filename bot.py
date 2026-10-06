import time
import requests
import pandas as pd
import pandas_ta as ta
import warnings
warnings.filterwarnings("ignore")

BOT_TOKEN = "8663767442:AAEFpBh0V1eu5tBrWWc0Ki2EmVdS9f_rHiQ"
CHAT_ID = "1494316515"
INTERVAL = "Min15"
WAIT_TIME = 20

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

notified_signals = {}

def send_telegram_message(bot_token, chat_id, message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML", "disable_web_page_preview": True}
    for attempt in range(3):
        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200 and response.json().get("ok", False):
                return True
        except Exception:
            time.sleep(2)
    return False

BINANCE_MEXC_SYMBOLS = [
    "BTC_USDT", "ETH_USDT", "SOL_USDT", "XRP_USDT", "BNB_USDT", "DOGE_USDT", "ADA_USDT", "AVAX_USDT", "LINK_USDT", "DOT_USDT",
    "NEAR_USDT", "SHIB_USDT", "LTC_USDT", "TRX_USDT", "BCH_USDT", "UNI_USDT", "ICP_USDT", "APT_USDT", "SUI_USDT",
    "FIL_USDT", "PEPE_USDT", "ETC_USDT", "RENDER_USDT", "INJ_USDT", "TIA_USDT", "STX_USDT", "OP_USDT", "ARB_USDT", "SEI_USDT",
    "FET_USDT", "GRT_USDT", "THETA_USDT", "FTM_USDT", "AAVE_USDT", "RUNE_USDT", "FLOW_USDT", "KAS_USDT", "ALGO_USDT", "GALA_USDT",
    "WIF_USDT", "FLOKI_USDT", "BONK_USDT", "ORDI_USDT", "LDO_USDT", "MKR_USDT", "SNX_USDT", "CRV_USDT", "SAND_USDT", "MANA_USDT",
    "DYDX_USDT", "AXS_USDT", "CHZ_USDT", "EGLD_USDT", "CFX_USDT", "BLUR_USDT", "COMP_USDT", "MINA_USDT", "KAVA_USDT", "ROSE_USDT",
    "JUP_USDT", "STRK_USDT", "ENA_USDT", "W_USDT", "NOT_USDT", "ZK_USDT", "MEW_USDT", "IO_USDT", "ZRO_USDT", "TURBO_USDT",
    "POPCAT_USDT", "NEIRO_USDT", "CATI_USDT", "HMSTR_USDT", "EIGEN_USDT", "1000SATS_USDT", "MEME_USDT", "BEAM_USDT", "ALT_USDT",
    "MANTA_USDT", "DYM_USDT", "PIXEL_USDT", "PORTAL_USDT", "AEVO_USDT", "ETHFI_USDT", "BOME_USDT", "REZ_USDT", "BB_USDT",
    "DOGS_USDT", "PENDLE_USDT", "WLD_USDT", "AR_USDT", "ENS_USDT", "GMT_USDT", "GMX_USDT", "IMX_USDT", "JASMY_USDT", "TRB_USDT"
]

def get_klines_mexc_futures(symbol, interval="Min15"):
    url = f"https://contract.mexc.com/api/v1/contract/kline/{symbol}?interval={interval}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=5)
        if response.status_code == 200:
            res_json = response.json()
            if res_json.get("success") and "data" in res_json:
                data = res_json["data"]
                df = pd.DataFrame({
                    "timestamp": data["time"],
                    "open": data["open"],
                    "close": data["close"],
                    "high": data["high"],
                    "low": data["low"]
                })
                df["high"] = df["high"].astype(float)
                df["low"] = df["low"].astype(float)
                df["close"] = df["close"].astype(float)
                return df
    except Exception:
        pass
    return None

def scan_market():
    symbols = list(set(BINANCE_MEXC_SYMBOLS))
    print(f"\n🏹 Bot Taranıyor... Toplam {len(symbols)} Parite", flush=True)
    
    match_count = 0
    success_count = 0

    for symbol in symbols:
        df = get_klines_mexc_futures(symbol, INTERVAL)
        if df is None or len(df) < 200:
            time.sleep(0.05)
            continue
            
        success_count += 1
        
        df["EMA20"] = ta.ema(df["close"], length=20)
        df["EMA50"] = ta.ema(df["close"], length=50)
        df["EMA100"] = ta.ema(df["close"], length=100)
        df["EMA200"] = ta.ema(df["close"], length=200)
        
        current_candle = df.iloc[-1]
        candle_timestamp = current_candle["timestamp"]
        high = current_candle["high"]
        low = current_candle["low"]
        current_close = current_candle["close"]
        
        ema20 = current_candle["EMA20"]
        ema50 = current_candle["EMA50"]
        ema100 = current_candle["EMA100"]
        ema200 = current_candle["EMA200"]

        if pd.isna(ema20) or pd.isna(ema50) or pd.isna(ema100) or pd.isna(ema200):
            continue

        is_bullish_aligned = ema20 > ema50 > ema100 > ema200
        is_bearish_aligned = ema20 < ema50 < ema100 < ema200

        diff_20_50 = (ema20 - ema50) / ema50
        diff_50_100 = (ema50 - ema100) / ema100
        
        is_bullish_expanded = (diff_20_50 > 0.003) and (diff_50_100 > 0.003)
        is_bearish_expanded = (diff_20_50 < -0.003) and (diff_50_100 < -0.003)

        ema20_touch = (low <= ema20 <= high)

        recent_candles = df.iloc[-12:-1]
        prev_candles = df.iloc[-35:-12]
        
        recent_max_high = recent_candles["high"].max()
        previous_max_high = prev_candles["high"].max()
        
        recent_min_low = recent_candles["low"].min()
        previous_min_low = prev_candles["low"].min()

        valid_bullish_breakout = is_bullish_aligned and is_bullish_expanded and (recent_max_high > previous_max_high * 1.004)
        valid_bearish_breakout = is_bearish_aligned and is_bearish_expanded and (recent_min_low < previous_min_low * 0.996)

        if ema20_touch and (valid_bullish_breakout or valid_bearish_breakout):
            signal_key = f"{symbol}_{candle_timestamp}"
            if notified_signals.get(symbol) == signal_key:
                continue

            clean_symbol = symbol.replace("_", "")
            binance_link = f"https://www.binance.com/tr/futures/{clean_symbol}"
            
            if valid_bullish_breakout:
                trend_type = "KATI SAPAN LONG (NET HH KIRILIMI)"
                desc = f"Fiyat yeni yüksek tepe ({recent_max_high}) yaptıktan sonra EMA20 desteğine çekildi!"
            else:
                trend_type = "KATI SAPAN SHORT (NET LL KIRILIMI)"
                desc = f"Fiyat yeni düşük dip ({recent_min_low}) yaptıktan sonra EMA20 direncine çekildi!"

            message = (
                f"🏹 SAPAN STRATEJİSİ SİNYALİ!\n\n"
                f"Parite: #{clean_symbol} (15m Futures)\n"
                f"Sinyal: {trend_type}\n"
                f"Anlık Fiyat: {current_close}\n\n"
                f"📊 EMA Değerleri:\n"
                f"• EMA 20: {round(ema20, 4)}\n"
                f"• EMA 50: {round(ema50, 4)}\n"
                f"• EMA 100: {round(ema100, 4)}\n"
                f"• EMA 200: {round(ema200, 4)}\n\n"
                f"💡 Açıklama: {desc}\n\n"
                f"🔗 <a href='{bin_link}'>Grafiği Tarayıcıda Aç</a>"
            ).replace("bin_link", binance_link)

            print(f"🎯 Temiz Sapan Sinyali: {clean_symbol}", flush=True)
            if send_telegram_message(BOT_TOKEN, CHAT_ID, message):
                notified_signals[symbol] = signal_key
                match_count += 1

        time.sleep(0.1)
    
    print(f"✅ Tarama bitti. İşlenen: {success_count}/{len(symbols)} | Sinyal: {match_count}", flush=True)

send_telegram_message(BOT_TOKEN, CHAT_ID, "🏹 Sapan Botu (Render 7/24 Sürümü) Başlatıldı!")

while True:
    try:
        scan_market()
        time.sleep(WAIT_TIME)
    except Exception as e:
        print(f"Hata oluştu: {e}", flush=True)
        time.sleep(10)

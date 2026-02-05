import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import xgboost as xgb
import re
import threading
import time
import sqlite3
import os
from datetime import datetime
from flask import Flask, request, jsonify, render_template

# --- BLINDAGEM DE DIRETÓRIO ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

app = Flask(__name__)

# --- CONFIGURAÇÕES DE CALIBRAÇÃO (MIRA DO SNIPER) ---
MAGIC_NUMBER = 44000
LOT_SIZE = 0.01             # Começando baixo para validar a nova mira
TIMEOUT_EXIT = 7200         # 2 Horas (Tempo para a tendência maturar)
STOP_LOSS_PONTOS = 800      # Mais respiro (Evita ser stopado pelo ruído)
TAKE_PROFIT_PONTOS = 2400   # Alvo de Tendência (Busca o lucro real)

# ALTERAÇÃO SOLICITADA: Baixando o rigor para evitar vetos excessivos
PROBABILIDADE_MINIMA_BASE = 0.62 

DB_NAME = os.path.join(BASE_DIR, "44trade_brain.db")
MODEL_NAME = os.path.join(BASE_DIR, "modelo_sniper_v3.json")

def log_interno(mensagem):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        with open(os.path.join(BASE_DIR, "monitor_interno.log"), "a", encoding='utf-8') as f:
            f.write(f"[{timestamp}] {mensagem}\n")
    except:
        pass
    print(mensagem)

# --- MÓDULO AUTO-EVOLUTIVO (AJUSTADO PARA NÃO TRAVAR) ---
def calcular_threshold_evolutivo():
    try:
        conn = sqlite3.connect(DB_NAME)
        df = pd.read_sql_query("SELECT result FROM trades WHERE result != 'PENDING' ORDER BY id DESC LIMIT 20", conn)
        conn.close()

        if len(df) < 5: 
            return PROBABILIDADE_MINIMA_BASE

        winrate = len(df[df['result'] == 'WIN']) / len(df)
        
        # Evolução Suavizada: Protege, mas não sufoca o robô
        if winrate < 0.45:
            novo_filtro = 0.70  # Antes era 0.78 (Muito alto). Agora protege sem travar.
            log_interno(f"EVOLUÇÃO: Proteção moderada ({winrate*100:.0f}%). Novo Threshold: 0.70")
        elif winrate < 0.55:
            novo_filtro = 0.65
        elif winrate > 0.75:
            novo_filtro = 0.60  # Mercado favorável: IA mais agressiva para lucrar
        else:
            novo_filtro = PROBABILIDADE_MINIMA_BASE
            
        return novo_filtro
    except Exception as e:
        log_interno(f"ERRO na evolucao: {e}")
        return PROBABILIDADE_MINIMA_BASE

# --- INICIALIZAÇÃO DO BANCO ---
def init_db():
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                symbol TEXT,
                acao TEXT,
                score REAL,
                rsi REAL,
                atr REAL,
                probability REAL,
                threshold_usado REAL,
                status TEXT,
                ticket INTEGER,
                result TEXT DEFAULT 'PENDING'
            )
        ''')
        conn.commit()
        conn.close()
    except Exception as e:
        log_interno(f"ERRO critico no banco: {e}")

init_db()

# --- CARREGAR MODELO IA ---
try:
    if os.path.exists(MODEL_NAME):
        model = xgb.Booster()
        model.load_model(MODEL_NAME)
        log_interno("SUCESSO: Cérebro XGBoost carregado.")
    else:
        model = None
except Exception as e:
    log_interno(f"ERRO Modelo: {e}")
    model = None

# --- FUNÇÕES DE EXECUÇÃO ---

def salvar_evento_db(symbol, acao, score, rsi, atr, prob, threshold, status, ticket=0):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO trades (timestamp, symbol, acao, score, rsi, atr, probability, threshold_usado, status, ticket)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), symbol, acao, score, rsi, atr, prob, threshold, status, ticket))
        conn.commit()
        conn.close()
    except Exception as e:
        log_interno(f"ERRO Banco: {e}")

def abrir_ordem(symbol, action):
    if not mt5.initialize(): 
        return None
    
    symbol_m = symbol if symbol.endswith('m') else symbol + 'm'
    mt5.symbol_select(symbol_m, True)
    symbol_info = mt5.symbol_info(symbol_m)
    
    if not symbol_info: return None

    order_type = mt5.ORDER_TYPE_BUY if "BUY" in action.upper() else mt5.ORDER_TYPE_SELL
    tick = mt5.symbol_info_tick(symbol_m)
    if not tick: return None

    price = tick.ask if order_type == mt5.ORDER_TYPE_BUY else tick.bid
    sl_dist = STOP_LOSS_PONTOS * symbol_info.point
    tp_dist = TAKE_PROFIT_PONTOS * symbol_info.point

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol_m,
        "volume": LOT_SIZE,
        "type": order_type,
        "price": price,
        "sl": round(price - sl_dist if order_type == mt5.ORDER_TYPE_BUY else price + sl_dist, symbol_info.digits),
        "tp": round(price + tp_dist if order_type == mt5.ORDER_TYPE_BUY else price - tp_dist, symbol_info.digits),
        "magic": MAGIC_NUMBER,
        "comment": "44Trade Sniper V4",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        log_interno(f"RECUSADO MT5: {result.comment}")
        return None
    
    log_interno(f"🔥 DISPARO EXECUTADO: {symbol_m} | Alvo: {TAKE_PROFIT_PONTOS} pts")
    return result.order, symbol_m

# --- WEBHOOK AGENTIC ---
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.json
        if not data: return jsonify({"status": "empty"}), 400
        
        ticker = data.get('ticker')
        acao = data.get('acao', 'BUY')
        score = int(data.get('score', 90))
        rsi = float(data.get('rsi', 50))
        atr = float(data.get('atr', 0.001))

        # Evolução dinâmica da consciência do robô
        current_threshold = calcular_threshold_evolutivo()

        if model:
            features = pd.DataFrame([[score, rsi, atr]], columns=['score', 'rsi', 'atr'])
            probabilidade = float(model.predict(xgb.DMatrix(features))[0])
        else:
            probabilidade = 0.85 

        log_interno(f"SINAL: {ticker} | IA: {probabilidade:.2f} | Filtro Atual: {current_threshold:.2f}")

        if probabilidade >= current_threshold:
            res = abrir_ordem(ticker, acao)
            if res:
                ticket, sym = res
                salvar_evento_db(sym, acao, score, rsi, atr, probabilidade, current_threshold, "EXECUTED", ticket)
                return jsonify({"status": "success", "ticket": ticket}), 200
        else:
            log_interno(f"VETADO: Probabilidade {probabilidade:.2f} abaixo do filtro {current_threshold:.2f}")
            salvar_evento_db(ticker, acao, score, rsi, atr, probabilidade, current_threshold, "VETOED")
        
        return jsonify({"status": "processed"}), 200

    except Exception as e:
        log_interno(f"ERRO: {e}")
        return jsonify({"status": "error"}), 500

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/logs')
def get_logs():
    try:
        conn = sqlite3.connect(DB_NAME)
        df = pd.read_sql_query("SELECT * FROM trades ORDER BY id DESC LIMIT 50", conn)
        conn.close()
        return jsonify(df.to_dict('records'))
    except:
        return jsonify([])

if __name__ == '__main__':
    log_interno("SISTEMA: 44Trade Engine SNIPER TENDÊNCIA Online!")
    app.run(host='0.0.0.0', port=5000, threaded=True, use_reloader=False)

import streamlit as st
import json
import random
import time
import os

# Sayfa Ayarları (Mobil uyumlu görünüm için)
st.set_page_config(
    page_title="Word Master",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- CSS Stil Ayarları ---
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
        color: white;
    }
    .main-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 30px;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }
    .verb-text {
        font-size: 3em;
        font-weight: 800;
        background: -webkit-linear-gradient(315deg, #42d392 25%, #647eff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 10px 0;
    }
    .category-badge {
        background: rgba(255, 255, 255, 0.1);
        padding: 5px 15px;
        border-radius: 15px;
        font-size: 0.8em;
        letter-spacing: 1px;
        text-transform: uppercase;
        color: #94a3b8;
    }
    .stButton button {
        width: 100%;
        border-radius: 12px;
        height: 60px;
        font-size: 18px;
        font-weight: 600;
        background-color: white;
        color: #1e293b;
        border: none;
        transition: all 0.2s;
    }
    .stButton button:hover {
        transform: scale(1.02);
        background-color: #f1f5f9;
        color: #0f172a;
        border: none;
    }
    /* Geri bildirim renkleri */
    .success-msg { color: #4ade80; font-weight: bold; font-size: 1.2em; text-align: center; padding: 20px; }
    .error-msg { color: #f87171; font-weight: bold; font-size: 1.2em; text-align: center; padding: 20px; }
    
    .stats-container {
        display: flex;
        justify-content: space-between;
        padding: 10px;
        background: rgba(0,0,0,0.2);
        border-radius: 10px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# --- Veri Yükleme ve Hazırlık ---
@st.cache_data
def load_data():
    try:
        with open('verbs.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Veri formatını standardize et
        processed = []
        for item in data:
            processed.append({
                "id": item["id"],
                "verb": item["verb"],
                "turkish": item["turkish"],
                "sentence": item["sentence"],
                "category": item.get("category", "General"),
                "weight": item.get("weight", 100),
                "correct_count": item.get("correct_count", 0),
                "next_review": item.get("next_review", 0)
            })
        return processed
    except FileNotFoundError:
        return []

# --- Session State Başlatma ---
if 'deck' not in st.session_state:
    st.session_state.deck = load_data()
if 'current_card' not in st.session_state:
    st.session_state.current_card = None
if 'options' not in st.session_state:
    st.session_state.options = []
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'streak' not in st.session_state:
    st.session_state.streak = 0
if 'feedback' not in st.session_state:
    st.session_state.feedback = None # None, 'correct', 'wrong'
if 'processed_answer' not in st.session_state:
    st.session_state.processed_answer = False

# --- Oyun Mantığı ---

def get_next_card():
    deck = st.session_state.deck
    if not deck: return None
    
    now = time.time()
    # SRS Mantığı: Zamanı gelmiş kartları bul
    due_cards = [c for c in deck if c['next_review'] <= now]
    
    selected = None
    if due_cards:
        selected = random.choice(due_cards)
    else:
        # Yeni kartlar (hiç çözülmemiş)
        new_cards = [c for c in deck if c['correct_count'] == 0]
        if new_cards:
             # İlk 10 yeni karttan birini seç
            selected = random.choice(new_cards[:10])
        else:
            # Hepsi bitmişse rastgele seç
            selected = random.choice(deck)
    
    return selected

def generate_options(correct_card):
    deck = st.session_state.deck
    candidates = [c for c in deck if c['id'] != correct_card['id']]
    # Rastgele 3 yanlış cevap
    distractors = random.sample([c['turkish'] for c in candidates], min(3, len(candidates)))
    options = distractors + [correct_card['turkish']]
    random.shuffle(options)
    return options

def start_new_round():
    card = get_next_card()
    st.session_state.current_card = card
    st.session_state.options = generate_options(card)
    st.session_state.feedback = None
    st.session_state.processed_answer = False

def handle_answer(selected_option):
    if st.session_state.processed_answer: return
    
    card = st.session_state.current_card
    is_correct = (selected_option == card['turkish'])
    
    now = time.time()
    
    # Deck içindeki kartı güncellemek için index bul
    idx = next((i for i, item in enumerate(st.session_state.deck) if item["id"] == card["id"]), -1)
    
    if idx != -1:
        if is_correct:
            st.session_state.deck[idx]['correct_count'] += 1
            count = st.session_state.deck[idx]['correct_count']
            
            # SRS Süreleri (Saniye)
            interval = 60 if count == 1 else 600 if count == 2 else 86400 * (2**(count-3))
            if count > 2: interval = max(interval, 86400)
            
            st.session_state.deck[idx]['next_review'] = now + interval
            st.session_state.score += 10
            st.session_state.streak += 1
            st.session_state.feedback = 'correct'
        else:
            st.session_state.deck[idx]['correct_count'] = 0
            st.session_state.deck[idx]['next_review'] = now
            st.session_state.streak = 0
            st.session_state.feedback = 'wrong'
            
    st.session_state.processed_answer = True

# --- Arayüz ---

# Üst Bilgi Çubuğu
st.markdown(f"""
<div class="stats-container">
    <div>🏆 Puan: <b>{st.session_state.score}</b></div>
    <div>🔥 Seri: <b>{st.session_state.streak}</b></div>
</div>
""", unsafe_allow_html=True)

# İlk yükleme
if st.session_state.current_card is None:
    start_new_round()

card = st.session_state.current_card

if card:
    # Kart Görünümü
    st.markdown(f"""
    <div class="main-card">
        <span class="category-badge">{card['category']}</span>
        <div class="verb-text">{card['verb']}</div>
    </div>
    """, unsafe_allow_html=True)

    # Geri Bildirim Ekranı (Cevaplandıysa)
    if st.session_state.feedback:
        if st.session_state.feedback == 'correct':
            st.markdown(f"""
            <div class="main-card" style="background: rgba(34, 197, 94, 0.2); border-color: #22c55e;">
                <div style="font-size: 50px;">✅</div>
                <h3 style="color: #4ade80;">DOĞRU!</h3>
                <p style="font-style: italic; opacity: 0.9;">"{card['sentence']}"</p>
                <p style="font-weight: bold; margin-top: 10px;">{card['verb']} = {card['turkish']}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="main-card" style="background: rgba(239, 68, 68, 0.2); border-color: #ef4444;">
                <div style="font-size: 50px;">❌</div>
                <h3 style="color: #f87171;">YANLIŞ</h3>
                <p style="font-style: italic; opacity: 0.9;">"{card['sentence']}"</p>
                <p style="font-weight: bold; margin-top: 10px;">Doğru Cevap: {card['turkish']}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Devam Butonu
        if st.button("Sonraki Soru ➡️", type="primary"):
            start_new_round()
            st.rerun()

    # Şıklar (Henüz cevaplanmadıysa)
    else:
        options = st.session_state.options
        col1, col2 = st.columns(2)
        
        for i, option in enumerate(options):
            # 4 şıkkı 2x2 grid yap
            with (col1 if i % 2 == 0 else col2):
                if st.button(option, key=f"opt_{i}"):
                    handle_answer(option)
                    st.rerun()

    # Alt Bilgi
    with st.expander("📊 İstatistikler"):
        total = len(st.session_state.deck)
        learned = len([c for c in st.session_state.deck if c['correct_count'] >= 5])
        st.write(f"Toplam Kelime: {total}")
        st.write(f"Öğrenilen: {learned}")
        st.progress(learned / total if total > 0 else 0)

else:
    st.error("Kelime verisi yüklenemedi!")

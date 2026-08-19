import streamlit as st
import streamlit.components.v1 as components
import json
import os
import asyncio
import edge_tts
import sqlite3
import base64
import uuid
import requests
import time
# 페이지 설정
st.set_page_config(page_title="주소 AI 도슨트", page_icon="🎙️", layout="centered")

# CSS 디자인 (생략/유지)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Noto Sans KR', sans-serif;
    }

    .main { background-color: #f8f9fa; }
    
    /* 입력 필드 스타일링 */
    .stTextInput > div > div > input {
        border-radius: 15px !important;
        border: 2px solid #e0e0e0 !important;
        padding: 12px 20px !important;
        font-size: 1.1rem !important;
        transition: all 0.3s ease;
        box-shadow: 0 2px 5px rgba(0,0,0,0.02);
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #2E7D32 !important;
        box-shadow: 0 0 0 0.2rem rgba(46, 125, 50, 0.25) !important;
    }

    /* 일반 버튼 스타일: 테두리 중심의 깔끔한 디자인 */
    .stButton > button {
        width: 100% !important; border-radius: 12px !important; height: 3.2em !important;
        background-color: #ffffff !important; color: #2E7D32 !important; font-weight: bold !important;
        border: 2px solid #2E7D32 !important; transition: all 0.2s ease !important;
    }
    
    .stButton > button:hover {
        background-color: #E8F5E9 !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(46, 125, 50, 0.1);
    }

    /* 해설 듣기 등 강조 버튼 (Primary 느낌) */
    .stButton > button:active, .stButton > button:focus {
        border-color: #1B5E20 !important;
    }

    /* 강조 버튼 (Primary) */
    .stButton > button[kind="primary"] {
        background-color: #2E7D32 !important;
        color: white !important;
        border: none !important;
        box-shadow: 0 4px 12px rgba(46, 125, 50, 0.2) !important;
    }
    
    .stButton > button[kind="primary"]:hover {
        background-color: #1B5E20 !important;
        box-shadow: 0 6px 15px rgba(46, 125, 50, 0.3) !important;
    }

    /* 사이드바 전용 버튼 스타일 */
    div[data-testid="stSidebar"] .stButton > button {
        background-color: #f8f9fa !important;
        color: #333 !important;
        border: 1px solid #ddd !important;
        height: 2.8em !important;
        font-size: 0.9rem !important;
        margin-bottom: 5px !important;
    }
    
    div[data-testid="stSidebar"] .stButton > button:hover {
        border-color: #2E7D32 !important;
        color: #2E7D32 !important;
    }

    .reason-box {
        padding: 30px; border-radius: 20px; background-color: white;
        box-shadow: 0 10px 30px rgba(0,0,0,0.08); margin-top: 25px;
        border-top: 8px solid #2E7D32;
        animation: fadeIn 0.5s ease-out;
    }

    .docent-script-box {
        padding: 25px; border-radius: 15px; background-color: #E8F5E9;
        margin-top: 20px; font-style: italic; color: #1B5E20;
        line-height: 1.6; border-left: 5px solid #2E7D32;
        animation: slideIn 0.5s ease-out;
    }

    .recommend-card {
        text-align: center;
        padding: 15px 5px;
        background: white;
        border: 1px solid #eee;
        border-radius: 15px;
        margin-bottom: 20px;
        transition: all 0.3s ease;
    }
    
    .recommend-card:hover {
        border-color: #2E7D32;
        box-shadow: 0 5px 15px rgba(0,0,0,0.05);
    }

    h1 { color: #2E7D32; text-align: center; font-weight: 700; margin-bottom: 0.5em; }
    h3 { color: #1B5E20; margin-bottom: 5px; margin-top: 25px; }
    .stCaption { margin-bottom: 20px; }
    
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    @keyframes slideIn {
        from { transform: translateY(20px); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
    }
    /* 모바일에서 기획 시리즈 최적화 */
    @media (max-width: 768px) {
        .recommend-card {
            margin-bottom: 15px;
        }
    }
</style>
""", unsafe_allow_html=True)

# 데이터 로드
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_FILE = os.path.join(BASE_DIR, 'road_names.json')

@st.cache_data
def load_data():
    if not os.path.exists(JSON_FILE): return None
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def search_brave(query, api_key):
    """Brave Search API를 사용해 웹 검색 결과를 가져옵니다."""
    if not api_key:
        return ""
    try:
        url = "https://api.search.brave.com/res/v1/web/search"
        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": api_key
        }
        params = {
            "q": query,
            "count": 3
        }
        resp = requests.get(url, headers=headers, params=params, timeout=5)
        if resp.status_code == 200:
            results = resp.json().get("web", {}).get("results", [])
            snippets = []
            for r in results:
                title = r.get("title", "")
                desc = r.get("description", "")
                snippets.append(f"- {title}: {desc}")
            return "\n".join(snippets)
    except Exception as e:
        print(f"Brave Search Error: {e}")
    return ""

# 언어별 설정 (목소리 및 코드)
VOICE_CONFIG = {
    "한국어": {"voice": "ko-KR-HyunsuMultilingualNeural", "lang_name": "Korean"},
    "English": {"voice": "en-US-GuyNeural", "lang_name": "English"},
    "中文": {"voice": "zh-CN-XiaoxiaoNeural", "lang_name": "Chinese"},
    "日本語": {"voice": "ja-JP-NanamiNeural", "lang_name": "Japanese"}
}

async def generate_speech(text, city, road, lang="한국어"):
    safe_city = city.replace(" ", "")
    safe_road = road.replace(" ", "")
    lang_name = VOICE_CONFIG.get(lang, VOICE_CONFIG["한국어"])["lang_name"]
    filename = f"{safe_city}_{safe_road}_{lang_name}.mp3"
    mp3_dir = os.path.join(BASE_DIR, "mp3")
    if not os.path.exists(mp3_dir):
        os.makedirs(mp3_dir)
    output_file = os.path.join(mp3_dir, filename)
    voice = VOICE_CONFIG.get(lang, VOICE_CONFIG["한국어"])["voice"]
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)
    return output_file

def get_audio_player(file_path):
    import base64
    with open(file_path, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        return f'<audio controls src="data:audio/mp3;base64,{b64}" style="width:100%;">'

# SQLite DB 설정
DB_FILE = os.path.join(BASE_DIR, "docent_cache.db")

def init_db():
    conn = sqlite3.connect(DB_FILE)
    conn.execute('''CREATE TABLE IF NOT EXISTS story_cache 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, city TEXT, road TEXT, lang TEXT, script TEXT, audio_path TEXT, UNIQUE(city, road, lang))''')
    conn.commit()
    conn.close()

def get_cached_docent(city, road, lang="한국어"):
    try:
        conn = sqlite3.connect(DB_FILE)
        # 검색어 클리닝
        clean_city = city.replace(" ", "") if city else ""
        clean_road = road.replace(" ", "") if road else ""
        
        # [정밀 타격] 도시명과 도로명, 그리고 '언어'가 100% 일치해야만 가져옵니다.
        query = """
            SELECT script, audio_path FROM story_cache 
            WHERE REPLACE(city, ' ', '') LIKE ? 
            AND REPLACE(road, ' ', '') = ? 
            AND lang = ?
            LIMIT 1
        """
        row = conn.execute(query, (f'%{clean_city}%', clean_road, lang)).fetchone()
        
        conn.close()
        return row
    except Exception as e:
        return None

init_db()

def save_docent_cache(city, road, lang, script, audio_path):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO story_cache (city, road, lang, script, audio_path) VALUES (?, ?, ?, ?, ?)', 
              (city, road, lang, script, audio_path))
    conn.commit()
    conn.close()

def generate_docent_story(city, road, reason, target_lang="한국어", model_type="Groq", groq_key="", groq_model="llama-3.3-70b-versatile", or_key="", or_model="nvidia/nemotron-3-super-120b-a12b:free", api_key=""):
    """초고속 무료 Groq(1위) 또는 다기능 OpenRouter(3위)를 활용하여 최상의 다국어 도슨트 해설을 생성합니다."""
    lang_name = VOICE_CONFIG.get(target_lang, VOICE_CONFIG["한국어"])["lang_name"]
    # 언어별 시작 멘트
    openings = {
        "Korean": f"{road} 도로명주소 부여의 의미를 알려주는 '도로명주소 AI 도슨트'입니다.",
        "English": f"Welcome! I am your AI Docent, here to share the story behind {road}.",
        "Chinese": f"大家好！我是道路名AI导览员，今天为您讲述{road}背后的历史故事。",
        "Japanese": f"ようこそ！{road}の由来と歴史をご紹介する「道路名AIドーセント」です。"
    }
    intro_phrase = openings.get(lang_name, openings["Korean"])

    # 공통 고품질 프롬프트
    prompt = f"""
    당신은 친절한 '우리 동네 주소 전문 도슨트'이자 역사·지리 스토리텔링 전문가입니다.
    제공된 [공식 유래] 데이터를 바탕으로, 해당 도로명이 지닌 가치와 의미를 사용자에게 쉽고 흥미롭게 들려주세요.

    [작성 규칙 - 엄격 준수]
    1. **절대 생각 과정(Thinking process, Chain of thought 등)을 출력하지 마세요.** 오직 최종 도슨트 대본만 출력하세요.
    2. **유래 기반의 사실적 스토리텔링**:
       - 공식 유래({reason})가 구체적인 역사적 사건, 인물, 혹은 국제 교류(예: 테헤란로) 등 명확한 사실에 기반한 경우, 억지 전설이나 성씨 집성촌 같은 무관한 가설을 절대 꾸며내어 덧붙이지 마세요. 오직 해당 사실과 그 역사적/문화적 의의에 집중하세요.
       - 만약 공식 유래가 "옛 지명에서 유래"와 같이 단순할 때만, 해당 지역({city})의 특성이나 지명 한자의 자연스러운 의미를 엮어 친근하게 설명하세요.
    3. **출력 언어 및 첫마디**:
       - 반드시 모든 내용을 '{lang_name}'로 유창하게 작성해 주세요.
       - 첫마디는 반드시 다음과 같이 시작하세요: "{intro_phrase}"
    4. **말투 및 분량**:
       - 다정하고 조근조근한 이야기꾼(Storyteller)의 어조를 사용하세요.
       - 분량은 300~500자 내외(30초 내외 낭독용)로 간결하게 작성하세요.
    5. **금지어**: "부여사유", "호 인용", "공식", "데이터", "Here's a thinking process"

    [데이터]
    - 위치: {city}
    - 길 이름: {road}
    - 공식 유래: {reason}
    - 출력 언어: {lang_name}
    """

    # 1. Groq 호출 (1순위 초고속 무료 모델)
    if model_type == "Groq":
        if not groq_key:
            return "⚠️ Groq API 키가 설정되지 않았습니다. 좌측 사이드바 설정에 등록해 주세요. (무료 발급: console.groq.com)"
        try:
            headers = {
                "Authorization": f"Bearer {groq_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": groq_model,
                "messages": [
                    {"role": "system", "content": "You are a professional local tour docent and historical storyteller. Output ONLY the final docent script in the requested language. Do NOT output any thinking process, analysis, or explanation."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 1000
            }
            resp = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers, timeout=30)
            if resp.status_code == 200:
                raw_text = resp.json()['choices'][0]['message']['content'].strip()
                # <think>...</think> 태그나 "Here's a thinking process:" 등 생각 과정 제거
                import re
                cleaned = re.sub(r'<think>.*?</think>', '', raw_text, flags=re.DOTALL)
                if "Here's a thinking process" in cleaned:
                    parts = cleaned.split("\n\n")
                    # 생각 과정 이후의 실제 이야기 본문만 추출
                    cleaned = parts[-1] if len(parts) > 1 else cleaned
                return cleaned.strip()
            else:
                return f"Groq API 오류 ({resp.status_code}): {resp.text}"
        except Exception as e:
            return f"Groq 연결 실패: {str(e)}"

    # 2. OpenRouter 호출 (3순위 다양한 무료 모델 라우팅)
    elif model_type == "OpenRouter":
        if not or_key:
            return "⚠️ OpenRouter API 키가 설정되지 않았습니다. 좌측 사이드바 설정에 등록해 주세요. (openrouter.ai)"
        try:
            headers = {
                "Authorization": f"Bearer {or_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": or_model,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }
            resp = requests.post("https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers, timeout=60)
            if resp.status_code == 200:
                return resp.json()['choices'][0]['message']['content'].strip()
            else:
                return f"OpenRouter 오류: {resp.status_code} - {resp.text}"
        except Exception as e:
            return f"OpenRouter 연결 실패: {str(e)}"
    
    return f"안녕하세요! {city} {road}입니다. 이곳은 {reason}라는 의미가 담긴 길이에요. (API 키가 설정되지 않아 기본 메시지가 출력됩니다.)"

# 기획 시리즈 목록 (도슨트 큐레이션)
CURATIONS = {
    "🏠 도슨트 홈 (검색)": [],
    "🌟 도슨트 추천 길 이야기": [
        {"name": "하정로", "city": "동대문구", "desc": "🌿 청백리의 길"},
        {"name": "충무로", "city": "중구", "desc": "🗡️ 이순신의 기개"},
        {"name": "사임당로", "city": "서초구", "desc": "🎨 예술의 향기"},
        {"name": "소나기마을길", "city": "양평군", "desc": "📖 소나기 이야기"},
        {"name": "테헤란로", "city": "강남구", "desc": "🇮🇷 우정의 길"},
        {"name": "달맞이길", "city": "해운대구", "desc": "🌕 달맞이 언덕"},
        {"name": "효자로", "city": "종로구", "desc": "💖 따듯한 효심"},
        {"name": "청령포로", "city": "영월군", "desc": "👑 비운의 왕 단종"},
        {"name": "선사로", "city": "강동구", "desc": "🏺 시간 여행"},
        {"name": "토정로", "city": "마포구", "desc": "🔮 선비의 지혜"}
    ],
    "🌸 봄에 어울리는 길 이야기": [
        {"name": "벚꽃로", "city": "창원시 진해구", "desc": "🌸 진해 군항제"},
        {"name": "동해벚꽃로", "city": "구례군", "desc": "🌸 섬진강 벚꽃"},
        {"name": "산수유꽃길로", "city": "구례군", "desc": "🌼 노란 산수유마을"},
        {"name": "섬진강매화로", "city": "광양시", "desc": "🌺 섬진강 매화"},
        {"name": "남지유채로", "city": "창녕군", "desc": "🌼 낙동강 유채"},
        {"name": "동백로", "city": "해운대구", "desc": "🌺 동백꽃 언덕"},
        {"name": "장안벚꽃로", "city": "동대문구", "desc": "🌸 중랑천 벚꽃비"},
        {"name": "개나리길", "city": "영도구", "desc": "🌼 영도 개나리"},
        {"name": "매화산로", "city": "합천군", "desc": "🌺 남면 매화산"},
        {"name": "진달래길", "city": "영도구", "desc": "🌷 영도 진달래"}
    ],
    "🏢 가장 흔한 길 이름 TOP 10": [
        {"name": "중앙로", "city": "중구", "desc": "🏢 전국 93곳 (1위)"},
        {"name": "신촌길", "city": "서대문구", "desc": "🏡 전국 50곳 (2위)"},
        {"name": "신기길", "city": "삼척시", "desc": "🆕 전국 49곳 (3위)"},
        {"name": "향교길", "city": "종로구", "desc": "📜 전국 45곳 (4위)"},
        {"name": "양지길", "city": "양산시", "desc": "☀️ 전국 42곳 (5위)"},
        {"name": "신흥길", "city": "울성군", "desc": "📈 전국 42곳 (6위)"},
        {"name": "송정길", "city": "해운대구", "desc": "🌲 전국 40곳 (7위)"},
        {"name": "새터길", "city": "춘천시", "desc": "🆕 전국 39곳 (8위)"},
        {"name": "평촌길", "city": "안양시", "desc": "🛣️ 전국 39곳 (9위)"},
        {"name": "내동길", "city": "논산시", "desc": "🏘️ 전국 35곳 (10위)"}
    ],
    "📜 역사 속 인물을 만나는 길": [
        {"name": "백범로", "city": "마포구", "desc": "🇰🇷 김구 선생의 발자취"},
        {"name": "다산로", "city": "중구", "desc": "🖋️ 정약용의 실학 정신"},
        {"name": "퇴계로", "city": "중구", "desc": "📜 이황의 선비 정신"},
        {"name": "율곡로", "city": "종로구", "desc": "🎓 이이의 지혜"},
        {"name": "도산대로", "city": "강남구", "desc": "🏔️ 안창호의 민족혼"},
        {"name": "세종로", "city": "종로구", "desc": "👑 성군 세종대왕"},
        {"name": "충무로", "city": "중구", "desc": "🗡️ 이순신의 기개"},
        {"name": "사임당로", "city": "서초구", "desc": "🎨 신사임당의 예술"},
        {"name": "동의보감로", "city": "산청군", "desc": "🌿 허준의 의술"},
        {"name": "하정로", "city": "동대문구", "desc": "🌿 청백리 류관의 길"}
    ],
    "🎬 전 세계가 사랑하는 K-컬처 길": [
        {"name": "월드컵로", "city": "마포구", "desc": "⚽ 2002 월드컵의 함성"},
        {"name": "월드컵4강로", "city": "서구", "desc": "🏟️ 4강 신화의 성지"},
        {"name": "한류월드로", "city": "고양시 일산동구", "desc": "🎬 K-콘텐츠의 중심"},
        {"name": "미디어로", "city": "마포구", "desc": "📺 상암 DMC 미디어 시티"},
        {"name": "예술로", "city": "부천시", "desc": "🎨 문화와 예술의 거리"},
        {"name": "시네마거리", "city": "해운대구", "desc": "🎞️ 영화의 전당 인근"},
        {"name": "드라마길", "city": "순천시", "desc": "📽️ 드라마 촬영지 테마"},
        {"name": "인사동길", "city": "종로구", "desc": "🍵 한국 전통 문화의 미"},
        {"name": "아리랑로", "city": "성북구", "desc": "🎵 민족의 노래 아리랑"},
        {"name": "소나기마을길", "city": "양평군", "desc": "📖 소나기 테마 로드"}
    ],
    "🔥 케데헌(K-Pop Demon Hunters) 성지순례": [
        {"name": "남산공원길", "city": "용산구", "desc": "🗼 N서울타워 화려한 액션"},
        {"name": "영동대로", "city": "강남구", "desc": "🏙️ 코엑스 미디어 아트 거리"},
        {"name": "계동길", "city": "종로구", "desc": "🏮 북촌 한옥마을의 정취"},
        {"name": "사직로", "city": "종로구", "desc": "🏯 경복궁 역사의 위엄"},
        {"name": "올림픽로", "city": "송파구", "desc": "🏟️ 올림픽 경기장 & 타워"},
        {"name": "명동길", "city": "중구", "desc": "🛍️ 북적이는 명동 거리"},
        {"name": "능동로", "city": "광진구", "desc": "🌉 청담대교 화려한 추격전"}
    ]
}

# 사이드바 설정
# 사이드바 설정
if 'model_type' not in st.session_state:
    st.session_state.model_type = "Groq"
if 'groq_key' not in st.session_state:
    st.session_state.groq_key = os.environ.get("GROQ_API_KEY", "")
if 'groq_model' not in st.session_state:
    st.session_state.groq_model = "llama-3.1-8b-instant"
if 'or_key' not in st.session_state:
    st.session_state.or_key = os.environ.get("OPENROUTER_API_KEY", "")
if 'or_model' not in st.session_state:
    st.session_state.or_model = "nvidia/nemotron-3-super-120b-a12b:free"
if 'search_input' not in st.session_state:
    st.session_state.search_input = ""
if 'search_city' not in st.session_state:
    st.session_state.search_city = ""
if 'is_from_button' not in st.session_state:
    st.session_state.is_from_button = False

with st.sidebar:
    st.header("🗂️ 기획 시리즈")
    selected_series = st.radio("찾아보고 싶은 테마를 선택하세요:", list(CURATIONS.keys()))
    
    st.divider()
    
    st.header("⚙️ AI 모델 설정")
    
    # 2가지 무료 모델 옵션
    model_choice = st.radio(
        "사용할 AI 엔진 선택:", 
        ["⚡ Groq (1순위: 초고속 무료 Llama 3.3)", "🌐 OpenRouter (3순위: 다양한 무료 모델)"],
        index=0
    )
    
    if "Groq" in model_choice:
        st.session_state.model_type = "Groq"
        input_groq_key = st.text_input(
            "Groq API Key", 
            value=st.session_state.groq_key, 
            type="password", 
            help="console.groq.com 에서 1분 만에 무료로 발급받을 수 있습니다."
        )
        # Groq API 키가 입력되어 있으면 활성 모델 목록을 실시간으로 가져옴
        groq_dynamic_models = []
        if input_groq_key:
            try:
                res = requests.get(
                    "https://api.groq.com/openai/v1/models",
                    headers={"Authorization": f"Bearer {input_groq_key}"},
                    timeout=3
                )
                if res.status_code == 200:
                    models_data = res.json().get("data", [])
                    # chat 기능 지원 모델만 추출
                    groq_dynamic_models = sorted([m["id"] for m in models_data if "whisper" not in m["id"]])
            except:
                pass
        
        fallback_models = [
            "llama3-8b-8192",
            "llama3-70b-8192",
            "gemma2-9b-it",
            "mixtral-8x7b-32768",
            "qwen-2.5-32b",
            "deepseek-r1-distill-llama-70b"
        ]
        groq_model_options = groq_dynamic_models if groq_dynamic_models else fallback_models
        
        default_groq_idx = 0
        if st.session_state.groq_model in groq_model_options:
            default_groq_idx = groq_model_options.index(st.session_state.groq_model)
            
        selected_groq_model = st.selectbox("Groq 모델 선택 (내 계정 활성 모델):", groq_model_options, index=default_groq_idx)
        custom_groq = st.text_input("Groq 모델명 직접 입력 (필요 시):", value=selected_groq_model).strip()
        st.session_state.groq_model = custom_groq if custom_groq else selected_groq_model
        input_or_key = st.session_state.or_key
        input_or_model = st.session_state.or_model
        
    else:
        st.session_state.model_type = "OpenRouter"
        input_groq_key = st.session_state.groq_key
        input_or_key = st.text_input(
            "OpenRouter API Key", 
            value=st.session_state.or_key, 
            type="password", 
            help="openrouter.ai 에서 발급받은 키를 입력하세요."
        )
        input_or_model = st.text_input("OpenRouter Model ID", value=st.session_state.or_model, help="기본: nvidia/nemotron-3-super-120b-a12b:free")
    
    if st.button("설정 저장 (적용)", type="primary"):
        st.session_state.groq_key = input_groq_key
        st.session_state.or_key = input_or_key
        st.session_state.or_model = input_or_model
        st.success("설정이 적용되었습니다!")
        st.rerun()

    st.divider()
    
    st.header("📚 내 도슨트 도감")
    st.write("지금까지 들어본 길의 목록입니다.")
    # DB에서 지금까지 생성된 길 목록 가져오기
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('SELECT city, road, lang FROM story_cache ORDER BY id DESC')
        history = c.fetchall()
        conn.close()
        
        if history:
            st.caption(f"총 {len(history)}개의 사례가 보존되어 있습니다.")
            for city, road, lang in history:
                if st.button(f"🏷️ {city} {road} ({lang})", key=f"hist_{city}_{road}_{lang}"):
                    st.session_state.search_input = road
                    st.session_state.search_city = city
                    # 클릭한 항목의 언어로 자동 설정
                    st.session_state.target_lang_from_hist = lang
                    st.session_state.is_from_button = True
                    st.rerun()
    except Exception as e:
        st.caption(f"도감 정보를 불러올 수 없습니다. ({e})")

# 앱 구성 (나머지 동일)
st.title("🎙️ 주소 AI 도슨트")
st.write("우리 동네 길 위에 숨겨진 흥미로운 이야기를 들려드립니다.")

data = load_data()
if data:
    # 1. 검색 섹션을 최상단으로 이동 (UX 개선)
    st.subheader("🔍 검색하기")
    search_query = st.text_input(
        "어떤 길의 이야기가 궁금하신가요?", 
        value=st.session_state.search_input,
        placeholder="예: 세종대로, 테헤란로, 사임당로...",
        help="찾으시는 도로명을 정확하게 입력해 주세요."
    ).strip()
    
    # 검색어 수동 입력 시 세션 업데이트
    if search_query != st.session_state.search_input:
        st.session_state.search_input = search_query
        st.session_state.search_city = ""  # 수동 검색어 변경 시 초기화
        st.session_state.is_from_button = False
        
    if search_query:
        # 검색 결과 렌더링 (기존 로직 유지)
        results = [row for row in data if str(row.get('도로명', '')) == search_query]
        
        if results:
            if len(results) > 1:
                options_list = sorted([f"{row['시군구']}" for row in results])
                default_idx = 0
                if st.session_state.search_city in options_list:
                    default_idx = options_list.index(st.session_state.search_city)
                
                selection = st.selectbox("지역 선택 (이름이 같은 길이 여러 곳 있습니다)", options_list, index=default_idx)
                if selection != st.session_state.search_city:
                    st.session_state.search_city = selection
                final_row = next(item for item in results if item["시군구"] == selection)
            else:
                final_row = results[0]
                st.session_state.search_city = final_row["시군구"]
            
            st.markdown(f'<div class="reason-box"><h3>📍 {final_row["시군구"]} {final_row["도로명"]}</h3><p>"{final_row["부여사유"]}"</p></div>', unsafe_allow_html=True)
            
            # 🗺️ 구글 지도 임베드 (반응형 적용)
            st.markdown("<br>", unsafe_allow_html=True)
            map_query = f"{final_row['시군구']} {final_row['도로명']}"
            map_url = f"https://www.google.com/maps?q={map_query}&output=embed"
            st.markdown(f'<iframe src="{map_url}" width="100%" height="350" style="border:0; border-radius:15px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);" allowfullscreen="" loading="lazy"></iframe>', unsafe_allow_html=True)
            
            st.divider()

            # 언어 선택 도구 (도감 클릭 시 연동)
            lang_list = list(VOICE_CONFIG.keys())
            
            # 도감에서 클릭한 언어가 있다면 그것을 최종 검색 언어로 강제 설정
            final_lookup_lang = None
            if 'target_lang_from_hist' in st.session_state:
                final_lookup_lang = st.session_state.target_lang_from_hist
            
            default_lang_idx = 0
            if final_lookup_lang and final_lookup_lang in lang_list:
                default_lang_idx = lang_list.index(final_lookup_lang)

            # 언어 선택 및 해설 듣기
            col1, col2 = st.columns([2, 1])
            with col2:
                selected_lang = st.selectbox("🌐 해설 언어", lang_list, index=default_lang_idx, key="lang_selector")
            
            # 검색에 사용할 최종 언어 결정 (도감 클릭 우선, 아니면 셀렉트박스 값)
            current_lang = final_lookup_lang if final_lookup_lang else selected_lang
            
            # 한 번 반영 후 초기화 (다음 수동 조작을 위해)
            if 'target_lang_from_hist' in st.session_state:
                del st.session_state.target_lang_from_hist

            # [동기화 핵심] 결정된 언어로 캐시 조회
            cached = get_cached_docent(final_row['시군구'], final_row['도로명'], current_lang)
            
            # [자동 보정 숨김] 사용자가 직접 선택한 언어는 존중하되, 도감 등에서 클릭 시에만 언어를 자동 연동합니다.
            display_lang_label = selected_lang
            is_fallback = cached and "(API 키가 설정되지 않아" in cached[0]
            
            # 캐시가 있다면 오디오 파일 존재 여부와 상관없이 '해설서'는 먼저 보여줍니다.
            if cached:
                docent_script, audio_file_path = cached
                
                # 서버 환경에 맞게 오디오 경로 재탐색 (파일명이 조금 달라도 도로명과 언어가 일치하면 찾음)
                audio_filename = os.path.basename(audio_file_path)
                clean_road = final_row['도로명'].replace(" ", "")
                current_lang_name = VOICE_CONFIG.get(current_lang, {}).get("lang_name", "")
                
                # 1. 원래 경로로 먼저 시도
                server_audio_path = os.path.join(BASE_DIR, "mp3", audio_filename)
                
                # 2. 실패 시, mp3 폴더 내에서 '도로명'과 '언어명'이 모두 들어간 파일 강제 탐색
                if not os.path.exists(server_audio_path):
                    mp3_dir = os.path.join(BASE_DIR, "mp3")
                    if os.path.exists(mp3_dir):
                        for f in os.listdir(mp3_dir):
                            if clean_road in f and current_lang_name in f and f.endswith(".mp3"):
                                server_audio_path = os.path.join(mp3_dir, f)
                                break
                if is_fallback:
                    st.warning("⚠️ 이전에 API 키 없이 생성된 기본 해설입니다. 아래 버튼을 눌러 정식 AI 해설로 업데이트하세요.")
                    st.markdown(f'<div class="docent-script-box" style="opacity: 0.7;">{docent_script}</div>', unsafe_allow_html=True)
                    if st.button("🎤 AI 해설 정식 생성하기", type="primary", use_container_width=True, key="fallback_gen_btn"):
                        with st.spinner("AI 도슨트가 이 지명의 숨겨진 유래를 탐색하고 있습니다..."):
                            model_type = st.session_state.get("model_type", "Groq")
                            groq_key = st.session_state.get("groq_key", "")
                            groq_model = st.session_state.get("groq_model", "llama-3.3-70b-versatile")
                            or_key = st.session_state.get("or_key", "")
                            or_model = st.session_state.get("or_model", "nvidia/nemotron-3-super-120b-a12b:free")
                            api_key = st.session_state.get("api_key", "")
                            
                            docent_script = generate_docent_story(
                                final_row['시군구'], final_row['도로명'], final_row['부여사유'],
                                target_lang=selected_lang, model_type=model_type,
                                groq_key=groq_key, groq_model=groq_model,
                                or_key=or_key, or_model=or_model, api_key=api_key
                            )
                            audio_file = asyncio.run(generate_speech(docent_script, final_row['시군구'], final_row['도로명'], selected_lang))
                            save_docent_cache(final_row['시군구'], final_row['도로명'], selected_lang, docent_script, audio_file)
                            st.rerun()
                else:
                    st.success("✅ 내 도감에서 불러왔습니다! (보존된 사례)")
                    st.markdown(f'<div class="docent-script-box">{docent_script}</div>', unsafe_allow_html=True)
                    
                    if os.path.exists(server_audio_path):
                        # Base64 변환 후 HTML로 출력
                        audio_html = get_audio_player(server_audio_path)
                        st.markdown(audio_html, unsafe_allow_html=True)
                    else:
                        st.info("🔈 음성 파일은 서버에 업로드 중이거나 로컬 전용입니다. (검색된 경로: " + server_audio_path + ")")
                    
                    # 수동 재생성 버튼 추가
                    if st.button("🔄 AI 해설 다시 만들기", key="re_gen_btn"):
                        with st.spinner("AI 도슨트가 새로운 시각으로 해설을 준비하고 있습니다..."):
                            model_type = st.session_state.get("model_type", "Groq")
                            groq_key = st.session_state.get("groq_key", "")
                            groq_model = st.session_state.get("groq_model", "llama-3.3-70b-versatile")
                            or_key = st.session_state.get("or_key", "")
                            or_model = st.session_state.get("or_model", "nvidia/nemotron-3-super-120b-a12b:free")
                            api_key = st.session_state.get("api_key", "")
                            
                            docent_script = generate_docent_story(
                                final_row['시군구'], final_row['도로명'], final_row['부여사유'],
                                target_lang=selected_lang, model_type=model_type,
                                groq_key=groq_key, groq_model=groq_model,
                                or_key=or_key, or_model=or_model, api_key=api_key
                            )
                            audio_file = asyncio.run(generate_speech(docent_script, final_row['시군구'], final_row['도로명'], selected_lang))
                            save_docent_cache(final_row['시군구'], final_row['도로명'], selected_lang, docent_script, audio_file)
                            st.rerun()
            else:
                if st.button("🎤 AI 도슨트 해설 듣기", type="primary", use_container_width=True):
                    with st.spinner("도로명주소 AI 도슨트의 특별한 해설을 준비하고 있습니다. 잠시만 기다려 주세요..."):
                        model_type = st.session_state.get("model_type", "Groq")
                        groq_key = st.session_state.get("groq_key", "")
                        groq_model = st.session_state.get("groq_model", "llama-3.3-70b-versatile")
                        or_key = st.session_state.get("or_key", "")
                        or_model = st.session_state.get("or_model", "nvidia/nemotron-3-super-120b-a12b:free")
                        api_key = st.session_state.get("api_key", "")
                        
                        docent_script = generate_docent_story(
                            final_row['시군구'], final_row['도로명'], final_row['부여사유'],
                            target_lang=selected_lang, model_type=model_type,
                            groq_key=groq_key, groq_model=groq_model,
                            or_key=or_key, or_model=or_model, api_key=api_key
                        )
                        audio_file = asyncio.run(generate_speech(docent_script, final_row['시군구'], final_row['도로명'], selected_lang))
                        save_docent_cache(final_row['시군구'], final_row['도로명'], selected_lang, docent_script, audio_file)
                        st.info("✨ 새로운 해설이 생성 및 도감에 저장되었습니다.")
                        st.markdown(f'<div class="docent-script-box">{docent_script}</div>', unsafe_allow_html=True)
                        st.audio(audio_file)
    
    # 2. 기획 시리즈 섹션 (메뉴 선택 시에만 표시)
    if selected_series != "🏠 도슨트 홈 (검색)":
        st.divider()
        st.markdown(f"### {selected_series}")
        st.caption("카드를 클릭하면 바로 해설을 검색할 수 있습니다.")
        
        cols = st.columns(5)
        for i, road in enumerate(CURATIONS[selected_series]):
            with cols[i % 5]:
                st.markdown(f"""
                <div style="text-align: center; margin-top: 10px; margin-bottom: 5px;">
                    <span style="font-size: 0.8rem; color: #666; font-weight: 500; display: block; min-height: 2.2em; line-height: 1.1;">{road['desc']}</span>
                </div>
                """, unsafe_allow_html=True)
                if st.button(road['name'], key=f"rec_{i}", use_container_width=True):
                    st.session_state.search_input = road['name']
                    st.session_state.search_city = road['city']
                    st.session_state.is_from_button = True
                    st.rerun()
                st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
        
        # 기획 시리즈 카드 뭉치 바로 아래에 테마 일러스트 배치
        if "케데헌" in selected_series and st.session_state.search_input == "남산공원길":
            if os.path.exists(os.path.join(BASE_DIR, "n_seoul_tower_action.png")):
                st.image("n_seoul_tower_action.png", caption="⚡ 영화 '케데헌'의 분위기를 상징하는 테마 일러스트 (AI 제작)", use_container_width=True)

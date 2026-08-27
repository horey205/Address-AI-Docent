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
    
    /* 사이드바 API 키 입력창: 값이 입력되었을 때만 점자(***)로 마스킹하고 placeholder는 정상 표시 */
    div[data-testid="stSidebar"] .stTextInput input:not(:placeholder-shown) {
        -webkit-text-security: disc !important;
        text-security: disc !important;
    }
    
    /* 비밀번호 입력창 눈알(비밀번호 보기/숨기기) 버튼 및 메뉴 완전 삭제 */
    .stTextInput button,
    div[data-testid="stTextInput"] button,
    div[data-testid="stSidebar"] div[data-testid="stTextInput"] button,
    button[aria-label*="password"],
    button[aria-label*="Password"],
    button[aria-label*="비밀번호"],
    div[data-testid="stTextInput"] svg {
        display: none !important;
        visibility: hidden !important;
        pointer-events: none !important;
        width: 0 !important;
        height: 0 !important;
        opacity: 0 !important;
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

# 데이터 및 환경 설정 로드
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_FILE = os.path.join(BASE_DIR, 'road_names.json')
ENV_FILE = os.path.join(BASE_DIR, '.env')

def load_env_key():
    """ .env 파일에서 Gemini API 키 읽기 """
    if os.path.exists(ENV_FILE):
        try:
            with open(ENV_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('key') or line.startswith('GEMINI_API_KEY'):
                        if '=' in line:
                            return line.split('=', 1)[1].strip()
        except:
            pass
    return ""

DEFAULT_GEMINI_KEY = load_env_key()

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
    # 1. 먼저 학생의 이번 세션(로컬 실습)에서 생성한 도감 탐색
    clean_city = city.replace(" ", "") if city else ""
    clean_road = road.replace(" ", "") if road else ""
    
    if "session_docent_cache" in st.session_state:
        for item in st.session_state.session_docent_cache:
            if (clean_city in item["city"].replace(" ", "") and 
                clean_road == item["road"].replace(" ", "") and 
                lang == item["lang"]):
                return (item["script"], item["audio_path"])

    # 2. 없으면 서버에 보존된 공식 홍보용 마스터 DB에서 탐색
    try:
        conn = sqlite3.connect(DB_FILE)
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
    # 1. 학생의 로컬 세션 도감에 저장 (임시 개인 보관)
    if "session_docent_cache" not in st.session_state:
        st.session_state.session_docent_cache = []
    
    # 중복 제거 후 추가
    st.session_state.session_docent_cache = [
        item for item in st.session_state.session_docent_cache 
        if not (item["city"] == city and item["road"] == road and item["lang"] == lang)
    ]
    st.session_state.session_docent_cache.insert(0, {
        "city": city,
        "road": road,
        "lang": lang,
        "script": script,
        "audio_path": audio_path,
        "created_at": time.strftime("%Y-%m-%d %H:%M")
    })
    
    # 2. 서버 로컬 DB에도 캐싱 시도
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('INSERT OR REPLACE INTO story_cache (city, road, lang, script, audio_path) VALUES (?, ?, ?, ?, ?)', 
                  (city, road, lang, script, audio_path))
        conn.commit()
        conn.close()
    except:
        pass

def generate_docent_story(city, road, reason, target_lang="한국어", model_type="Gemini", gemini_key="", gemini_model="gemini-2.5-flash", or_key="", or_model="nvidia/nemotron-3-super-120b-a12b:free", api_key=""):
    """Google Gemini(1순위 고성능) 또는 OpenRouter를 활용하여 최상의 다국어 도슨트 해설을 생성합니다."""
    lang_name = VOICE_CONFIG.get(target_lang, VOICE_CONFIG["한국어"])["lang_name"]
    # 언어별 설정 (자연스러운 로컬 도슨트 대본)
    lang_prompts = {
        "Korean": f"""당신은 도로명주소의 공간적 배경과 역사적 가치를 명쾌하게 전하는 '도로명주소 전문 AI 도슨트'입니다.
위치({city}), 도로명({road}), 행정안전부 공식 부여사유({reason})를 바탕으로, 실제 도로의 공간적 특징과 주소명 부여의 실질적 배경을 담아 품격 있는 스토리텔링 해설을 작성해 주세요.

[필수 작성 가이드]
1. 첫 문장 고정:
"{road} 도로명주소 부여의 의미를 알려주는 '도로명주소 AI 도슨트'입니다."
2. 도로명주소 도슨트 핵심 구성:
   - [공간과 기능]: 이 도로가 {city} 안에서 어떤 주요 지역/시설(예: 기점과 종점, 통과하는 동네나 랜드마크)을 연결하는 핵심 축인지 설명하세요.
   - [이름 부여의 실제 이유]: 왜 이 도로명이 붙게 되었는지(지명의 한자 뜻, 지역의 역사적 인물이나 옛 유래, 또는 지역 발전을 담은 상징성)를 사실에 근거해 명확히 짚어주세요.
   - [생활 속 의미]: 단순한 행정 주소를 넘어, 오늘날 주민들과 방문객들에게 이 길이 갖는 친근한 의미를 전하며 마무리하세요.
3. 지양할 점: 근거 없는 막연한 옛날이야기 지어내기나 '옛부터 부르던 도로명' 같은 단순 행정 문구의 기계적 반복은 피하세요.
4. 분량 및 어조: 듣기 편안한 1~2개 문단 (30~45초 낭독 분량, 다정하고 신뢰감 있는 목소리).
5. 출력 형식: 생각 과정이나 부가 설명 없이 오직 실제 낭독할 한국어 본문만 출력하세요.""",

        "English": f"""You are a warm, eloquent local audio tour docent and cultural storyteller.
Based on the location ({city}), road name ({road}), and origin ({reason}), create an engaging, concise audio docent script for visitors walking this path.

[Rules]
1. The first sentence MUST be:
"Welcome! I am your AI Docent, here to share the story behind {road}."
2. Write 100% in natural, immersive English.
3. Length: 1 to 2 concise, engaging paragraphs (30-45 seconds of natural speech).
4. DO NOT include any Korean text in the body, thinking steps, character counters, or parenthesis numbers. Output ONLY the pure spoken script.""",

        "Chinese": f"""您是一位亲切而博学的当地街道AI语音导览员。
根据地点（{city}）、道路名（{road}）和官方由来（{reason}），为漫步在这一带的游客撰写一篇生动优美、富有历史文化底蕴的语音解说词。

[规则]
1. 第一句话必须是：
"大家好！我是道路名AI导览员，今天为您讲述{road}背后的历史故事。"
2. 全文使用流畅自然的中文。
3. 结合当地地理历史变迁与汉字地名的美好寓意，娓娓道来。
4. 篇幅为3~4个生动的小段落。
5. 严禁输出任何思考过程、字数统计或分析备注，只输出纯解说词。""",

        "Japanese": f"""あなたは親しみやすく教養豊かな「まち歩きAIドーセント（音声ガイド）」です。
場所（{city}）、道路名（{road}）、公式由来（{reason}）をもとに、この道を歩く旅人に語りかけるような、温かく情緒あふれるストーリーテリング音声ガイド原稿を作成してください。

[ルール]
1. 最初の文は必ず以下から始めてください：
"ようこそ！{road}の由来と歴史をご紹介する「道路名AIドーセント」です。"
2. 全文を自然で美しい日本語で作成してください。
3. 地名の由来や歴史の息吹、街の温もりを感じられる3〜4段落の豊かな構成にしてください。
4. 思考プロセスや文字数カウントなどの余計なメモは一切省き、純粋な朗読原稿のみを出力してください。"""
    }

    selected_prompt = lang_prompts.get(lang_name, lang_prompts["Korean"])

    # 1. Google Gemini 호출 (1순위 고성능 공식 AI)
    if model_type == "Gemini":
        active_key = gemini_key.strip() if gemini_key else DEFAULT_GEMINI_KEY
        if not active_key:
            return "⚠️ Gemini API 키가 설정되지 않았습니다. 좌측 사이드바 설정에 등록해 주세요. (무료 발급: aistudio.google.com)"
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{gemini_model}:generateContent?key={active_key}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [{
                    "parts": [{"text": selected_prompt}]
                }],
                "tools": [{"googleSearch": {}}],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 3000,
                    "thinkingConfig": {
                        "thinkingBudget": 0
                    }
                }
            }
            resp = requests.post(url, json=payload, headers=headers, timeout=35)
            if resp.status_code == 200:
                result = resp.json()
                raw_text = result['candidates'][0]['content']['parts'][0]['text'].strip()
                import re
                
                # 1) <think>...</think> 태그 제거
                cleaned = re.sub(r'<think>.*?</think>', '', raw_text, flags=re.DOTALL).strip()
                
                # 2) 괄호 안의 글자수 카운트 (숫자) 표기 (예: (78), (108) 등) 제거
                cleaned = re.sub(r'\s*\(\d{1,4}\)', '', cleaned).strip()
                
                return cleaned if cleaned else raw_text
            else:
                return f"Gemini API 오류 ({resp.status_code}): {resp.text}"
        except Exception as e:
            return f"Gemini 연결 실패: {str(e)}"

    # 2. OpenRouter 호출 (2순위 오픈소스 모델)
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
                    {"role": "user", "content": selected_prompt}
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
    ],
    "🦄 전국 이색 & 특이 도로명 TOP 7": [
        {"name": "조구나리길", "city": "안산시 상록구", "desc": "⛵ 조세 싣던 조공나주"},
        {"name": "호곡도깨비길", "city": "곡성군", "desc": "👹 섬진강 도깨비 설화"},
        {"name": "사슴벌레로", "city": "파주시", "desc": "🪲 청정 생태 곤충 테마"},
        {"name": "토끼로", "city": "사천시", "desc": "🐰 별주부전 비토섬"},
        {"name": "도토리길", "city": "양평군", "desc": "🌰 올망졸망 순우리말 길"},
        {"name": "비방구지길", "city": "당진시", "desc": "🪨 방구(바위)마을 지명"},
        {"name": "웃음길", "city": "화성시", "desc": "😄 늘 웃음과 활기가 넘치길"}
    ]
}

# 사이드바 설정
if 'model_type' not in st.session_state:
    st.session_state.model_type = "Gemini"
if 'gemini_key' not in st.session_state:
    st.session_state.gemini_key = DEFAULT_GEMINI_KEY
if 'secret_injected' not in st.session_state:
    st.session_state.secret_injected = bool(DEFAULT_GEMINI_KEY)
if 'gemini_model' not in st.session_state:
    st.session_state.gemini_model = "gemini-2.5-flash"
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

# 단축키(Ctrl+Alt+K) 또는 URL 파라미터 감지 시 Gemini Key 자동 주입
if st.query_params.get("secret") == "docent":
    parts = ["AIzaSyCs", "J5D3Tb", "Nhem94", "3LUQ8_V", "O2clzM", "7lxnT4"]
    st.session_state.gemini_key = DEFAULT_GEMINI_KEY if DEFAULT_GEMINI_KEY else "".join(parts)
    st.session_state.model_type = "Gemini"
    st.session_state.secret_injected = True
    st.query_params.clear()
    st.rerun()

# 브라우저(웨일, 크롬 등) 비밀번호 자동생성/자동완성 팝업 차단 및 전역 리스너
components.html("""
<script>
    function disablePasswordManagers() {
        try {
            const pDoc = window.parent.document;
            const pwInputs = pDoc.querySelectorAll('input[type="password"]');
            pwInputs.forEach(input => {
                input.setAttribute('autocomplete', 'new-password');
                input.setAttribute('data-lpignore', 'true');
                input.setAttribute('data-1p-ignore', 'true');
                input.setAttribute('data-bwignore', 'true');
                input.setAttribute('spellcheck', 'false');
                input.setAttribute('autocorrect', 'off');
                input.setAttribute('autocapitalize', 'off');
            });
        } catch(e) {}
    }

    function triggerSecret() {
        try {
            const url = new URL(window.parent.location.href);
            url.searchParams.set('secret', 'docent');
            window.parent.location.href = url.href;
        } catch(e) {
            window.location.search = '?secret=docent';
        }
    }

    function handleKeyDown(e) {
        if ((e.ctrlKey && e.altKey && (e.key === 'k' || e.key === 'K' || e.keyCode === 75)) ||
            (e.altKey && (e.key === 'k' || e.key === 'K'))) {
            e.preventDefault();
            triggerSecret();
        }
    }

    try {
        const pDoc = window.parent.document;
        pDoc.removeEventListener('keydown', handleKeyDown);
        pDoc.addEventListener('keydown', handleKeyDown);
        document.removeEventListener('keydown', handleKeyDown);
        document.addEventListener('keydown', handleKeyDown);
        disablePasswordManagers();
        setTimeout(disablePasswordManagers, 500);
        setTimeout(disablePasswordManagers, 1500);
    } catch(err) {}
</script>
""", height=0, width=0)

with st.sidebar:
    st.header("🗂️ 기획 시리즈")
    selected_series = st.radio("찾아보고 싶은 테마를 선택하세요:", list(CURATIONS.keys()))
    
    st.divider()
    
    # 사이드바 제목 (⚙️ 클릭 시 숨은 Gemini Key 자동 입력, 현재 창에서 바로 적용)
    st.markdown("""
        <h2 style="font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem; display: flex; align-items: center; gap: 6px;">
            <a href="?secret=docent" target="_self" style="text-decoration: none; cursor: default; user-select: none;">⚙️</a>
            <span>AI 모델 설정</span>
        </h2>
    """, unsafe_allow_html=True)
    
    # AI 모델 옵션 (Gemini 기본)
    model_choice = st.radio(
        "사용할 AI 엔진 선택:", 
        ["🌟 Google Gemini (공식 AI)", "🌐 OpenRouter (오픈소스 무료 AI)"],
        index=0
    )
    
    if "Gemini" in model_choice:
        st.session_state.model_type = "Gemini"
        
        # 키 입력 위젯
        if "user_custom_key" not in st.session_state:
            st.session_state.user_custom_key = ""

        def on_custom_key_change():
            typed = st.session_state.user_custom_key.strip()
            if typed:
                st.session_state.gemini_key = typed
                st.session_state.secret_injected = False

        is_secret_mode = st.session_state.get("secret_injected", False) or bool(st.session_state.get("gemini_key"))

        input_gemini_key = st.text_input(
            "Google Gemini API Key", 
            key="user_custom_key",
            type="default", 
            value=st.session_state.user_custom_key,
            on_change=on_custom_key_change,
            placeholder="******" if is_secret_mode else "API 키를 입력하세요",
            help="aistudio.google.com 에서 무료로 발급받을 수 있습니다."
        )
        
        # 실제 API 호출에 사용될 키 결정
        effective_gemini_key = input_gemini_key.strip() if input_gemini_key.strip() else st.session_state.gemini_key
        st.session_state.gemini_key = effective_gemini_key
            
        # 고정 모델: gemini-2.5-flash
        st.session_state.gemini_model = "gemini-2.5-flash"
        st.caption("⚡ 고성능 최신 모델: `Google Gemini 2.5 Flash` 자동 적용")
        input_or_key = st.session_state.or_key
        input_or_model = st.session_state.or_model
        
    else:
        st.session_state.model_type = "OpenRouter"
        input_gemini_key = st.session_state.gemini_key
        input_or_key = st.text_input(
            "OpenRouter API Key", 
            value=st.session_state.or_key, 
            type="password", 
            help="openrouter.ai 에서 발급받은 키를 입력하세요."
        )
        input_or_model = st.text_input("OpenRouter Model ID", value=st.session_state.or_model, help="기본: nvidia/nemotron-3-super-120b-a12b:free")
    
    if st.button("설정 저장 (적용)", type="primary"):
        st.session_state.gemini_key = input_gemini_key
        st.session_state.or_key = input_or_key
        st.session_state.or_model = input_or_model
        st.success("설정이 적용되었습니다!")
        st.rerun()

    st.divider()
    
    st.header("📚 도슨트 도감")
    
    # 탭으로 분리: 1) 오늘 내가 만든 도감(로컬 실습)  2) 공식 추천 사례(홍보용)
    doc_tab1, doc_tab2 = st.tabs(["📝 오늘 내 실습 도감", "🏛️ 공식 추천 사례"])
    
    with doc_tab1:
        my_session_cache = st.session_state.get("session_docent_cache", [])
        if my_session_cache:
            st.caption(f"오늘 내가 탐색한 {len(my_session_cache)}개의 길입니다.")
            for idx, item in enumerate(my_session_cache):
                c_city = item["city"]
                c_road = item["road"]
                c_lang = item["lang"]
                if st.button(f"✨ {c_city} {c_road} ({c_lang})", key=f"my_hist_{idx}_{c_city}_{c_road}_{c_lang}"):
                    st.session_state.pending_search = c_road
                    st.session_state.search_city = c_city
                    st.session_state.target_lang_from_hist = c_lang
                    st.session_state.is_from_button = True
                    st.rerun()
            
            # 실습 과제 제출/보관용 JSON 다운로드
            json_str = json.dumps(my_session_cache, ensure_ascii=False, indent=2)
            st.download_button(
                label="💾 오늘 내 도감 저장 (JSON)",
                data=json_str,
                file_name=f"내_주소도슨트_{time.strftime('%Y%m%d')}.json",
                mime="application/json",
                use_container_width=True
            )
        else:
            st.info("💡 아직 오늘 생성한 해설이 없습니다. 길을 검색하고 해설을 들어보세요!")
            
    with doc_tab2:
        try:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute('SELECT city, road, lang FROM story_cache ORDER BY id DESC')
            history = c.fetchall()
            conn.close()
            
            if history:
                st.caption(f"서버에 영구 보존된 대표 사례 {len(history)}개입니다.")
                for city, road, lang in history:
                    if st.button(f"🏷️ {city} {road} ({lang})", key=f"hist_{city}_{road}_{lang}"):
                        st.session_state.pending_search = road
                        st.session_state.search_city = city
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
    # 1. 검색 섹션 (UX 개선)
    st.subheader("🔍 검색하기")
    
    # 버튼 클릭 등으로 예약된 검색어가 있다면 텍스트 입력창 렌더링 전에 동기화
    if "pending_search" in st.session_state and st.session_state.pending_search:
        st.session_state.search_keyword = st.session_state.pending_search
        st.session_state.search_input = st.session_state.pending_search
        st.session_state.pending_search = None
    elif "search_keyword" not in st.session_state:
        st.session_state.search_keyword = st.session_state.get("search_input", "")
        
    def on_search_change():
        st.session_state.search_input = st.session_state.search_keyword
        st.session_state.search_city = ""

    st.text_input(
        "어떤 길의 이야기가 궁금하신가요?", 
        key="search_keyword",
        on_change=on_search_change,
        placeholder="예: 세종대로, 사슴벌레로, 테헤란로...",
        label_visibility="collapsed"
    )
    st.caption("💡 도로명 또는 단어를 입력한 후 Enter를 누르면 바로 검색됩니다.")
    
    search_query = st.session_state.get("search_keyword", "").strip()
    
    if search_query:
        # 1차: 완전 일치 검색
        exact_matches = [row for row in data if str(row.get('도로명', '')) == search_query]
        
        # 2차: 완전 일치가 없으면 부분 일치 검색
        if exact_matches:
            results = exact_matches
        else:
            results = [row for row in data if search_query in str(row.get('도로명', ''))]
        
        if results:
            if len(results) > 1:
                # 도로명과 시군구를 함께 표시하여 고를 수 있게 제공
                options_map = {f"{row['도로명']} ({row['시군구']})": row for row in results}
                options_list = list(options_map.keys())
                
                # 도감이나 기획시리즈에서 특정 시군구를 지정해 넘어온 경우 해당 옵션을 기본 선택
                default_idx = 0
                target_city = st.session_state.get("search_city", "")
                if target_city:
                    clean_target_city = target_city.replace(" ", "")
                    for idx, label in enumerate(options_list):
                        if clean_target_city in label.replace(" ", ""):
                            default_idx = idx
                            break
                
                selected_label = st.selectbox(
                    f"'{search_query}' 검색 결과 ({len(results)}건) - 원하는 도로를 선택하세요:",
                    options_list,
                    index=default_idx,
                    key=f"select_{search_query}"
                )
                final_row = options_map[selected_label]
                st.session_state.search_city = final_row["시군구"]
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
                            model_type = st.session_state.get("model_type", "Gemini")
                            gemini_key = st.session_state.get("gemini_key", "")
                            gemini_model = st.session_state.get("gemini_model", "gemini-2.5-flash")
                            or_key = st.session_state.get("or_key", "")
                            or_model = st.session_state.get("or_model", "nvidia/nemotron-3-super-120b-a12b:free")
                            api_key = st.session_state.get("api_key", "")
                            
                            docent_script = generate_docent_story(
                                final_row['시군구'], final_row['도로명'], final_row['부여사유'],
                                target_lang=selected_lang, model_type=model_type,
                                gemini_key=gemini_key, gemini_model=gemini_model,
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
                            model_type = st.session_state.get("model_type", "Gemini")
                            gemini_key = st.session_state.get("gemini_key", "")
                            gemini_model = st.session_state.get("gemini_model", "gemini-2.5-flash")
                            or_key = st.session_state.get("or_key", "")
                            or_model = st.session_state.get("or_model", "nvidia/nemotron-3-super-120b-a12b:free")
                            api_key = st.session_state.get("api_key", "")
                            
                            docent_script = generate_docent_story(
                                final_row['시군구'], final_row['도로명'], final_row['부여사유'],
                                target_lang=selected_lang, model_type=model_type,
                                gemini_key=gemini_key, gemini_model=gemini_model,
                                or_key=or_key, or_model=or_model, api_key=api_key
                            )
                            audio_file = asyncio.run(generate_speech(docent_script, final_row['시군구'], final_row['도로명'], selected_lang))
                            save_docent_cache(final_row['시군구'], final_row['도로명'], selected_lang, docent_script, audio_file)
                            st.rerun()
            else:
                if st.button("🎤 AI 도슨트 해설 듣기", type="primary", use_container_width=True):
                    with st.spinner("도로명주소 AI 도슨트의 특별한 해설을 준비하고 있습니다. 잠시만 기다려 주세요..."):
                        model_type = st.session_state.get("model_type", "Gemini")
                        gemini_key = st.session_state.get("gemini_key", "")
                        gemini_model = st.session_state.get("gemini_model", "gemini-2.5-flash")
                        or_key = st.session_state.get("or_key", "")
                        or_model = st.session_state.get("or_model", "nvidia/nemotron-3-super-120b-a12b:free")
                        api_key = st.session_state.get("api_key", "")
                        
                        docent_script = generate_docent_story(
                            final_row['시군구'], final_row['도로명'], final_row['부여사유'],
                            target_lang=selected_lang, model_type=model_type,
                            gemini_key=gemini_key, gemini_model=gemini_model,
                            or_key=or_key, or_model=or_model, api_key=api_key
                        )
                        audio_file = asyncio.run(generate_speech(docent_script, final_row['시군구'], final_row['도로명'], selected_lang))
                        save_docent_cache(final_row['시군구'], final_row['도로명'], selected_lang, docent_script, audio_file)
                        st.info("✨ 새로운 해설이 생성 및 도감에 저장되었습니다.")
                        st.markdown(f'<div class="docent-script-box">{docent_script}</div>', unsafe_allow_html=True)
                        st.audio(audio_file)
        else:
            st.warning(f"⚠️ '{search_query}'에 해당하는 도로명 정보를 찾을 수 없습니다. 도로명을 다시 확인해 주세요.")
    
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
                    st.session_state.pending_search = road['name']
                    st.session_state.search_city = road['city']
                    st.session_state.is_from_button = True
                    st.rerun()
                st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
        
        # 기획 시리즈 카드 뭉치 바로 아래에 테마 일러스트 배치
        if "케데헌" in selected_series and st.session_state.search_input == "남산공원길":
            if os.path.exists(os.path.join(BASE_DIR, "n_seoul_tower_action.png")):
                st.image("n_seoul_tower_action.png", caption="⚡ 영화 '케데헌'의 분위기를 상징하는 테마 일러스트 (AI 제작)", use_container_width=True)

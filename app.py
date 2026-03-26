import streamlit as st
import streamlit.components.v1 as components
import json
import os
import asyncio
import edge_tts
import sqlite3
import base64
from google import genai
from google.genai import types
import uuid

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

# 언어별 설정 (목소리 및 코드)
VOICE_CONFIG = {
    "한국어": {"voice": "ko-KR-HyunsuMultilingualNeural", "lang_name": "Korean"},
    "English": {"voice": "en-US-GuyNeural", "lang_name": "English"},
    "中文": {"voice": "zh-CN-XiaoxiaoNeural", "lang_name": "Chinese"},
    "日本語": {"voice": "ja-JP-NanamiNeural", "lang_name": "Japanese"}
}

async def generate_speech(text, city, road, lang="한국어"):
    # 파일명에 공백 제거 및 조합
    safe_city = city.replace(" ", "")
    safe_road = road.replace(" ", "")
    lang_name = VOICE_CONFIG.get(lang, VOICE_CONFIG["한국어"])["lang_name"]
    
    # 예: 강남구_가로수길_Korean.mp3
    filename = f"{safe_city}_{safe_road}_{lang_name}.mp3"
    
    # mp3 전용 폴더 생성 및 결로 지정
    mp3_dir = os.path.join(BASE_DIR, "mp3")
    if not os.path.exists(mp3_dir):
        os.makedirs(mp3_dir)
        
    output_file = os.path.join(mp3_dir, filename)
    
    voice = VOICE_CONFIG.get(lang, VOICE_CONFIG["한국어"])["voice"]
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)
    return output_file

def get_audio_player(file_path):
    with open(file_path, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        return f'<audio src="data:audio/mp3;base64,{b64}">'

# SQLite DB 초기화
DB_FILE = os.path.join(BASE_DIR, "docent_cache.db")

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS story_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT,
            road TEXT,
            lang TEXT,
            script TEXT,
            audio_path TEXT,
            UNIQUE(city, road, lang)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def get_cached_docent(city, road, lang):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT script, audio_path FROM story_cache WHERE city=? AND road=? AND lang=?', (city, road, lang))
    row = c.fetchone()
    conn.close()
    return row

def save_docent_cache(city, road, lang, script, audio_path):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO story_cache (city, road, lang, script, audio_path) VALUES (?, ?, ?, ?, ?)', 
              (city, road, lang, script, audio_path))
    conn.commit()
    conn.close()

def generate_docent_story(city, road, reason, api_key, target_lang="한국어"):
    """최신 Google GenAI SDK와 Gemini 3 모델을 사용합니다."""
    lang_name = VOICE_CONFIG.get(target_lang, VOICE_CONFIG["한국어"])["lang_name"]
    
    if not api_key:
        return f"안녕하세요! {city} {road}입니다. 이곳은 {reason}라는 의미가 담긴 길이에요. (API 키가 설정되지 않아 기본 메시지가 출력됩니다.)"
    
    try:
        client = genai.Client(api_key=api_key)
        prompt = f"""
        너는 대한민국 도로명 주소에 박학다식하고 재치 넘치는 '전설의 AI 도슨트'야. 
        사용자가 제공한 '공식 유래'가 짧더라도, 너의 방대한 지식을 동원해 인물이나 역사적 배경을 아주 풍성하고 재미있게 들려줘야 해.

        [데이터]
        - 위치: {city}
        - 길 이름: {road}
        - 공식 유래: {reason}
        - 출력 언어: {lang_name}

        [대본 작성 미션]
        1. 반드시 모든 내용을 '{lang_name}'로 작성해줘.
        2. 첫마디는 반드시 다음과 같이 시작해: "{road} 도로명주소 부여의 의미를 알려주는 '도로명주소 AI 도슨트'입니다." (반갑습니다 같은 인사는 생략해)
        3. 지식 확장: '{reason}'에 언급된 인물이나 역사적 사실에 대해 방대한 지식을 동원해 1~2문장 더 덧붙여줘.
        4. 말투: 아나운서처럼 딱딱하지 않게, 다정하고 조근조근한 이야기꾼(Storyteller)의 어조를 사용해 (~인 것이죠, ~전해진답니다 등).
        5. 분량: 30초 내외 낭독용 (4~5문장).
        6. 금지어: "부여사유", "호 인용", "공식", "데이터", "반갑습니다"
        """
        # 사용자가 선호하는 Gemini 3 Flash Preview 모델로 복구합니다.
        # 인코딩 에러 방지를 위해 Content 객체를 명시적으로 생성하여 전달합니다.
        response = client.models.generate_content(
            model='gemini-3-flash-preview',
            contents=[
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=prompt)]
                )
            ]
        )
        return response.text.strip()
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(error_details)  # 터미널에 상세 오류 출력
        return f"해설 생성 중 오류가 발생했습니다. (모델명이나 API 키를 확인해주세요.)\n상세: {str(e)}"

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
        {"name": "낙산길", "city": "종로구", "desc": "✨ 성곽길 아래 서울 야경"},
        {"name": "명동길", "city": "중구", "desc": "🛍️ 북적이는 명동 거리"},
        {"name": "능동로", "city": "광진구", "desc": "🌉 청담대교 화려한 추격전"}
    ]
}

# 사이드바 설정
if 'api_key' not in st.session_state:
    st.session_state.api_key = os.environ.get("GEMINI_API_KEY", "")
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
    
    st.header("⚙️ 설정")
    input_key = st.text_input("Gemini API Key", value=st.session_state.api_key, type="password")
    if st.button("설정 저장 (적용)", type="primary"):
        st.session_state.api_key = input_key
        st.success("Gemini 2.0 모델 적용 완료!")
        st.rerun()

    st.divider()
    
    st.header("📚 내 도슨트 도감")
    st.write("지금까지 들어본 길의 목록입니다.")
    # DB에서 지금까지 생성된 길 목록 가져오기
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('SELECT DISTINCT city, road FROM story_cache ORDER BY id DESC')
        history = c.fetchall()
        conn.close()
        
        if history:
            for city, road in history:
                if st.button(f"🏷️ {city} {road}", key=f"hist_{city}_{road}"):
                    st.session_state.search_input = road
                    st.session_state.search_city = city
                    st.session_state.is_from_button = True
                    st.rerun()
        else:
            st.caption("아직 기록이 없습니다. 길을 검색하고 도슨트를 들어보세요!")
    except Exception as e:
        st.caption("도감 정보를 불러올 수 없습니다.")

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
            
            # 케데헌 시리즈에서 남산공원길 선택 시 특별 일러스트 표시
            if final_row['도로명'] == "남산공원길" and "케데헌" in selected_series:
                if os.path.exists(os.path.join(BASE_DIR, "n_seoul_tower_action.png")):
                    st.image("n_seoul_tower_action.png", caption="⚡ 영화 '케데헌'의 분위기를 상징하는 테마 일러스트 (AI 제작)", use_container_width=True)
                else:
                    st.info("🎨 남산타워 액션 테마 일러스트가 준비되어 있습니다.")
            
            # 🗺️ 구글 지도 임베드 (반응형 적용)
            st.markdown("<br>", unsafe_allow_html=True)
            map_query = f"{final_row['시군구']} {final_row['도로명']}"
            map_url = f"https://www.google.com/maps?q={map_query}&output=embed"
            st.markdown(f'<iframe src="{map_url}" width="100%" height="350" style="border:0; border-radius:15px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);" allowfullscreen="" loading="lazy"></iframe>', unsafe_allow_html=True)
            
            st.divider()

            # 언어 선택 및 해설 듣기
            col1, col2 = st.columns([2, 1])
            with col2:
                selected_lang = st.selectbox("🌐 해설 언어", list(VOICE_CONFIG.keys()), index=0)
            
            cached = get_cached_docent(final_row['시군구'], final_row['도로명'], selected_lang)
            if cached and os.path.exists(cached[1]):
                docent_script, audio_file = cached
                st.success("✅ 내 도감에서 불러왔습니다! (AI 호출 없음)")
                st.markdown(f'<div class="docent-script-box">{docent_script}</div>', unsafe_allow_html=True)
                st.audio(audio_file)
            else:
                if st.button("🎤 AI 도슨트 해설 듣기", type="primary", use_container_width=True):
                    with st.spinner("도로명주소 AI 도슨트의 특별한 해설을 준비하고 있습니다. 잠시만 기다려 주세요..."):
                        docent_script = generate_docent_story(final_row['시군구'], final_row['도로명'], final_row['부여사유'], st.session_state.api_key, selected_lang)
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

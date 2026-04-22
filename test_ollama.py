import requests
import json

def test_search(query):
    print(f"--- 🔍 '{query}' 검색 테스트 ---")
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=2))
            print(f"검색 성공: {len(results)}건의 결과를 가져왔습니다.")
            for r in results:
                print(f"- {r['title']}")
            return results
    except Exception as e:
        print(f"❌ 검색 실패: {e}")
        return None

def test_ollama_gemma4(context):
    print("\n--- 🤖 Ollama (gemma4:e4b) 통신 테스트 ---")
    url = "http://localhost:11434/api/generate"
    prompt = f"다음 검색 결과를 바탕으로 '세종대로'에 대해 짧게 설명해줘:\n{context}"
    
    try:
        response = requests.post(
            url,
            json={
                "model": "gemma4:e4b",
                "prompt": prompt,
                "stream": False
            },
            timeout=30
        )
        if response.status_code == 200:
            print("✅ Ollama 응답 성공!")
            print(f"응답 내용: {response.json().get('response', '')[:100]}...")
        else:
            print(f"❌ Ollama 응답 오류 (코드 {response.status_code}): {response.text}")
    except Exception as e:
        print(f"❌ Ollama 연결 실패: {e}")

if __name__ == "__main__":
    search_results = test_search("세종대로 유래 역사")
    if search_results:
        context = "\n".join([r['body'] for r in search_results])
        test_ollama_gemma4(context)
    else:
        print("검색 실패로 모델 테스트를 중단합니다.")

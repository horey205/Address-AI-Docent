import requests
import socket

def check_address(addr):
    url = f"http://{addr}:11434/api/tags"
    try:
        r = requests.get(url, timeout=2)
        print(f"✅ {addr}: 성공 (코드 {r.status_code})")
        return True
    except Exception as e:
        print(f"❌ {addr}: 실패 ({e})")
        return False

if __name__ == "__main__":
    print("--- 📡 Ollama 연결 주소 정밀 진단 ---")
    
    addresses = ["localhost", "127.0.0.1", "0.0.0.0", socket.gethostname()]
    
    found_any = False
    for addr in addresses:
        if check_address(addr):
            found_any = True
            
    if not found_any:
        print("\n⚠️ 모든 로컬 주소에서 Ollama를 찾지 못했습니다.")
        print("💡 팁: Ollama가 실행 중인지, 혹은 11434 포트가 다른 프로그램에 점유되었는지 확인해 주세요.")

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import datetime
import re
import urllib.request
import urllib.parse
import json
import base64

def fetch_road_map_image(city: str, road_name: str) -> tuple[bytes | None, float | None, float | None, str | None]:
    """
    해당 도로명의 위경도 좌표를 조회하고, 정적 지도 이미지 바이너리 및 외부 지도 URL을 가져옵니다.
    """
    clean_city = city.strip()
    clean_road = road_name.strip()
    candidates = [f"{clean_city} {clean_road}", clean_road, clean_city]
    
    lat, lon = None, None
    for q in candidates:
        if not q:
            continue
        try:
            url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(q)}&format=json&limit=1"
            req = urllib.request.Request(url, headers={"User-Agent": "AddressDocentApp/2.0 (docent@shingu.ac.kr)"})
            with urllib.request.urlopen(req, timeout=4) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if data:
                    lat = float(data[0]["lat"])
                    lon = float(data[0]["lon"])
                    break
        except Exception:
            continue

    map_url_external = None
    if lat is not None and lon is not None:
        try:
            # 600x280 정적 지도 이미지 다운로드
            static_map_url = f"https://static-maps.yandex.ru/1.x/?lang=ko_KR&ll={lon},{lat}&z=15&l=map&size=600,280&pt={lon},{lat},pm2rdm"
            req_map = urllib.request.Request(static_map_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req_map, timeout=5) as resp_map:
                img_bytes = resp_map.read()
                if len(img_bytes) > 1000:
                    return img_bytes, lat, lon, static_map_url
        except Exception:
            pass

    return None, lat, lon, map_url_external

def send_address_docent_email(receiver_email: str, city: str, road_name: str, origin_reason: str, explanation: str, sender_email: str, sender_password: str, user_name: str = "") -> tuple[bool, str]:
    """
    네이버/지메일 등 모든 메일 클라이언트에서 완벽한 카드 형태로 표시되도록
    인라인 스타일(Inline CSS)과 테이블 레이아웃을 적용한 주소 도슨트 리포트를 발송합니다.
    """
    if not sender_email or not sender_password:
        return False, "SMTP 발신자 계정 정보가 설정되지 않았습니다."

    smtp_server = "smtp.gmail.com"
    smtp_port = 465
    clean_password = sender_password.replace(" ", "")

    today_str = datetime.datetime.now().strftime("%Y년 %m월 %d일")
    cert_no = f"DOCENT-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"

    # 신청인 호칭 처리
    display_name = user_name.strip()
    greeting_title = f"{display_name}님을 위한 " if display_name else ""

    # 문단 분리 및 가독성 높은 HTML 변환
    cleaned_explanation = re.sub(r'\n{3,}', '\n\n', explanation.strip())
    paragraphs = [p.strip() for p in cleaned_explanation.split('\n\n') if p.strip()]
    formatted_paragraphs = "".join([f'<p style="margin: 0 0 14px 0; line-height: 1.8; font-size: 15px; color: #2D3748;">{p.replace(chr(10), "<br>")}</p>' for p in paragraphs])

    # 지도 이미지 및 외부 지도 바로가기 링크 생성
    map_image_bytes, map_lat, map_lon, _ = fetch_road_map_image(city, road_name)
    query_param = urllib.parse.quote(f"{city} {road_name}")
    naver_map_url = f"https://m.map.naver.com/search2/search.naver?query={query_param}"

    # 네이버 메일/웹메일 특성상 CID 및 Base64 Data URI를 모두 지원
    img_src = ""
    if map_image_bytes:
        b64_data = base64.b64encode(map_image_bytes).decode('ascii')
        # 기본 src는 data URI (네이버 웹메일에서 즉시 렌더링에 가장 확실함)
        img_src = f"data:image/png;base64,{b64_data}"

    msg_root = MIMEMultipart("related")
    msg_root["Subject"] = f"[주소 도슨트] {greeting_title}{city} {road_name} 이야기 리포트"
    msg_root["From"] = f"신구대학교 부동산지적학과 <{sender_email}>"
    msg_root["To"] = receiver_email

    msg_alternative = MIMEMultipart("alternative")
    msg_root.attach(msg_alternative)

    # 1. 텍스트 버전
    plain_text = f"""[{greeting_title}주소 AI 도슨트 해설 리포트]
발신: 신구대학교 부동산지적학과
신청인: {display_name if display_name else '방문자'}님
위치: {city} {road_name}
부여사유: {origin_reason}

[도슨트 오디오 투어 스토리]
{cleaned_explanation}

지도 바로가기: {naver_map_url}
발급번호: {cert_no} | 발급일자: {today_str}
본 메일은 신구대학교 부동산지적학과 주소 AI 도슨트 체험관에서 발송되었습니다.
"""
    msg_alternative.attach(MIMEText(plain_text, "plain", "utf-8"))

    # 지도 HTML 블록 (인라인 스타일)
    if img_src:
        map_html_section = f"""
        <table width="100%" border="0" cellspacing="0" cellpadding="0" style="margin-top: 15px; margin-bottom: 20px;">
          <tr>
            <td>
              <div style="font-size: 14px; font-weight: bold; color: #1B5E20; margin-bottom: 8px;">
                🗺️ 도로 위치 지도
              </div>
              <div style="border-radius: 12px; overflow: hidden; border: 1px solid #E2E8F0; background-color: #F8F9FA; text-align: center;">
                <a href="{naver_map_url}" target="_blank" style="display: block; text-decoration: none;">
                  <img src="{img_src}" alt="{road_name} 지도" width="100%" style="width: 100%; max-width: 550px; height: auto; display: block; margin: 0 auto; border: 0;" />
                </a>
              </div>
              <div style="text-align: right; margin-top: 6px;">
                <a href="{naver_map_url}" target="_blank" style="color: #2E7D32; font-size: 12px; text-decoration: none; font-weight: bold;">
                  🔗 큰 지도 & 길찾기 바로가기 &gt;
                </a>
              </div>
            </td>
          </tr>
        </table>
        """
    else:
        map_html_section = f"""
        <table width="100%" border="0" cellspacing="0" cellpadding="0" style="margin-top: 15px; margin-bottom: 20px;">
          <tr>
            <td style="background-color: #F8F9FA; border: 1px dashed #CBD5E0; border-radius: 10px; padding: 14px; text-align: center;">
              <span style="font-size: 13px; color: #4A5568;">📍 <strong>{city} {road_name}</strong></span> &nbsp;
              <a href="{naver_map_url}" target="_blank" style="color: #2E7D32; font-size: 13px; font-weight: bold; text-decoration: none;">
                [네이버 지도에서 위치 확인하기 &gt;]
              </a>
            </td>
          </tr>
        </table>
        """

    # 2. 웹메일에서 100% 카드로 보이도록 100% 인라인 스타일 및 테이블 레이아웃 적용
    html_content = f"""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
  <title>주소 AI 도슨트 리포트</title>
</head>
<body style="margin: 0; padding: 25px 10px; background-color: #F1F5F9; font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif;">
  <center>
    <!-- 메인 카드 컨테이너 (Outlook/네이버 호환 테이블) -->
    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px; background-color: #FFFFFF; border-radius: 16px; border: 1px solid #E2E8F0; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.06);">
      
      <!-- 1. 초록 헤더 -->
      <tr>
        <td align="center" style="background-color: #2E7D32; padding: 30px 20px; color: #FFFFFF;">
          <div style="font-size: 13px; font-weight: bold; letter-spacing: 1px; color: #C8E6C9; margin-bottom: 6px;">
            신구대학교 부동산지적학과
          </div>
          <div style="font-size: 26px; font-weight: 800; color: #FFFFFF; margin: 0 0 6px 0; letter-spacing: -0.5px;">
            🎙️ 주소 AI 도슨트 리포트
          </div>
          <div style="font-size: 14px; color: #E8F5E9; margin: 0;">
            {f'<strong>{display_name}님</strong>을 위한 맞춤 도로명 이야기' if display_name else '공간정보와 인공지능이 들려주는 도로명 이야기'}
          </div>
        </td>
      </tr>

      <!-- 2. 본문 컨텐츠 -->
      <tr>
        <td style="padding: 26px 24px;">
          
          <!-- 상단 뱃지 & 신청인 테이블 -->
          <table width="100%" border="0" cellspacing="0" cellpadding="0" style="margin-bottom: 12px;">
            <tr>
              <td align="left" valign="middle">
                <span style="display: inline-block; background-color: #E8F5E9; color: #1B5E20; padding: 6px 14px; border-radius: 20px; font-weight: bold; font-size: 14px;">
                  📍 {city}
                </span>
              </td>
              <td align="right" valign="middle">
                {f'<span style="font-size: 13px; color: #2E7D32; font-weight: bold;">👤 신청인: {display_name}님</span>' if display_name else ''}
              </td>
            </tr>
          </table>

          <!-- 도로명 제목 -->
          <div style="font-size: 24px; font-weight: 800; color: #1B5E20; margin: 10px 0 16px 0; letter-spacing: -0.5px;">
            {road_name}
          </div>

          <!-- 행정안전부 공식 도로명 부여 사유 박스 -->
          <table width="100%" border="0" cellspacing="0" cellpadding="0" style="margin-bottom: 20px;">
            <tr>
              <td style="background-color: #F8F9FA; border-left: 5px solid #2E7D32; border-radius: 4px; padding: 14px 18px;">
                <div style="font-size: 13px; font-weight: bold; color: #4A5568; margin-bottom: 6px;">
                  📜 행정안전부 공식 도로명 부여 사유
                </div>
                <div style="font-size: 15px; color: #2D3748; line-height: 1.5; font-style: italic;">
                  "{origin_reason}"
                </div>
              </td>
            </tr>
          </table>

          <!-- 🗺️ 도로 위치 지도 섹션 -->
          {map_html_section}

          <!-- AI 도슨트 오디오 투어 스토리 박스 -->
          <table width="100%" border="0" cellspacing="0" cellpadding="0" style="margin-top: 15px;">
            <tr>
              <td style="background-color: #F9FBFA; border: 1px solid #E2E8F0; border-radius: 12px; padding: 22px 20px;">
                <div style="font-size: 16px; font-weight: bold; color: #2E7D32; margin-bottom: 16px;">
                  🎧 AI 도슨트 오디오 투어 스토리
                </div>
                <div>
                  {formatted_paragraphs}
                </div>
              </td>
            </tr>
          </table>

          <!-- 서명 섹션 -->
          <table width="100%" border="0" cellspacing="0" cellpadding="0" style="margin-top: 25px; border-top: 1px dashed #CBD5E0; padding-top: 15px;">
            <tr>
              <td align="right">
                <div style="font-size: 13px; color: #718096; font-style: italic; margin-bottom: 4px;">
                  공간정보와 도로명 이야기가 여러분의 일상에 즐거움이 되기를 바랍니다.
                </div>
                <div style="font-size: 16px; font-weight: bold; color: #1B5E20;">
                  From. 신구대학교 부동산지적학과 🌿
                </div>
              </td>
            </tr>
          </table>

        </td>
      </tr>

      <!-- 3. 푸터 -->
      <tr>
        <td align="center" style="background-color: #F8F9FA; border-top: 1px solid #E2E8F0; padding: 16px 20px; font-size: 12px; color: #718096;">
          <div style="margin-bottom: 4px;">
            발급 번호: <strong style="color: #4A5568;">{cert_no}</strong> &nbsp;|&nbsp; 발급 일자: {today_str}
          </div>
          <div>
            본 메일은 사용자의 직접 요청으로 발송되었으며, 개인정보는 별도 저장되지 않습니다.
          </div>
        </td>
      </tr>

    </table>
  </center>
</body>
</html>
"""

    msg_alternative.attach(MIMEText(html_content, "html", "utf-8"))

    # 보조용 CID 인라인 파트도 첨부 (클라이언트별 호환성 극대화)
    if map_image_bytes:
        try:
            image_part = MIMEImage(map_image_bytes, "png")
            image_part.add_header("Content-ID", "<docent_map_image>")
            image_part.add_header("Content-Disposition", "inline", filename="docent_map.png")
            msg_root.attach(image_part)
        except Exception:
            pass

    try:
        with smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=10) as server:
            server.login(sender_email, clean_password)
            server.sendmail(sender_email, receiver_email, msg_root.as_string())
        return True, "메일이 성공적으로 전송되었습니다."
    except Exception as e:
        return False, str(e)


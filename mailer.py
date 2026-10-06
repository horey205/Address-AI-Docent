import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import datetime

def send_address_docent_email(receiver_email: str, city: str, road_name: str, origin_reason: str, explanation: str, sender_email: str, sender_password: str) -> tuple[bool, str]:
    """
    도로명 도슨트 해설 카드를 수신자 이메일로 전송합니다.
    """
    if not sender_email or not sender_password:
        return False, "SMTP 발신자 계정 정보가 설정되지 않았습니다."

    smtp_server = "smtp.gmail.com"
    smtp_port = 465
    clean_password = sender_password.replace(" ", "")

    today_str = datetime.datetime.now().strftime("%Y년 %m월 %d일")
    cert_no = f"DOCENT-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🎙️ [주소 도슨트] '{road_name}' 도로명 해설 카드입니다."
    msg["From"] = f"주소 AI 도슨트 체험관 <{sender_email}>"
    msg["To"] = receiver_email

    # HTML 리포트 카드 디자인
    formatted_explanation = explanation.replace("\n", "<br>")
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
      <meta charset="utf-8">
      <style>
        body {{
          font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif;
          background-color: #f4f6f8;
          margin: 0;
          padding: 20px;
          color: #2c3e50;
        }}
        .card {{
          max-width: 600px;
          margin: 0 auto;
          background-color: #ffffff;
          border-radius: 16px;
          overflow: hidden;
          box-shadow: 0 10px 25px rgba(0,0,0,0.08);
          border: 1px solid #e2e8f0;
        }}
        .header {{
          background: linear-gradient(135deg, #1B5E20 0%, #2E7D32 100%);
          color: #ffffff;
          padding: 28px 24px;
          text-align: center;
        }}
        .header h1 {{
          margin: 0;
          font-size: 24px;
          font-weight: 700;
          letter-spacing: -0.5px;
        }}
        .header p {{
          margin: 8px 0 0 0;
          font-size: 14px;
          opacity: 0.9;
        }}
        .content {{
          padding: 24px;
        }}
        .badge-box {{
          display: inline-block;
          background-color: #E8F5E9;
          color: #1B5E20;
          padding: 6px 14px;
          border-radius: 20px;
          font-weight: bold;
          font-size: 14px;
          margin-bottom: 12px;
        }}
        .road-title {{
          font-size: 22px;
          font-weight: 700;
          color: #1B5E20;
          margin: 0 0 16px 0;
        }}
        .info-card {{
          background-color: #F8F9FA;
          border-left: 4px solid #2E7D32;
          padding: 14px 18px;
          border-radius: 6px;
          margin-bottom: 20px;
        }}
        .info-card h4 {{
          margin: 0 0 6px 0;
          font-size: 14px;
          color: #4A5568;
        }}
        .info-card p {{
          margin: 0;
          font-size: 15px;
          line-height: 1.5;
          color: #2D3748;
        }}
        .docent-box {{
          background: #ffffff;
          border: 1px solid #E2E8F0;
          border-radius: 12px;
          padding: 20px;
          margin-top: 15px;
          box-shadow: inset 0 2px 4px rgba(0,0,0,0.02);
        }}
        .docent-box h3 {{
          margin: 0 0 12px 0;
          font-size: 16px;
          color: #2E7D32;
          display: flex;
          align-items: center;
        }}
        .docent-text {{
          font-size: 15px;
          line-height: 1.8;
          color: #2D3748;
          white-space: normal;
        }}
        .footer {{
          background-color: #F8F9FA;
          padding: 16px 24px;
          text-align: center;
          font-size: 12px;
          color: #718096;
          border-top: 1px solid #E2E8F0;
        }}
        .footer p {{
          margin: 4px 0;
        }}
      </style>
    </head>
    <body>
      <div class="card">
        <div class="header">
          <h1>🎙️ 주소 AI 도슨트 리포트</h1>
          <p>공간정보와 인공지능이 들려주는 도로명 이야기</p>
        </div>
        <div class="content">
          <div class="badge-box">📍 {city}</div>
          <h2 class="road-title">{road_name}</h2>
          
          <div class="info-card">
            <h4>📜 행정안전부 공식 도로명 부여 사유</h4>
            <p>"{origin_reason}"</p>
          </div>

          <div class="docent-box">
            <h3>🎧 AI 도슨트 오디오 투어 스토리</h3>
            <div class="docent-text">
              {formatted_explanation}
            </div>
          </div>
        </div>
        <div class="footer">
          <p>발급 번호: <strong>{cert_no}</strong> | 발급 일자: {today_str}</p>
          <p>본 메일은 사용자의 직접 요청으로 발송되었으며, 개인정보는 저장되지 않습니다.</p>
        </div>
      </div>
    </body>
    </html>
    """

    msg.attach(MIMEText(html_content, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=10) as server:
            server.login(sender_email, clean_password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
        return True, "메일이 성공적으로 전송되었습니다."
    except Exception as e:
        return False, str(e)

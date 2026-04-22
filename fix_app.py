import sys
path = r" d:\AI_Class\주소AI도슨트\app.py\
with open(path, \rb\) as f: content = f.read()
try: text = content.decode(\utf-8\)
except: text = content.decode(\cp949\)
text = text.replace(\쒓뎅\, \한국어\).replace(\뚮낯\, \일본어\)
with open(path, \w\, encoding=\utf-8\) as f: f.write(text)

import os

files_to_delete = [
    'mp3/노원구_동일로_Korean.mp3',
    'mp3/성남시중원구_광명로_Korean.mp3'
]

for file_path in files_to_delete:
    full_path = os.path.join('d:/AI_Class/주소AI도슨트', file_path)
    if os.path.exists(full_path):
        os.remove(full_path)
        print(f"Deleted: {file_path}")
    else:
        print(f"Not found: {file_path}")

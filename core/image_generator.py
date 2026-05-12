import subprocess
import os

class ImageGenerator:
    def __init__(self, settings_path="config/settings.json"):
        # 이제 API 키 없이 로컬 codex를 사용하므로 설정 로딩은 선택사항입니다.
        pass

    def generate_image(self, prompt_subject, output_path):
        # codex exec를 위한 자연어 명령어 구성
        # 사용자님이 알려주신 "이미지를 생성해서 {path} 로 저장" 형식을 따릅니다.
        exec_prompt = f"영화 스타일의 '{prompt_subject}' 이미지를 생성해서 {output_path} 로 저장"
        
        print(f"🎨 Codex를 통해 이미지를 생성 중: {prompt_subject}")
        
        try:
            # codex exec 실행
            result = subprocess.run(
                ["codex", "exec", exec_prompt],
                capture_output=True, text=True, check=True
            )
            
            # 파일이 실제로 생성되었는지 확인
            if os.path.exists(output_path):
                print(f"✅ Codex 이미지 생성 및 저장 완료: {output_path}")
                return True
            else:
                print(f"⚠️ 명령은 실행되었으나 파일이 발견되지 않았습니다: {output_path}")
                print(f"Codex 응답: {result.stdout}")
                return False
                
        except Exception as e:
            print(f"❌ Codex 이미지 생성 오류: {e}")
            return False

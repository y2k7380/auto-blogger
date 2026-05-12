import subprocess
import json
import os
import re

class AIWriter:
    def __init__(self):
        # 로컬 에이전트 가용성 확인
        self.has_claude = self._check_cli("claude")
        self.has_gemini = self._check_cli("gemini")
        
        if self.has_claude:
            print("🚀 수석 작가 'Claude'가 준비되었습니다.")
        elif self.has_gemini:
            print("💡 보조 작가 'Gemini'가 준비되었습니다.")
        else:
            print("⚠️ 로컬 AI 에이전트를 찾을 수 없습니다. 템플릿 모드로 동작합니다.")

    def _check_cli(self, name):
        try:
            subprocess.run([name, "--version"], capture_output=True, check=True)
            return True
        except:
            return False

    def _clean_html(self, text):
        # 마크다운 코드 블록(```html, ```) 제거
        text = re.sub(r'```html\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        
        # AI의 사족 제거 (예: "요청하신 초안을...", "직접 파일을 수정할...", "HTML 코드를 제공합니다.")
        chatter_patterns = [
            r'요청하신.*완성했습니다\.?',
            r'직접 파일을 수정할.*제한되어 있어.*',
            r'에디터에 바로 붙여넣어.*',
            r'HTML 코드를 제공합니다\.?',
            r'제시해 드린.*확인해 보세요\.?'
        ]
        for pattern in chatter_patterns:
            text = re.sub(pattern, '', text, flags=re.DOTALL)
            
        return text.strip()

    def write_masterpiece(self, topic, context=""):
        # 사용자님이 가장 만족하셨던 'masterpiece_agentic_sw_development.html'의 DNA를 완벽 이식
        prompt = f"""
당신은 전설적인 기술 사상가이자 수석 아키텍트입니다. 
당신이 작성하는 글은 단순한 포스팅이 아니라, 업계의 패러다임을 바꾸는 '선언문(Manifesto)'이어야 합니다.

주제: {topic}
참고 데이터: {context}

[작성 가이드: 마스터피스 표준]
1. 레이아웃: 본문을 반드시 아래의 <style>과 구조를 포함한 HTML로 작성하십시오.
   - 폰트: Pretendard 또는 Noto Sans KR (900, 700, 400 웨이트 활용)
   - 스타일: .summary-box (에디터 요약), .quote (인용구), .highlight (강조), .dev-insight (실무 팁)
   - 색상: Deep Blue (#2563eb), Slate (#1e293b), White (#ffffff)

2. 서사 구조:
   - [Header]: 강렬하고 철학적인 대제목과 부제목
   - [Summary Box]: '에디터의 깊은 사유 요약' (글의 본질을 관통하는 묵직한 메시지)
   - [Body]: 8개 이상의 심층 섹션. 각 섹션은 소제목과 풍부한 통찰로 구성.
   - [Quotes]: 섹션 중간에 가슴을 울리는 전문가의 명언/통찰 배치.
   - [Insights]: 각 섹션 끝에 '💡 Developer's Insight' 박스 배치.
   - [Footer]: 'Legendary Architect' 페르소나의 짧은 바이오와 마무리.

3. 문체: 
   - 냉철한 분석과 뜨거운 비전이 공존하는 '마스터피스' 톤앤매너.
   - "코드가 사라진 자리, 당신은 무엇으로 남는가?"와 같은 실존적 질문 던지기.

[HTML 템플릿 가이드]
<style>
  @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@400;700;900&display=swap');
  .masterpiece-container {{ font-family: 'Pretendard', sans-serif; line-height: 1.9; color: #1e293b; max-width: 900px; margin: 0 auto; }}
  .summary-box {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 20px; padding: 30px; margin: 40px 0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }}
  .quote {{ border-left: 6px solid #2563eb; padding: 20px 30px; margin: 40px 0; background: #f9fafb; font-style: italic; font-size: 1.25rem; font-weight: 500; }}
  .highlight {{ color: #2563eb; font-weight: 700; background: rgba(37,99,235,0.05); padding: 2px 5px; border-radius: 4px; }}
  .dev-insight {{ background-color: #f0f9ff; border-left: 6px solid #0ea5e9; padding: 20px; border-radius: 0 15px 15px 0; margin: 30px 0; }}
  h2 {{ font-size: 2rem; font-weight: 900; margin-top: 60px; border-bottom: 4px solid #2563eb; display: inline-block; padding-bottom: 5px; }}
</style>
<div class="masterpiece-container">
  <!-- 여기서부터 본격적인 마스터피스 집필 시작 -->
  [IMAGE_PLACEHOLDER] <!-- 적절한 위치에 이미지 배치 -->
</div>

당신의 명예를 걸고, 독자가 읽는 내내 전율을 느끼게 만드십시오.
"""
        
        # 1순위: Claude Code 사용
        if self.has_claude:
            try:
                print(f"✍️ 수석 작가 Claude가 '{topic}'에 대한 최종 진화형 마스터피스를 집필합니다...")
                result = subprocess.run(
                    ["claude", "-p", prompt, "--raw-output", "--accept-raw-output-risk"],
                    capture_output=True, text=True, check=True
                )
                if result.stdout.strip():
                    return self._clean_html(result.stdout)
            except Exception as e:
                print(f"❌ Claude 집필 중 오류 발생: {e}")

        # 2순위: Gemini CLI 사용
        if self.has_gemini:
            try:
                print(f"✍️ 보조 작가 Gemini가 '{topic}'에 대한 최종 진화형 마스터피스를 집필합니다...")
                result = subprocess.run(
                    ["gemini", prompt],
                    capture_output=True, text=True, check=True
                )
                if result.stdout.strip():
                    return self._clean_html(result.stdout)
            except Exception as e:
                print(f"❌ Gemini 집필 중 오류 발생: {e}")

        return None

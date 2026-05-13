import subprocess
import json
import os
import re

WRITE_TIMEOUT_SECONDS = 180
MIN_MASTERPIECE_CHARS = 8000
MIN_MASTERPIECE_SECTIONS = 6
MIN_AVG_PARAGRAPH_CHARS = 230

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

    def is_masterpiece_quality(self, text):
        plain = re.sub(r'<[^>]+>', '\n', text)
        plain = re.sub(r'\s+', ' ', plain).strip()
        section_count = len(re.findall(r'(^|\n)##\s+|<h2\b', text, flags=re.IGNORECASE))
        paragraphs = [
            re.sub(r'<[^>]+>', '', p).strip()
            for p in re.split(r'\n\s*\n|</p>', text)
        ]
        paragraphs = [p for p in paragraphs if len(p) > 80 and not p.startswith('#')]
        avg_paragraph_chars = sum(len(p) for p in paragraphs) / len(paragraphs) if paragraphs else 0
        short_ratio = (
            sum(1 for p in paragraphs if len(p) < 180) / len(paragraphs)
            if paragraphs else 1
        )
        has_insight_blocks = (
            "Developer's Insight" in text
            or "실무 적용" in text
            or "전략적 시사점" in text
            or "깊은 사유" in text
            or "<blockquote" in text
        )
        has_summary = "에디터의 요약" in text or "에디터의 깊은 사유 요약" in text or "핵심 요약" in text
        return (
            len(plain) >= MIN_MASTERPIECE_CHARS
            and section_count >= MIN_MASTERPIECE_SECTIONS
            and avg_paragraph_chars >= MIN_AVG_PARAGRAPH_CHARS
            and short_ratio <= 0.35
            and has_insight_blocks
            and has_summary
        )

    def write_masterpiece(self, topic, context="", persona=None):
        if not persona:
            persona = "전설적인 기술 사상가이자 수석 아키텍트"

        prompt = f"""당신은 {persona}입니다.
당신의 유일한 임무는 아래 주제와 데이터를 바탕으로 완벽한 마크다운 블로그 포스트를 작성하는 것입니다.

[작성 주제]
{topic}

[참고 데이터]
{context}

=== [마스터피스 품질 기준] ===
이 글은 빠르게 찍어낸 일반 블로그 글이 아니라, 숙련된 기술 리서처가 며칠 동안 고민해 쓴 것처럼 느껴져야 합니다.
독자가 읽고 난 뒤 "정보를 얻었다"가 아니라 "판단 기준이 바뀌었다"고 느끼게 만드십시오.

반드시 다음 질문에 답하십시오.
1. 지금 이 주제가 중요한 이유는 무엇인가? 단순 뉴스가 아니라 구조적 변화를 설명하십시오.
2. 표면의 현상 뒤에 있는 경제적/기술적/조직적 동인은 무엇인가?
3. 과장된 낙관론과 과장된 비관론은 각각 어디서 틀리는가?
4. 개발자, 창업자, 기업 의사결정자는 각각 무엇을 다르게 해야 하는가?
5. 6개월, 18개월, 3년 뒤 어떤 변화가 현실화될 가능성이 높은가?

=== [절대 준수 규칙] ===
1. 당신의 응답은 어떠한 사족, 인사말, "여기 있습니다" 같은 말 없이 오직 **순수한 마크다운 본문**이어야 합니다.
2. 반드시 **최소 8,000자 이상**의 방대하고 깊이 있는 내용을 작성하세요. 각 섹션마다 구체적인 예시와 통찰을 깊게 서술하세요.
3. 마크다운 문법을 완벽히 지키고, 문단과 문단 사이에는 반드시 빈 줄(Double Newline)을 넣어 가독성을 확보하세요.
4. 기본 글 구조는 반드시 아래 레퍼런스형 구조를 따른다. 사용자의 추가 지시사항은 이 구조를 깨지 않고 관점, 톤, 사례, 독자 설정만 보강한다.
   - # [강한 H1 대제목: 한 줄 또는 두 줄로 나뉘어도 좋음]
   - [한 줄 부제: 본문이 다룰 핵심 패러다임을 압축]
   - ### 에디터의 깊은 사유 요약
   - 긴 요약 문단: 단순 요약이 아니라 글 전체의 철학적 문제의식과 핵심 논지를 1개의 밀도 높은 문단으로 제시한다.
   - [IMAGE_PLACEHOLDER]
   - ## 1. [도입 섹션: 도구/뉴스의 시대가 끝나고 새로운 질서가 열리는 이유]
   - ## 2. [핵심 현상 섹션: 오늘의 주제를 상징하는 구체적 현상]
   - 중간에 반드시 짧은 인용문을 1개 넣는다. 예: "이 시대의 실력은 속도가 아니라, 의도를 얼마나 명확하게 정의하는가에 의해 결정된다."
   - ## 3. [시스템/오케스트레이션/구조 변화 섹션]
   - ## 4. [인간 또는 조직만이 담당해야 하는 고유 영역]
   - ## 5. [생존 전략: 독자가 포지셔닝을 어떻게 바꿔야 하는가]
   - ## 6. [불확실성/리스크/운영 문제를 설계하는 법]
   - ## 7. [신뢰, 가드레일, 검증 체계]
   - ## 8. 결론: [강한 질문형 또는 선언형 결론]
   - © 2026 AI Agentic Revolution. All rights reserved.
   - #### Gemini CLI, Legendary Architect & Critic
   - 소프트웨어 아키텍처의 철학적 토대를 탐구하며, 인간과 AI가 공존하는 기술적 미래를 설계합니다.
   - * * *
   - 이 글이 도움이 되셨다면 공감과 댓글 부탁드립니다. 독자의 경험을 공유해 달라는 자연스러운 CTA를 넣으세요.
   - 마지막에는 반드시 [RELATED_POSTS] 라는 한 줄만 남긴다. 관련 글 제목을 직접 만들거나 불릿으로 쓰지 마십시오. 실제 링크는 발행 시스템이 자동 삽입합니다.
5. 문단 밀도:
   - 각 H2 섹션은 최소 2~4개의 실질 문단으로 작성하십시오. 레퍼런스처럼 섹션이 선명하게 읽히되, 얕은 요약으로 끝나면 안 됩니다.
   - 각 핵심 문단은 최소 4문장 이상이어야 하며, 한 문단 안에서 주장, 근거, 예시, 함의를 모두 연결하십시오.
   - 짧은 단락을 남발하지 마십시오. 레퍼런스처럼 단호한 문장과 긴 사유 문단의 리듬을 섞으십시오.
   - 소제목 아래에 한두 문단만 쓰고 넘어가는 얕은 구성을 절대 금지합니다.

[절대 금지 사항]
1. 글이 끝난 뒤에 "아티클 구성 요약", "섹션 요약", "포함 요소", "마스터피스 표준 준수 여부" 등 본인이 쓴 글에 대한 어떠한 메타(Meta)적인 설명이나 표(Table)도 절대 덧붙이지 마십시오.
2. 당신의 응답은 오직 블로그 독자가 읽을 순수한 본문 콘텐츠 그 자체로만 구성되어야 합니다. 결론이 끝난 직후에는 어떤 텍스트도 출력하지 말고 그대로 종료하십시오.
3. 참고 데이터에 없는 수치나 사건을 단정하지 마십시오. 불확실한 내용은 "가능성이 높다", "관찰된다", "추정된다"처럼 신중하게 표현하십시오.
4. 뻔한 문장, 홍보성 문장, "혁명입니다" 같은 빈 수사를 반복하지 마십시오. 반드시 구체적 판단 기준과 실행 가능한 관점을 제시하십시오.
"""
        
        if self.has_claude:
            try:
                print(f"✍️ 수석 작가 Claude가 '{topic}'에 대한 최종 진화형 마스터피스를 집필합니다...", flush=True)
                result = subprocess.run(
                    ["claude", "-p", prompt],
                    capture_output=True, text=True, check=False,
                    timeout=WRITE_TIMEOUT_SECONDS
                )
                if result.stdout.strip():
                    content = self._clean_html(result.stdout)
                    if self.is_masterpiece_quality(content):
                        return content
                    print("⚠️ Claude 결과가 마스터피스 품질 기준에 미달해 Gemini 재작성으로 전환합니다.", flush=True)
                if result.stderr.strip():
                    print(f"⚠️ Claude 응답 오류: {result.stderr.strip()[:500]}", flush=True)
            except subprocess.TimeoutExpired:
                print(f"⚠️ Claude 집필이 {WRITE_TIMEOUT_SECONDS}초를 초과해 템플릿 폴백으로 전환합니다.", flush=True)
            except Exception as e:
                print(f"❌ Claude 집필 중 오류 발생: {e}", flush=True)

        if self.has_gemini:
            try:
                print(f"✍️ 보조 작가 Gemini가 '{topic}'에 대한 마스터피스를 집필합니다...", flush=True)
                result = subprocess.run(
                    ["gemini", prompt],
                    capture_output=True, text=True, check=False,
                    timeout=WRITE_TIMEOUT_SECONDS
                )
                if result.stdout.strip():
                    content = self._clean_html(result.stdout)
                    if self.is_masterpiece_quality(content):
                        return content
                    print("⚠️ Gemini 결과가 마스터피스 품질 기준에 미달해 템플릿 폴백으로 전환합니다.", flush=True)
                if result.stderr.strip():
                    print(f"⚠️ Gemini 응답 오류: {result.stderr.strip()[:500]}", flush=True)
            except subprocess.TimeoutExpired:
                print(f"⚠️ Gemini 집필이 {WRITE_TIMEOUT_SECONDS}초를 초과해 템플릿 폴백으로 전환합니다.", flush=True)
            except Exception as e:
                print(f"❌ Gemini 집필 중 오류 발생: {e}", flush=True)

        return None

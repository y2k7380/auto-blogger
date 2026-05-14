import subprocess
import json
import os
import re
import logging

logger = logging.getLogger(__name__)

WRITE_TIMEOUT_SECONDS = 180
MIN_MASTERPIECE_CHARS = 4000
MIN_MASTERPIECE_SECTIONS = 4
MIN_AVG_PARAGRAPH_CHARS = 100

class AIWriter:
    def __init__(self):
        # 로컬 에이전트 가용성 확인
        self.has_claude = self._check_cli("claude")
        self.has_gemini = self._check_cli("gemini")
        
        if self.has_claude:
            logger.info("🚀 수석 작가 'Claude'가 준비되었습니다.")
        elif self.has_gemini:
            logger.info("💡 보조 작가 'Gemini'가 준비되었습니다.")
        else:
            logger.warning("⚠️ 로컬 AI 에이전트를 찾을 수 없습니다. 템플릿 모드로 동작합니다.")

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
        char_count = len(plain)
        section_count = len(re.findall(r'(^|\n)##\s+|<h2\b', text, flags=re.IGNORECASE))
        paragraphs = [
            re.sub(r'<[^>]+>', '', p).strip()
            for p in re.split(r'\n\s*\n|</p>', text)
        ]
        paragraphs = [p for p in paragraphs if len(p) > 50 and not p.startswith('#')]
        avg_paragraph_chars = sum(len(p) for p in paragraphs) / len(paragraphs) if paragraphs else 0

        # 핵심 품질 기준: 충분한 분량 + 섹션 구조만 확인 (톤/스타일은 프롬프트가 담당)
        passed = (
            char_count >= MIN_MASTERPIECE_CHARS
            and section_count >= MIN_MASTERPIECE_SECTIONS
            and avg_paragraph_chars >= MIN_AVG_PARAGRAPH_CHARS
        )
        if not passed:
            logger.warning(f"📊 품질 체크 실패 — 글자수:{char_count}/{MIN_MASTERPIECE_CHARS} 섹션:{section_count}/{MIN_MASTERPIECE_SECTIONS} 평균문단:{avg_paragraph_chars:.0f}/{MIN_AVG_PARAGRAPH_CHARS}")
        else:
            logger.info(f"📊 품질 체크 통과 — 글자수:{char_count} 섹션:{section_count} 평균문단:{avg_paragraph_chars:.0f}")
        return passed

    def write_masterpiece(self, topic, context="", persona=None):
        if not persona:
            persona = "10년차 현직 시니어 개발자 출신 테크 칼럼니스트"

        prompt = f"""당신은 {persona}입니다.
당신의 임무는 아래 주제와 데이터를 바탕으로, **독자가 처음부터 끝까지 빠져들어 읽고, 북마크하고, 다시 찾아오게 만드는** 블로그 포스트를 작성하는 것입니다.

[작성 주제]
{topic}

[참고 데이터]
{context}

═══════════════════════════════════════
📖 [글쓰기 철학: 독자가 늘어나는 글이란?]
═══════════════════════════════════════

이 글은 학술 논문이 아닙니다. 옆자리 시니어 동료가 커피 한 잔 하면서 알려주는 이야기처럼 써야 합니다.
독자는 이 글을 읽고 **월요일 아침에 당장 써먹을 수 있는 것**을 얻어가야 합니다.
- "오, 이건 몰랐는데! 당장 써먹어야지" (실질적 정보)
- "나도 이렇게 해봐야겠다" (구체적 영감)
- "글이 술술 읽힌다, 부담이 없다" (편안한 가독성)
- "이 블로그 다른 글도 봐야지, 믿을 수 있다" (신뢰 기반 재방문)

⚠️ **가장 중요한 원칙: AI가 쓴 글처럼 보이면 실패입니다.**
사람이 실제 경험을 바탕으로 고민하며 쓴 글처럼 느껴져야 합니다.
아래 패턴은 전형적인 AI 글투이므로 절대 사용하지 마세요:
- "~의 시대가 도래했습니다", "~이 혁명을 일으키고 있습니다" 같은 거창한 선언
- 모든 문단을 "~입니다"로 끝내는 단조로운 어미 반복
- "첫째~, 둘째~, 셋째~"로 기계적으로 나열하는 구성
- "결론적으로", "요약하자면", "종합하면" 같은 틀에 박힌 전환어
- 구체적 경험 없이 "~하는 것이 중요합니다"만 반복하는 공허한 조언

대신 이런 톤을 사용하세요:
- "솔직히 말하면, 저도 처음엔 반신반의했습니다"
- "제가 실제로 겪어본 바로는~"
- "여기서 재밌는 건~"
- "근데 함정이 하나 있어요"
- 어미를 ~입니다/~합니다/~거든요/~했어요/~죠 등으로 자연스럽게 섞으세요

═══════════════════════════════════════
✍️ [반드시 지켜야 할 작성 원칙]
═══════════════════════════════════════

1. **첫 문장에서 승부하라**: 독자는 3초 안에 읽을지 말지 결정합니다. 놀라운 사실, 질문, 생생한 장면 묘사로 시작하세요.
   - ❌ "최근 AI 기술이 빠르게 발전하고 있습니다"
   - ✅ "지난주, 한 1인 개발자가 AI 에이전트 3개를 조합해 72시간 만에 SaaS를 출시했습니다"

2. **쉬운 말로 쓰되, 얕지 않게**: 전문 용어가 나오면 반드시 괄호 안에 친절한 설명을 넣거나, "쉽게 말해~" 같은 보충을 다세요.
   - ❌ "에이전틱 워크플로우의 오케스트레이션이 핵심입니다"
   - ✅ "에이전틱 워크플로우(AI가 스스로 계획을 세우고 도구를 골라 쓰는 작업 방식)가 핵심입니다. 쉽게 말해, AI에게 '이거 해줘'가 아니라 '이 목표를 달성해줘'라고 맡기는 겁니다."

3. **구체적인 숫자와 사례를 앞세워라**: "많은 기업이 도입하고 있다" 대신 "2025년 Fortune 500 기업 중 73%가 도입했다"처럼 쓰세요. 확인되지 않은 수치는 "약~", "추정~"으로 표현합니다.

4. **문단의 리듬을 만들어라**:
   - 긴 설명 문단(4~5문장) 뒤에는 짧고 강렬한 한 줄을 넣으세요
   - "결국 핵심은 이겁니다." 같은 전환 문장으로 독자의 집중을 리셋하세요
   - 불릿 포인트(•)와 이모지(💡, 📌, ⚡, 👉, 🔑, ✅)를 적극 활용하여 눈에 확 들어오게 만드세요

5. **독자에게 직접 말을 걸어라**: "여러분이 만약~", "한번 상상해 보세요", "지금 당장 해볼 수 있는 건~" 같은 2인칭 표현을 자연스럽게 섞으세요.

6. **인용문으로 감성 포인트를 찍어라**: 글 중간에 영감을 주는 짧은 인용문을 1~2개 넣으세요. 독자가 캡처해서 공유하고 싶을 만한 문장이어야 합니다.

═══════════════════════════════════════
🏗️ [글 구조 — 반드시 이 뼈대를 따르세요]
═══════════════════════════════════════

# [클릭을 부르는 강한 H1 대제목]
  - 호기심을 자극하거나, 핵심 가치를 한 줄로 약속하는 제목
  - 예: "AI 에이전트 시대, 개발자가 코드 대신 설계해야 할 것" 또는 "72시간 만에 SaaS를 만든 1인 개발자의 비밀 무기"

[한 줄 부제: 이 글을 읽으면 얻게 될 것을 한 문장으로]

### 📌 핵심 요약 — 바쁜 독자를 위한 3줄 정리
  - 글 전체의 핵심을 3개의 불릿 포인트로 압축. 바쁜 독자도 이것만 읽으면 핵심을 파악할 수 있게.

[IMAGE_PLACEHOLDER]

## 1. 🔥 [눈길을 사로잡는 오프닝: 구체적 사실이나 놀라운 사례로 시작]
  - 이 주제가 왜 지금 중요한지를 "피부에 와닿는 사례"로 보여주세요
  - 독자가 "오, 진짜?" 하고 반응할 만한 구체적 정보를 첫 문단에 배치

## 2. 🧩 [쉽게 풀어쓰는 핵심 원리: 이게 도대체 뭔데?]
  - 기술이나 트렌드의 핵심 개념을 비유와 일상 언어로 설명
  - 전문 용어에는 반드시 (쉬운 설명)을 병기
  - "한마디로 정리하면~" 같은 요약 문장을 섹션 끝에 배치

## 3. 💡 [실전 인사이트: 겉으로 안 보이는 진짜 변화]
  - 표면적 트렌드 너머의 구조적 의미를 분석
  - 단, 난해하게 쓰지 말고 "이게 왜 중요하냐면~"으로 시작하는 톤을 유지
  - 인용문 1개를 여기에 배치

## 4. 🎯 [지금 당장 해볼 수 있는 것: 이번 주에 바로 써먹는 가이드]
  - ⭐ 이 섹션이 글의 핵심 가치입니다. 독자가 이 섹션 하나 때문에 블로그를 북마크합니다.
  - 뜬구름 잡는 "~을 고려해보세요" 금지. "터미널을 열고 이 명령어를 입력하세요" 수준의 구체성이 필요합니다.
  - 실제 도구 이름, 설정법, 코드 스니펫, 명령어, 무료 서비스 URL 등을 포함하세요.
  - "이번 주말에 2시간만 투자하면~" 같은 실행 가능한 제안
  - 독자가 읽고 "아, 이건 저장해둬야겠다"라고 느끼는 실용적 정보를 담으세요

## 5. ⚡ [주의할 점: 흔한 실수와 과대광고 구별법]
  - 과장된 기대와 현실의 간극을 솔직하게 짚기
  - "~라고들 하지만, 실제로는~" 패턴 활용
  - 독자가 판단력을 기를 수 있는 구체적 기준 제시

## 6. 🔮 [앞으로 어떻게 될까: 가까운 미래 전망]
  - 3개월, 1년, 3년 단위로 나눠서 간결하게 전망
  - 불확실한 예측은 솔직하게 "아직은 알 수 없지만~"으로 표현
  - 독자가 어떤 신호를 관찰하면 좋은지 안내

## 7. 🎬 마무리: [강한 한 줄로 끝내기]
  - 긴 결론 대신, 독자의 마음에 남을 강렬한 마무리 한 문장
  - 그 뒤에 "여러분의 생각은 어떠신가요?" 같은 자연스러운 참여 유도

---
© 2026 AI Agentic Revolution. All rights reserved.
#### Gemini CLI, Legendary Architect & Critic
소프트웨어 아키텍처의 철학적 토대를 탐구하며, 인간과 AI가 공존하는 기술적 미래를 설계합니다.
* * *
💬 이 글이 도움이 되셨다면 공감과 댓글 부탁드립니다. 여러분이 현장에서 겪은 경험도 공유해 주세요!
[RELATED_POSTS]

═══════════════════════════════════════
🚫 [절대 금지 사항]
═══════════════════════════════════════

1. 응답은 어떠한 사족, 인사말, "여기 있습니다" 없이 오직 **순수한 마크다운 본문**만 출력하세요.
2. 반드시 **최소 7,000자 이상** 작성하세요. 각 섹션은 실질적 내용으로 채우세요.
3. 마크다운 문법을 완벽히 지키고, 문단 사이에는 반드시 빈 줄을 넣으세요.
4. 글이 끝난 뒤에 "구성 요약", "포함 요소", "준수 여부" 등 메타 설명을 절대 붙이지 마세요.
5. 확인되지 않은 수치를 단정하지 마세요. "약~", "추정~", "가능성이 높다"로 표현하세요.
6. 뻔한 홍보 문장("혁명입니다!", "게임 체인저!") 금지. 구체적 근거와 사례로 대체하세요.
7. 난해한 학술 톤 금지. 고등학생도 이해할 수 있되, 전문가도 고개를 끄덕일 깊이를 유지하세요.
8. 마지막에는 반드시 [RELATED_POSTS] 한 줄만 남기세요. 관련 글 제목을 직접 만들지 마세요.
"""
        
        if self.has_claude:
            try:
                logger.info(f"✍️ 수석 작가 Claude가 '{topic}'에 대한 독자 친화적 마스터피스를 집필합니다...")
                result = subprocess.run(
                    ["claude", "-p", prompt],
                    capture_output=True, text=True, check=False,
                    timeout=WRITE_TIMEOUT_SECONDS
                )
                if result.stdout.strip():
                    content = self._clean_html(result.stdout)
                    if self.is_masterpiece_quality(content):
                        return content
                    logger.warning("⚠️ Claude 결과가 마스터피스 품질 기준에 미달해 Gemini 재작성으로 전환합니다.")
                if result.stderr.strip():
                    logger.warning(f"⚠️ Claude 응답 오류: {result.stderr.strip()[:500]}")
            except subprocess.TimeoutExpired:
                logger.warning(f"⚠️ Claude 집필이 {WRITE_TIMEOUT_SECONDS}초를 초과해 템플릿 폴백으로 전환합니다.")
            except Exception as e:
                logger.error(f"❌ Claude 집필 중 오류 발생: {e}")

        if self.has_gemini:
            try:
                logger.info(f"✍️ 보조 작가 Gemini가 '{topic}'에 대한 마스터피스를 집필합니다...")
                result = subprocess.run(
                    ["gemini", prompt],
                    capture_output=True, text=True, check=False,
                    timeout=WRITE_TIMEOUT_SECONDS
                )
                if result.stdout.strip():
                    content = self._clean_html(result.stdout)
                    if self.is_masterpiece_quality(content):
                        return content
                    logger.warning("⚠️ Gemini 결과가 마스터피스 품질 기준에 미달해 템플릿 폴백으로 전환합니다.")
                if result.stderr.strip():
                    logger.warning(f"⚠️ Gemini 응답 오류: {result.stderr.strip()[:500]}")
            except subprocess.TimeoutExpired:
                logger.warning(f"⚠️ Gemini 집필이 {WRITE_TIMEOUT_SECONDS}초를 초과해 템플릿 폴백으로 전환합니다.")
            except Exception as e:
                logger.error(f"❌ Gemini 집필 중 오류 발생: {e}")

        return None

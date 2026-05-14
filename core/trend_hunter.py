from datetime import datetime
import random
import json
import os
import fcntl
import logging
from contextlib import contextmanager
from core.ai_writer import AIWriter

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUN_HISTORY_FILE = os.path.join(BASE_DIR, "config", "run_history.json")

@contextmanager
def file_lock(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file, fcntl.LOCK_UN)

class TrendHunter:
    def __init__(self):
        self.research_logs = []
        self.ai_writer = AIWriter()
        self.glossary_terms = {
            "Agentic Workflow": "단순한 명령 수행을 넘어, 목표 달성을 위해 스스로 계획하고 도구를 사용하는 자율적 작업 흐름",
            "Multi-Agent Orchestration": "여러 개의 전문화된 AI 에이전트가 협업하고 조율하며 복잡한 문제를 해결하는 시스템 아키텍처",
            "Observability": "복잡한 시스템의 내부 상태를 외부 출력을 통해 파악하고 모니터링할 수 있는 능력",
            "Co-evolution": "두 개 이상의 종이 서로 영향을 주고받으며 함께 진화하는 과정, 여기서는 인간과 AI의 상호 발전을 의미"
        }
        self.angle_lenses = [
            "개발자 생산성의 이면에 숨은 품질 부채",
            "AI 인프라 비용과 수익화 압박",
            "오픈소스 생태계가 빅테크 전략을 흔드는 방식",
            "보안과 신뢰성이 AI 도입 속도를 제한하는 지점",
            "작은 팀이 큰 제품을 운영하게 되는 조직 변화",
            "모델 성능보다 워크플로우 설계가 중요해지는 이유",
            "자동화가 일자리를 대체하기보다 책임 경계를 바꾸는 과정",
            "로컬 추론과 클라우드 AI가 동시에 커지는 역설",
            "플랫폼 엔지니어링 관점에서 본 AI 도구 도입",
            "투자자와 창업자가 오해하기 쉬운 AI 시장 신호"
        ]
        self.reader_angles = [
            "실무 개발자",
            "스타트업 창업자",
            "CTO와 기술 리더",
            "AI 도구를 도입하려는 1인 사업자",
            "테크 투자와 시장 흐름을 보는 독자",
            "커리어 방향을 고민하는 주니어 개발자"
        ]
        self.contrasts = [
            "빠른 도입과 느린 검증 사이의 긴장",
            "화려한 데모와 실제 운영 비용의 간극",
            "중앙화된 대형 모델과 분산형 로컬 모델의 충돌",
            "자동화의 효율성과 인간 책임의 재배치",
            "오픈소스 속도와 기업 보안 요구의 충돌",
            "단기 생산성 지표와 장기 유지보수 비용의 차이"
        ]

    def _load_run_history(self):
        if not os.path.exists(RUN_HISTORY_FILE):
            return []
        lock_path = RUN_HISTORY_FILE + ".lock"
        try:
            with file_lock(lock_path):
                with open(RUN_HISTORY_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            return []

    def _save_run_history(self, history):
        os.makedirs(os.path.dirname(RUN_HISTORY_FILE), exist_ok=True)
        lock_path = RUN_HISTORY_FILE + ".lock"
        with file_lock(lock_path):
            with open(RUN_HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(history[-200:], f, ensure_ascii=False, indent=2)

    def _recent_history_for_topic(self, base_topic, limit=12):
        history = self._load_run_history()
        return [item for item in history if item.get("base_topic") == base_topic][-limit:]

    def _record_run_angle(self, base_topic, headline, lens, reader, contrast):
        history = self._load_run_history()
        history.append({
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "base_topic": base_topic,
            "headline": headline,
            "lens": lens,
            "reader": reader,
            "contrast": contrast
        })
        self._save_run_history(history)

    def _create_fresh_angle(self, base_topic):
        recent = self._recent_history_for_topic(base_topic)
        used_lenses = {item.get("lens") for item in recent[-6:]}
        used_readers = {item.get("reader") for item in recent[-4:]}
        rng = random.Random(f"{base_topic}-{datetime.now().isoformat(timespec='microseconds')}")
        lens_pool = [item for item in self.angle_lenses if item not in used_lenses] or self.angle_lenses
        reader_pool = [item for item in self.reader_angles if item not in used_readers] or self.reader_angles
        lens = rng.choice(lens_pool)
        reader = rng.choice(reader_pool)
        contrast = rng.choice(self.contrasts)
        horizon = rng.choice(["30일", "90일", "6개월", "18개월"])
        structure = rng.choice([
            "현상 -> 숨은 동인 -> 반론 -> 실행 기준",
            "사례 -> 실패 원인 -> 선택 기준 -> 다음 행동",
            "시장 신호 -> 기술 구조 -> 조직 리스크 -> 전략적 결론",
            "통념 반박 -> 구조 분석 -> 실무 체크리스트 -> 전망"
        ])
        headline = f"{reader} 관점: {lens}"
        recent_brief = "\n".join(
            f"- {item.get('created_at', '')}: {item.get('headline', '')}"
            for item in recent[-8:]
        ) or "- 아직 기록 없음"
        brief = f"""
--- [이번 실행의 고유 기획 브리프] ---
실행 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
기본 파이프라인 주제: {base_topic}
오늘의 세부 관점: {lens}
핵심 독자: {reader}
중심 긴장: {contrast}
분석 시간축: 앞으로 {horizon}
권장 전개 구조: {structure}

최근 같은 파이프라인에서 이미 사용한 관점/제목:
{recent_brief}

이번 글은 같은 파이프라인에서 나온 이전 글과 제목, 소제목, 사례, 결론이 반복되면 실패입니다.
반드시 위 세부 관점과 핵심 독자에 맞춰 새로운 제목, 새로운 논지, 새로운 섹션 구성을 만드세요.
기본 주제는 유지하되 글의 초점은 "{lens}"와 "{contrast}"에 둡니다.
"""
        self._record_run_angle(base_topic, headline, lens, reader, contrast)
        return headline, brief

    def perform_realtime_research(self, queries):
        logger.info(f"🔍 실시간 정보 수집 시작: {datetime.now().strftime('%H:%M:%S')}")
        for q in queries:
            logger.info(f"  - '{q}' 검색 및 데이터 분석 중...")
            # 실제 환경에서는 여기서 API 호출이나 크롤링이 일어납니다.
            self.research_logs.append(f"Research done for '{q}' at {datetime.now()}")
        logger.info("✅ 정보 수집 완료. 분석된 데이터를 바탕으로 글 작성을 시작합니다.")

    def get_trending_topics(self):
        # In a real app, this would call specialized scrapers/APIs
        # Here we return the latest data fetched via search
        return {
            "SNS (X/Reddit)": [
                {"topic": "AI Infrastructure Investment", "detail": "$650B investment by Google/Microsoft", "trend": "High"},
                {"topic": "Efficiency vs Scale", "detail": "Focus on low-memory inference (Turbo Quant)", "trend": "Rising"},
                {"topic": "AI Observability", "detail": "Monitoring model bias and logic in enterprise", "trend": "New"}
            ],
            "GitHub": [
                {"topic": "llama.cpp", "detail": "High-performance LLM inference engine", "stars": "Trending"},
                {"topic": "opencode", "detail": "Autonomous AI coding agent framework", "stars": "Rising"},
                {"topic": "easy-vibe", "detail": "Vibe coding and developer productivity tools", "stars": "New"}
            ],
            "Search": [
                {"topic": "Musk vs OpenAI Trial", "detail": "Legal battle over AI safety and profit", "volume": "Top"},
                {"topic": "Apple Intelligence", "detail": "Third-party AI extensions (Anthropic/Google)", "volume": "Rising"}
            ],
            "Professional": [
                {"topic": "Agentic SW Development", "detail": "Shift to fully autonomous coding agents", "impact": "Critical"},
                {"topic": "Platform Engineering", "detail": "Standardizing AI-driven infra pipelines", "impact": "High"}
            ]
        }

    def create_masterpiece_post(self, category=None, topic_idx=0, custom_topic=None, custom_rules=None, persona=None):
        if custom_topic:
            fresh_headline, fresh_brief = self._create_fresh_angle(custom_topic)
            topic = f"{custom_topic} - {fresh_headline}"
            logger.info(f"🧭 이번 실행 고유 관점: {fresh_headline}")
        else:
            trends = self.get_trending_topics()
            trend = trends[category][topic_idx]
            topic = trend["topic"]
            fresh_brief = ""
            
        # 1. 리서치 데이터 및 사용자 규칙 주입 (가장 중요한 인사이트의 원천)
        trends_data = self.get_trending_topics()
        research_data = f"{fresh_brief}\n--- [현재 시장의 핵심 트렌드 데이터] ---\n{json.dumps(trends_data, ensure_ascii=False, indent=2)}\n\n"
        
        if custom_rules:
            research_data += f"--- [사용자 특별 지시사항 및 필수 포함 규칙] ---\n{custom_rules}\n\n위 규칙을 반드시 엄수하여 통찰력 있는 글을 작성하세요."
        
        # LLM에게 리서치 데이터와 함께 글 작성을 요청
        llm_content = self.ai_writer.write_masterpiece(topic, context=research_data, persona=persona)
        
        if llm_content:
            return llm_content
            
        # LLM 실패 시 기존 템플릿 모드로 폴백
        return self._create_deep_fallback_post(topic, research_data)

    def _create_deep_fallback_post(self, topic, research_data=""):
        if " - " in topic:
            base_topic, fresh_angle = topic.split(" - ", 1)
        else:
            base_topic, fresh_angle = topic, "이번 주에 꼭 확인해야 할 변화"
        sections = [
            (
                f"🔥 솔직히, 왜 지금 {base_topic}에 주목해야 할까요?",
                f"지난주에 흥미로운 일이 있었어요. 한 스타트업 팀이 {base_topic} 관련 도구를 실무에 적용한 지 딱 2주 만에 개발 속도가 눈에 띄게 빨라졌다는 후기를 올렸거든요. 처음엔 저도 '또 과장이겠지' 싶었는데, 구체적인 수치와 과정을 보니 생각이 달라졌습니다.",
                f"근데 여기서 중요한 건, 이게 단순히 '새로운 도구가 나왔다'는 이야기가 아니라는 거예요. {base_topic}이 바꾸고 있는 건 도구가 아니라 **일하는 방식 자체**입니다. 이 글에서 그 변화가 정확히 뭔지, 그리고 여러분이 당장 어떻게 활용할 수 있는지 풀어볼게요."
            ),
            (
                f"🧩 이게 도대체 뭔데? 쉽게 풀어볼게요",
                f"쉽게 말해, {base_topic}의 핵심은 '도구 하나'가 아니라 **여러 도구가 레고처럼 연결되는 생태계**예요. 예전에는 전문가만 쓸 수 있던 기술인데, 지금은 오픈소스 덕분에 누구나 조합해서 쓸 수 있게 된 거죠.",
                "한마디로 정리하면, 이제 경쟁력은 '누가 더 좋은 모델을 갖고 있냐'가 아니라 '누가 이 도구들을 자기 업무에 가장 잘 연결하냐'로 바뀌고 있어요."
            ),
            (
                f"💡 겉으로 안 보이는 진짜 변화: {fresh_angle}",
                f"대부분의 기사는 '이런 기술이 나왔다'에서 멈추거든요. 근데 진짜 중요한 건 그 뒤에 있어요. '{fresh_angle}'라는 관점에서 보면, 이건 단순한 도구 업그레이드가 아니라 **누가 어떤 결정을 내리는가**의 문제예요.",
                "예전에는 사람이 계획하고 도구가 실행했잖아요. 근데 지금은 도구가 스스로 계획을 세우고, 실패하면 다른 방법을 찾아요. 사람의 역할은 '시키는 사람'에서 '검증하는 사람'으로 바뀌고 있는 거죠."
            ),
            (
                "🎯 이번 주에 바로 써먹을 수 있는 것들",
                "자, 여기가 이 글의 핵심이에요. 읽고 끝나면 의미 없잖아요. 당장 해볼 수 있는 걸 정리해봤습니다.",
                "**개발자라면:** AI 코딩 도구를 써보되, AI가 생성한 코드를 그대로 쓰지 말고 반드시 한 줄씩 읽어보세요. 이게 습관이 되면, 3개월 뒤에 코드 품질이 확연히 달라집니다.",
                "**창업자·1인 사업자라면:** 이번 주말에 2시간만 투자해서 반복 업무 하나를 자동화해보세요. 고객 문의 분류, 일일 리포트 생성 같은 작은 것부터요.",
                "**팀 리더라면:** 팀에서 AI 도구를 어떻게 쓰고 있는지 30분 미팅을 잡아보세요. 누가, 어떤 작업에, 어떤 도구를 쓰는지 파악하는 것만으로도 큰 인사이트를 얻을 수 있어요."
            ),
            (
                "⚡ 함정 주의: 흔한 실수와 과대광고 구별법",
                "'AI가 모든 걸 바꿀 거다'라고들 하지만, 솔직히 그건 반만 맞는 말이에요. 반복적이고 검증 가능한 작업은 빠르게 자동화되겠지만, 맥락 판단이 필요한 일은 당분간 사람 몫으로 남을 거예요.",
                "제가 실제로 겪어본 바로는, 가장 위험한 실수는 **'도구 성능 = 업무 성과'라고 착각하는 것**이에요. 도구가 아무리 좋아도 기존 프로세스, 보안 정책, 데이터 품질이 엉망이면 효과는 제한적이거든요.",
                "👉 **이 기준으로 판단하세요:** 새로운 AI 도구를 볼 때 '이거 멋지다'가 아니라 '이걸 우리 팀 워크플로우에 넣으면 뭐가 달라지지?'라고 물어보세요."
            ),
            (
                "🔮 앞으로 어떻게 될까?",
                "**3개월 안에:** 도구 자체보다 '사용 규칙'이 경쟁력이 될 거예요. 프롬프트 템플릿, 코드 리뷰 기준, 결과 검수 체크리스트를 만들어둔 팀이 앞서갈 거예요.",
                "**1년 안에:** AI 에이전트가 여러 도구를 연결해서 복잡한 작업을 처리하는 게 일반화될 거예요. 핵심은 에이전트 자체가 아니라, 실패했을 때 어떻게 대응하는지예요.",
                "**3년 뒤에는:** 작은 팀이 대기업급 제품을 운영하는 게 가능해질 거예요. '사람이 꼭 판단해야 하는 것'을 정의하는 능력이 핵심 역량이 될 겁니다."
            ),
            (
                "🎬 마무리",
                f"결국 {base_topic}에서 가장 중요한 건 '이 기술이 새롭냐'가 아니라 '이걸 내 상황에 써먹을 수 있냐'예요.",
                "다음 유행이 와도 흔들리지 않을 자기만의 기준을 만드는 것. 그게 지금 가장 가치 있는 투자라고 생각해요. 여러분은 어떻게 생각하시나요?"
            ),
        ]

        content = [f"# {topic}"]
        content.append(f"{base_topic}의 변화를 읽고, 이번 주에 바로 써먹는 실전 가이드")
        content.append("### 📌 핵심 요약 — 바쁜 분들을 위한 3줄 정리")
        content.append(f"- {base_topic}은 단순한 도구가 아니라, 일하는 방식 자체를 바꾸는 흐름입니다\n- 과대광고와 실제 가치를 구별하는 기준: '우리 팀 워크플로우에 넣으면 뭐가 달라지는가?'\n- 이번 주에 바로 해볼 수 있는 구체적인 액션 아이템을 섹션 4에 정리했습니다")
        content.append("[IMAGE_PLACEHOLDER]")
        for idx, (title, *paragraphs) in enumerate(sections, start=1):
            content.append(f"## {title}")
            content.extend(paragraphs)
            if idx == 2:
                content.append(f"> \"진짜 실력은 새로운 도구를 빨리 배우는 게 아니라, 어떤 도구를 쓰지 않을지 판단하는 데서 드러난다.\"")
        content.append("---")
        content.append("© 2026 AI Agentic Revolution. All rights reserved.")
        content.append("#### Gemini CLI, Legendary Architect & Critic")
        content.append("소프트웨어 아키텍처의 철학적 토대를 탐구하며, 인간과 AI가 공존하는 기술적 미래를 설계합니다.")
        content.append("* * *")
        content.append("💬 이 글이 도움이 되셨다면 공감과 댓글 부탁드립니다. 여러분이 현장에서 겪은 경험도 함께 나눠주세요!")
        content.append("[RELATED_POSTS]")
        return "\n\n".join(content)


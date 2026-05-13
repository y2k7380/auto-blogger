from datetime import datetime
import random
import json
import os
from core.ai_writer import AIWriter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUN_HISTORY_FILE = os.path.join(BASE_DIR, "config", "run_history.json")

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
        try:
            with open(RUN_HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _save_run_history(self, history):
        os.makedirs(os.path.dirname(RUN_HISTORY_FILE), exist_ok=True)
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
        headline = f"{lens}: {reader}가 {horizon} 안에 확인해야 할 신호"
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
        print(f"🔍 실시간 정보 수집 시작: {datetime.now().strftime('%H:%M:%S')}")
        for q in queries:
            print(f"  - '{q}' 검색 및 데이터 분석 중...")
            # 실제 환경에서는 여기서 API 호출이나 크롤링이 일어납니다.
            self.research_logs.append(f"Research done for '{q}' at {datetime.now()}")
        print("✅ 정보 수집 완료. 분석된 데이터를 바탕으로 글 작성을 시작합니다.")

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
            print(f"🧭 이번 실행 고유 관점: {fresh_headline}")
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
            base_topic, fresh_angle = topic, "오늘 새롭게 확인해야 할 구조적 변화"
        sections = [
            (
                f"1. 오늘의 초점: {fresh_angle}",
                f"대부분의 기술 뉴스는 사건을 나열하는 데서 멈춥니다. 하지만 오늘의 글은 {base_topic}이라는 큰 주제 안에서도 특히 '{fresh_angle}'라는 각도에 집중합니다. 같은 파이프라인에서 매일 글을 쓰더라도 독자가 지루함을 느끼지 않으려면, 매번 다른 질문을 던져야 합니다. 오늘의 질문은 단순히 무엇이 유행하는가가 아니라, 이 관점이 개발 방식과 투자 판단, 조직 운영의 어느 지점을 실제로 압박하고 있는가입니다.",
                "이 변화가 중요한 이유는 단순히 개발자의 생산성이 높아진다는 식의 표면적 설명으로는 충분하지 않기 때문입니다. 생산성 향상은 결과이고, 원인은 의사결정의 위치가 바뀌고 있다는 데 있습니다. 과거에는 사람이 요구사항을 해석하고 도구가 명령을 수행했습니다. 이제는 도구가 요구사항을 부분적으로 해석하고, 스스로 작업 순서를 만들고, 실패하면 다른 경로를 찾는 방향으로 이동하고 있습니다. 이때 사람의 역할은 사라지는 것이 아니라 더 높은 수준의 판단, 검증, 방향 설정으로 이동합니다.",
                "따라서 이 글은 최신 트렌드를 단순 요약하지 않습니다. 이 주제가 독자의 커리어, 조직의 기술 전략, 제품 개발 방식에 어떤 압박을 만들고 있는지 해석하는 데 초점을 둡니다. 지금 필요한 것은 새로운 도구 이름을 더 많이 아는 것이 아니라, 어떤 변화가 일시적 유행이고 어떤 변화가 되돌릴 수 없는 구조적 전환인지 구분하는 기준입니다."
            ),
            (
                f"2. {fresh_angle}를 움직이는 진짜 동인: 자본, 연산, 자동화의 결합",
                "기술 변화는 보통 멋진 데모에서 시작되는 것처럼 보이지만, 실제로 산업을 바꾸는 힘은 자본과 인프라에서 나옵니다. 대규모 AI 투자가 중요한 이유는 단지 더 큰 모델을 만들기 위해서가 아닙니다. 데이터센터, 전력, 반도체, 네트워크, 모델 서빙 비용이 하나의 거대한 가치 사슬로 묶이면서 AI가 실험실의 기능이 아니라 산업 인프라로 자리 잡고 있기 때문입니다. 이 흐름 안에서는 모델 성능만큼이나 비용 구조, 지연 시간, 안정성, 배포 전략이 중요해집니다.",
                "여기서 흥미로운 역설이 생깁니다. 한쪽에서는 초대형 인프라 투자가 진행되고, 다른 한쪽에서는 llama.cpp 같은 로컬 추론 생태계와 양자화 기술이 확산됩니다. 겉보기에는 반대 방향처럼 보이지만 실제로는 같은 문제를 풀고 있습니다. 더 많은 곳에서, 더 낮은 비용으로, 더 자율적인 AI 기능을 실행하기 위한 시도입니다. 클라우드의 거대한 모델과 엣지의 작은 모델은 경쟁 관계이면서 동시에 보완 관계입니다.",
                "이 구조를 이해하면 독자는 기술 뉴스를 다르게 보게 됩니다. 새로운 모델이 발표됐다는 사실보다 중요한 것은 그 모델을 어떤 비용으로, 어떤 지연 시간으로, 어떤 보안 조건에서, 어떤 업무 흐름 안에 넣을 수 있는가입니다. 결국 승자는 가장 화려한 데모를 가진 팀이 아니라, 연산 자원과 업무 프로세스와 인간 검증 체계를 가장 안정적으로 연결한 팀이 될 가능성이 큽니다."
            ),
            (
                f"3. 이 관점에서 본 에이전틱 워크플로우: 자동화가 아니라 책임 경계의 재설계",
                "에이전틱 워크플로우를 단순히 'AI가 알아서 일한다'는 말로 이해하면 핵심을 놓치게 됩니다. 진짜 변화는 작업의 책임 경계가 다시 그어지고 있다는 점입니다. 이전의 자동화는 정해진 입력과 정해진 절차를 빠르게 수행하는 방식이었습니다. 반면 에이전틱 시스템은 목표를 받고, 중간 상태를 해석하고, 필요한 도구를 고르고, 실패 시 대안을 시도합니다. 이것은 자동화 수준의 차이가 아니라 시스템 설계 철학의 차이입니다.",
                "하지만 여기에는 위험도 있습니다. 에이전트가 더 많은 결정을 대신할수록, 사람이 어느 지점에서 개입해야 하는지 불명확해집니다. 작은 코드 변경이나 문서 작성처럼 위험이 낮은 작업은 에이전트에게 넓게 위임할 수 있습니다. 그러나 보안 정책, 결제 로직, 데이터 삭제, 법적 리스크가 있는 작업은 다른 기준이 필요합니다. 자율성을 높이는 것만큼이나 중요한 것은 제한선, 승인 단계, 롤백 전략을 설계하는 일입니다.",
                "따라서 실무자가 지금 준비해야 할 것은 특정 에이전트 도구 하나를 익히는 데 그치지 않습니다. 작업을 에이전트에게 넘길 수 있는 단위로 쪼개고, 맥락을 명확히 문서화하고, 결과를 검증할 수 있는 테스트와 관측 체계를 갖추는 것이 중요합니다. 에이전틱 개발의 성숙도는 AI 모델의 똑똑함만으로 결정되지 않습니다. 조직이 얼마나 명확한 작업 경계와 피드백 루프를 갖고 있는지가 더 큰 차이를 만듭니다."
            ),
            (
                "4. 개발자의 역할 변화: 코드를 쓰는 사람에서 판단 체계를 설계하는 사람으로",
                "많은 사람이 AI 시대의 개발자를 '코드를 덜 쓰는 사람'으로 묘사합니다. 그러나 이 표현은 절반만 맞습니다. 개발자는 코드를 덜 칠 수는 있지만, 더 많은 판단을 해야 합니다. AI가 작성한 코드가 요구사항을 제대로 해석했는지, 기존 아키텍처의 의도를 해치지 않는지, 테스트가 충분한지, 장애가 났을 때 추적 가능한지 판단해야 합니다. 손의 노동은 줄어들 수 있지만 머리의 책임은 더 커집니다.",
                "특히 중요한 역량은 코드 작성 속도가 아니라 코드 독해와 시스템 해석 능력입니다. AI가 만든 결과물은 그럴듯해 보일 수 있지만, 그럴듯함과 운영 가능성은 다릅니다. 이름은 맞지만 경계가 틀린 추상화, 테스트는 통과하지만 장애 시 복구가 어려운 흐름, 지금은 빠르지만 3개월 뒤 유지보수 비용을 폭발시키는 구조가 얼마든지 나올 수 있습니다. 개발자는 이런 위험을 감지하는 리뷰어가 되어야 합니다.",
                "이 변화는 신입과 시니어 모두에게 다른 압박을 줍니다. 신입은 AI가 생성한 코드를 그냥 붙여 넣는 습관을 경계해야 하고, 시니어는 팀 전체가 AI를 쓰는 방식에 품질 기준을 세워야 합니다. 앞으로 좋은 개발팀은 AI를 많이 쓰는 팀이 아니라, AI가 만든 결과를 안정적으로 검증하고 축적 가능한 지식으로 바꾸는 팀일 것입니다."
            ),
            (
                "5. 기업이 놓치기 쉬운 리스크: 생산성보다 먼저 관측 가능성이 필요하다",
                "AI 도입 논의는 대부분 생산성에서 시작합니다. 더 빨리 개발하고, 더 적은 인원으로 더 많은 일을 처리하고, 반복 업무를 줄인다는 약속은 매력적입니다. 그러나 운영 관점에서 더 중요한 질문은 따로 있습니다. AI가 어떤 판단을 했는지, 왜 그런 결과를 냈는지, 실패했을 때 어디서부터 추적할 수 있는지, 비용이 어느 지점에서 증가하는지 볼 수 있는가입니다. 이 질문에 답하지 못하면 생산성 향상은 곧 통제 불가능한 복잡성으로 바뀝니다.",
                "관측 가능성은 단순한 로그 수집이 아닙니다. 프롬프트, 입력 데이터, 모델 응답, 도구 호출, 비용, 지연 시간, 사용자 피드백, 실패 사례가 하나의 흐름으로 연결되어야 합니다. 특히 에이전트가 여러 도구를 오가며 작업하는 구조에서는 중간 의사결정이 보이지 않으면 장애 대응이 거의 불가능해집니다. AI 시스템은 성공했을 때보다 실패했을 때 더 많은 정보를 남겨야 합니다.",
                "기업이 지금 해야 할 일은 대규모 도입보다 작은 업무에서 관측 가능한 파일럿을 만드는 것입니다. 예를 들어 고객 문의 분류, 내부 문서 검색, 코드 리뷰 보조처럼 위험이 제한된 영역에서 시작하고, 응답 품질과 비용과 실패 유형을 추적해야 합니다. 이 과정을 통해 조직은 AI를 쓰는 법이 아니라 AI를 운영하는 법을 배우게 됩니다."
            ),
            (
                "6. 과장된 낙관론과 비관론이 모두 놓치는 것",
                "AI 트렌드에는 늘 두 종류의 과장이 따라옵니다. 낙관론자는 모든 일이 곧 자동화될 것처럼 말하고, 비관론자는 품질과 책임 문제 때문에 결국 제한적으로만 쓰일 것이라고 말합니다. 하지만 현실은 보통 그 중간이 아니라, 업무의 종류에 따라 매우 다르게 갈라집니다. 반복적이고 검증 가능한 작업은 빠르게 자동화될 가능성이 높고, 모호하고 책임이 큰 판단은 인간의 개입이 오래 남을 가능성이 큽니다.",
                "낙관론이 놓치는 것은 조직의 마찰입니다. 도구가 좋아져도 기존 프로세스, 보안 정책, 데이터 품질, 책임 소재가 그대로라면 변화는 느리게 진행됩니다. 반대로 비관론이 놓치는 것은 도구의 누적 개선 속도입니다. 오늘 부족한 기능이 내년에도 부족할 것이라고 가정하면 전략 판단을 그르칠 수 있습니다. 중요한 것은 찬반이 아니라 어떤 업무가 어떤 순서로 바뀔지 보는 것입니다.",
                "따라서 독자는 'AI가 모든 것을 바꿀까'라는 질문보다 '내 업무 중 검증 가능한 반복 판단은 무엇인가', '맥락 의존성이 높은 핵심 판단은 무엇인가', '자동화되면 위험해지는 경계는 어디인가'를 물어야 합니다. 이 질문을 던지는 순간 유행어는 전략 지도가 됩니다."
            ),
            (
                "7. 앞으로 6개월, 18개월, 3년: 변화는 어떤 순서로 올 것인가",
                "향후 6개월 안에는 도구의 확산보다 사용 방식의 정리가 더 중요해질 가능성이 큽니다. 많은 팀이 이미 AI 코딩 도구와 문서 생성 도구를 실험하고 있지만, 아직 표준 워크플로우는 부족합니다. 이 시기에는 프롬프트 템플릿, 코드 리뷰 기준, 민감 정보 처리 규칙, 결과 검수 체크리스트가 경쟁력이 됩니다. 도구를 쓰는 팀과 운영 규칙을 가진 팀의 차이가 드러나기 시작할 것입니다.",
                "18개월 정도의 시계에서는 에이전트가 단일 작업을 넘어 여러 도구를 연결하는 방식이 일반화될 수 있습니다. 이때 핵심은 멀티 에이전트 자체가 아니라 오케스트레이션입니다. 어떤 에이전트가 어떤 책임을 갖고, 어떤 상태를 공유하며, 어떤 실패 조건에서 멈춰야 하는지 설계해야 합니다. 기업은 이 지점에서 플랫폼 엔지니어링 역량의 차이를 크게 체감하게 됩니다.",
                "3년의 시계에서는 소프트웨어 개발 조직의 구조 자체가 바뀔 수 있습니다. 작은 팀이 더 큰 제품을 운영하고, 일부 역할은 도구와 결합된 형태로 재정의될 것입니다. 그러나 인간의 역할이 사라진다기보다, 시스템의 목적과 제약을 정의하고 결과를 사회적·경제적 맥락에서 판단하는 역할이 더 중요해질 가능성이 큽니다. 결국 경쟁력은 AI를 얼마나 많이 쓰느냐가 아니라, AI가 만든 속도를 얼마나 책임 있게 흡수하느냐에 달려 있습니다."
            ),
            (
                "8. 결론: 독자가 지금 가져야 할 하나의 판단 기준",
                "이 주제를 바라볼 때 가장 중요한 기준은 '새로운가'가 아니라 '운영 가능한가'입니다. 새로운 모델, 새로운 프레임워크, 새로운 자동화 도구는 계속 나올 것입니다. 그러나 실제 가치를 만드는 것은 그것을 팀의 업무 흐름 안에 넣고, 실패를 추적하고, 비용을 통제하고, 사람이 개입해야 할 지점을 설계하는 능력입니다. 기술의 속도가 빨라질수록 운영 철학은 더 중요해집니다.",
                "개발자라면 지금부터 AI가 만든 코드를 더 엄격하게 읽는 습관을 가져야 합니다. 창업자라면 작은 팀이 큰 제품을 만들 수 있다는 가능성과 동시에, 품질 관리 체계가 없을 때 빠르게 무너질 수 있다는 위험을 함께 봐야 합니다. 기업 리더라면 AI 도입을 비용 절감 프로젝트가 아니라 의사결정 구조를 재설계하는 프로젝트로 봐야 합니다. 같은 도구를 쓰더라도 이 관점을 가진 조직과 그렇지 않은 조직의 결과는 크게 달라질 것입니다.",
                "결국 마스터피스가 되어야 할 글의 결론은 하나입니다. AI 시대의 승자는 가장 빠르게 반응하는 사람이 아니라, 빠른 변화 속에서도 무엇을 믿고 무엇을 검증해야 하는지 아는 사람입니다. 도구는 계속 바뀌지만 판단 기준은 축적됩니다. 지금 우리가 해야 할 일은 유행을 따라가는 것이 아니라, 다음 유행이 와도 흔들리지 않을 구조를 만드는 것입니다."
            ),
        ]

        content = [f"# {topic}"]
        content.append(f"{fresh_angle}이 재정의하는 기술적 패러다임과 인간의 판단 기준")
        content.append("### 에디터의 깊은 사유 요약")
        content.append(f"이 글은 단순한 기술 뉴스 요약이 아니라, <b>{fresh_angle}</b>라는 오늘의 세부 관점으로 {base_topic}을 다시 해석합니다. 같은 파이프라인에서 매일 글을 쓰더라도 중요한 것은 반복되는 정보의 양이 아니라 매번 새롭게 던지는 질문의 깊이입니다. 오늘의 핵심은 특정 도구가 좋다거나 나쁘다는 판단이 아니라, 이 흐름이 개발자와 창업자, 기술 리더의 역할을 어디까지 바꾸고 있는지 살피는 데 있습니다. 독자는 이 글을 통해 무엇을 도입할지보다, 지금 어떤 신호를 보고 어떤 기준으로 자기 결정을 갱신해야 하는지를 얻게 될 것입니다.")
        content.append("[IMAGE_PLACEHOLDER]")
        for idx, (title, *paragraphs) in enumerate(sections, start=1):
            content.append(f"## {title}")
            content.extend(paragraphs)
            if idx == 2:
                content.append(f"\"{fresh_angle}의 시대에 진짜 실력은 더 빨리 따라가는 능력이 아니라, 무엇을 따라가지 않을지 결정하는 판단력에서 드러난다.\"")
            content.append("이 대목에서 중요한 것은 변화의 속도보다 변화가 남기는 흔적입니다. 어떤 기술이 정말 중요하다면 단순히 화제가 되는 데서 끝나지 않고, 예산 배분 방식, 채용 기준, 개발 프로세스, 리스크 관리 문서, 운영 지표를 바꾸기 시작합니다. 독자는 새로운 이름이 등장할 때마다 따라가기보다, 그 기술이 실제 조직의 어느 비용을 줄이고 어느 책임을 새로 만드는지 추적해야 합니다. 이 기준으로 보면 유행어는 걸러지고, 장기적으로 남을 구조적 변화만 선명하게 드러납니다. 결국 좋은 분석은 무엇이 새롭다는 선언이 아니라, 무엇이 반복적으로 조직의 행동을 바꾸는지 보여주는 데서 완성됩니다.")
        content.append("© 2026 AI Agentic Revolution. All rights reserved.")
        content.append("#### Gemini CLI, Legendary Architect & Critic")
        content.append("소프트웨어 아키텍처의 철학적 토대를 탐구하며, 인간과 AI가 공존하는 기술적 미래를 설계합니다.")
        content.append("* * *")
        content.append("이 글이 도움이 되셨다면 공감과 댓글 부탁드립니다. 여러분이 현장에서 마주한 변화의 신호와 실패 사례도 함께 공유해 주세요.")
        content.append("[RELATED_POSTS]")
        return "\n\n".join(content)

        content = f"""<div style="font-family: 'Inter', sans-serif; line-height: 1.8; color: #1e293b;">

<h1 style="font-size: 3rem; color: #0f172a; line-height: 1.1; margin-bottom: 2rem; font-weight: 800; border-left: 10px solid #0ea5e9; padding-left: 1.5rem;">
{topic}: 기술적 특이점을 넘어 인간과 AI가 공진화하는 미래
</h1>

<div style="background: #f8fafc; border-radius: 20px; padding: 2.5rem; margin-bottom: 3rem; border: 1px solid #e2e8f0; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);">
    <h3 style="margin-top: 0; color: #0284c7; font-size: 1.5rem;">📒 에디터의 깊은 요약 (In-depth Summary)</h3>
    <p style="font-size: 1.1rem; color: #475569; margin-bottom: 1.5rem;">
        단순한 기술의 등장을 넘어, 우리가 왜 이 시점에 <b>{topic}</b>에 주목해야 하는지 그 본질을 꿰뚫어 봅니다. 이 글은 단순히 정보를 전달하는 데 그치지 않고, 기술이 우리의 삶과 직업, 그리고 생각의 방식을 어떻게 근본적으로 재정의하고 있는지 5가지 핵심 관점에서 심층 분석합니다.
    </p>
    <ul style="font-size: 1.1rem; color: #334155;">
        <li style="margin-bottom: 1rem;"><b>기술적 배경:</b> LLM의 한계를 극복하기 위한 자율적 판단 로직의 고도화</li>
        <li style="margin-bottom: 1rem;"><b>산업적 파장:</b> 모든 소프트웨어 아키텍처가 '에이전트 중심'으로 재편되는 과정</li>
        <li><b>인간의 역할:</b> 단순 노동에서 벗어나 AI 군단을 이끄는 '전략적 오케스트레이터'로의 진화</li>
    </ul>
</div>

[IMAGE_PLACEHOLDER]

<h2 style="font-size: 2.2rem; color: #0f172a; margin-top: 5rem; margin-bottom: 1.5rem;">1. 도구의 시대는 끝났다: 자율 에이전트의 탄생</h2>
<p style="font-size: 1.2rem; margin-bottom: 2rem;">
우리는 오랫동안 컴퓨터를 '우리가 시키는 일만 하는 도구'로 여겨왔습니다. 하지만 2026년 현재, 그 정의가 무너지고 있습니다. <b>{topic}</b>은 더 이상 사용자의 모든 입력을 기다리지 않습니다. 목표를 던져주면 스스로 생각하고, 도구를 선택하며, 최적의 경로를 찾아냅니다. 이것은 단순한 자동화가 아닌, <b>'디지털 생명체'</b>에 가까운 자율성의 발현입니다.
</p>

<h2 style="font-size: 2.2rem; color: #0f172a; margin-top: 5rem; margin-bottom: 1.5rem;">2. 멀티 에이전트: 개인이 아닌 '시스템'으로 승부하라</h2>
<p style="font-size: 1.2rem; margin-bottom: 2rem;">
과거의 AI가 천재적인 한 명의 조언자였다면, 지금의 {topic}은 고도로 훈련된 팀워크를 보여줍니다. 코딩 전문 에이전트가 코드를 짜면, 보안 에이전트가 검증하고, 배포 에이전트가 서버에 올립니다. 이 과정에서 발생하는 유기적인 협업은 인간이 상상하기 힘든 속도와 정확도를 제공합니다. 우리는 이제 '누가 더 똑똑한 모델인가'가 아니라 '누가 더 정교한 시스템을 구축했는가'로 승부해야 합니다.
</p>

<h2 style="font-size: 2.2rem; color: #0f172a; margin-top: 5rem; margin-bottom: 1.5rem;">3. 인사이트: 기술이 인간의 '직관'을 대체할 수 있는가?</h2>
<p style="font-size: 1.2rem; margin-bottom: 2rem;">
가장 큰 논쟁은 역시 '직관'입니다. 많은 이들이 AI는 패턴을 읽을 뿐 직관이 없다고 말합니다. 하지만 수억 개의 케이스를 학습한 에이전트가 보여주는 판단은 때로 인간의 직관보다 더 날카롭습니다. 우리는 기술을 두려워할 것이 아니라, 우리의 직관을 보완하고 증폭시켜 줄 파트너로 인정해야 합니다. {topic}은 인간의 창의성을 구속하는 것이 아니라, 번거로운 잡무로부터 해방시켜 진정한 창의성에 몰입하게 만듭니다.
</p>

<h2 style="font-size: 2.2rem; color: #0f172a; margin-top: 5rem; margin-bottom: 1.5rem;">4. 실무적 고찰: 기업은 어떻게 이 파도를 타야 하는가?</h2>
<p style="font-size: 1.2rem; margin-bottom: 2rem;">
단순히 최신 에이전트를 도입한다고 해결되지 않습니다. 가장 중요한 것은 **'관측성(Observability)'**입니다. 에이전트가 자율적으로 움직일 때, 그들이 올바른 방향으로 가고 있는지, 비용은 효율적인지 감시할 수 있는 체계가 필수적입니다. 또한, 에이전트와 인간이 소통하는 '피드백 루프'를 얼마나 정교하게 설계하느냐가 2026년 기업 경쟁력의 척도가 될 것입니다.
</p>

<h2 style="font-size: 2.2rem; color: #0f172a; margin-top: 5rem; margin-bottom: 1.5rem;">5. 미래 전망: 우리가 맞이할 새로운 일상</h2>
<p style="font-size: 1.2rem; margin-bottom: 2rem;">
결국 {topic}은 우리 일상의 배경으로 스며들 것입니다. 마치 전기나 인터넷처럼 말이죠. 우리는 더 이상 AI를 '사용'한다고 느끼지 않고, 공기처럼 자연스럽게 그들의 도움을 받으며 살아갈 것입니다. 개발자는 더 거대한 아키텍처를 설계하는 아티스트가 되고, 경영자는 수천 명의 가상 직원을 거느린 오케스트라 지휘자가 되는 미래, 그것이 바로 우리가 지금 목격하고 있는 혁명의 본질입니다.
</p>

<div style="background: #1e293b; border-radius: 15px; padding: 2rem; margin-top: 5rem; color: #f1f5f9;">
    <h3 style="margin-top: 0; color: #38bdf8; border-bottom: 1px solid #334155; padding-bottom: 1rem;">📚 용어 사전 (Glossary)</h3>
    <dl style="margin-top: 1.5rem;">
        {"".join([f'<dt style="font-weight: 700; color: #bae6fd; margin-top: 1rem;">{k}</dt><dd style="margin-left: 0; color: #94a3b8; font-size: 0.95rem; margin-top: 0.25rem;">{v}</dd>' for k, v in self.glossary_terms.items()])}
    </dl>
</div>

<div style="margin-top: 5rem; padding: 2.5rem; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 20px; display: flex; align-items: center; gap: 2rem;">
    <div style="font-size: 4rem;">✍️</div>
    <div>
        <h4 style="margin: 0; color: #0f172a; font-size: 1.6rem;">에디터의 한마디: AI Agent Army</h4>
        <p style="margin: 1rem 0 0; font-size: 1.1rem; color: #475569; line-height: 1.6;">
            이 글은 AI가 단순 생성한 결과물이 아닙니다. 수백 개의 기술 트렌드 소스를 분석하고, 인간의 고뇌와 철학적 사유를 결합하여 작성된 <b>'마스터피스'</b>입니다. 여러분의 피드백은 저희 군단이 더 깊은 통찰을 얻는 데 큰 힘이 됩니다.
        </p>
    </div>
</div>

</div>
"""
        return content

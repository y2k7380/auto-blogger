document.addEventListener('DOMContentLoaded', () => {
    // CLOCK
    setInterval(() => {
        document.getElementById('current-time').textContent = new Date().toLocaleTimeString('ko-KR') + ' KST';
    }, 1000);

    // NAVIGATION
    const navItems = document.querySelectorAll('.nav-item[data-target]');
    const sections = document.querySelectorAll('.view-section');

    function activateSection(targetId) {
        navItems.forEach(nav => nav.classList.toggle('active', nav.dataset.target === targetId));
        sections.forEach(sec => sec.classList.toggle('active', sec.id === targetId));
        if (targetId === 'dashboard') loadPipelines(false);
        if (targetId === 'oneoff') loadOneoffHistory();
        if (targetId === 'logs') {
            fetchLogs();
            fetchQueueStatus();
        }
    }
    
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            activateSection(item.dataset.target);
        });
    });

    // MODAL
    const modal = document.getElementById('pipeline-modal');
    const baseMasterpieceRules = `1. 이 글은 빠르게 찍어낸 일반 정보글이 아니라, 숙련된 리서처가 오래 고민해 쓴 마스터피스처럼 느껴져야 한다.
2. 기본 구조는 사용자가 선호한 레퍼런스 구조를 따른다: 강한 H1, 한 줄 부제, "에디터의 깊은 사유 요약", 8개 번호형 H2, 중간 인용문, 저자/CTA/함께 읽으면 좋은 글.
3. 추가 지시사항은 이 기본 구조를 깨지 않고 톤, 독자, 사례, 관점, 결론의 방향을 보강하는 방식으로만 반영한다.
4. 첫 요약 문단은 독자의 문제의식, 불안, 호기심을 강하게 건드리되 단순 요약이 아니라 글 전체의 철학적 문제의식을 압축해야 한다.
5. 단순 뉴스 요약이 아니라 "왜 지금 중요한가", "무엇이 바뀌는가", "독자는 무엇을 다르게 해야 하는가"를 끝까지 밀고 나간다.
6. 각 섹션은 현상 -> 숨은 원인 -> 반론/위험 -> 실무적 의미를 자연스럽게 품되, 레퍼런스처럼 제목이 선명하고 읽는 리듬이 살아 있어야 한다.
7. 뻔한 찬양, 과장된 혁명론, 추상적 문장을 피하고 구체적인 판단 기준과 실행 포인트를 제시한다.
8. 제목과 소제목은 클릭을 유도하되 낚시가 아니라 본문에서 반드시 회수되는 약속이어야 한다.
9. 최소 8,000자 이상, H2 섹션 8개 이상, 글 말미에는 독자가 자기 상황에 대입해 생각하게 만드는 강한 결론을 작성한다.`;

    const templateAddons = {
        masterpiece_default: `10. 독자가 "이 글은 흔한 AI 요약이 아니라 관점이 있다"고 느끼도록 전체 논지를 하나의 큰 주장으로 묶어라.
11. 도입부에는 현재 변화가 독자의 일, 돈, 시간, 커리어에 어떤 압박으로 다가오는지 구체적으로 보여줘라.
12. 중간중간 짧고 날카로운 문장으로 리듬을 만들고, 긴 설명 뒤에는 반드시 한 문장짜리 핵심 판단을 남겨라.`,
        breaking_trend: `10. 글의 톤은 "지금 놓치면 뒤처지는 변화"를 다루는 긴급 분석이어야 한다.
11. 첫 문단에서 최근 변화가 왜 단순 유행이 아니라 구조적 전환인지 선명하게 제시한다.
12. 독자가 바로 확인해야 할 신호, 앞으로 30~90일 동안 지켜봐야 할 지표, 과장 가능성을 분리해 설명한다.
13. 빠른 뉴스 요약이 아니라 "이 뉴스가 다음 변화를 예고하는 이유"를 파고든다.`,
        contrarian: `10. 모두가 당연하게 믿는 통념 하나를 정면으로 의심하며 시작한다.
11. 반대 관점을 공격적으로 쓰되 선정적으로 몰아가지 말고, 데이터와 구조적 이유로 설득한다.
12. "사람들이 틀리는 지점", "진짜 승자가 생기는 지점", "대부분이 뒤늦게 깨닫는 지점"을 별도 섹션으로 다룬다.
13. 결론은 독자가 기존 생각을 바꾸게 만드는 질문으로 닫는다.`,
        developer_deepdive: `10. 독자는 실무 개발자다. 추상적 전망보다 아키텍처, 도구 선택, 운영 리스크, 코드 품질 문제를 중심으로 설명한다.
11. 각 섹션 끝에 Developer's Insight를 넣고, 실제로 무엇을 학습/도입/경계해야 하는지 명확히 적는다.
12. 로컬 개발, CI/CD, 관측 가능성, 보안, 비용 최적화 관점을 반드시 포함한다.
13. "내일부터 팀에서 적용한다면 무엇부터 바꿀 것인가"라는 실행 계획을 제시한다.`,
        executive_brief: `10. 독자는 CEO, CTO, 팀 리더, 투자 판단자다. 기술 세부보다 전략적 의미, 비용, 리스크, 조직 변화에 집중한다.
11. 시장 구조, 경쟁 우위, 도입 비용, 실패 리스크, 인력 재배치 관점을 분리해 설명한다.
12. 단기 액션, 중기 투자, 장기 방어 전략을 명확히 제시한다.
13. 결론에는 "지금 결정하지 않으면 생기는 비용"을 설득력 있게 보여준다.`,
        beginner_bridge: `10. 어려운 개념을 쉽게 풀되 수준을 낮추지 않는다. 초보자도 읽히지만 전문가도 가볍다고 느끼지 않게 쓴다.
11. 모든 핵심 용어는 쉬운 비유와 실제 사례를 함께 붙인다.
12. 독자가 중간에 길을 잃지 않도록 각 섹션 첫 문장에 "이 섹션에서 이해할 것"을 자연스럽게 암시한다.
13. 마지막에는 입문자가 다음으로 읽거나 해볼 만한 행동을 제시한다.`,
        future_scenario: `10. 6개월, 18개월, 3년 시나리오를 반드시 나누어 작성한다.
11. 각 시나리오마다 낙관, 현실, 비관 케이스를 비교한다.
12. "무엇이 현실화되면 이 예측이 맞았다고 볼 수 있는가"라는 관찰 지표를 제시한다.
13. 미래 예측은 단정하지 말고 확률과 조건을 중심으로 신중하게 쓴다.`,
        case_study: `10. 실제 기업이나 팀에서 이 주제를 도입한다고 가정하고, 성공 사례와 실패 사례를 구체적으로 구성한다.
11. 실패 원인은 기술 부족, 조직 저항, 데이터 품질, 비용 폭증, 보안 리스크로 나누어 분석한다.
12. 독자가 자기 조직에 적용할 수 있도록 체크리스트와 단계별 도입 전략을 포함한다.
13. "겉으로는 성공처럼 보이지만 실제로는 실패인 경우"를 반드시 다룬다.`,
        comparison: `10. 비슷한 도구, 접근법, 전략을 비교하며 독자가 선택 기준을 얻도록 쓴다.
11. 비교 기준은 성능, 비용, 유지보수성, 학습 곡선, 생태계, 리스크로 나눈다.
12. 특정 선택지를 무조건 추천하지 말고 상황별 최적 선택을 제시한다.
13. 결론에는 독자가 자신의 상황을 판단할 수 있는 5가지 질문을 포함한다.`,
        monetization: `10. 독자가 이 글을 읽고 구매, 도입, 학습, 투자 중 하나를 판단할 수 있게 만든다.
11. 장점만 쓰지 말고 단점과 맞지 않는 사람을 분명히 적어 신뢰를 확보한다.
12. 수익화 포인트는 과장하지 말고 비용 대비 효과, 회수 기간, 필요한 역량을 중심으로 설명한다.
13. 행동 유도는 노골적인 판매 문구가 아니라 "이런 상황이라면 지금 검토하라"는 판단형 문장으로 작성한다.`
    };

    function buildRules(templateKey = 'masterpiece_default') {
        const addon = templateAddons[templateKey] || templateAddons.masterpiece_default;
        return `${baseMasterpieceRules}\n\n[템플릿별 추가 지시]\n${addon}`;
    }

    document.getElementById('open-pipeline-modal').addEventListener('click', () => {
        document.getElementById('modal-title').textContent = '새로운 마스터피스 파이프라인';
        document.getElementById('pipe-id').value = '';
        document.getElementById('pipe-topic').value = '';
        document.getElementById('pipe-time').value = '09:00';
        document.getElementById('pipe-persona').value = 'Masterpiece';
        document.getElementById('rule-template').value = 'masterpiece_default';
        document.getElementById('pipe-rules').value = buildRules('masterpiece_default');
        modal.classList.add('active');
    });
    document.getElementById('close-modal').addEventListener('click', () => modal.classList.remove('active'));

    // TOPIC PILLS
    document.querySelectorAll('.topic-pill').forEach(pill => {
        pill.addEventListener('click', () => {
            document.getElementById('pipe-topic').value = pill.textContent.replace('💡 ', '');
        });
    });

    // RULE TEMPLATES
    document.getElementById('rule-template').addEventListener('change', (e) => {
        if(e.target.value) {
            document.getElementById('pipe-rules').value = buildRules(e.target.value);
        }
    });

    // PIPELINES
    let currentPipelines = [];
    let pipelinesLoaded = false;

    // Helper: Time to Cron (e.g. "09:30" -> "30 9 * * *")
    function timeToCron(timeStr) {
        const [hours, minutes] = timeStr.split(':');
        return `${parseInt(minutes, 10)} ${parseInt(hours, 10)} * * *`;
    }

    // Helper: Cron to Time (e.g. "30 9 * * *" -> "09:30")
    function cronToTime(cronStr) {
        try {
            const parts = cronStr.split(' ');
            const m = parts[0].padStart(2, '0');
            const h = parts[1].padStart(2, '0');
            return `${h}:${m}`;
        } catch { return "09:00"; }
    }

    function shortText(value, limit = 420) {
        const text = value || '';
        return text.length > limit ? `${text.slice(0, limit).trim()}...` : text;
    }

    async function loadPipelines(force = true) {
        if (pipelinesLoaded && !force) return;
        const grid = document.getElementById('pipeline-list');
        grid.innerHTML = '<div style="color:var(--text-muted);">로딩 중...</div>';
        try {
            const res = await fetch('/api/pipelines');
            const data = await res.json();
            currentPipelines = data.pipelines;
            pipelinesLoaded = true;
            
            if(data.pipelines.length === 0) {
                grid.innerHTML = '<div style="color:var(--text-muted); grid-column: 1/-1;">등록된 파이프라인이 없습니다. 우측 상단의 버튼을 눌러 파이프라인을 생성하세요.</div>';
                return;
            }
            
            grid.innerHTML = '';
            data.pipelines.forEach(pipe => {
                const card = document.createElement('div');
                card.className = 'pipeline-card';
                card.innerHTML = `
                    <div class="pipe-header">
                        <span class="pipe-badge">${pipe.persona}</span>
                        <span class="pipe-id">#${pipe.id}</span>
                    </div>
                    <div class="pipe-topic">${pipe.topic}</div>
                    <div class="pipe-cron">⏱️ 매일 ${cronToTime(pipe.schedule)} 발행</div>
                    <div class="pipe-rules">${escapeHtml(shortText(pipe.rules)).replace(/\n/g, '<br>')}</div>
                    <div class="pipe-actions">
                        <button type="button" class="btn-card-action" data-action="edit" data-id="${pipe.id}">편집</button>
                        <button type="button" class="btn-card-action primary" data-action="run" data-id="${pipe.id}">지금 실행</button>
                        <button type="button" class="btn-card-action danger" data-action="delete" data-id="${pipe.id}">삭제</button>
                    </div>
                `;
                grid.appendChild(card);
            });
        } catch (e) {
            grid.innerHTML = '<div style="color:var(--error);">파이프라인을 불러오지 못했습니다.</div>';
        }
    }

    async function savePipelineData() {
        const timeVal = document.getElementById('pipe-time').value;
        const cronVal = timeToCron(timeVal);
        
        const payload = {
            id: document.getElementById('pipe-id').value,
            topic: document.getElementById('pipe-topic').value,
            schedule: cronVal,
            persona: document.getElementById('pipe-persona').value,
            rules: document.getElementById('pipe-rules').value
        };
        
        if(!payload.topic || !payload.rules) { alert('주제와 규칙을 모두 입력하세요.'); return null; }
        
        try {
            const res = await fetch('/api/pipeline/save', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload)
            });
            if(res.ok) {
                const result = await res.json();
                modal.classList.remove('active');
                loadPipelines();
                return result.pipeline || payload;
            } else {
                alert('저장 실패');
                return null;
            }
        } catch(e) { alert('서버 연결 오류'); return null; }
    }

    document.getElementById('save-pipeline').addEventListener('click', savePipelineData);

    document.getElementById('pipeline-list').addEventListener('click', (event) => {
        const button = event.target.closest('button[data-action]');
        if (!button) return;

        const id = button.dataset.id;
        const action = button.dataset.action;
        if (action === 'edit') editPipeline(id);
        if (action === 'run') runPipeline(id, button);
        if (action === 'delete') deletePipeline(id);
    });

    function editPipeline(id) {
        const pipe = currentPipelines.find(p => p.id === id);
        if(!pipe) return;
        document.getElementById('modal-title').textContent = '파이프라인 수정';
        document.getElementById('pipe-id').value = pipe.id;
        document.getElementById('pipe-topic').value = pipe.topic;
        document.getElementById('pipe-time').value = cronToTime(pipe.schedule);
        document.getElementById('pipe-persona').value = pipe.persona;
        document.getElementById('rule-template').value = '';
        document.getElementById('pipe-rules').value = pipe.rules && pipe.rules.length > 500
            ? pipe.rules
            : `${baseMasterpieceRules}\n\n[기존 파이프라인 추가 지시]\n${pipe.rules || ''}`;
        modal.classList.add('active');
    }

    async function deletePipeline(id) {
        if(!confirm('이 파이프라인(크론 포함)을 삭제하시겠습니까?')) return;
        try {
            const res = await fetch('/api/pipeline/delete', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({id})
            });
            if(res.ok) {
                pipelinesLoaded = false;
                loadPipelines(true);
            }
            else alert('삭제 실패');
        } catch(e) { alert('서버 에러'); }
    }

    async function runPipeline(id, button) {
        if (button) {
            button.disabled = true;
            button.textContent = '실행 중...';
        }
        try {
            const res = await fetch('/api/run', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({id})
            });
            if(!res.ok) {
                const text = await res.text();
                alert(`실행 요청 실패: ${text}`);
                return;
            }
            const result = await res.json();
            if (result.status === 'queued') {
                button.textContent = '큐 등록됨';
            }
            fetchLogs();
            fetchQueueStatus();
        } catch(e) {
            alert(`서버 에러: ${e.message}`);
        } finally {
            if (button && button.textContent !== '큐 등록됨') {
                button.disabled = false;
                button.textContent = '지금 실행';
            }
            if (button && button.textContent === '큐 등록됨') {
                setTimeout(() => {
                    button.disabled = false;
                    button.textContent = '지금 실행';
                }, 1500);
            }
        }
    }

    window.editPipeline = editPipeline;
    window.deletePipeline = deletePipeline;
    window.runPipeline = runPipeline;

    // ONE-OFF PUBLISH
    const oneoffHistoryList = document.getElementById('oneoff-history-list');
    const runOneoffButton = document.getElementById('run-oneoff');

    function statusLabel(status) {
        const labels = {
            queued: '대기',
            running: '작성 중',
            completed: '완료',
            failed: '실패'
        };
        return labels[status] || status || '대기';
    }

    async function loadOneoffHistory() {
        if (!oneoffHistoryList) return;
        try {
            const res = await fetch('/api/oneoff/history');
            const data = await res.json();
            const history = data.history || [];
            if (!history.length) {
                oneoffHistoryList.innerHTML = '<div class="history-empty">아직 단발 발행 이력이 없습니다.</div>';
                return;
            }
            oneoffHistoryList.innerHTML = history.map(item => {
                const title = escapeHtml(item.title || item.topic || '제목 없음');
                const preview = escapeHtml(item.prompt_preview || item.message || '');
                const created = escapeHtml(item.created_at || item.started_at || '');
                const finished = item.finished_at ? `완료 ${escapeHtml(item.finished_at)}` : '';
                const url = item.url
                    ? `<a class="history-link" href="${escapeHtml(item.url)}" target="_blank" rel="noopener noreferrer">발행 글 열기</a>`
                    : '';
                return `
                    <div class="history-item">
                        <div class="history-title">${title}</div>
                        <div class="history-meta">
                            <span class="history-status ${escapeHtml(item.status || 'queued')}">${statusLabel(item.status)}</span>
                            <span>#${escapeHtml(item.id || '')}</span>
                            <span>${created}</span>
                            <span>${finished}</span>
                        </div>
                        ${preview ? `<div class="history-preview">${preview}</div>` : ''}
                        ${url}
                    </div>
                `;
            }).join('');
        } catch (e) {
            oneoffHistoryList.innerHTML = '<div class="history-empty">단발 발행 이력을 불러오지 못했습니다.</div>';
        }
    }

    async function runOneoff() {
        const topic = document.getElementById('oneoff-topic').value.trim();
        const prompt = document.getElementById('oneoff-prompt').value.trim();
        const persona = document.getElementById('oneoff-persona').value;
        const publishMode = document.getElementById('oneoff-publish-mode').value;
        if (!prompt) {
            alert('프롬프트, 자료, 링크 또는 조사 내용을 입력하세요.');
            return;
        }

        runOneoffButton.disabled = true;
        runOneoffButton.textContent = '큐 등록 중...';
        try {
            const res = await fetch('/api/oneoff/run', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    topic,
                    prompt,
                    persona,
                    publish_mode: publishMode
                })
            });
            if (!res.ok) {
                const text = await res.text();
                alert(`단발 발행 요청 실패: ${text}`);
                return;
            }
            runOneoffButton.textContent = '큐 등록됨';
            await loadOneoffHistory();
            fetchLogs();
            fetchQueueStatus();
        } catch (e) {
            alert(`서버 에러: ${e.message}`);
        } finally {
            setTimeout(() => {
                runOneoffButton.disabled = false;
                runOneoffButton.textContent = '마스터피스 단발 발행';
            }, 1500);
        }
    }

    if (runOneoffButton) runOneoffButton.addEventListener('click', runOneoff);
    const refreshOneoff = document.getElementById('refresh-oneoff-history');
    if (refreshOneoff) refreshOneoff.addEventListener('click', loadOneoffHistory);

    // LOGS
    const logViewer = document.getElementById('log-viewer');
    const queueStatus = document.getElementById('queue-status');
    let lastLogContent = "";
    const MAX_VISIBLE_LOG_LINES = 300;

    function escapeHtml(value) {
        return value
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function linkifyLogLine(line) {
        const escaped = escapeHtml(line);
        return escaped.replace(/(https?:\/\/[^\s<]+)/g, (url) => {
            const cleanUrl = url.replace(/[),.;]+$/, '');
            const suffix = url.slice(cleanUrl.length);
            return `<a href="${cleanUrl}" target="_blank" rel="noopener noreferrer" class="log-link">${cleanUrl}</a>${suffix}`;
        });
    }
    
    async function fetchLogs() {
        if(!document.getElementById('logs').classList.contains('active')) return;
        try {
            const res = await fetch('/api/logs');
            const text = await res.text();
            
            if (text === lastLogContent) return; // Prevent unnecessary DOM updates
            lastLogContent = text;
            
            const lines = text.split('\n').filter(line => line.trim());
            const visibleLines = lines.slice(-MAX_VISIBLE_LOG_LINES);
            const hiddenCount = Math.max(0, lines.length - visibleLines.length);
            const hiddenNotice = hiddenCount
                ? `<div class="log-entry muted">이전 로그 ${hiddenCount}줄은 화면 속도를 위해 접었습니다. 최신 ${MAX_VISIBLE_LOG_LINES}줄만 표시합니다.</div>`
                : '';
            const html = visibleLines
                .filter(line => line.trim())
                .map(line => {
                    let className = 'log-entry';
                    if(line.includes('Success') || line.includes('✅') || line.includes('=== Pipeline')) className += ' success';
                    else if(line.includes('Error') || line.includes('❌') || line.includes('Fail')) className += ' error';
                    return `<div class="${className}">${linkifyLogLine(line)}</div>`;
                })
                .join('');
            logViewer.innerHTML = hiddenNotice + (html || '<div class="log-entry muted">로그가 없습니다.</div>');
            logViewer.scrollTop = logViewer.scrollHeight;
        } catch(e) { console.error(e); }
    }

    async function fetchQueueStatus() {
        if(!document.getElementById('logs').classList.contains('active')) return;
        try {
            const res = await fetch('/api/queue');
            const data = await res.json();
            const running = data.running
                ? `<div class="queue-item running">실행 중: ${escapeHtml(data.running.topic || data.running.pipeline_id)} <span>#${data.running.run_id}</span></div>`
                : '<div class="queue-item idle">현재 실행 중인 작업 없음</div>';
            const queued = data.queued.length
                ? data.queued.map(item => `<div class="queue-item queued">대기 중: ${escapeHtml(item.topic || item.pipeline_id)} <span>#${item.run_id}</span></div>`).join('')
                : '<div class="queue-muted">대기열 없음</div>';
            queueStatus.innerHTML = `${running}<div class="queue-list">${queued}</div>`;
        } catch(e) {
            queueStatus.innerHTML = '<div class="queue-muted">큐 상태를 불러오지 못했습니다.</div>';
        }
    }
    
    document.getElementById('clear-logs').addEventListener('click', async () => {
        try {
            await fetch('/api/logs/clear', {method: 'POST'});
            logViewer.innerHTML = '<div style="color:var(--text-muted);">로그가 완전히 삭제되었습니다. 새로운 작업을 시작하면 기록됩니다.</div>';
            lastLogContent = "";
        } catch(e) {}
    });

    setInterval(fetchLogs, 3000);
    setInterval(fetchQueueStatus, 3000);
    loadPipelines(true);
});

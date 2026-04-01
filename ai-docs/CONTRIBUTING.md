# ai-docs Contributing Guide

이 문서는 ai-docs 디렉토리의 문서를 업데이트할 때 따라야 할 가이드라인입니다.

---

## 📋 원칙

1. **코드와 문서는 항상 동기화**: 코드 변경 시 문서도 반드시 업데이트
2. **실제 코드와 일치**: 문서는 실제 구현을 그대로 반영해야 함 (추측 NO)
3. **누락 방지**: 새로운 함수/메서드/기능 추가 시 문서에도 추가
4. **오류 즉시 수정**: 잘못된 정보 발견 시 즉시 수정
5. **README도 업데이트**: 메인 README.md와 ai-docs 양쪽 모두 최신 상태 유지

---

## 🔍 문서 업데이트 시 확인사항

### 코드 변경 시 반드시 확인할 것들:

| 코드 변경 유형 | 업데이트할 문서 |
|---------------|----------------|
| 새로운 에이전트 추가 | `AGENTS.md`, `README.md` |
| 에이전트 instructions 변경 | `AGENTS.md` |
| 새로운 provider 추가 | `CONFIG.md`, `AGENTS.md`, `README.md` |
| 새로운 도구/함수 추가 | `TOOLS.md` |
| 새로운 skill 관련 | `SKILLS.md` |
| 새로운 API 엔드포인트 | `API.md` |
| 새 파일/디렉토리 생성 | `DEVELOPMENT.md` (프로젝트 구조 변경 시) |
| 디자인/스타일 변경 | `CHATOUTO_STYLE.md` |

---

## 📝 체크리스트 (문서 업데이트 전)

코드 변경 후 문서 업데이트 시:

- [ ] `outo/agents.py` 변경 → `AGENTS.md` 확인
- [ ] `outo/providers.py` 변경 → `CONFIG.md` 확인  
- [ ] `outo/skills.py` 변경 → `SKILLS.md` 확인
- [ ] `outo/tools.py` 변경 → `TOOLS.md` 확인
- [ ] `run.py` 변경 → `API.md`, `DEVELOPMENT.md` 확인
- [ ] `outo/server/discord_bot.py` 변경 → `CONFIG.md`, `API.md` 확인
- [ ] provider/agent 수 변경 → `README.md` 확인
- [ ] 새로운 파일 생성 → `DEVELOPMENT.md` 구조 업데이트
- [ ] 문서 내 provider 수, agent 수 등이 정확한지 확인

---

## 🔄 코드 → 문서 매핑

### 핵심 코드 파일들:

```
outo/
├── agents.py     → AGENTS.md (에이전트 정의, temperature, instructions)
├── providers.py  → CONFIG.md (provider 설정, 모델 목록)
├── skills.py    → SKILLS.md (스킬 관리 메서드)
└── tools.py     → TOOLS.md (기본 도구 정의)

run.py           → API.md (API 엔드포인트)
                 → DEVELOPMENT.md (프로젝트 구조)

outo/server/discord_bot.py → CONFIG.md (Discord 설정)
                           → API.md (Discord API 엔드포인트)
```

### 확인해야 할 주요 사항:

1. **AGENTS.md**
   - 에이전트 수와 이름이 정확한지
   - temperature 값이 정확한지
   - instructions가 코드와 일치하는지 (특히 skill_info 포함 여부)
   - provider priority 순서가 정확한지

2. **CONFIG.md**
   - provider 수가 8개인지
   - 모델 목록이 정확한지
   - base_url이 정확한지

3. **SKILLS.md**
   - 모든 메서드가 문서화되어 있는지
   - AGENT_SKILL_PATHS가 정확한지

4. **TOOLS.md**
   - DEFAULT_TOOLS와 일치하는지

5. **API.md**
   - 엔드포인트가 최신인지
   - 응답 형식이 정확한지

6. **README.md**
   - 프로바이더 목록이 정확한지
   - 에이전트 목록이 정확한지

---

## ⚠️ 자주 하는 실수 방지

1. **INSTALL.md 참조**: `PHILOSOPHY.md` 등에서 INSTALL.md를 참조하지만 실제 파일은 없음 → 참조 제거 또는 삭제

2. **provider 수 오류**: 문서에 "15 providers"这样的话 → 실제는 8개 provider

3. **메서드 누락**: 코드에 있는데 문서에 없는 메서드 → `SKILLS.md`에서 자주 발생

4. **instructions 불일치**: 에이전트 instructions가 코드는 물론 문서와도 다름

---

## 📦 새로운 기능 추가 시

1. 코드 구현
2. 관련 문서 파일 업데이트
3. `DEVELOPMENT.md`의 "Recent Changes" 섹션에 날짜와 함께 변경사항 추가
4. README.md도 업데이트가 필요하면 함께 수정

---

## 🧪 검증

문서 업데이트 후:

1. 실제 코드와 비교하여 정보 일치 확인
2. 링크가失效하지 않았는지 확인
3. 문법/포맷 일관성 확인

---

이 가이드라인을 따라 ai-docs를 최신 상태로 유지해주세요.

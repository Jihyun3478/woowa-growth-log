# obsidian-growth-log

우테코 레벨2 성장 기록 자동화 시스템

## 구조

```
.github/
├── prompts/
│   ├── growth-report-style.md   # 리포트 말투/규칙
│   ├── morning.md               # 아침 리포트 프롬프트
│   ├── evening.md               # 저녁 리포트 프롬프트
│   └── weekly.md                # 주간 리포트 프롬프트
├── scripts/
│   ├── generate_report.py       # Claude API로 리포트 생성
│   └── update_learning_backlog.py  # NVIDIA NIM으로 백로그 업데이트
└── workflows/
    ├── morning-report.yml       # 매일 오전 10시 (KST)
    ├── evening-report.yml       # 매일 오후 6시 (KST)
    └── weekly-report.yml        # 매주 일요일 오후 11시 (KST)
00_daily/                        # 데일리 회고 (직접 작성)
reports/
├── morning/                     # 아침 리포트 (자동 생성)
├── evening/                     # 저녁 리포트 (자동 생성)
└── weekly/                      # 주간 리포트 (자동 생성)
09_learning_backlog/             # 학습 백로그 (자동 업데이트)
```

## 설정

### 1. GitHub Secrets 등록

레포 Settings → Secrets and variables → Actions에서 아래 두 개 등록:

| Secret | 설명 |
|--------|------|
| `ANTHROPIC_API_KEY` | Claude API 키 |
| `NIM_API_KEY` | NVIDIA NIM API 키 |

### 2. 데일리 회고 작성

매일 `00_daily/YYYY-MM-DD.md` 파일을 작성하고 push하면 됨.
`YYYY-MM-DD.md`를 템플릿으로 복사해서 사용.

### 3. 자동 실행 확인

- 오전 10시: `morning-report.yml` 실행 → `reports/morning/` 에 리포트 생성
- 오후 6시: `evening-report.yml` 실행 → `reports/evening/` 에 리포트 생성
- 일요일 오후 11시: `weekly-report.yml` 실행 → `reports/weekly/` 에 리포트 생성

### 4. 수동 실행

GitHub Actions 탭 → 워크플로우 선택 → Run workflow

## 학습법 v3 연동

데일리 회고의 "6. 백로그" 항목에 물음표(?)를 남기면
저녁 리포트 실행 시 학습 백로그에 자동 반영됨.

```
## 6. 백로그 (물음표 + 맥락)
- [ ] JdbcTemplate PreparedStatement 인덱스: 왜 1부터 시작하는지 모름
```

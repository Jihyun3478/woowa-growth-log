#!/usr/bin/env python3
"""Generate morning/evening/weekly growth reports using NVIDIA NIM API."""

from __future__ import annotations

import json
import os
import sys
import urllib.request
import urllib.error
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")
ROOT = Path.cwd()

DAILY_DIR = Path("00_daily")
REPORT_DIR = Path("reports")
BACKLOG_FILE = Path("09_learning_backlog/learning-backlog.md")
SKILL_GOAL_DIR = Path("01_Project")

PROMPTS_DIR = Path(".github/prompts")
STYLE_FILE = PROMPTS_DIR / "growth-report-style.md"

NIM_API_KEY = os.environ.get("NIM_API_KEY", "").strip()
NIM_API_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
NIM_MODEL = "z-ai/glm-5.1"


def report_date() -> date:
    raw = os.environ.get("REPORT_DATE", "").strip()
    if raw:
        return date.fromisoformat(raw)
    return datetime.now(KST).date()


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def read_daily_note(target_date: date) -> str:
    path = ROOT / DAILY_DIR / f"{target_date.isoformat()}.md"
    return read_text(path)


def read_recent_notes(today: date, days: int = 7) -> str:
    notes = []
    for i in range(days):
        d = today - timedelta(days=i)
        content = read_daily_note(d)
        if content:
            notes.append(f"## {d.isoformat()}\n\n{content}")
    return "\n\n---\n\n".join(notes)


def read_backlog() -> str:
    return read_text(ROOT / BACKLOG_FILE)


def read_style() -> str:
    return read_text(ROOT / STYLE_FILE)


def read_prompt(mode: str) -> str:
    return read_text(ROOT / PROMPTS_DIR / f"{mode}.md")


def find_skill_goals() -> str:
    results = []
    for goal_file in sorted((ROOT / SKILL_GOAL_DIR).rglob("*스킬 목표.md")):
        content = read_text(goal_file)
        if content:
            results.append(f"### {goal_file.stem}\n\n{content}")
    return "\n\n".join(results)


def build_morning_prompt(today: date) -> str:
    yesterday = today - timedelta(days=1)
    yesterday_note = read_daily_note(yesterday)
    if not yesterday_note:
        yesterday_note = read_daily_note(today)

    style = read_style()
    prompt_template = read_prompt("morning")
    backlog = read_backlog()
    goals = find_skill_goals()

    return f"""다음 규칙과 프롬프트 지시에 따라 오늘의 아침 성장 리마인드 리포트를 생성해줘.

## 말투/문장 규칙
{style}

## 프롬프트 지시
{prompt_template}

## 어제 데일리 회고
{yesterday_note if yesterday_note else "기록 없음"}

## 현재 학습 백로그
{backlog if backlog else "기록 없음"}

## 하드스킬/소프트스킬 목표
{goals if goals else "기록 없음"}

오늘 날짜: {today.isoformat()}
"""


def build_evening_prompt(today: date) -> str:
    today_note = read_daily_note(today)
    style = read_style()
    prompt_template = read_prompt("evening")
    backlog = read_backlog()
    goals = find_skill_goals()

    return f"""다음 규칙과 프롬프트 지시에 따라 오늘의 저녁 성장 피드백 리포트를 생성해줘.

## 말투/문장 규칙
{style}

## 프롬프트 지시
{prompt_template}

## 오늘 데일리 회고
{today_note if today_note else "오늘 데일리 회고가 아직 없습니다. 최근 기록을 기반으로 생성합니다."}

## 현재 학습 백로그
{backlog if backlog else "기록 없음"}

## 하드스킬/소프트스킬 목표
{goals if goals else "기록 없음"}

오늘 날짜: {today.isoformat()}
"""


def build_weekly_prompt(today: date) -> str:
    recent_notes = read_recent_notes(today, days=7)
    style = read_style()
    prompt_template = read_prompt("weekly")
    backlog = read_backlog()
    goals = find_skill_goals()

    iso_year, iso_week, _ = today.isocalendar()

    return f"""다음 규칙과 프롬프트 지시에 따라 주간 성장 리포트를 생성해줘.

## 말투/문장 규칙
{style}

## 프롬프트 지시
{prompt_template}

## 최근 7일 데일리 회고
{recent_notes if recent_notes else "기록 없음"}

## 현재 학습 백로그
{backlog if backlog else "기록 없음"}

## 하드스킬/소프트스킬 목표
{goals if goals else "기록 없음"}

오늘 날짜: {today.isoformat()}
주차: {iso_year}년 {iso_week}주차
"""


def call_nim(prompt: str) -> str:
    if not NIM_API_KEY:
        raise ValueError("NIM_API_KEY is not set")

    payload = {
        "model": NIM_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "당신은 우테코 크루의 성장을 돕는 코치입니다. 데일리 회고를 바탕으로 성장 리포트를 작성합니다.",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 3000,
        "stream": False,
    }

    request = urllib.request.Request(
        NIM_API_URL,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {NIM_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=120) as response:
        data = json.loads(response.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"]


def save_report(content: str, mode: str, today: date) -> Path:
    if mode == "weekly":
        iso_year, iso_week, _ = today.isocalendar()
        filename = f"{iso_year}-W{iso_week:02d}.md"
    else:
        filename = f"{today.isoformat()}-{mode}.md"

    output_dir = ROOT / REPORT_DIR / mode
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename

    frontmatter = f"""---
created: {datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")} KST
report_date: {today.isoformat()}
mode: {mode}
tags:
  - growth/feedback
  - growth/{mode}
---

"""
    output_path.write_text(frontmatter + content, encoding="utf-8")
    print(f"Report saved: {output_path}")
    return output_path


def write_github_env(key: str, value: str) -> None:
    env_path = os.environ.get("GITHUB_ENV")
    if not env_path:
        return
    with Path(env_path).open("a", encoding="utf-8") as f:
        f.write(f"{key}={value}\n")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python generate_report.py <morning|evening|weekly>")
        sys.exit(1)

    mode = sys.argv[1].lower()
    if mode not in ("morning", "evening", "weekly"):
        print(f"Unknown mode: {mode}. Use morning, evening, or weekly.")
        sys.exit(1)

    today = report_date()
    print(f"Generating {mode} report for {today.isoformat()}...")

    if mode == "morning":
        prompt = build_morning_prompt(today)
    elif mode == "evening":
        prompt = build_evening_prompt(today)
    else:
        prompt = build_weekly_prompt(today)

    try:
        content = call_nim(prompt)
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        print(f"API call failed: {e}")
        sys.exit(1)

    output_path = save_report(content, mode, today)
    write_github_env("REPORT_FILE", output_path.as_posix())
    write_github_env("REPORT_MODE", mode)
    write_github_env("REPORT_DATE", today.isoformat())

    print(f"Done: {output_path}")


if __name__ == "__main__":
    main()
    

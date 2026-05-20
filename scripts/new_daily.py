#!/usr/bin/env python3
import argparse
import csv
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
import re
from typing import Optional


ROOT = Path(__file__).resolve().parents[1]
TOPICS_PATH = ROOT / "topics" / "topics.csv"
TEMPLATE_PATH = ROOT / "templates" / "daily.md"
DAILY_DIR = ROOT / "daily"


@dataclass(frozen=True)
class Topic:
    category: str
    topic: str
    question: str
    keywords: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a daily liberal arts input note.")
    parser.add_argument("--date", default=date.today().isoformat(), help="YYYY-MM-DD. Defaults to today.")
    parser.add_argument("--topic", help="Topic title. If omitted, one topic is selected from topics/topics.csv.")
    return parser.parse_args()


def parse_date(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise SystemExit("--date must be YYYY-MM-DD") from exc


def load_topics() -> list[Topic]:
    with TOPICS_PATH.open(encoding="utf-8", newline="") as f:
        rows = csv.DictReader(f)
        return [
            Topic(
                category=row["category"].strip(),
                topic=row["topic"].strip(),
                question=row["question"].strip(),
                keywords=row["keywords"].strip(),
            )
            for row in rows
        ]


def select_topic(target_date: date, topics: list[Topic], requested_topic: Optional[str]) -> Topic:
    if requested_topic:
        for topic in topics:
            if topic.topic == requested_topic:
                return topic
        return Topic(
            category="未分類",
            topic=requested_topic,
            question=f"{requested_topic}について、何を理解すると世界の見方が広がるか？",
            keywords="",
        )

    if not topics:
        raise SystemExit(f"No topics found: {TOPICS_PATH}")

    start = date(target_date.year, 1, 1)
    index = (target_date - start).days % len(topics)
    return topics[index]


def safe_filename_part(value: str) -> str:
    cleaned = re.sub(r'[\\/:*?"<>|]', "", value).strip()
    cleaned = re.sub(r"\s+", "_", cleaned)
    return cleaned[:40] or "untitled"


def next_available_path(target_date: date, topic: Topic) -> Path:
    base = f"{target_date.isoformat()}_{safe_filename_part(topic.topic)}"
    candidate = DAILY_DIR / f"{base}.md"
    if not candidate.exists():
        return candidate

    version = 2
    while True:
        candidate = DAILY_DIR / f"{base}_v{version}.md"
        if not candidate.exists():
            return candidate
        version += 1


def render_template(target_date: date, topic: Topic) -> str:
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    return (
        template.replace("{{date}}", target_date.isoformat())
        .replace("{{category}}", topic.category)
        .replace("{{topic}}", topic.topic)
        .replace("{{question}}", topic.question)
        .replace("{{keywords}}", topic.keywords)
    )


def main() -> None:
    args = parse_args()
    target_date = parse_date(args.date)
    topics = load_topics()
    topic = select_topic(target_date, topics, args.topic)
    DAILY_DIR.mkdir(exist_ok=True)

    path = next_available_path(target_date, topic)
    path.write_text(render_template(target_date, topic), encoding="utf-8")
    print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()

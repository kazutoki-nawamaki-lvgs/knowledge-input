#!/usr/bin/env python3
import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Optional


ROOT = Path(__file__).resolve().parents[1]
TOPICS_PATH = ROOT / "topics" / "saas_topics.csv"
TEMPLATE_PATH = ROOT / "templates" / "saas.md"
SAAS_DIR = ROOT / "saas"


@dataclass(frozen=True)
class Topic:
    category: str
    topic: str
    question: str
    keywords: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a SaaS product-development reading note.")
    parser.add_argument("--topic", help="Topic title. If omitted, one topic is selected from topics/saas_topics.csv.")
    return parser.parse_args()


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


def select_topic(number: int, topics: list[Topic], requested_topic: Optional[str]) -> Topic:
    if requested_topic:
        for topic in topics:
            if topic.topic == requested_topic:
                return topic
        return Topic(
            category="未分類",
            topic=requested_topic,
            question=f"{requested_topic}について、SaaS開発者として何を理解するとプロダクトの見方が変わるか？",
            keywords="",
        )

    if not topics:
        raise SystemExit(f"No topics found: {TOPICS_PATH}")

    index = (number - 1) % len(topics)
    return topics[index]


def safe_filename_part(value: str) -> str:
    cleaned = re.sub(r'[\\/:*?"<>|]', "", value).strip()
    cleaned = re.sub(r"\s+", "_", cleaned)
    return cleaned[:40] or "untitled"


def existing_numbers() -> list[int]:
    numbers = []
    if not SAAS_DIR.exists():
        return numbers

    for path in SAAS_DIR.glob("*.md"):
        match = re.match(r"^(\d{3})_", path.name)
        if match:
            numbers.append(int(match.group(1)))

    return numbers


def next_number() -> int:
    numbers = existing_numbers()
    return max(numbers, default=0) + 1


def next_available_path(number: int, topic: Topic) -> Path:
    base = f"{number:03d}_{safe_filename_part(topic.topic)}"
    candidate = SAAS_DIR / f"{base}.md"
    if not candidate.exists():
        return candidate

    version = 2
    while True:
        candidate = SAAS_DIR / f"{base}_v{version}.md"
        if not candidate.exists():
            return candidate
        version += 1


def render_template(number: int, topic: Topic) -> str:
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    return (
        template.replace("{{number}}", f"{number:03d}")
        .replace("{{category}}", topic.category)
        .replace("{{topic}}", topic.topic)
        .replace("{{question}}", topic.question)
        .replace("{{keywords}}", topic.keywords)
    )


def main() -> None:
    args = parse_args()
    topics = load_topics()
    SAAS_DIR.mkdir(exist_ok=True)
    number = next_number()
    topic = select_topic(number, topics, args.topic)

    path = next_available_path(number, topic)
    path.write_text(render_template(number, topic), encoding="utf-8")
    print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()

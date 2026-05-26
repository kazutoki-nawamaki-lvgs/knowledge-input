#!/usr/bin/env python3
import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Optional


ROOT = Path(__file__).resolve().parents[1]
TOPICS_PATH = ROOT / "topics" / "topics.csv"
TEMPLATE_PATH = ROOT / "templates" / "daily.md"
LIBERAL_ARTS_DIR = ROOT / "liberal-arts"


@dataclass(frozen=True)
class Topic:
    category: str
    topic: str
    question: str
    keywords: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a liberal arts input note.")
    parser.add_argument("--topic", help="Topic title. If omitted, one topic is selected from topics/topics.csv.")
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


def select_topic(topics: list[Topic], requested_topic: Optional[str]) -> Topic:
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

    for topic in topics:
        if not topic_note_exists(topic):
            return topic

    index = existing_note_count() % len(topics)
    return topics[index]


def safe_filename_part(value: str) -> str:
    cleaned = re.sub(r'[\\/:*?"<>|]', "", value).strip()
    cleaned = re.sub(r"\s+", "_", cleaned)
    return cleaned[:40] or "untitled"


def category_dir(topic: Topic) -> Path:
    return LIBERAL_ARTS_DIR / safe_filename_part(topic.category)


def topic_note_exists(topic: Topic) -> bool:
    directory = category_dir(topic)
    if not directory.exists():
        return False

    filename_part = safe_filename_part(topic.topic)
    return any(path.name[4:].removesuffix(".md").split("_v", 1)[0] == filename_part for path in directory.glob("*.md"))


def existing_numbers(directory: Path) -> list[int]:
    numbers = []
    if not directory.exists():
        return numbers

    for path in directory.glob("*.md"):
        match = re.match(r"^(\d{3})_", path.name)
        if match:
            numbers.append(int(match.group(1)))

    return numbers


def next_number(directory: Path) -> int:
    numbers = existing_numbers(directory)
    return max(numbers, default=0) + 1


def existing_note_count() -> int:
    if not LIBERAL_ARTS_DIR.exists():
        return 0
    return sum(1 for path in LIBERAL_ARTS_DIR.rglob("*.md") if path.is_file())


def next_available_path(directory: Path, number: int, topic: Topic) -> Path:
    base = f"{number:03d}_{safe_filename_part(topic.topic)}"
    candidate = directory / f"{base}.md"
    if not candidate.exists():
        return candidate

    version = 2
    while True:
        candidate = directory / f"{base}_v{version}.md"
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
    LIBERAL_ARTS_DIR.mkdir(exist_ok=True)
    topic = select_topic(topics, args.topic)
    directory = category_dir(topic)
    directory.mkdir(parents=True, exist_ok=True)
    number = next_number(directory)

    path = next_available_path(directory, number, topic)
    path.write_text(render_template(number, topic), encoding="utf-8")
    print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()

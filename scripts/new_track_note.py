#!/usr/bin/env python3
import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Optional


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = ROOT / "templates" / "practical.md"


@dataclass(frozen=True)
class Topic:
    category: str
    topic: str
    question: str
    keywords: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a practical learning note for a topic track.")
    parser.add_argument("--track-dir", required=True, help="Output directory name, such as design-system.")
    parser.add_argument("--topics", required=True, help="Topic CSV path relative to the repository root.")
    parser.add_argument("--topic", help="Topic title. If omitted, the first unused CSV topic is selected.")
    parser.add_argument(
        "--fallback-question",
        default="{topic}について、実務で何を判断できるようになるべきか？",
        help="Question template used when --topic is not found in the CSV.",
    )
    return parser.parse_args()


def load_topics(path: Path) -> list[Topic]:
    with path.open(encoding="utf-8", newline="") as f:
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


def safe_filename_part(value: str) -> str:
    cleaned = re.sub(r'[\\/:*?"<>|]', "", value).strip()
    cleaned = re.sub(r"\s+", "_", cleaned)
    return cleaned[:40] or "untitled"


def topic_note_exists(track_dir: Path, topic: Topic) -> bool:
    if not track_dir.exists():
        return False

    filename_part = safe_filename_part(topic.topic)
    for path in track_dir.glob("*.md"):
        if path.name == "README.md":
            continue
        current = path.name[4:].removesuffix(".md").split("_v", 1)[0]
        if current == filename_part:
            return True
    return False


def existing_numbers(track_dir: Path) -> list[int]:
    numbers = []
    if not track_dir.exists():
        return numbers

    for path in track_dir.glob("*.md"):
        match = re.match(r"^(\d{3})_", path.name)
        if match:
            numbers.append(int(match.group(1)))

    return numbers


def next_number(track_dir: Path) -> int:
    return max(existing_numbers(track_dir), default=0) + 1


def select_topic(
    topics: list[Topic],
    requested_topic: Optional[str],
    track_dir: Path,
    fallback_question: str,
) -> Topic:
    if requested_topic:
        for topic in topics:
            if topic.topic == requested_topic:
                return topic
        return Topic(
            category="未分類",
            topic=requested_topic,
            question=fallback_question.format(topic=requested_topic),
            keywords="",
        )

    if not topics:
        raise SystemExit("No topics found.")

    for topic in topics:
        if not topic_note_exists(track_dir, topic):
            return topic

    index = len(existing_numbers(track_dir)) % len(topics)
    return topics[index]


def next_available_path(track_dir: Path, number: int, topic: Topic) -> Path:
    base = f"{number:03d}_{safe_filename_part(topic.topic)}"
    candidate = track_dir / f"{base}.md"
    if not candidate.exists():
        return candidate

    version = 2
    while True:
        candidate = track_dir / f"{base}_v{version}.md"
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
    topics_path = ROOT / args.topics
    track_dir = ROOT / args.track_dir
    topics = load_topics(topics_path)
    topic = select_topic(topics, args.topic, track_dir, args.fallback_question)

    track_dir.mkdir(exist_ok=True)
    number = next_number(track_dir)
    path = next_available_path(track_dir, number, topic)
    path.write_text(render_template(number, topic), encoding="utf-8")
    print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()

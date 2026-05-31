import argparse
import os
import re
from pathlib import Path


DEFAULT_SENTENCE_BREAKS = 1
DEFAULT_PARAGRAPH_BREAKS = 2
DEFAULT_SECTION_BREAKS = 4


def load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def add_text_preprocessing_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Send the input text as-is instead of cleaning Markdown.",
    )
    parser.add_argument(
        "--sentence-breaks",
        type=int,
        default=DEFAULT_SENTENCE_BREAKS,
        help=f"Newlines to insert after sentence-ending punctuation. Default: {DEFAULT_SENTENCE_BREAKS}",
    )
    parser.add_argument(
        "--paragraph-breaks",
        type=int,
        default=DEFAULT_PARAGRAPH_BREAKS,
        help=f"Newlines to keep between paragraphs. Default: {DEFAULT_PARAGRAPH_BREAKS}",
    )
    parser.add_argument(
        "--section-breaks",
        type=int,
        default=DEFAULT_SECTION_BREAKS,
        help=f"Newlines to place around Markdown headings. Default: {DEFAULT_SECTION_BREAKS}",
    )


def clamp_breaks(count: int, minimum: int = 0, maximum: int = 8) -> int:
    return max(minimum, min(count, maximum))


def ensure_sentence_end(text: str) -> str:
    text = text.strip()
    if not text or re.search(r"[。！？.!?]$", text):
        return text
    return f"{text}。"


def clean_markdown(text: str, section_breaks: int = DEFAULT_SECTION_BREAKS) -> str:
    section_gap = "\n" * clamp_breaks(section_breaks)
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    text = re.sub(r"^No\.\s*\d+\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^カテゴリ:\s*.*$", "", text, flags=re.MULTILINE)

    def replace_heading(match: re.Match[str]) -> str:
        heading = ensure_sentence_end(match.group(1))
        return f"{section_gap}{heading}{section_gap}"

    text = re.sub(r"^#{1,6}\s+(.+?)\s*$", replace_heading, text, flags=re.MULTILINE)
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = text.replace("**", "").replace("__", "").replace("`", "")
    return text.strip()


def add_reading_pauses(text: str, sentence_breaks: int, paragraph_breaks: int) -> str:
    sentence_gap = "\n" * clamp_breaks(sentence_breaks)
    paragraph_gap = "\n" * clamp_breaks(paragraph_breaks, minimum=1)

    lines = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            lines.append("")
            continue
        line = re.sub(r"([。！？!?])\s*", rf"\1{sentence_gap}", line)
        lines.append(line.strip())

    text = "\n".join(lines)
    text = re.sub(r"\n{2,}", paragraph_gap, text)
    return text.strip()


def prepare_input_text(input_path: Path, args: argparse.Namespace) -> str:
    text = input_path.read_text(encoding="utf-8").strip()
    if input_path.suffix == ".md" and not args.raw:
        text = clean_markdown(text, args.section_breaks)
    if not args.raw:
        text = add_reading_pauses(text, args.sentence_breaks, args.paragraph_breaks)
    return text


def split_text(text: str, max_chars: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]

    chunks = []
    current = ""
    paragraphs = [paragraph.strip() for paragraph in text.split("\n\n") if paragraph.strip()]
    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            chunks.append(current)
        if len(paragraph) <= max_chars:
            current = paragraph
            continue

        sentences = re.split(r"(?<=[。！？])", paragraph)
        current = ""
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            candidate = f"{current}{sentence}" if current else sentence
            if len(candidate) <= max_chars:
                current = candidate
            else:
                if current:
                    chunks.append(current)
                current = sentence
    if current:
        chunks.append(current)
    return chunks

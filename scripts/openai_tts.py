#!/usr/bin/env python3
import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

from tts_common import add_text_preprocessing_args, load_env_file, prepare_input_text, split_text


DEFAULT_MODEL = "tts-1"
DEFAULT_VOICE = "alloy"
DEFAULT_FORMAT = "mp3"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert one text file to spoken audio using OpenAI TTS."
    )
    parser.add_argument("input", help="Text file to convert.")
    parser.add_argument(
        "-o",
        "--output",
        default=f"speech.{DEFAULT_FORMAT}",
        help=f"Output audio path. Default: speech.{DEFAULT_FORMAT}",
    )
    parser.add_argument(
        "--voice",
        default=DEFAULT_VOICE,
        help=f"Voice name. Default: {DEFAULT_VOICE}",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"TTS model. Default: {DEFAULT_MODEL}",
    )
    parser.add_argument(
        "--format",
        default=DEFAULT_FORMAT,
        choices=["mp3", "opus", "aac", "flac", "wav", "pcm"],
        help=f"Audio format. Default: {DEFAULT_FORMAT}",
    )
    parser.add_argument(
        "--instructions",
        default="落ち着いた自然な日本語で、聞き取りやすい速度で読み上げてください。",
        help="Style instructions for the voice.",
    )
    add_text_preprocessing_args(parser)
    parser.add_argument(
        "--max-chars",
        type=int,
        default=None,
        help="Maximum characters per API request. Defaults to a conservative value for GPT TTS.",
    )
    return parser.parse_args()


def build_request(api_key: str, text: str, args: argparse.Namespace) -> urllib.request.Request:
    payload = {
        "model": args.model,
        "voice": args.voice,
        "input": text,
        "response_format": args.format,
    }
    if args.model.startswith("gpt-4o-mini-tts") and args.instructions:
        payload["instructions"] = args.instructions

    return urllib.request.Request(
        "https://api.openai.com/v1/audio/speech",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )


def create_speech(api_key: str, text: str, args: argparse.Namespace) -> bytes:
    request = build_request(api_key, text, args)
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.read()


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    load_env_file(repo_root / ".env")

    args = parse_args()
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY is missing. Put it in .env or export it in your shell.", file=sys.stderr)
        return 1

    input_path = Path(args.input)
    output_path = Path(args.output)
    text = prepare_input_text(input_path, args)
    if not text:
        print(f"{input_path} is empty.", file=sys.stderr)
        return 1

    max_chars = args.max_chars
    if max_chars is None:
        max_chars = 1600 if args.model.startswith("gpt-4o-mini-tts") else 12000
    chunks = split_text(text, max_chars)

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"".join(create_speech(api_key, chunk, args) for chunk in chunks))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        print(f"OpenAI API request failed: HTTP {error.code}\n{detail}", file=sys.stderr)
        return 1

    print(f"Wrote {output_path} from {len(chunks)} chunk(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
import argparse
import base64
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Optional

from tts_common import add_text_preprocessing_args, load_env_file, prepare_input_text, split_text


DEFAULT_VOICE = "ja-JP-Neural2-B"
DEFAULT_LANGUAGE = "ja-JP"
DEFAULT_FORMAT = "mp3"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert one text file to spoken audio using Google Cloud Text-to-Speech."
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
        help=f"Google voice name. Default: {DEFAULT_VOICE}",
    )
    parser.add_argument(
        "--language-code",
        default=DEFAULT_LANGUAGE,
        help=f"BCP-47 language code. Default: {DEFAULT_LANGUAGE}",
    )
    parser.add_argument(
        "--format",
        default=DEFAULT_FORMAT,
        choices=["mp3", "wav", "ogg"],
        help=f"Audio format. Default: {DEFAULT_FORMAT}",
    )
    parser.add_argument(
        "--speaking-rate",
        type=float,
        default=0.95,
        help="Speaking rate between 0.25 and 4.0. Default: 0.95",
    )
    parser.add_argument(
        "--pitch",
        type=float,
        default=0.0,
        help="Speaking pitch between -20.0 and 20.0. Default: 0.0",
    )
    add_text_preprocessing_args(parser)
    parser.add_argument(
        "--max-chars",
        type=int,
        default=1400,
        help="Maximum characters per API request. Default: 1400",
    )
    parser.add_argument(
        "--quota-project",
        default=os.environ.get("GOOGLE_CLOUD_QUOTA_PROJECT"),
        help="Google Cloud project to use for quota and billing when authenticating with ADC.",
    )
    return parser.parse_args()


def audio_encoding(output_format: str) -> str:
    return {
        "mp3": "MP3",
        "wav": "LINEAR16",
        "ogg": "OGG_OPUS",
    }[output_format]


def gcloud_access_token() -> Optional[str]:
    for command in (
        ["gcloud", "auth", "application-default", "print-access-token"],
        ["gcloud", "auth", "print-access-token"],
    ):
        try:
            result = subprocess.run(command, check=True, capture_output=True, text=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            continue
        token = result.stdout.strip()
        if token:
            return token
    return None


def build_request(text: str, args: argparse.Namespace) -> urllib.request.Request:
    payload = {
        "input": {"text": text},
        "voice": {
            "languageCode": args.language_code,
            "name": args.voice,
        },
        "audioConfig": {
            "audioEncoding": audio_encoding(args.format),
            "speakingRate": args.speaking_rate,
            "pitch": args.pitch,
        },
    }

    api_key = os.environ.get("GOOGLE_CLOUD_API_KEY")
    url = "https://texttospeech.googleapis.com/v1/text:synthesize"
    headers = {"Content-Type": "application/json"}
    if api_key:
        url = f"{url}?{urllib.parse.urlencode({'key': api_key})}"
    else:
        access_token = os.environ.get("GOOGLE_OAUTH_ACCESS_TOKEN") or gcloud_access_token()
        if not access_token:
            raise RuntimeError(
                "Google credentials are missing. Set GOOGLE_CLOUD_API_KEY, "
                "GOOGLE_OAUTH_ACCESS_TOKEN, or authenticate with gcloud."
            )
        headers["Authorization"] = f"Bearer {access_token}"
        if args.quota_project:
            headers["X-Goog-User-Project"] = args.quota_project

    return urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=headers,
        method="POST",
    )


def create_speech(text: str, args: argparse.Namespace) -> bytes:
    request = build_request(text, args)
    with urllib.request.urlopen(request, timeout=120) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return base64.b64decode(payload["audioContent"])


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    load_env_file(repo_root / ".env")

    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    text = prepare_input_text(input_path, args)
    if not text:
        print(f"{input_path} is empty.", file=sys.stderr)
        return 1

    chunks = split_text(text, args.max_chars)

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"".join(create_speech(chunk, args) for chunk in chunks))
    except RuntimeError as error:
        print(error, file=sys.stderr)
        return 1
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        print(f"Google TTS request failed: HTTP {error.code}\n{detail}", file=sys.stderr)
        return 1

    print(f"Wrote {output_path} from {len(chunks)} chunk(s) using {args.voice}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

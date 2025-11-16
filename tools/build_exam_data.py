#!/usr/bin/env python3
import argparse
import json
import re
import sys
from pathlib import Path
from typing import List, Optional


OPTION_PATTERN = re.compile(r"^([A-E])\.\s*(.*)")


def parse_question_block(block: str) -> Optional[dict]:
    lines = [line.rstrip() for line in block.strip().splitlines()]
    if not lines:
        return None

    stem_lines: List[str] = []
    options: List[str] = []
    explanation_lines: List[str] = []
    seen_letters = []
    stage = "stem"
    current_option_lines: List[str] = []

    def flush_option():
        nonlocal current_option_lines
        if current_option_lines:
            text = " ".join(part.strip() for part in current_option_lines if part.strip())
            options.append(text)
            current_option_lines = []

    for line in lines:
        stripped = line.strip()
        match = OPTION_PATTERN.match(stripped)

        if stage == "stem":
            if match and match.group(1) == "A":
                stage = "options"
                seen_letters.append("A")
                current_option_lines = [match.group(2)]
            else:
                stem_lines.append(line)
            continue

        if stage == "options":
            if match:
                letter = match.group(1)
                text = match.group(2)
                if letter in seen_letters:
                    flush_option()
                    explanation_lines.append(line)
                    stage = "explanation"
                else:
                    flush_option()
                    seen_letters.append(letter)
                    current_option_lines = [text]
            else:
                current_option_lines.append(line)
            continue

        explanation_lines.append(line)

    flush_option()

    if not stem_lines or not options:
        return None

    explanation_text = "\n".join(explanation_lines).strip()

    question = {
        "stem": "\n".join(stem_lines).strip(),
        "options": options,
        "correct_index": None,
        "explanation": explanation_text,
        "tags": [],
    }
    return question


def detect_correct_index(question: dict) -> Optional[int]:
    explanation = question.get("explanation") or ""
    for line in explanation.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        match = OPTION_PATTERN.match(stripped)
        if match:
            letter = match.group(1)
            idx = ord(letter) - ord("A")
            if 0 <= idx < len(question["options"]):
                return idx
        break
    return None


def parse_year(year: int, source_dir: Path, output_dir: Path, key_dir: Path):
    raw_path = source_dir / f"prep_{year}.txt"
    if not raw_path.exists():
        raise FileNotFoundError(f"Missing raw text file: {raw_path}")

    text = raw_path.read_text(encoding="utf-8")
    question_pattern = re.compile(r"(?mi)^Question:\s*\d+\s*$")
    matches = list(question_pattern.finditer(text))

    questions: List[dict] = []

    for idx, match in enumerate(matches):
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        block = text[start:end]
        question = parse_question_block(block)
        if question:
            detected = detect_correct_index(question)
            if detected is not None:
                question["correct_index"] = detected
            questions.append(question)

    if not questions:
        raise ValueError(f"No questions parsed for year {year}")

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"prep_{year}.json"
    output_path.write_text(json.dumps(questions, indent=2, ensure_ascii=False), encoding="utf-8")

    key_lines = []
    for idx, question in enumerate(questions, start=1):
        correct_index = question.get("correct_index")
        letter = "-" if correct_index is None else chr(ord("A") + correct_index)
        key_lines.append(f"{idx}. {letter}")

    key_dir.mkdir(parents=True, exist_ok=True)
    key_path = key_dir / f"prep_{year}_key.txt"
    key_path.write_text("\n".join(key_lines), encoding="utf-8")

    print(f"Processed {len(questions)} questions for {year}")


def main():
    parser = argparse.ArgumentParser(description="Parse PREP MCQ text dumps into JSON and answer keys.")
    parser.add_argument(
        "--years",
        nargs="*",
        type=int,
        default=[2015, 2016, 2017, 2019, 2022],
        help="Years to process (default: 2015 2016 2017 2019 2022)",
    )
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=Path("raw_txt"),
        help="Directory containing raw text files.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("questions"),
        help="Directory to store JSON outputs.",
    )
    parser.add_argument(
        "--key-dir",
        type=Path,
        default=Path("keys"),
        help="Directory to store answer key text files.",
    )
    args = parser.parse_args()

    for year in args.years:
        try:
            parse_year(year, args.source_dir, args.output_dir, args.key_dir)
        except Exception as exc:  # noqa: BLE001 - provide context and continue
            print(f"Failed to process {year}: {exc}", file=sys.stderr)


if __name__ == "__main__":
    main()

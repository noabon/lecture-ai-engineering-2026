"""第1回: 素のLLMに質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask --interactive

ツールは使わず、--interactive では同じチャットセッションで会話履歴を保つ。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse
import time

from google import genai
from google.genai import errors
from google.genai import types

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def ask(question: str, temperature: float | None = None) -> str:
    client = genai.Client(api_key=get_api_key())
    config = (
        types.GenerateContentConfig(temperature=temperature)
        if temperature is not None
        else None
    )
    response = client.models.generate_content(
        model=MODEL, contents=question, config=config
    )
    _print_usage(response)
    return response.text


def _print_usage(response: types.GenerateContentResponse) -> None:
    usage = response.usage_metadata
    if usage is None:
        print("[トークン数] 使用量情報を取得できませんでした")
    else:
        print(
            f"[トークン数] 入力: {usage.prompt_token_count}, "
            f"出力: {usage.candidates_token_count}"
        )


def ask_interactively(
    initial_question: str | None, temperature: float | None = None
) -> None:
    client = genai.Client(api_key=get_api_key())
    config = (
        types.GenerateContentConfig(temperature=temperature)
        if temperature is not None
        else None
    )
    chat = client.chats.create(model=MODEL, config=config)
    question = initial_question

    print("会話を開始します。終了するには「終了」または Ctrl-D を入力してください。")
    while True:
        if question is None:
            try:
                question = input("質問: ")
            except (EOFError, KeyboardInterrupt):
                print("\n会話を終了します。")
                return

        question = question.strip()
        if question.casefold() in {"終了", "exit", "quit"}:
            print("会話を終了します。")
            return
        if not question:
            question = None
            continue

        response = chat.send_message(question)
        print(f"\n回答: {response.text}")
        _print_usage(response)
        print()
        question = None


def compare_models_and_questions(
    models: list[str],
    questions: list[str],
    temperature: float | None = None,
) -> None:
    client = genai.Client(api_key=get_api_key())
    config = (
        types.GenerateContentConfig(temperature=temperature)
        if temperature is not None
        else None
    )
    total = len(models) * len(questions)
    print(f"実行回数: {total}（モデル数 × 質問数）。順番に実行します。")

    for model in models:
        for question_index, question in enumerate(questions, start=1):
            started_at = time.perf_counter()
            response = client.models.generate_content(
                model=model, contents=question, config=config
            )
            elapsed = time.perf_counter() - started_at

            usage = response.usage_metadata
            if usage is None:
                input_tokens = output_tokens = "不明"
            else:
                input_tokens = str(usage.prompt_token_count)
                output_tokens = str(usage.candidates_token_count)

            print(
                f"\n[モデル] {model} / [質問 {question_index}] {question}\n"
                f"[応答時間] {elapsed:.2f} 秒 / "
                f"[トークン数] 入力: {input_tokens}, 出力: {output_tokens}"
            )
            if response.text is None:
                print("[回答] 取得できませんでした")
            else:
                print(f"[回答]\n{response.text}")


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?")
    parser.add_argument(
        "--temperature",
        type=float,
        help="回答のランダムさを調整する値（例: 0.2）",
    )
    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="会話履歴を保ちながら続けて質問する",
    )
    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="複数のモデルや質問で応答時間・トークン数を比較する",
    )
    parser.add_argument(
        "--benchmark-model",
        action="append",
        default=[],
        metavar="MODEL",
        help="比較するモデル（複数回指定。省略時は AIE_MODEL のモデル）",
    )
    parser.add_argument(
        "--benchmark-question",
        action="append",
        default=[],
        metavar="QUESTION",
        help="比較する質問（複数回指定。省略時は既定の質問）",
    )
    args = parser.parse_args()

    if args.interactive and args.benchmark:
        parser.error("--interactive と --benchmark は同時に指定できません")
    if args.benchmark:
        models = args.benchmark_model or [MODEL]
        questions = args.benchmark_question or [args.question or DEFAULT_QUESTION]
        if len(set(models)) < 2 and len(set(questions)) < 2:
            parser.error(
                "--benchmark では異なるモデルか異なる質問を2つ以上指定してください"
            )
    elif args.benchmark_model or args.benchmark_question:
        parser.error("--benchmark-model と --benchmark-question には --benchmark が必要です")

    print(f"[model] {MODEL}")
    if args.temperature is not None:
        print(f"[temperature] {args.temperature}")
    try:
        if args.benchmark:
            compare_models_and_questions(models, questions, args.temperature)
        elif args.interactive:
            ask_interactively(args.question, temperature=args.temperature)
        else:
            question = args.question or DEFAULT_QUESTION
            print(f"[質問] {question}\n")
            print(ask(question, temperature=args.temperature))
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()

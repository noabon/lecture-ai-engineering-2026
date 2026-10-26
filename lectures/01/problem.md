# 第1回 演習・宿題：開発環境を整え、LLMに質問する

## この回のゴール

- 自分の fork を Codespaces で開き、Gemini API を呼び出せる
- GitHub Copilot でコードを少し直せる
- 作業ブランチから PR を出して提出できる（以降の回もこの流れで提出する）

## 準備するもの

- GitHub の個人アカウント（会社が管理するアカウントは、組織の設定で Codespaces や Copilot が使えないことがあります）
- Google の個人アカウント（会社の Google Workspace アカウントは、管理者の設定で AI Studio が使えないことがあります）

## 演習（45分）

### 1. 講座 repo を fork する

講座 repo の右上の **Fork** から、自分のアカウントに fork を作ります。以降の作業はすべて自分の fork で行います。

### 2. Gemini API キーを発行する

[Google AI Studio](https://aistudio.google.com/apikey) で API キーを作成し、コピーします。

> APIキーは秘密情報です。コードやチャット、コミットに貼らないでください。漏れた場合は AI Studio でキーを削除し、作り直してください。

### 3. Codespaces secret に登録する

GitHub の **Settings → Codespaces → Secrets → New secret** で次のように登録します。

- Name: `GEMINI_API_KEY`
- Value: 手順2のキー
- Repository access: **自分の fork** を選ぶ

> Codespaces を起動する前に登録してください。起動後に登録した場合は、Codespaces の再起動が必要です。

### 4. Codespaces を起動する

自分の fork で **Code → Codespaces → Create codespace on main**。初回は環境の準備に数分かかります。ターミナルで次を実行し、テストが通ることを確認します。

```bash
uv run pytest -q
```

### 5. 素のLLMに質問する

```bash
uv run python -m app.ask "LoRAとは何ですか？"
uv run python -m app.ask "AIE2026の講座の宿題にある「3レベル」とは何ですか？"
```

1つ目は一般的な用語なので、おおむね正しい答えが返ります。2つ目は講座に固有の「宿題の3レベル」について質問します。素のLLMは講座のことを知らないため、「分からない」と答えるか、一般論でもっともらしく答えます。正しい内容は `data/glossary.json` の `homework-levels` にあります。モデルの答えと比べてみましょう。

余裕があれば、ほかの講座に固有の質問も試してください。同じ質問でも実行ごとに答えが変わること、知らないことでも確信を持って答えることがあることに注目しましょう。

```bash
uv run python -m app.ask "AIE2026の講座で使う「lecNN-start タグ」とは何ですか？"
uv run python -m app.ask "AIE2026の第2回では何を学びますか？"
```

### 6. Copilot でトークン数を表示させる

`app/ask.py` の `TODO(第1回 演習)` の場所で、入力トークン数と出力トークン数を表示するよう改修します。Copilot の補完やチャットを使ってかまいません。提案されたコードは、読んで理解してから採用してください。

### 7. ブランチを作って PR を出す

```bash
git switch -c lec01
# lectures/01/answer.md を書く
git add -A
git commit -m "第1回 演習"
git push -u origin lec01
```

GitHub の自分の fork で、`lec01` → `main` の PR を作成します。**base repository が自分の fork になっていることを確認してください**（講座 repo に PR を出さないこと）。

### 8. Codespaces を停止する

左下の「Codespaces」→ **Stop Current Codespace**。起動したままだと無料枠を消費し続けます。

## 宿題（どれか1つで完了）

| レベル | 内容 |
|---|---|
| 基礎 | 同じ質問を3回ずつ、モデルを変えて（`AIE_MODEL` 環境変数）、または temperature を変えて実行し、回答の違いを answer.md にまとめる |
| 実装 | `app/ask.py` を改修し、会話履歴を保ったまま続けて質問できるようにする |
| 発展 | 応答時間とトークン数を計測し、複数のモデルや質問で比較する。無料枠のレート制限との関係も考察する |

モデルの切り替え例：

```bash
AIE_MODEL=gemini-3.5-flash uv run python -m app.ask "LoRAとは何ですか？"
```

temperature を変えるには、`--temperature` オプションを使います。

```bash
uv run python -m app.ask --temperature 0.2 "LoRAとは何ですか？"
```

値を変えて同じ質問を実行し、回答の違いを比べてみましょう。

会話履歴を保って続けて質問するには、`--interactive` を指定します。質問を引数で渡すと最初の質問として送信し、省略すると入力待ちになります。会話を終えるには「終了」と入力してください。

```bash
uv run python -m app.ask --interactive
uv run python -m app.ask --interactive "LoRAとは何ですか？"
```

応答時間とトークン数を比較するには、`--benchmark` と `--benchmark-model` / `--benchmark-question` を使います。比較する値はそれぞれ複数回指定できます。次の例は2モデル × 2質問の計4回のAPI呼び出しを、順番に行います。

```bash
uv run python -m app.ask --benchmark \
  --benchmark-model gemini-3.5-flash-lite \
  --benchmark-model gemini-3.5-flash \
  --benchmark-question "LoRAとは何ですか？" \
  --benchmark-question "RAGとは何ですか？"
```

片方だけを比較する場合も、モデルまたは質問を異なる値で2つ以上指定してください。応答時間はAPI呼び出し全体の経過時間で、ネットワークなどの待ち時間も含みます。実行回数が増えると無料枠のレート制限に達しやすくなるため、最初は少ない組み合わせで試してください。429エラーが出た場合はその時点で中断し、しばらく待ってから再実行します。

結果を `answer.md` にまとめる際は、条件（モデル・質問）、応答時間、入力/出力トークン数、回答の違いに加えて、無料枠の1分あたり・1日あたりの上限と、実行回数が制限にどう影響したかを考察してください。

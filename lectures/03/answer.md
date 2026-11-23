# 第3回 解答

## 演習

- 第1回の素のLLMと、エージェントの回答の違い
  - 素のLLMは用語集を参照せずに推測しがちだったのに対し、エージェントは `search_glossary` を先に使うため、講座固有の用語と定義を根拠にして答えることができた。
- `--trace` で見えたツール呼び出し
  - `search_glossary({'query': 'LoRA'})` のように、調べたい用語がそのままツールの引数になっていることがわかった。
  - `ToolCallPart` と `ToolReturnPart` を確認することで、どのツールがどの時点で呼ばれたかを追うことができた。
- 1回の質問での LLM 呼び出し回数
  - `[usage]` の `requests` を見て、検索のたびに LLM の呼び出し回数が増えることを確認した。
- 追加したツールと docstring の意図
  - `save_learning_log` は学習ログを保存するためのツールであり、docstring に「学習した内容を `learning_log/` に保存するときに使う」と書くことで、モデルがどの場面で使うべきかを理解しやすくした。

## 実装宿題

- 取り組んだレベル：実装
- 実施内容
  - `app/tools.py` に `save_learning_log` を追加し、学習メモを `learning_log/` に Markdown 形式で保存できるようにした。
  - `app/agent.py` では `save_learning_log` を `requires_approval=True` 付きで登録し、`DeferredToolRequests` を受け取るようにした。
  - CLI 上では保存前に利用者へ確認を出し、承認された場合のみ `message_history` と `deferred_tool_results` を渡して再実行するようにした。
- 実際の結果
  - 保存ツールは `learning_log/` にタイムスタンプ付きのファイルを作成した。
  - `NameError` を避けるため、`DATA_DIR` と `LEARNING_LOG_DIR` の順を修正し、`datetime` を import した。
- 気づき
  - ツールの docstring は、モデルがどのツールを使うかを決める重要な入力になっていることがわかった。
  - 承認付きツールはそのまま実行されず、`DeferredToolRequests` で止まるので、利用者確認の設計が必要だと感じた。

### 何ができたら完成か

- `save_learning_log` を呼ぶと、`learning_log/` にファイルが保存されること。
- 保存の直前に、利用者へ「本当に保存してよいか」を聞く承認待ちになること。
- 承認後に `DeferredToolRequests` を `result.output.build_results(approvals=...)` で処理し、再度 `run_sync` を実行して通常の応答へ進めること。
- 最終的に、保存した学習メモがファイルとして残ること。

### どう確かめたか

- 実装前に、`DeferredToolRequests` の実際の型と `approvals` の扱いを確認した。
  - 実行コードでは `isinstance(result.output, DeferredToolRequests)` が `True` になり、`len(result.output.approvals)` も 1 であることを確認した。
  - その後、`approvals = {a.tool_call_id: True for a in result.output.approvals}` を使い、`result.output.build_results(approvals=approvals)` により次の `run_sync` が動くことを確認した。
- 実際に CLI で `uv run python -m app.agent --trace "学習ログを保存して。トピックは「第3回 学習メモ」。メモは ... "` を実行し、`save_learning_log を保存しますか？ [y/N]: y` と承認を求めることを確認した。
- 承認後に `学習ログの保存を行いました。` と表示され、`ls -1 learning_log` で `20261109-045045-954307.md` が作成されていることを確認した。
- そのファイルの中身を開いて、題名とメモが保存されていることを最終確認した。

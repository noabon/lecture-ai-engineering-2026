from types import SimpleNamespace

from app import ask as ask_module


def test_interactive_questions_share_chat_history(monkeypatch):
    class FakeChat:
        def __init__(self):
            self.questions = []

        def send_message(self, question):
            self.questions.append(question)
            return SimpleNamespace(text=question, usage_metadata=None)

    class FakeChats:
        def __init__(self, client):
            self.client = client

        def create(self, *, model, config):
            self.client.model = model
            self.client.chat_config = config
            return self.client.chat

    class FakeClient:
        def __init__(self):
            self.chat = FakeChat()
            self.chat_config = None
            self.chats = FakeChats(self)

    client = FakeClient()

    def fake_client(*, api_key):
        assert api_key == "test-key"
        return client

    monkeypatch.setattr(ask_module.genai, "Client", fake_client)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    questions = iter(("LoRAとは？", "その利点は？", "終了"))
    monkeypatch.setattr("builtins.input", lambda _: next(questions))

    ask_module.ask_interactively(initial_question=None, temperature=0.2)

    assert client.chat.questions == ["LoRAとは？", "その利点は？"]
    assert client.chat_config.temperature == 0.2


def test_benchmark_measures_each_model_and_question(monkeypatch, capsys):
    class FakeModels:
        def __init__(self):
            self.calls = []

        def generate_content(self, *, model, contents, config):
            self.calls.append((model, contents, config))
            return SimpleNamespace(
                text=f"{model}: {contents}",
                usage_metadata=SimpleNamespace(
                    prompt_token_count=10,
                    candidates_token_count=5,
                ),
            )

    class FakeClient:
        def __init__(self):
            self.models = FakeModels()

    client = FakeClient()

    def fake_client(*, api_key):
        assert api_key == "test-key"
        return client

    monkeypatch.setattr(
        ask_module.genai,
        "Client",
        fake_client,
    )
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    timestamps = iter((1.0, 1.25, 2.0, 2.5, 3.0, 3.75, 4.0, 5.0))
    monkeypatch.setattr(ask_module.time, "perf_counter", lambda: next(timestamps))

    ask_module.compare_models_and_questions(
        models=["model-a", "model-b"],
        questions=["question-a", "question-b"],
        temperature=0.4,
    )

    assert [
        (model, question) for model, question, _ in client.models.calls
    ] == [
        ("model-a", "question-a"),
        ("model-a", "question-b"),
        ("model-b", "question-a"),
        ("model-b", "question-b"),
    ]
    assert all(config.temperature == 0.4 for _, _, config in client.models.calls)
    output = capsys.readouterr().out
    assert "実行回数: 4" in output
    assert output.count("[応答時間]") == 4
    assert output.count("入力: 10, 出力: 5") == 4
    assert "0.25 秒" in output

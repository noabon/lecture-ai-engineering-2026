from app.retrieval import add_neighbor_pages


def test_add_neighbor_pages_deduplicates_and_stays_within_document():
    pages = [
        {"page_id": "doc-a-p009", "document_id": "doc-a", "page": 9, "content": "前々"},
        {"page_id": "doc-a-p010", "document_id": "doc-a", "page": 10, "content": "前"},
        {"page_id": "doc-a-p011", "document_id": "doc-a", "page": 11, "content": "検索結果"},
        {"page_id": "doc-a-p012", "document_id": "doc-a", "page": 12, "content": "次"},
        {"page_id": "doc-b-p010", "document_id": "doc-b", "page": 10, "content": "別資料"},
    ]
    hits = [
        {**pages[1], "distance": 0.1},
        {**pages[2], "distance": 0.2},
    ]

    results = add_neighbor_pages(hits, pages)

    assert [page["page_id"] for page in results] == [
        "doc-a-p010", "doc-a-p011", "doc-a-p009", "doc-a-p012",
    ]
    assert results[2]["content"] == "前々"
    assert results[2]["distance"] is None


def test_add_neighbor_pages_returns_empty_results_for_no_hits():
    assert add_neighbor_pages([], []) == []

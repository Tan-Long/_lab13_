from app.metrics import percentile, record_request, snapshot


def test_percentile_basic() -> None:
    assert percentile([100, 200, 300, 400], 50) >= 100


def test_percentile_empty() -> None:
    assert percentile([], 95) == 0.0


def test_percentile_p95() -> None:
    values = list(range(1, 101))
    assert percentile(values, 95) >= 95


def test_percentile_single() -> None:
    assert percentile([42], 50) == 42.0


def test_snapshot_structure() -> None:
    s = snapshot()
    assert "traffic" in s
    assert "latency_p95" in s
    assert "total_cost_usd" in s
    assert "quality_avg" in s

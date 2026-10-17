from src.nebius_client import NebiusClient


def test_nebius_client_returns_fallback_when_disabled() -> None:
    client = NebiusClient()
    result = client.score_intake_judge(
        "clarification_quality",
        {"case_id": "H11"},
        fallback={"score": 0.0, "label": "fail"},
    )
    assert result["score"] == 0.0
    assert result["label"] == "fail"

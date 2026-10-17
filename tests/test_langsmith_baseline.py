from scripts.langsmith_baseline import build_evaluators


def test_build_evaluators_includes_route_and_judge_metrics() -> None:
    evaluators = build_evaluators()
    names = {e.__name__ for e in evaluators}
    assert "route_exact_match" in names
    assert "clarification_quality" in names
    assert "issue_capture_completeness" in names

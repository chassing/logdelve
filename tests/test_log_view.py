"""Tests for LogView incremental line appending (tailing / chunked loading)."""

from __future__ import annotations

import pytest
from textual.app import App, ComposeResult

from logdelve.models import ContentType, LogLevel, LogLine
from logdelve.widgets.log_view import LogView


def _make_line(line_number: int, raw: str, log_level: LogLevel | None = None) -> LogLine:
    return LogLine(
        line_number=line_number,
        raw=raw,
        content_type=ContentType.TEXT,
        log_level=log_level,
    )


class _LogViewTestApp(App[None]):
    def compose(self) -> ComposeResult:
        yield LogView(id="log-view")


class TestAppendLineLevelFilter:
    @pytest.mark.asyncio
    async def test_new_line_below_min_level_is_excluded(self) -> None:
        app = _LogViewTestApp()
        async with app.run_test():
            log_view = app.query_one(LogView)
            log_view.set_lines([_make_line(1, "existing error", log_level=LogLevel.ERROR)])
            log_view.set_min_level(LogLevel.ERROR)

            log_view.append_line(_make_line(2, "new info", log_level=LogLevel.INFO))

            assert [line.line_number for line in log_view.lines] == [1]

    @pytest.mark.asyncio
    async def test_new_line_at_or_above_min_level_is_included(self) -> None:
        app = _LogViewTestApp()
        async with app.run_test():
            log_view = app.query_one(LogView)
            log_view.set_lines([_make_line(1, "existing error", log_level=LogLevel.ERROR)])
            log_view.set_min_level(LogLevel.ERROR)

            log_view.append_line(_make_line(2, "new fatal", log_level=LogLevel.FATAL))

            assert [line.line_number for line in log_view.lines] == [1, 2]


class TestAppendLineAnomalyFilter:
    @pytest.mark.asyncio
    async def test_new_line_without_anomaly_score_is_excluded_when_filter_active(self) -> None:
        app = _LogViewTestApp()
        async with app.run_test():
            log_view = app.query_one(LogView)
            log_view.set_lines([_make_line(1, "anomalous existing line")])
            log_view.set_anomaly_scores({0: 1.0})
            log_view.toggle_anomaly_filter()

            log_view.append_line(_make_line(2, "new line, no anomaly score yet"))

            assert [line.line_number for line in log_view.lines] == [1]


class TestAppendLinesLevelFilter:
    @pytest.mark.asyncio
    async def test_mixed_batch_only_keeps_lines_at_or_above_min_level(self) -> None:
        app = _LogViewTestApp()
        async with app.run_test():
            log_view = app.query_one(LogView)
            log_view.set_lines([_make_line(1, "existing error", log_level=LogLevel.ERROR)])
            log_view.set_min_level(LogLevel.ERROR)

            log_view.append_lines(
                [
                    _make_line(2, "new info", log_level=LogLevel.INFO),
                    _make_line(3, "new fatal", log_level=LogLevel.FATAL),
                ]
            )

            assert [line.line_number for line in log_view.lines] == [1, 3]

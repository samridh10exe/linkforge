from flask import Flask

from app.metrics import CLICK_EVENT_ENQUEUE_FAILURES
from app.services import events as events_service


def test_get_executor_reuses_single_executor_with_configured_worker_count():
    app = Flask(__name__)
    app.config["CLICK_EVENT_WORKERS"] = 3
    events_service._executor = None

    with app.app_context():
        first = events_service._get_executor()
        second = events_service._get_executor()

    assert first is second
    assert first._max_workers == 3


def test_enqueue_click_event_submits_background_write_job(monkeypatch):
    app = Flask(__name__)
    app.config["CLICK_EVENT_WORKERS"] = 2
    submitted = {}

    class FakeExecutor:
        def submit(self, fn, *args):
            submitted["fn_name"] = fn.__name__
            submitted["args"] = args

    with app.app_context():
        monkeypatch.setattr(events_service, "_get_executor", lambda: FakeExecutor())
        events_service.enqueue_click_event(11, 7, {"short_code": "abc123"})

    assert submitted["fn_name"] == "_write_click_event"
    assert submitted["args"] == (11, 7, {"short_code": "abc123"})


def test_enqueue_click_event_increments_failure_metric_when_executor_submit_fails(monkeypatch):
    app = Flask(__name__)
    app.config["CLICK_EVENT_WORKERS"] = 2
    before = CLICK_EVENT_ENQUEUE_FAILURES._value.get()

    class BrokenExecutor:
        def submit(self, fn, *args):
            raise RuntimeError("submit failed")

    with app.app_context():
        monkeypatch.setattr(events_service, "_get_executor", lambda: BrokenExecutor())
        events_service.enqueue_click_event(12, 8, {"short_code": "def456"})

    assert CLICK_EVENT_ENQUEUE_FAILURES._value.get() == before + 1


def test_write_click_event_increments_failure_metric_when_event_insert_fails(monkeypatch):
    before = CLICK_EVENT_ENQUEUE_FAILURES._value.get()

    class FakeDb:
        class _Context:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        def connection_context(self):
            return self._Context()

    monkeypatch.setattr(events_service, "db", FakeDb())
    monkeypatch.setattr(events_service, "create_event", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("write failed")))

    events_service._write_click_event(13, 9, {"short_code": "ghi789"})

    assert CLICK_EVENT_ENQUEUE_FAILURES._value.get() == before + 1

import threading
import sys
import pathlib

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from streamlit_extension.middleware.correlation import (
    CorrelationManager,
    RequestLifecycleTracker,
)
from streamlit_extension.middleware.context_manager import ContextManager, ContextMiddleware


def test_correlation_id_propagation():
    manager = CorrelationManager()
    cid = manager.get_or_create()
    assert manager.get_correlation_id() == cid


def test_cross_request_correlation():
    manager = CorrelationManager()
    tracker = RequestLifecycleTracker()
    context_mgr = ContextManager(manager)
    middleware = ContextMiddleware(context_mgr, tracker)

    middleware.process_request({"session_id": "s1"})
    cid1 = context_mgr.get_context().correlation_id
    middleware.process_response({"status": "ok"})

    middleware.process_request({"session_id": "s2"})
    cid2 = context_mgr.get_context().correlation_id
    middleware.process_response({"status": "ok"})

    assert cid1 != cid2
    assert len(tracker.events) == 4  # start/end for two requests


def test_correlation_in_async_operations():
    manager = CorrelationManager()
    results = []

    def worker():
        results.append(manager.get_or_create())

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(set(results)) == 2
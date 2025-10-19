from progressorx import ProgressManager
from progressorx.backends.memory import InMemoryStore


def test_set_and_get():
    store = InMemoryStore()
    mgr = ProgressManager(store)
    progress = 10


    mgr.create('t1')
    mgr.report_progress('t1', progress=progress)
    assert mgr.get_progress('t1').progress == progress




def test_increment():
    store = InMemoryStore()
    mgr = ProgressManager(store)
    mgr.create('t2')
    mgr.report_progress('t2', progress=90)
    mgr.report_progress('t2', increase=10)
    assert mgr.get_progress('t2').progress == 100
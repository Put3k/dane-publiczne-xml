from datetime import date

from mailer import Status, DeveloperResult, _build_subject, _build_body


RUN_DATE = date(2026, 6, 10)


def test_subject_all_ok():
    results = [
        DeveloperResult('ARCUS', Status.PROCESSED),
        DeveloperResult('XETTO', Status.PROCESSED),
        DeveloperResult('KRYNICA', Status.SKIPPED),
    ]
    subject = _build_subject(results, RUN_DATE)
    assert subject == '[dane-publiczne] 2026-06-10 OK — 2 processed, 1 skipped'


def test_subject_with_failures():
    results = [
        DeveloperResult('ARCUS', Status.PROCESSED),
        DeveloperResult('XETTO', Status.FAILED, 'Traceback ...'),
        DeveloperResult('KRYNICA', Status.FAILED, 'Traceback ...'),
    ]
    subject = _build_subject(results, RUN_DATE)
    assert subject == '[dane-publiczne] 2026-06-10 FAILED — 2 of 3'


def test_body_lists_ok_one_line_each():
    results = [
        DeveloperResult('ARCUS', Status.PROCESSED),
        DeveloperResult('XETTO', Status.SKIPPED),
    ]
    body = _build_body(results, RUN_DATE)
    assert 'ARCUS — processed' in body
    assert 'XETTO — skipped' in body
    assert 'FAILURES' not in body


def test_body_expands_failure_with_traceback():
    tb = 'Traceback (most recent call last):\n  ValueError: boom'
    results = [
        DeveloperResult('ARCUS', Status.PROCESSED),
        DeveloperResult('XETTO', Status.FAILED, tb),
    ]
    body = _build_body(results, RUN_DATE)
    assert 'FAILURES' in body
    assert 'XETTO — failed' in body
    assert tb in body
    # ok developer still listed, not under failures section
    assert 'ARCUS — processed' in body

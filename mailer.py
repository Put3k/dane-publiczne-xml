import smtplib
import logging
from enum import Enum
from dataclasses import dataclass
from datetime import date
from email.message import EmailMessage

from settings import (
    SMTP_HOST,
    SMTP_PORT,
    SMTP_USER,
    SMTP_PASSWORD,
    SMTP_FROM,
    SMTP_TO,
)


logger = logging.getLogger('root')


class Status(Enum):
    PROCESSED = 'processed'
    SKIPPED = 'skipped'
    FAILED = 'failed'


@dataclass
class DeveloperResult:
    code: str
    status: Status
    error: str | None = None


def _counts(results):
    return {
        status: sum(1 for r in results if r.status is status)
        for status in Status
    }


def _build_subject(results, run_date):
    counts = _counts(results)
    failed = counts[Status.FAILED]
    if failed:
        state = f'FAILED — {failed} of {len(results)}'
    else:
        state = (
            f'OK — {counts[Status.PROCESSED]} processed, '
            f'{counts[Status.SKIPPED]} skipped'
        )
    return f'[dane-publiczne] {run_date.isoformat()} {state}'


def _build_body(results, run_date):
    counts = _counts(results)
    lines = [
        f'Run date: {run_date.isoformat()}',
        (
            f'Processed: {counts[Status.PROCESSED]}, '
            f'skipped: {counts[Status.SKIPPED]}, '
            f'failed: {counts[Status.FAILED]}'
        ),
        '',
    ]

    for result in results:
        if result.status is not Status.FAILED:
            lines.append(f'{result.code} — {result.status.value}')

    failures = [r for r in results if r.status is Status.FAILED]
    if failures:
        lines.append('')
        lines.append('FAILURES')
        lines.append('========')
        for result in failures:
            lines.append('')
            lines.append(f'{result.code} — failed')
            lines.append(result.error or '(no traceback captured)')

    return '\n'.join(lines)


def send_run_summary(results, run_date=None):
    """Build, log, and best-effort email the run summary.

    The summary is always logged first so the logfile stays authoritative;
    the email send is wrapped so a delivery failure never crashes the run.
    """
    run_date = run_date or date.today()
    subject = _build_subject(results, run_date)
    body = _build_body(results, run_date)

    logger.info('RUN SUMMARY: %s\n%s', subject, body)

    try:
        message = EmailMessage()
        message['Subject'] = subject
        message['From'] = SMTP_FROM
        message['To'] = SMTP_TO
        message.set_content(body)

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
            smtp.starttls()
            if SMTP_USER:
                smtp.login(SMTP_USER, SMTP_PASSWORD)
            smtp.send_message(message)
        logger.info('summary email sent to %s', SMTP_TO)
    except Exception:
        logger.exception('failed to send summary email')

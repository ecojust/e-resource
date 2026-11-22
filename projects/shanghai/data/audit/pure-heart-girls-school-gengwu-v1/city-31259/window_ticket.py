"""Replay an issued 324 window result without granting the same physical slot twice."""
from pathlib import Path
from guest_result import digest, load, verify

def existing_result(work, kind, host, report):
    work, host = Path(work), Path(host)
    paths = [p for suffix in ('deferred','returned') if (p:=work/f'324-{kind}-{suffix}.json').exists()]
    if not paths:
        return None
    assert len(paths) == 1
    ticket = load(paths[0])
    assert ticket['order'] == 324 and ticket['host'] == 259 and ticket['phase'] == kind
    assert Path(ticket['host_closed']).resolve() == host.resolve()
    assert ticket['host_closed_sha256'] == digest(host) and ticket['host_report_sha256'] == digest(report)
    if 'actual_receipt' in ticket:
        source = Path(ticket['actual_receipt'])
        assert digest(source) == ticket['sha256']
        outcome = verify(kind,host,source)
        assert (outcome == 'complete') == (ticket.get('passed') is True)
        if outcome != 'complete':
            assert ticket['deferred'] and ticket['guest_outcome'] == outcome
    else:
        assert ticket['deferred'] and ticket['missing'] and ticket['remaining']==[]
        assert ticket['native_started'] is False and ticket['viewer_started'] is False
    return ticket

#!/usr/bin/env python3
"""Run one frozen reviewer CLI in-process with a strict <1GiB address-space cap."""
import argparse
import hashlib
import json
from pathlib import Path
import resource
import runpy
import sys
import time

HERE=Path(__file__).resolve().parent

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--resource-report',type=Path,required=True)
    ap.add_argument('command',nargs=argparse.REMAINDER)
    a=ap.parse_args();cmd=a.command
    if cmd and cmd[0]=='--':cmd=cmd[1:]
    assert cmd and Path(cmd[0]).resolve().is_relative_to(HERE/'checker-v2')
    assert a.resource_report.resolve().is_relative_to(HERE) and not a.resource_report.exists()
    cap=900*1024*1024
    resource.setrlimit(resource.RLIMIT_AS,(cap,cap))
    sys.argv=cmd;sys.path.insert(0,str(Path(cmd[0]).resolve().parent))
    start=time.monotonic();exitcode=0;error=None
    try:runpy.run_path(cmd[0],run_name='__main__')
    except SystemExit as e:exitcode=int(e.code or 0)
    except Exception as e:
        exitcode=2;error={'type':type(e).__name__,'message':str(e)}
        import traceback;traceback.print_exc()
    usage=resource.getrusage(resource.RUSAGE_SELF)
    report={'schema':'museum-bounded-review-execution-v1','command':cmd,'exit_code':exitcode,
            'elapsed_seconds':time.monotonic()-start,'maximum_rss_kib':usage.ru_maxrss,
            'address_space_limit_bytes':cap,'exception':error,
            'resource_runner_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'result_is_not_model_acceptance':True}
    a.resource_report.parent.mkdir(parents=True,exist_ok=True)
    a.resource_report.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report));raise SystemExit(exitcode)

if __name__=='__main__':main()

#!/usr/bin/env python3
"""Run the explicitly frozen external area adapter inside the bounded runner.

No subprocess: the original900MiB process limit and resource accounting remain
in force. The adapter and its declared source files are verified before entry.
"""
import hashlib,json,runpy,sys
from pathlib import Path

BASE=Path(__file__).resolve().parents[3]
ADAPTER_ROOT=BASE/'registration-museum-v2-preparation/request-adaptation'
FREEZE_SHA='2e324ecd6a88945549335eb2f48263dda74b9e1ad024d2def42902371c1084a8'
ADAPTER_SHA='05d7515cd4d38a625dd5f0f63ad19b7e8f7e5eab4d216eded03c77144d60d018'


def main():
    freeze=ADAPTER_ROOT/'source-freeze.json'
    data=freeze.read_bytes();assert hashlib.sha256(data).hexdigest()==FREEZE_SHA
    for row in json.loads(data)['files']:
        path=Path(row['file']);content=path.read_bytes()
        assert len(content)==row['bytes'] and hashlib.sha256(content).hexdigest()==row['sha256'], str(path)
    adapter=ADAPTER_ROOT/'run_area_seating_v3.py'
    assert hashlib.sha256(adapter.read_bytes()).hexdigest()==ADAPTER_SHA
    sys.path.insert(0,str(ADAPTER_ROOT))
    sys.argv=[str(adapter),*sys.argv[1:]]
    runpy.run_path(str(adapter),run_name='__main__')


if __name__=='__main__':main()

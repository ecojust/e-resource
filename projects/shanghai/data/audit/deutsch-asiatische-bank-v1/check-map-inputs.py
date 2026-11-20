"""Capture all browser resources for this model and compare them to the published working tree."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
from urllib.parse import quote, urljoin
from urllib.request import urlopen

AUDIT = Path(__file__).resolve().parent
PROJECT = AUDIT.parents[2]
BASE = PROJECT / 'data/audit/concert-hall-v1/check-map-inputs.py'
spec = importlib.util.spec_from_file_location('map_inputs',BASE)
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)


def capture(args):
    report=json.loads(args.browser_report.read_bytes())
    assert report['completed'] and report['city_count']==143 and report['model_id']=='huangpu-deutsch-asiatische-bank'
    start=datetime.fromisoformat(report['started_utc'].replace('Z','+00:00')).timestamp()
    end=datetime.fromisoformat(report['finished_utc'].replace('Z','+00:00')).timestamp()
    records={}
    generation={}
    for row in map(json.loads,args.server_log.read_text().splitlines()):
        if not start<=row['at']<=end:continue
        assert row['status'] in (200,206)
        name=row['path']
        cached=row['origin'].startswith('git-blob-verified-')
        source=(args.server_log.parent/'objects' if cached else args.project)/name
        if source.is_file():
            data=source.read_bytes()
        else:
            # The multi-site server keeps an immutable cache shared across
            # ports. Re-read from this run's origin and require its recorded
            # SHA256 and size, exactly as for a local per-site cache.
            assert cached,name
            with urlopen(urljoin(report['server'],quote(name)),timeout=90) as response:
                assert response.status==200,name
                data=response.read()
        item={'bytes':len(data),'sha256':base.digest(data),'git_blob':base.git_blob(data)}
        assert item['sha256']==row['sha256'] and item['bytes']==row['bytes'],name
        if cached:
            receipt_file=source.with_name(source.name+'.receipt.json')
            if receipt_file.is_file():
                receipt=json.loads(receipt_file.read_bytes())
                assert receipt['git_blob']==receipt['actual_git_blob']==item['git_blob'],name
            else:
                assert args.revision and base.git_entry(args.project,name,args.revision)==item['git_blob'],name
        assert item==records.get(name,item),name
        records[name]=item
    for name,expected in report['bindings'].items():
        data=(args.project/name).read_bytes()
        item={'bytes':len(data),'sha256':base.digest(data),'git_blob':base.git_blob(data)}
        assert item['sha256']==expected,name
        if name.startswith('data/global-models/') or 'inventory' in name:
            generation[name]=item
        else:
            assert item==records.get(name,item),name
            records[name]=item
    runtime_receipt=AUDIT/'selected-facade-label-http.json'
    override=json.loads(runtime_receipt.read_bytes())
    assert override['passed'] and override['original_catalog_sha256']==override['new_catalog_sha256']==report['bindings']['data/candidate-city-integrations.json']
    for resource in override['files']:
        name=resource['path']
        if not name.startswith('src/'): continue
        with urlopen(urljoin(report['server'],resource['actual_url']),timeout=90) as response:
            assert response.status==200,name
            data=response.read()
        item={'bytes':len(data),'sha256':base.digest(data),'git_blob':base.git_blob(data)}
        assert item['bytes']==resource['bytes'] and item['sha256']==resource['sha256'],name
        assert item==records.get(name,item),name
        records[name]=item
    for item in report['http_assets']+report['map_files_seen']:
        assert records[item['file']]['sha256']==item['sha256'],item['file']
    out={'model_id':report['model_id'],'run_sha256':base.digest(args.browser_report.read_bytes()),
         'scope':'Logged upstream resources for the browser run, runtime modules re-read through the final proxy using their imported URLs, and registration inputs. Ranges are identified by the digest of the complete file.',
         'generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
         'proxy_runtime_receipt_sha256':base.digest(runtime_receipt.read_bytes()),
         'catalog_generation_inputs':dict(sorted(generation.items())),'files':dict(sorted(records.items()))}
    args.inventory.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print(f'Recorded {len(records)} resources and {len(generation)} catalog records.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['capture','verify'])
    parser.add_argument('--project',type=Path,default=PROJECT)
    parser.add_argument('--browser-report',type=Path,default=AUDIT/'main-map-browser.json')
    parser.add_argument('--inventory',type=Path,default=AUDIT/'main-map-inputs.json')
    parser.add_argument('--server-log',type=Path)
    parser.add_argument('--revision')
    parser.add_argument('--receipt',type=Path)
    a=parser.parse_args()
    if a.action=='capture' and not a.server_log:parser.error('--server-log is required to capture')
    (capture if a.action=='capture' else base.verify)(a)

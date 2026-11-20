"""Read and hash every immutable input through the same server as the live map."""
from argparse import ArgumentParser
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.parse import quote, urljoin
from urllib.request import urlopen

def sha(data):
    return hashlib.sha256(data).hexdigest()

def main():
    parser=ArgumentParser(description=__doc__)
    parser.add_argument('snapshot',type=Path)
    parser.add_argument('url')
    parser.add_argument('receipt',type=Path)
    args=parser.parse_args()
    snapshot=json.loads(args.snapshot.read_bytes())
    def check(entry):
        path,expected=entry
        with urlopen(urljoin(args.url,quote(path)),timeout=120) as response:
            assert response.status==200,(path,response.status)
            data=response.read()
        actual=sha(data)
        assert actual==expected,(path,actual,expected)
        return path,{'bytes':len(data),'sha256':actual}
    start=datetime.now(timezone.utc).isoformat()
    with ThreadPoolExecutor(max_workers=2) as pool:
        files=dict(pool.map(check,snapshot['files'].items()))
    result={'started_utc':start,'finished_utc':datetime.now(timezone.utc).isoformat(),
            'base_url':args.url,'snapshot_sha256':sha(args.snapshot.read_bytes()),
            'script_sha256':sha(Path(__file__).read_bytes()),'count':snapshot['resulting_count'],
            'passed':len(files)==len(snapshot['files']),'verified_files':len(files),'files':files}
    args.receipt.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(len(files),'HTTP 200 resources match',result['count'])

if __name__=='__main__':main()

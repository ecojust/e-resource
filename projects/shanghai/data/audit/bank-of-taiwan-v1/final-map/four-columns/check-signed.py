"""Check every HTTP input from a signed Shanghai catalog, streaming each asset once."""
from argparse import ArgumentParser
from datetime import datetime,timezone
import hashlib,http.client,json,time
from pathlib import Path
from urllib.parse import quote,urlsplit
cli=ArgumentParser(description=__doc__);cli.add_argument('snapshot',type=Path);cli.add_argument('base');cli.add_argument('output',type=Path)
args=cli.parse_args();snapshot=json.loads(args.snapshot.read_bytes());origin=urlsplit(args.base);records=[];changes=[]
conn=None
for path,expected in snapshot['files'].items():
    for attempt in range(3):
        try:
            if conn is None:conn=http.client.HTTPConnection(origin.hostname,origin.port,timeout=90)
            conn.request('GET',origin.path.rstrip('/')+'/'+quote(path));response=conn.getresponse()
            assert response.status==200,(path,response.status)
            h=hashlib.sha256();length=0
            while block:=response.read(128*1024):
                h.update(block);length+=len(block)
            assert h.hexdigest()==expected,(path,h.hexdigest(),expected)
            records.append({'file':path,'sha256':h.hexdigest(),'bytes':length});break
        except (OSError,http.client.HTTPException):
            if conn:conn.close()
            conn=None
            if attempt==2:raise
            changes.append({'file':path,'retry':attempt+1})
conn.close()
report={'base':args.base,'checked_utc':datetime.now(timezone.utc).isoformat(),'snapshot_sha256':hashlib.sha256(args.snapshot.read_bytes()).hexdigest(),'checker_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'catalog_sha256':snapshot['files']['data/candidate-city-integrations.json'],'count':snapshot['resulting_count'],'files_verified':len(records),'total_bytes':sum(r['bytes']for r in records),'retries':changes,'files':records}
args.output.parent.mkdir(exist_ok=True,parents=True)
args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(report['count'],report['files_verified'],report['total_bytes'])

"""After visual review of eleven captures, archive the evidence and enqueue it for the normal publisher."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys
work=Path(__file__).parent
audit=Path('/workspace/e-resource/projects/shanghai/data/audit/qianxin-historic-front-v1')
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('actual_visual_review',type=Path)
    row=parser.parse_args()
    for script,extra in [('review.py',[row.actual_visual_review]),('archive-attempts.py',[])]:
        subprocess.run([sys.executable,'-B',work/script,*extra],check=True)
    terminal=work/'257-map-slot-released.json'
    done=json.loads(terminal.read_bytes())
    assert done['passed'] and done['views_reviewed'] and len(done['screenshots'])==11
    paths=['README.md','viewer.json','city-31257','historical-marker-31257-http.json','registered-marker-31257.json']
    if (audit/'archived-browser-attempts.json').exists():paths.append('archived-browser-attempts.json')
    subprocess.run([sys.executable,'-B','/tmp/shanghai-signed-release-inbox/submit.py','257',*paths],check=True)
    inbox=Path('/tmp/shanghai-signed-release-inbox/257.json')
    queued=json.loads(inbox.read_bytes())
    assert queued['order']==257 and queued['model']=='huangpu-qianxin-building-historic-front'
    for name,value in queued['files'].items():assert hashlib.sha256((audit/name).read_bytes()).hexdigest()==value
if __name__=='__main__':main()

"""After visual review of eleven captures, archive the evidence and enqueue it for the normal publisher."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys
work=Path(__file__).parent
audit=Path('/workspace/e-resource/projects/shanghai/data/audit/pure-heart-girls-school-gengwu-v1')
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('actual_visual_review',type=Path)
    row=parser.parse_args()
    for script,extra in [('review-display.py',[row.actual_visual_review]),('archive-attempts-display.py',[])]:
        subprocess.run([sys.executable,'-B',work/script,*extra],check=True)
    terminal=work/'259-map-slot-released.json'
    done=json.loads(terminal.read_bytes())
    assert done['passed'] and done['views_reviewed'] and len(done['screenshots'])==11
    paths=['README.md','viewer.json','city-31259','31259-all-http.json','historical-marker-31259-http.json','registered-marker-31259.json']
    paths.extend(image['filename'] for image in json.loads((audit/'viewer.json').read_bytes())['views'])
    if (audit/'archived-browser-attempts.json').exists():paths.append('archived-browser-attempts.json')
    subprocess.run([sys.executable,'-B','/tmp/shanghai-signed-release-inbox/submit.py','259',*paths],check=True)
    inbox=Path('/tmp/shanghai-signed-release-inbox/259.json')
    queued=json.loads(inbox.read_bytes())
    assert queued['order']==259 and queued['model']=='huangpu-pure-heart-girls-school-gengwu-front'
    for name,value in queued['files'].items():assert hashlib.sha256((audit/name).read_bytes()).hexdigest()==value
if __name__=='__main__':main()

"""Save all four ordinary Hongde Church downloads from both actual map versions and compare the public navigation."""
import argparse
from datetime import datetime,timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import tempfile
from urllib.request import Request,urlopen

ID='hongkou-hongde-church'
MACRO='14-13720-6692'
audit=Path(__file__).resolve().parent
project=audit.parents[3]
source=project/'source/precise'/ID/'revisions/entrance-guardians'
digest=lambda b:hashlib.sha256(b).hexdigest()
now=lambda:datetime.now(timezone.utc).isoformat()
class Anchor(HTMLParser):
    def __init__(self):super().__init__();self.card=False;self.dest=[];self.count=0
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='article' and 'data-landmark' in a:
            self.count+=1;self.card=a['data-landmark']==ID
        if self.card and tag=='a':self.dest.append(a['href'])
    def handle_endtag(self,tag):
        if tag=='article':self.card=False
def get(base,f):
    with urlopen(Request(base+f,headers={'Accept-Encoding':'identity'}),timeout=90)as res:
        assert res.status==200;return res.read()

def saved(base,r):
    with tempfile.TemporaryDirectory(prefix='hongde-139-save-') as scratch:
        out=Path(scratch)/Path(r['file']).name
        with urlopen(Request(base+r['file'],headers={'Accept-Encoding':'identity'}),timeout=120)as res,out.open('xb')as stream:
            assert res.status==200
            for chunk in iter(lambda:res.read(131072),b''):stream.write(chunk)
            url=res.geturl()
        with out.open('rb')as stream:sig=hashlib.file_digest(stream,'sha256').hexdigest()
        assert out.stat().st_size==r['bytes'] and sig==r['sha256']
        return {'download_url':url,'filename':out.name,'saved_bytes':out.stat().st_size,'sha256':sig}
def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('signed',type=Path);cli.add_argument('out',type=Path);opt=cli.parse_args()
    report={'id':ID,'started':now(),'script_sha256':digest(Path(__file__).read_bytes()),'versions':{}}
    old=None
    for n in [138,139]:
        base=f'http://127.0.0.1:{24000+n}/';snap=json.loads((opt.signed/f'{n}-production.json').read_bytes());assert snap['resulting_count']==176
        layer=json.loads((opt.signed/f'{n}-comparison.json').read_bytes());assert layer['passed'];urls={i['path']:i['actual_url']for i in layer['files']}
        files={}
        def binding(f):
            b=get(base,urls.get(f,f));h=digest(b)
            if f in snap['files']:assert h==snap['files'][f],f
            files[f]={'url':base+urls.get(f,f),'bytes':len(b),'sha256':h};return b
        card=Anchor();card.feed(binding('landmarks.html').decode());assert card.count==176 and card.dest==[f'index.html#landmark={ID}&mode=walk']*2
        city=json.loads(binding('data/candidate-city-integrations.json'));assert city['resulting_city_count']==176 and not any(r['id']==ID for r in city['models'])
        landmarks=json.loads(binding('data/landmarks.json'));entry=next(r for r in landmarks if r['id']==ID)
        reg=json.loads(binding('data/precise-buildings-v6.json'));ptr=reg['ordinary_catalog'];b=binding(ptr['file']);assert digest(b)==ptr['sha256']
        macro=next(r for r in json.loads(b)['macros']if r['id']==MACRO);index=binding(macro['file']);assert digest(index)==macro['sha256']
        rows=json.loads(index)['models'];model=next(r for r in rows if r['id']==ID);assert model['owner']['feature_local_id']==2557
        if n==138:
            rec=json.loads((source/'baseline.json').read_bytes())['assets'];old=(landmarks,rows,city,entry,model,card.dest)
        else:
            rec=json.loads(binding('source/precise/'+ID+'/revisions/entrance-guardians/manifest.json'))['assets']
            keep=lambda rows:[r for r in rows if r['id']!=ID]
            assert keep(old[0])==keep(landmarks) and keep(old[1])==keep(rows) and old[2]==city and old[5]==card.dest
            for k in ['id','name','lng','lat','bearing','height_m','district','stand_distance_m','heading','spawn','navigation']:
                assert entry.get(k)==old[3].get(k),k
            assert model['owner']==old[4]['owner']
        assert model['web_sha256']==rec.get('full',rec.get('web'))['sha256'] and model['lod_sha256']==rec['lod']['sha256']
        report['versions'][str(n)]={'base':base,'count':card.count,'city_directory_navigation':card.dest,'marker_unchanged_at':[entry['lng'],entry['lat']],'macro_owner':model['owner'],'bound_files':files,'saved_downloads':{r:saved(base,v) for r,v in rec.items()}}
    report['completed']=now();report['passed']=True;opt.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()

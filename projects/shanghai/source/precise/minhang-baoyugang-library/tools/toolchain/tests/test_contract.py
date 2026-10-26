"""Tiny policy controls; no architecture assets or acceptance records created."""
from pathlib import Path
import hashlib,json,sys,tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from modern_contract import bound,target,external_gltfpack

checks=[]
def rejected(name,fn):
    try:fn()
    except (ValueError,FileNotFoundError):checks.append({'name':name,'rejected':True})
    else:raise AssertionError(name+' unexpectedly passed')

with tempfile.TemporaryDirectory(prefix='modern-contract-small-controls-') as scratch:
    p=Path(scratch);f=p/'marker.txt';f.write_bytes(b'not-a-model\n')
    row={'source':str(f),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
    assert bound(row)==f
    rejected('100000000-byte equality exceeds strict limit',lambda:bound({**row,'bytes':100_000_000}))
    rejected('Zero-byte input is not a valid artifact',lambda:bound({**row,'bytes':0}))
    rejected('Changed bytes cannot reuse prior SHA',lambda:bound({**row,'sha256':'0'*64}))
    rejected('Malformed SHA rejected',lambda:bound({**row,'sha256':'pending'}))
    link=p/'link.txt';link.symlink_to(f)
    rejected('Symlink artifact rejected',lambda:bound({**row,'source':str(link)}))
    rejected('Missing actual descriptor rejected',lambda:bound(None))
    rejected('Unreviewed external packager rejected',lambda:external_gltfpack(p/'unknown-gltfpack'))
    for file in (Path(__file__).resolve().parents[1]/'targets').glob('*.pending.json'):
        rejected('Pending target '+file.name,lambda file=file:target(file))
print(json.dumps({'schema':'modern-package-small-policy-controls-v11','passed':True,'building_model_test':False,'checks':checks},indent=2))

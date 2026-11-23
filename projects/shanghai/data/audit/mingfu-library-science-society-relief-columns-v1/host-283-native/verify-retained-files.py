"""Verify the 81 restored Mingfu published files and the observed reopening against a project tree."""
from pathlib import Path
import argparse, hashlib, json
HERE=Path(__file__).resolve().parent
def read(name):return json.loads((HERE/name).read_bytes())
def digest(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(root):
    index=read('retained-source-index.json');certificate=read('native-closed.json')
    edit=read('verified-editable.json');total=0
    for row in index['files']:
        path=root/row['path'];assert path.stat().st_size==row['bytes'] and digest(path)==row['sha256'],path
        total+=row['bytes']
    assert certificate['passed']and certificate['all_processes_closed']and certificate['remaining']==[]
    assert all(i['exit']==0 and i['remaining']==[] for i in certificate['native_stages'])
    assert len({i['pid']for i in certificate['native_stages']})==2
    assert edit['match_raw']and digest(HERE/'verified-editable.json')==certificate['reopened_sha256']
    return dict(files=len(index['files']),total_bytes=total,mesh_groups=edit['mesh_count'],triangles=edit['triangles'],materials=edit['materials'],cameras=len(edit['hall_piers']['cameras']),uv_loops=edit['hall_piers']['uv_loops'],native_stages=len(certificate['native_stages']))
if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('repository',type=Path);a=cli.parse_args()
    print(json.dumps(main(a.repository),indent=2))

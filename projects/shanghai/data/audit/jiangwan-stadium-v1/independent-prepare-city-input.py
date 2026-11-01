"""Restore only the five immutable baseline city inputs for this candidate's review.
Usage: repository-root private-cache-directory. No remote fetch or source photo copying.
"""
from pathlib import Path
import hashlib,json,subprocess,sys
repo,out=map(Path,sys.argv[1:3]);here=Path(__file__).resolve().parent;record=json.loads((here/'independent-source-git-bindings.json').read_text());prior=json.loads((here/'independent-original-city-projection.json').read_text());out.mkdir(parents=True,exist_ok=True)
for row in record['records']:
 b=subprocess.check_output(['git','show',row['git_commit']+':'+row['repository_path']],cwd=repo)
 assert len(b)==row['bytes'] and hashlib.sha256(b).hexdigest()==row['sha256'];(out/row['private_file']).write_bytes(b)
(out/'initial-local-frame.json').write_text(json.dumps({'anchor':prior['frame']},indent=2)+'\n')
b=(here/'independent-display-mask-input.json').read_bytes();assert hashlib.sha256(b).hexdigest()==prior['bindings']['clip_preflight_sha256'];(out/'clip-preflight.json').write_bytes(b)
print('Restored five baseline city files and independently reviewed display-mask/frame inputs.')

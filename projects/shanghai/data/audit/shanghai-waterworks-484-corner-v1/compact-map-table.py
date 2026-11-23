"""Check all four Markdown cell values before reusing the compact row emitter."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime,timezone
import json,os,shutil
w=Path(__file__).parent
parent=Path('/tmp/puguangfront298')
child=Path('/tmp/waterworkscornerlog299')
project=Path('/workspace/e-resource')
path='projects/shanghai/tools/build_model_todo.py'
normal='| {cell(m[\'id\'])} | {cell(m[\'name\'])} | {cell(m[\'district\'])} | 核身份／去重／查建筑参考 |'
compact='|{cell(m[\'id\'])}|{cell(m[\'name\'])}|{cell(m[\'district\'])}|核身份／去重／查建筑参考|'
def sha(b):return sha256(b).hexdigest()
proof={}
for root in (parent,child,project):
 f=root/'README.md';text=f.read_text();rows=[q for q in text.splitlines()if q.lstrip().startswith('|') and q.rstrip().endswith('核身份／去重／查建筑参考 |')];new=['|'+'|'.join(cell.strip()for cell in row.split('|')[1:-1])+'|'for row in rows]
 a=[[c.strip()for c in row.split('|')[1:-1]]for row in rows];b=[row.split('|')[1:-1]for row in new]
 assert a==b and all(len(c)==4 for c in b) and len(rows)>900
 proof[str(root)]={'input_readme_sha256':sha(f.read_bytes()),'row_count':len(a),'cell_count':len(a)*4,'id_count':len({c[0]for c in a}),'before_normalized_sha256':sha(json.dumps(a,ensure_ascii=False).encode()),'after_normalized_sha256':sha(json.dumps(b,ensure_ascii=False).encode()),'saved_bytes':sum(len(x.encode())-len(y.encode())for x,y in zip(rows,new))}
assert os.path.samefile(child/path,parent/path)
old_parent=sha((parent/path).read_bytes())
for root in (child,project):
 f=root/path;old=f.read_text();assert old.count(normal)==1 and compact not in old
 backup=w/('child' if root==child else 'live');backup=backup.with_suffix('.original-build-todo.py')
 if not backup.exists():backup.write_bytes(f.read_bytes())
 before=sha(f.read_bytes());temp=f.with_name('.'+f.name+'.compact');temp.write_text(old.replace(normal,compact));shutil.copymode(f,temp);temp.replace(f)
 proof[str(root)].update(generator=f.as_posix(),previous_sha256=before,updated_sha256=sha(f.read_bytes()))
assert sha((parent/path).read_bytes())==old_parent and not os.path.samefile(child/path,parent/path)
(w/'readme-render-equivalence.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n');print(json.dumps(proof,ensure_ascii=False))

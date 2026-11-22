#!/usr/bin/env python3
"""Forward the normal Blender job with the Nanshi cameras and second-open verification."""
import json
import os
from pathlib import Path
import sys
from collections import Counter
from native_layout import ALIASES, SCHEDULE_SHA256, schedule_hash

def prepare_native(source):
    data=json.loads(source.read_bytes())
    metadata=data['metadata']
    rights={key:metadata[key] for key in ('geometry_license','copyright','third_party_materials')}
    os.environ['NANSHI_BANK_RIGHTS_JSON']=json.dumps(rights,ensure_ascii=False)
    groups=data['groups']
    by_group={}
    for name, geometry in groups.items():
        slots=geometry['materials']
        by_group[name]=Counter(slots[i] for i in geometry['face_materials'])
    assert schedule_hash(by_group)==SCHEDULE_SHA256
    assert {name for name in groups if len(name.encode())>63}==set(ALIASES)
    data['groups']={ALIASES.get(name,name):geometry for name,geometry in groups.items()}
    assert len(data['groups'])==len(groups)==196
    assert all(len(name.encode())<=63 for name in data['groups'])
    converted=source.with_name('bank-editable-parts.json')
    converted.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')))
    return converted

if __name__=='__main__':
    here=Path(__file__).resolve().parent
    args=sys.argv[1:]
    script=args.index('--python')
    sep=args.index('--')
    name=Path(args[script+1]).name
    if name=='make_native.py':
        args[sep+1]=str(prepare_native(Path(args[sep+1])))
        args[script:script]=['--python',str(here/'native_camera.py')]
    elif name=='verify_editable_model.py':
        args[sep:sep]=['--python',str(here/'verify_native_finish.py')]
    executable=os.environ['NANSHI_BANK_BLENDER']
    os.execvp(executable,[executable,*args])

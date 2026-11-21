"""Keep Blender object identifiers within its limit and preserve original group names."""
import os,sys,json
from pathlib import Path
args=sys.argv[1:]
for i,opt in enumerate(args[:-1]):
    if opt=='--threads':args[i+1]='1'
create=next((i for i,opt in enumerate(args[:-1])if opt=='--python' and Path(args[i+1]).name=='make_native.py'),None)
verify=any(opt=='--python' and Path(args[i+1]).name=='verify_editable_model.py'for i,opt in enumerate(args[:-1]))
here=Path(__file__).resolve().parent
if create is not None:
    position=args.index('--')+1
    original=Path(args[position])
    data=json.loads(original.read_bytes())
    groups={};full_names={}
    for name,parts in data['groups'].items():
        if len(name.encode())<=63:key=name
        else:
            family,detail=name.split('/',1)
            assert family=='Fifth Warehouse north elevation'
            key='Warehouse/'+detail
        assert len(key.encode())<=63 and key not in groups
        groups[key]=parts
        if key!=name:full_names[key]=name
    assert full_names
    data['groups']=groups
    fd=os.memfd_create('warehouse-groups-with-short-identifiers')
    os.set_inheritable(fd,True)
    with os.fdopen(fd,'w',closefd=False)as output:json.dump(data,output,separators=(',',':'))
    args[position]=f'/proc/{os.getpid()}/fd/{fd}'
    os.environ['WAREHOUSE_FULL_GROUP_LABELS']=json.dumps(full_names)
    args[create:create]=['--python',str(here/'remember-warehouse-labels.py')]
if verify:
    end=args.index('--');args[end:end]=['--python',str(here/'verify-warehouse-labels.py')]
blender = os.environ.get('FIFTH_WAREHOUSE_BLENDER', 'blender')
os.execvp(blender,[blender,*args])

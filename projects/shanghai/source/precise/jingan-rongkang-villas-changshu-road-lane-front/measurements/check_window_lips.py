"""Project both faces of the two cast lintels and two sills above the southern gate."""
from pathlib import Path
import hashlib,json,sys
import numpy as np

source=Path(sys.argv[1]);sys.path.insert(0,str(source))
from check_street_windows import acceleration,intersections,mesh,projector
output=Path(sys.argv[2]);paths=list(map(Path,sys.argv[3:]));table=json.loads((source/'street-window-openings.json').read_bytes())
record=json.loads((source/'south-inner-window-stations.json').read_bytes())
f=table['surfaces']['south-inner-return'];assert f['inward_sign']==-1
output.mkdir(exist_ok=True,parents=True);rows=[]
for path in paths:
    tri,ids,names,_,sha=mesh(path);rays=[]
    for station,cam in record['sources'].items():
        P=np.array(cam['local_xyz_to_image']);acc=acceleration(P,tri,ids)
        for o in table['openings']:
            if o['facade']!='south-inner-return' or station not in o['observed']:continue
            for label,d,z in [('sill',-.250,o['z0']-.045),('lintel',-.240,o['z1']+.045)]:
                for u in np.linspace(o['u0']+.08,o['u1']-.08,3):
                    front=f['frame_plane']+d*f['inward_sign']
                    xyz=(front,u,z);x,y,depth=projector(P,xyz);hits=intersections(acc,x,y)
                    own=next((v for v,i in hits if names[i]=='Rongkang | grey cast window surrounds'and abs(depth-v)<.014),None)
                    rays.append(dict(station=station,opening=o['id'],element=label,xyz=[round(float(v),4)for v in xyz],
                                     photo_px=[round(float(x),3),round(float(y),3)],hit=own is not None,
                                     depth_error_m=round(float(own-depth),5)if own is not None else None,
                                     first_surface=names[hits[0][1]] if hits else None,proud_of_wall_m=round(front-(-1.77),4)))
    rows.append(dict(file=path.name,sha256=sha,count=len(rays),hits=sum(q['hit']for q in rays),observations=rays))
p=output/'two-north-facing-sills-and-lintels.json';p.write_text(json.dumps(rows,indent=2)+'\n')
print([(r['count'],r['hits'])for r in rows],hashlib.sha256(p.read_bytes()).hexdigest())
assert all(r['count']==r['hits'] for r in rows)

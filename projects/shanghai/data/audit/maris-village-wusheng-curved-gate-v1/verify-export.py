"""Cast rays into the exported sign disks, gate leaves, masonry and adjoining railings."""
from pathlib import Path
import json,runpy,sys
import numpy as np
HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
SOURCE=PROJECT/'source/precise/huangpu-maris-village-wusheng-curved-gate'
sys.path.insert(0,str(SOURCE/'source'))
from photo_plane import position
from gate_leaves import MEMBERS
inspect=runpy.run_path(str(PROJECT/'data/audit/central-reserve-bank-changshu-front-v1/verify-export.py'))['inspect']

def cases():
    out=[]
    def ray(label, x,y,z, names, near,far, direction=(0,1,0)):
        out.append(dict(name=label,origin=[float(x),float(y),float(z)],direction=list(direction),
                        length=far+.01,allowed=names,range_m=[near,far] if names else None))
    gold=json.loads((SOURCE/'measurements/gilt-witnesses.json').read_bytes())['points']
    for i,point in enumerate(gold):
        u,v=point['detail_2021_px'];eye=position(u,v,-1.8);aim=position(u,v,.6)
        sight=aim-eye;sight/=np.linalg.norm(sight)
        names=['Black painted sign disks'] if point['expected']=='black' else ['Raised gilt letters','Shadowed gilt edges']
        ray('Sign evidence '+str(i+1),*eye,names,1.75,2.24,direction=sight)
    for name,(a,b),_,depth,kind in MEMBERS:
        x,z=.38*np.array(a)+.62*np.array(b)
        from_courtyard=name=='east shoulder rail'
        ray(name,x,.70 if from_courtyard else -.70,z,['Gate picket iron' if kind=='picket' else 'Gate frame iron'],
            .70-depth/2-.003,.70-depth/2+.003,(0,-1 if from_courtyard else 1,0))
    for label,z in [('lower gate clear opening',.322),('upper gate clear opening',1.63)]:
        for i,x in enumerate((-.8,.457,1.285)):
            if z==1.63 and i==0:
                ray('West notice holder obscures opening',x,-.35,z,['Pale notice backing'],.312,.317)
            else:
                ray(label+str(i),x,-.35,z,None,0,.65)
    for j in range(12):
        ray('Red brick facing '+str(j),1.738,-.6,.035+.13*j,['Weathered red facing brick'],.588,.595)
        ray('Visible vertical mortar joint '+str(j),1.787,-.6,.035+.13*j,['Buff brick mortar'],.601,.606)
    for j in range(6):
        ray('Left fence individual tile '+str(j),-2.07,-1.28,.037+j*.064,['Pale ceramic facing tile'],.343,.36)
    for i,z in enumerate((.15,1.5,2.11)):
        x=position(145,131,.035)[0]
        ray('Left gatepost from clear courtyard '+str(i),x,.27,z,['Painted iron entrance frame'],.198,.205,(0,-1,0))
    return out
if __name__=='__main__':
    files=list(map(Path,sys.argv[1:])); probes=cases()
    roles=['raw','full','lod'] if len(files)==4 else ['model']
    reports={r:inspect(f,probes)for r,f in zip(roles,files[:-1])}
    files[-1].write_text(json.dumps(reports,ensure_ascii=False,indent=1)+'\n')
    failures={k:[(v['name'],v['first_hit'] and (v['first_hit']['material'],v['first_hit']['distance_m'])) for v in val['cases'] if not v['passed']]for k,val in reports.items()}
    print(len(probes),failures);sys.exit(any(failures.values()))

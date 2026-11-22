"""Read each exported mesh and test the photographed bars, openings, grooves and enamel."""
from pathlib import Path
import json,sys,runpy
import numpy as np
from shapely.geometry import Polygon
HERE=Path(__file__).absolute().parent
P=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').exists())
SOURCE=P/'source/precise/huangpu-sinan-road-36-lattice-side-gate'
sys.path.insert(0,str(SOURCE/'source'))
sys.path.insert(0,str(P/'source/precise/hongkou-general-post-office/source/common'))
from photo_plane import position
from address_plaque import registration,project_poly,GREEN,WHITE,FINE
from iron_panel import MEASURED_SECTIONS,IRON
from piers import PIERS,SHADOW,FACE_Y
inspect=runpy.run_path(str(P/'data/audit/central-reserve-bank-changshu-front-v1/verify-export.py'))['inspect']
def cases():
    probes=[]
    def add(name,x,z,materials):
        probes.append(dict(name=name,origin=[float(x),-1.7,float(z)],direction=[0,1,0],length=2.4,allowed=materials,range_m=None))
    def sample(name,u,v,y,materials):
        x,_,z=position(u,v,y)
        add(name,x,z,materials)
    for name,_,coords,width,thickness in MEASURED_SECTIONS:
        # Use each visible segment's longest sub-run. Stay off the two ends
        # where the section is received in masonry or partly behind the sign.
        v=np.array(coords);lines=v[1:]-v[:-1];j=np.argmax(np.linalg.norm(lines,axis=1))
        u,w=v[j]+.52*lines[j]
        if name=='right fan 5 visible 1':
            sample(name+' notice occlusion',u,w,0.,['Pale removable notice','Weathered notice edging'])
            x,_,z=position(u,w)
            probes.append(dict(name=name+' behind notice',origin=[float(x),-.023,float(z)],direction=[0,1,0],length=.2,allowed=[IRON],range_m=None))
        else:
            sample(name,u,w,0.,[IRON])
    for i,(u,v) in enumerate([(222,350),(240,329),(460,346),(510,366),(360,273),(347,237),(325,309),(380,313),(220,499),(222,551),(477,464),(504,440)]):
        sample('open lattice '+str(i),u,v,0.,None)
    for p in PIERS:
        for i,(top,foot) in enumerate(p['flutes']):
            a=position(*top,FACE_Y);b=position(*foot,FACE_Y)
            for k in [.26,.61,.83]:
                x,_,z=(1-k)*a+k*b;add(p['name']+' incised line '+str(i)+' '+str(k),x,z,[SHADOW])
    data,H=registration()
    for label,groups in data['groups'].items():
        for j,group in enumerate(groups):
            poly=Polygon(group['shell'],group['holes'])
            pt=project_poly(poly,H).representative_point()
            add('sign '+label+' '+str(j),pt.x,pt.y,[WHITE,FINE])
    for i,(u,v) in enumerate([(.1,.2),(.11,.48),(.92,.12),(.9,.89),(.15,.88)]):
        q=H@[u,v,1];add('green enamel '+str(i),q[0]/q[2],q[1]/q[2],[GREEN])
    return probes
if __name__=='__main__':
    args=list(map(Path,sys.argv[1:]));roles=['raw','full','lod'] if len(args)==4 else ['model']
    reports={k:inspect(mesh,cases())for k,mesh in zip(roles,args[:-1])}
    args[-1].write_text(json.dumps(reports,ensure_ascii=False,indent=1)+'\n')
    bad={k:[(x['name'],x['first_hit']and x['first_hit']['material']) for x in v['cases'] if not x['passed']]for k,v in reports.items()}
    print(len(cases()),bad);sys.exit(int(any(bad.values())))

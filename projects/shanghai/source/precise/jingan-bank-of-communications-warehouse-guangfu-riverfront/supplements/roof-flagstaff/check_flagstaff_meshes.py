"""Check both named, closed meshes, independent decoding and their contact with the published roof."""
from collections import Counter
import argparse,json,struct,sys
from hashlib import sha256
from pathlib import Path
import numpy as np
from roof_flagstaff import STEEL,STONE,DECK,AXIS,TIP

def examine(project,meshes,house):
    sys.path.insert(0,str(project/'source/precise/xuhui-pathe-records-office/measurements/city-contact'))
    from glb_triangles import SerialScene,load_triangles
    reports=[]
    for f,old in zip(meshes,house,strict=True):
        buf=f.read_bytes();n=struct.unpack_from('<I',buf,12)[0];gl=json.loads(buf[20:20+n])
        names={n['name']for n in gl['nodes'] if 'mesh' in n}
        assert names=={'Flagstaff | tapered metal shaft','Flagstaff | foot block'},names
        tris,ids,labels,asset=load_triangles(f)
        groups=[]
        for index,material in enumerate(labels):
            tri=tris[ids==index]
            if not len(tri):continue
            centred=tri-tri.reshape(-1,3).mean(0)
            volume=float(np.sum(centred[:,0]*np.cross(centred[:,1],centred[:,2]))/6)
            coords=np.unique(tri.reshape(-1,3).round(6),axis=0,return_inverse=True)[1].reshape(-1,3)
            edges=Counter((int(a),int(b))for row in coords for a,b in zip(row,np.roll(row,-1)))
            assert len(edges)>10 and all(a!=b and v==edges[b,a]==1 for (a,b),v in edges.items())
            assert volume>0
            groups.append(dict(material=material,triangles=len(tri),outward_volume_m3=volume))
        s=SerialScene(f);base=SerialScene(old)
        hits=[]
        def check(scene,origin,direction,expected,length,coord=None):
            v=scene.ray(origin,direction,length);assert v and v['material']==expected,(origin,v)
            if coord is not None:assert abs(v['point_enu_m'][2]-coord)<.001
            hits.append(dict(origin=list(origin),direction=list(direction),first=v))
        for x,y in [AXIS,(-.27,.97),(-.27,1.29),(.13,.97),(.13,1.29)]:check(base,[x,y,30.],[0,0,-1],'Guanger terrace | jointed stone paving',18.,DECK)
        check(s,[*AXIS,30.],[0,0,-1],STEEL,14.,TIP)
        for z in [18.7,20.,23.,25.,26.8]:
            for dx,dy in [(1,0),(0,1),(-1,0),(0,-1)]:
                check(s,[AXIS[0]-.5*dx,AXIS[1]-.5*dy,z],[dx,dy,0],STEEL,1.)
        for x,y in [(-.24,1.),(-.23,1.25),(.09,1.25)]: check(s,[x,y,19.],[0,0,-1],STONE,1.0,DECK+.20)
        reports.append(dict(asset=asset,published_building_sha256=sha256(old.read_bytes()).hexdigest(),editable_nodes=sorted(names),groups=groups,hits=hits,checks=len(hits)))
    return reports

if __name__=='__main__':
    q=argparse.ArgumentParser(description=__doc__);q.add_argument('project',type=Path);q.add_argument('output',type=Path);q.add_argument('--meshes',nargs=3,type=Path,required=True);q.add_argument('--house',nargs=3,type=Path,required=True);a=q.parse_args()
    a.output.write_text(json.dumps({'passed':True,'variants':examine(a.project,a.meshes,a.house)},indent=2)+'\n')

"""Trace garden-elevation picture samples and test each editable ornament shell.

Run from projects/shanghai or specify its absolute path with --project.
"""
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import sys
import runpy
import numpy as np

def try_scene(project):
    return runpy.run_path(project/'data/audit/postal-office-v1/independent-glb-review-helpers.py')['SerialScene']

def photo_sites(f,o):
    sets=[
      ('west brick field', f.GRAY, [(405,412),(527,424),(667,424),(817,426)]),
      ('west glass',o.GLASS,[(580,424),(599,422),(616,419)]),
      ('west glazing bars',o.LEAD,[(589,420),(607,419),(600,399)]),
      ('east brick field',f.GRAY,[(1718,475),(1804,463),(1872,388),(1980,475)]),
      ('east plaque ground',f.STONE,[(1848,432),(1889,436)]),
      ('east plaque projecting frame',f.STONE,[(1834,451),(1902,447),(1867,478)]),
      ('east relief',o.PALE,[(1870,458),(1872,456),(1884,465),(1857,463)]),
      ('frieze ground',f.STONE,[(1841,503),(1875,505)]),
      ('stone brackets',f.STONE,[(489,414),(710,421),(1789,459),(1944,467)]),
      ('rail posts',f.GRAY,[(951,435),(1209,443)]),
      ('handrail',f.STONE,[(1024,408),(1151,415),(1303,425),(1424,433)]),
      ('stone stems',f.STONE,[(u,o.at([(968,403),(1199,415)],u)+21) for u in o.BOTTLES[0]]
                      +[(u,o.at([(1226,418),(1444,429)],u)+21) for u in o.BOTTLES[1]]),
      ('open gaps','open railing',[(1001,433),(1064,439),(1129,442),(1255,447),(1376,455),(1422,452)]),
      ('wood knee',o.WOOD,[(467,538),(648,540),(673,545),(854,547)]),
      ('wood canopy beam',o.WOOD,[(466,509),(579,512),(715,516),(827,520)]),
      ('metal posts',o.IRON,[(455,621),(661,630),(867,646)]),
      ('balcony handrail',o.WOOD,[(496,661),(620,666),(743,670),(816,672)]),
      ('balcony railing',o.IRON,[(453+14.1*i,703) for i in (5,9,12,17,19,22,24,27)]),
    ]
    return [(group,mat,(float(x),float(y))) for group,mat,coords in sets for x,y in coords]

def trace(path,scene_type,f,o):
    scene=scene_type(path)
    eye=o.balcony_eye(f.metric)
    rows=[]
    for group,mat,uv in photo_sites(f,o):
        x,z=f.metric(*uv)
        if group in ('wood knee','wood canopy beam','metal posts','balcony handrail','balcony railing'):
            hit=scene.ray(eye,np.array([x,0.,z])-eye,120.)
        else:
            hit=scene.ray(np.array([x,-6.,z]),np.array([0.,1.,0.]),90.)
        actual=hit['material'] if hit else None
        if mat=='open railing':
            ok=not hit or 'turned baluster' not in hit.get('node','') and actual!=f.STONE
        elif group=='stone brackets':ok=actual in (f.STONE,o.PALE)
        else:ok=actual==mat
        rows.append(dict(group=group,photo_pixel=list(uv),allowed=mat,first_hit=hit,passed=bool(ok)))
    # The two return rails are seen edge-on in a front elevation. Sideways
    # virtual sections check that all six return pickets actually fill the depth.
    section=[]
    def xyz(u,v,y):
        x,z=f.metric(u,v);q=np.array([x,0.,z]);return q+(eye-q)*(y/eye[1])
    for side,u,vt,vb in [('west',455,659,755),('east',867,673,767)]:
        xt,_,zt=xyz(u,vt,-.87);_,_,zb=xyz(u,vb,-.87);direction=-1 if side=='east' else 1
        for d in (-.66,-.44,-.22):
            start=np.array([xt-.15*direction,d,.52*zt+.48*zb])
            hit=scene.ray(start,np.array([float(direction),0.,0.]),.25)
            section.append({'feature':side+' return picket','y':d,'hit':hit,'passed':bool(hit and hit['material']==o.IRON)})
    def vertical(name,uv,front,y,allowed):
        x,_,z=xyz(*uv,front);hit=scene.ray(np.array([x,y,z+.18]),np.array([0.,0.,-1.]),.37)
        section.append({'feature':name,'y':y,'hit':hit,'passed':bool(hit and hit['material'] in allowed)})
    for d in [-.77,-.45,-.18]:
        vertical('balcony floor',(633,761.1),-.945,d,[f.STONE])
        vertical('balcony canopy',(633,508.5),-.993,d,[o.IRON,o.WOOD])
    return dict(file=path.name,sha256=sha256(path.read_bytes()).hexdigest(),passed=sum(i['passed'] for i in rows),total=len(rows),observations=rows,
                section_passed=sum(i['passed']for i in section),section_total=len(section),section=section)

def topology(f,o,lod):
    b=f.NanlinBuilder(dict(f.PALETTE));o.add_ornaments(b,lod,f.metric)
    low=float('inf'); counts=Counter();edges_bad=[];mid=[];tri=0
    for part in b.parts:
        v=np.array(part['vertices']);t=np.array(part['triangles']);tri+=len(t)
        _,inv=np.unique(np.round(v,7),axis=0,return_inverse=True)
        directed=Counter(tuple(e) for tt in inv[t] for e in zip(tt,np.roll(tt,-1)))
        xyz=v[t];vol=np.einsum('ij,ij->i',xyz[:,0],np.cross(xyz[:,1],xyz[:,2])).sum()/6
        low=min(low,vol)
        if vol<=0 or not all(directed[e]==1 and directed[e[::-1]]==1 for e in directed):edges_bad.append(part['label'])
        counts[part['material']]+=1
        if 'turned baluster' in part['label']:mid.append(part['label'])
    assert len(mid)==28
    assert not edges_bad,edges_bad
    return dict(editable_parts=len(b.parts),faces=tri,closed_positive=len(b.parts),minimum_volume_m3=low,material_meshes=counts,
                balusters=len(mid))

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--project',type=Path,default=Path.cwd());ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('roles',nargs='+',type=Path);args=ap.parse_args()
    p=args.project.resolve();sys.path.insert(0,str(Path(__file__).absolute().parent.parent/'source'))
    import fabric as f
    import nanlin_ornaments as o
    scene=try_scene(p)
    rows=[trace(role,scene,f,o)for role in args.roles]
    doc=dict(source='Fayhoo, Nanlinshifanxuexiao Jiuzhi.JPG, native 2144 × 1424',projection='Facade chart with facade-normal rays on the parapets. Balcony rays are oblique from the 27-mm-equivalent photo pose fitted to the same chart; the 0.85 m projection is estimated.',
        native={k:topology(f,o,lod)for k,lod in [('near',False),('far',True)]},roles=rows)
    args.output.parent.mkdir(parents=True,exist_ok=True);temporary=args.output.with_suffix('.tmp');temporary.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n');temporary.replace(args.output)
    for row in rows:
        print(row['file'],row['passed'],row['total'],row['section_passed'],row['section_total'],[(v['group'],v['photo_pixel'],v['first_hit']['material']if v['first_hit']else None)for v in row['observations']if not v['passed']])

if __name__=='__main__':
    main()

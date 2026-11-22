"""Measure the partial cut and each actual near/far roof section where the portico joins the retained original."""
from pathlib import Path
import json, runpy
import numpy as np
import shapely as g
from shapely.geometry import Polygon, LineString, mapping

w=Path(__file__).resolve().parent
src=runpy.run_path(str(w/'decode-source.py'))
frame=src['cfg']; anchor=src['anchor']; axes=src['axes']; rad=src['rad']; t0=src['t0']
def geographic(coords):
    east,north=(coords@axes).T
    return np.column_stack((anchor['lng']+np.degrees(east/rad),np.degrees(np.arctan(np.sinh(t0+north/rad)))))
mask=Polygon([(-5.55,-.89),(5.55,-.89),(5.55,2.30),(5.34,2.30),(5.34,4.30),(.75,4.30),(.75,4.60),(-.75,4.60),(-.75,4.30),(-5.34,4.30),(-5.34,2.30),(-5.55,2.30)])
by_role={}; neighbors={}; proof=[]
for group in frame['groups']:
    for role,t,owners,gap in src['decode'](group):
        for who in set([1292,*frame['checked_neighbors']]).intersection(group['owners']):
            cells=t[owners==who]; highest=float(cells[:,:,2].max()); top=cells[cells[:,:,2].min(axis=1)>highest-.15]
            roof=g.make_valid(g.union_all(g.polygons(top[:,:,:2]))); inside=roof.intersection(mask)
            if who!=1292:
                assert inside.area<1e-7 and mask.distance(src['polygons'][who])>0
                neighbors.setdefault(str(who),{})[role]=dict(count=len(cells),height=highest,area=roof.area,retained=roof.difference(mask).area,removed=inside.area,gap_m=roof.distance(mask),group=group['file'],group_sha256=group['sha256'])
                continue
            assert 43<inside.area<50 and roof.difference(mask).area>510 and abs(highest-29.5)<.03
            sidepieces=[]
            for a,b in zip(mask.exterior.coords, list(mask.exterior.coords)[1:]):
                side=LineString([a,b]).intersection(roof)
                for line in g.get_parts(side):
                    if line.geom_type=='LineString' and line.length>1e-4:sidepieces.append(list(line.simplify(1e-5).coords))
            assert len(sidepieces)==11,(role,len(sidepieces),sidepieces)
            by_role[role]=dict(source_m2=roof.area,removed_m2=inside.area,retained_m2=roof.difference(mask).area,height=highest,triangles=len(cells),seams=sidepieces)
        proof.append(dict(group=group['file'],role=role,source_sha256=group['sha256'],decoded_triangles=len(t),minimum_source_owner_assignment_gap=gap))
assert len(neighbors)==13 and all(len(z)==2 for z in neighbors.values()) and set(by_role)=={'near','far'}
result=dict(owner=1292,macro='14-13719-6694',cut_local=mapping(mask),cut_wgs=mapping(g.transform(mask,geographic)),geometry=by_role,other_owners=neighbors,groups=proof,scope='真实台阶半宽5.530米，至两侧短返面2.276米。较窄檐侧后退到4.30米。仅在开启的中央门扇后方保留宽1.50米、深0.30米的额外净空。其余原屋保留。')
(w/'proposed-source-cut.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print('326',['%s %s %s'%(role,round(r['removed_m2'],5),len(r['seams'])) for role,r in by_role.items()])

"""Intersect rays with actual meshes and project their outer cornice arrises into the source photograph."""
from pathlib import Path
import json,runpy,sys
import numpy as np
HERE=Path(__file__).absolute().parent
P=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').exists())
SOURCE=P/'source/precise/huangpu-jiangxi-320-paired-pediment-windows'
sys.path.insert(0,str(SOURCE/'source'))
from photo_plane import H,D,CROP,WIDTH,HEIGHT,position,pixel,upright
lib=runpy.run_path(str(P/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))
inspect=runpy.run_path(str(P/'data/audit/central-reserve-bank-changshu-front-v1/verify-export.py'))['inspect']
survey=json.loads((SOURCE/'measurements/observed-raking-edges.json').read_bytes())
STONE='Pale carved limestone';LIGHT='Cream arris';SHADE='Weathered moulding return';GLASS=['Charcoal grey glass','Grey blue reflection','Warm smoky glass']
def cases():
    out=[]
    camera=np.linalg.solve(np.column_stack([H[:,0],D,H[:,1]]),-H[:,2])
    def shot(label,u,v,materials):
        pt=position(u,v,0);ray=pt-camera;ray/=np.linalg.norm(ray)
        out.append(dict(name=label,origin=camera.tolist(),direction=ray.tolist(),length=80,allowed=materials,range_m=None))
    for bay,coords in [('left',[(166,457),(153,372),(151,430),(113,548),(176,630),(194,767),(151,885)]),
                       ('right',[(409,319),(421,222),(408,275),(380,407),(419,486),(458,670),(440,779)])]:
        for tag,pt,allowed in zip(['console','tympanum','console top','awning','upper light','lower light','sill'],coords,
                                 [[STONE,LIGHT],[STONE,SHADE,LIGHT],[STONE,LIGHT],['Dusty blue awning stripe','Dark canvas hem'],GLASS,GLASS,['Cut stone sill','Cream arris']]):
            shot(bay+' '+tag,*pt,allowed)
    for side,x,lo,hi,alts in [('left outer',69,605,737,['Dusty blue awning stripe','Warm flax awning stripe']),('left inner',225,539,657,['Dusty blue awning stripe','Warm flax awning stripe']),('right outer',315,484,626,['Dusty blue awning stripe','Warm flax awning stripe']),('right inner',506,378,526,['Dusty blue awning stripe','Warm flax awning stripe'])]:
        for v in np.linspace(lo,hi,8):shot(side+' woven return '+str(round(v)),x,float(v),alts)
    for i,z in enumerate(np.linspace(-.22,3.9,16)):
        for x in (-2.06,2.06):
            out.append(dict(name='outer masonry '+str(x)+' '+str(i+1),origin=[x,-2,float(z)],direction=[0,1,0],length=5,allowed=['Warm grey lime render','Lime joint'],range_m=[1.98,2.02]))
    for j,(x,z) in enumerate([(-2.24,2.8),(2.26,2.64),(-1.2,4.23),(1.1,4.31),(-.6,-.6),(.92,-.62)]):
        out.append(dict(name='open space '+str(j+1),origin=[x,-2,z],direction=[0,1,0],length=4,allowed=None,range_m=None))
    return out
def edges(mesh):
    tri,ids,names,rec=lib['load_triangles'](mesh)
    # Standalone outer raking lips have a 60 mm setback on their exterior edge.
    take=(np.array(names)[ids]==STONE)&np.isclose(tri[:,:,1],-.06,atol=2e-5).sum(axis=1).__eq__(2)
    lines=[]
    for t in tri[take]:
        a,b=t[np.isclose(t[:,1],-.06,atol=2e-5)]
        lines.append(np.array([upright(*pixel(a)),upright(*pixel(b))]))
    assert len(lines)>=4
    result=[]
    for s in survey['held_out_edge_stations']:
        if not s['accepted']:continue
        target=np.array(s['xy']);dist=[]
        for a,b in lines:
            d=b-a;t=np.dot(target-a,d)/np.dot(d,d)
            if 0<t<1:dist.append(np.linalg.norm(target-(a+t*d)))
        result.append({**s,'mesh_distance_px':float(min(dist))})
    residual=np.array([r['mesh_distance_px'] for r in result])
    return dict(count=len(result),median_px=float(np.median(residual)),p95_px=float(np.percentile(residual,95)),maximum_px=float(residual.max()),stations=result)
if __name__=='__main__':
    args=list(map(Path,sys.argv[1:]));roles=['raw','full','lod'] if len(args)==4 else ['model'];out={}
    for name,m in zip(roles,args[:-1]):
        r=inspect(m,cases());r['rake_edges']=edges(m);r['passed'] &= r['rake_edges']['p95_px']<10
        out[name]=r;print(name,'triangles',r['triangles'],'edges',r['rake_edges']['median_px'],r['rake_edges']['p95_px'],[(i['name'],i['first_hit'] and i['first_hit']['material']) for i in r['cases'] if not i['passed']])
    args[-1].write_text(json.dumps(out,indent=1)+'\n')
    sys.exit(int(not all(r['passed'] for r in out.values())))

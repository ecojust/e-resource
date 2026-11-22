"""Check the geometry produced from all separately recorded clear openings."""
import hashlib
import gzip
import json
import sys
from pathlib import Path
import numpy as np

project = Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
outdir = Path(sys.argv[2]).resolve() if len(sys.argv)>2 else project.parents[2]/'data/audit/nanyang-continental-court-street-front-v1/sashes'
outdir.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(project/'source'))
import continental_window_sashes as window

schedule = json.loads((project/'measurements/street-window-schedule.json').read_text())
layout = json.loads((project/'measurements/street-frontage-layout.json').read_text())


class Mesh:
    def __init__(self):
        self.parts=[]
    def add(self, verts, polygons, material, label):
        xyz = np.array(verts, dtype=float)
        tri = np.array([(f[0], f[j], f[j+1]) for f in polygons for j in range(1,len(f)-1)])
        assert np.all(np.isfinite(xyz))
        self.parts.append(dict(vertices=xyz, triangles=tri, material=material, label=label))


cell_checks=[]

def check_mesh(mesh,coarse):
    tri_count = 0
    for part in mesh.parts:
        v, tri = part['vertices'], part['triangles']
        uv = np.array(part['texcoords'])
        assert len(v) == len(uv) and np.isfinite(uv).all()
        ab = uv[tri[:,1]]-uv[tri[:,0]]
        ac = uv[tri[:,2]]-uv[tri[:,0]]
        assert np.abs(ab[:,0]*ac[:,1]-ab[:,1]*ac[:,0]).min()>1e-8
        edges = np.sort(tri[:,[[0,1],[1,2],[2,0]]].reshape(-1,2),axis=1)
        assert (np.unique(edges, axis=0,return_counts=True)[1]==2).all()
        assert len(v)%8==0
        volumes=[]
        for k in range(len(v)//8):
            pts = v[k*8:k*8+8,:]
            s = tri[k*12:k*12+12] - k*8
            pa,pb,pc=(pts-pts.mean(axis=0))[s].transpose((1,0,2))
            signed_volume=float(np.einsum('ij,ij->i',pa,np.cross(pb,pc)).sum()/6)
            assert signed_volume>0 and set(np.unique(s))==set(range(8))
            directed=s[:,[[0,1],[1,2],[2,0]]].reshape(-1,2)
            as_edges=set(map(tuple,directed))
            assert len(as_edges)==36 and all((j,i) in as_edges for i,j in as_edges)
            volumes.append(round(signed_volume,11))
        cell_checks.append([coarse,part['label'],part['material'],len(volumes),volumes])
        tri_count += len(tri)
    return tri_count


def cast(mesh, x, z):
    """Orthographic first intersection from the street with actual triangles."""
    hits=[]
    for p in mesh.parts:
        v=p['vertices'][p['triangles']]
        a,b,c=v.transpose(1,0,2)
        ab=b-a; ac=c-a
        den=ab[:,0]*ac[:,2]-ab[:,2]*ac[:,0]
        valid=abs(den)>1e-12
        ab,ac,a,den=ab[valid],ac[valid],a[valid],den[valid]
        u=((x-a[:,0])*ac[:,2]-(z-a[:,2])*ac[:,0])/den
        w=(ab[:,0]*(z-a[:,2])-ab[:,2]*(x-a[:,0]))/den
        use=(u>=-1e-8)&(w>=-1e-8)&(u+w<=1+1e-8)
        if use.any():
            hits.append((float((a[:,1]+u*ab[:,1]+w*ac[:,1])[use].min()),p['label'],p['material']))
    return min(hits) if hits else None


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


# A few definite boundaries measured in the 55 px/m orthorectification of
# Gao08. The three fixed cross-rail heights and bar counts are an external
# comparison with the original independent photo, not generated mesh samples.
photo_edges=[
    (7,4,0, (67,203,125,296),243,4,4),
    (7,3,0, (66,435,119,539),475,4,4),
    (7,3,1, (173,435,224,538),462,2,4),
    (7,2,0, (67,666,122,771),701,4,4),
]
trace=[]
summary=[]
read_edges=[]
for coarse in (False,True):
    totals=dict(physical_openings=0,groups=0,triangles=0,ray_tests=0,glass_uv_vertices=0)
    for row in schedule['bays']:
        bay=row['bay']
        for fl in row['floors']:
            floor=fl['floor']
            low,high=fl['sill_z'],fl['head_z']
            for index,(a,b) in enumerate(fl['openings_u_m']):
                mesh=Mesh();args={'strip_index':index} if bay in (0,5,10) else {}
                d=fl['sash_recess_m']+fl['face_depth_m']
                window.add_sash(mesh,coarse,lambda x,y,z:(x,y,z),bay,floor,index,a,b,low,high,d,**args)
                totals['physical_openings']+=1
                totals['groups']+=len(mesh.parts)
                totals['triangles']+=check_mesh(mesh,coarse)
                totals['glass_uv_vertices']+=sum(len(p['texcoords']) for p in mesh.parts if p['material'] in (window.GREY_GLASS,window.LIGHT_GLASS,window.DARK_GLASS))
                def at(x,z):
                    hit=cast(mesh,x,z)
                    trace.append([coarse,bay,floor,index,round(x,6),round(z,6),None if hit is None else [round(hit[0],6),hit[1],hit[2]]])
                    return hit
                for x,z in ((a+.024,low+.257),(b-.024,high-.34),(a+(b-a)*.44,high-.019),(a+(b-a)*.37,low+.026)):
                    j=at(x,z);assert j is not None and 'fixed jamb and head' in j[1], (bay,floor,index,x,z,j)
                    assert abs(j[0]-d)<1e-8
                # Nothing asserts the stone pier's position by occlusion here:
                # a probe above/below the sash must pass, including at open leaves.
                for x,z in ((a+.12,high+.055),(b-.12,low-.055)):
                    assert at(x,z) is None
                totals['ray_tests']+=6
                if (bay,floor,index)==(7,4,0):
                    for s in (.44,.56):
                        h=at(a+(b-a)*s,low+.43*(high-low))
                        assert h is None, h
                    h=at((a+b)/2,low+.43*(high-low))
                    assert h is not None and 'fixed interior centre stile' in h[1]
                    totals['ray_tests']+=3
                for eb,ef,ei,box,rail,cols,rows in photo_edges:
                    if (eb,ef,ei)!=(bay,floor,index):continue
                    x0,y0,x1,y1=box
                    predicted=[]
                    for t in np.arange(.50,.81,.002):
                        q=at(a+(b-a)*.31,low+(high-low)*t)
                        if q is not None and q[1].endswith('transom rail'):predicted.append(t)
                    assert predicted
                    fraction=float(np.mean(predicted))
                    err=float(abs((y1-fraction*(y1-y0))-rail))
                    assert err<3.6,(bay,floor,index,err)
                    groups=[p for p in mesh.parts if p['label'].endswith('lower leaf 1 glazing') or p['label'].endswith('lower leaf 2 glazing')]
                    assert len(groups)==2
                    if not coarse:assert sum(len(p['vertices'])//8 for p in groups)==cols*rows
                    if not coarse:read_edges.append(dict(bay=bay,storey=floor,opening=index,source='Gao08 orthorectified street-camera-plan at 55px/m',window_box_px=box,transom_y_px=rail,lower_columns=cols,lower_rows=rows,model_height_fraction=round(fraction,3),rail_difference_px=round(err,3)))
                    totals['ray_tests']+=len(np.arange(.50,.81,.002))
            if bay in (0,5,10):
                # Test the public broad-opening API and both masonry intervals.
                (a,b),(c,d),(e,f)=fl['openings_u_m']
                m=Mesh();window.add_sash(m,coarse,lambda x,y,z:(x,y,z),bay,floor,0,a,f,low,high,fl['sash_recess_m'],stone_mullions=((b,c),(d,e)))
                for x in ((b+c)/2,(d+e)/2):
                    assert cast(m,x,low+.83) is None
                    trace.append([coarse,bay,floor,'between',round(x,6),round(low+.83,6),None])
                totals['ray_tests']+=2
    assert totals['physical_openings']==75
    summary.append(dict(lod='distant' if coarse else 'near',**totals))
out=dict(source='continental_window_sashes.py',source_sha256=digest(project/'source/continental_window_sashes.py'),texture_sha256=digest(project/'source/window-glazing.png'),schedule_sha256=digest(project/'measurements/street-window-schedule.json'),scope='Window components in actual recorded clear openings. Parent wall, stone, and awnings are separate.',external_reference=read_edges,results=summary)
assert len(trace)==sum(item['ray_tests'] for item in summary)
out['edit_group_solids']={name:dict(groups=len(rows),closed_positive_solids=sum(r[3] for r in rows),min_volume_m3=min(min(r[4])for r in rows),max_volume_m3=max(max(r[4])for r in rows))for name,rows in [(level,[r for r in cell_checks if r[0]==coarse]) for level,coarse in [('near',False),('distant',True)]]}
out['solid_fields']=['distant','edit_group','material','independent_solids','solid_volumes_m3']
out['component_joinery']='The editable frames collect individually closed steel sections. Contact faces at butt joints are preserved as the mating faces of separate pieces. For each eight-vertex solid, each directed triangle edge is paired with its reverse.'
(outdir/'window-frame-group-solids.json.gz').write_bytes(gzip.compress(json.dumps(cell_checks,separators=(',',':')).encode(),mtime=0))
out['rays_fields']=['distant','bay','floor','opening','u_m','z_m','first_hit_depth_m_group_material']
(outdir/'local-sash-rays.json.gz').write_bytes(gzip.compress(json.dumps(trace,separators=(',',':')).encode(),mtime=0))
(outdir/'whole-street-geometry-check.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(summary),flush=True)

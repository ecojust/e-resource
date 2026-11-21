"""Probe the serialized corner crown, glazing, 48 Gaoan entrance and unobstructed street."""
from pathlib import Path
import argparse, hashlib, json, runpy
import numpy as np

def check(scene):
    # Recover the three independent street axes from the calibrated frozen ring.
    coords=np.array([[ -36.90109165, 37.99145046],[-4.12140754,-.44],[4.12140754,-.44],[7.322,17.916]])
    ux=(np.array([11.41717174,40.83301115])-np.array([4.12140754,0]))
    coords[-1]=[4.12140754,0]+18.2*ux/np.linalg.norm(ux)
    segments=[]
    for a,b in zip(coords,coords[1:]):
        along=(b-a)/np.linalg.norm(b-a)
        outward=np.array([along[1],-along[0]])
        segments.append(((a+b)/2,along,outward,np.linalg.norm(b-a)))
    def loc(face,s):
        length=segments[face][3]
        return length/2-s if face==0 else s-length/2 if face==2 else s
    results=[]
    def test(name,origin,dir,length,materials,distance,tol=.04):
        hit=scene.ray(origin,dir,length)
        if materials is None:
            assert hit is None,(name,hit)
        else:
            assert hit and hit['material'] in materials and abs(hit['distance_m']-distance)<tol,(name,origin,hit,materials,distance,tol)
        results.append(dict(feature=name,origin_m=origin,direction=dir,maximum_distance_m=length,first_hit=hit))
    def probe(name,f,s,z,offset,material,delta=0,span=6,tol=.04):
        c,t,n,_=segments[f];point=c+(loc(f,s)+delta)*t+5*n
        test(name,[*point,z],[*-n,0],span,{material},5-offset,tol)
    gl='blue gray street glazing';frame='dark painted window frames';wall='warm ochre roughcast';ivory='ivory cement'
    for f,s in [(0,5.59),(0,12.86),(0,26.98),(0,35.82),(2,5.64),(1,0)]:
        depth=.67 if f==1 else .62
        for storey in (0,3,7):
            z=4.64+2.98*storey
            probe('projected centre pane',f,s,z+.36,depth+.055-.204,gl,.18)
            probe('projected centre mullion',f,s,z+.36,depth+.055-.103,frame)
            probe('solid bay apron',f,s,z-.22,depth,wall,.12)
        for storey in (8,9):
            probe('two flat upper-storey windows',f,s,4.64+2.98*storey+.31,-.204,gl,.14)
    for f,s,width,depth in [(0,5.59,2.28,.62),(0,26.98,2.28,.62),(1,0,2.81,.67),(2,5.64,2.28,.62)]:
        c,t,n,_=segments[f];base=c+loc(f,s)*t
        # Probe perpendicular to both splayed lights. The short start distance keeps
        # each ray in front of this facet, without cutting through an adjacent bay.
        for sign in (-1,1):
            outer=base+sign*t*width/2-.085*n
            inner=base+sign*t*width*(.5-.19)+depth*n
            along=inner-outer;out=np.array([along[1],-along[0]])/np.linalg.norm(along)
            if np.dot(out,n)<0:out=-out
            origin=(outer+inner)/2+.14*out
            test('inclined side pane of three-plane oriel',[*origin,5.11],[*-out,0],.70,{gl},.14+.204-.055)
    for f,s in [(0,2.32),(0,16.42),(0,42.25),(2,2.29),(2,9.00),(1,-2.91),(1,2.91)]:
        for storey in (1,9):
            depth=.62+.055-.204 if s==42.25 and storey<8 else -.204
            probe('alternating wing sash or narrow corner light',f,s,4.98+2.98*storey,depth,gl,.14)
    for s in (-2.78,0,2.78):
        probe('three glazed corner shopfront bays',1,s,1.40,-.204,'shop glazing',.21)
    for s in (0,.476,-.952,1.428,-1.904):
        probe('stepped crown rises above wing parapet',1,s,33.74+.48,.25,ivory,.136)
    for side in (-1,1):
        probe('closed deep green leaf at back of entry',0,31.35,1.80,-.9025,'deep green metal',side*.31)
        probe('entrance outer pilaster',0,31.35,1.8,.13,ivory,side*1.92)
        probe('48 canopy projects clear of entry',0,31.35,3.25,1.08,ivory,side*.41)
    for delta,z in [(-1.05,2.55),(1.05,2.55),(-1.05,2.92),(1.05,2.92)]:
        probe('rectangular carved lintel extends above both closed leaves',0,31.35,z,.042,ivory,delta)
    probe('address plate green field',0,31.35,1.68,.06,'address plate green',-1.30)
    probe('white address digit 4',0,31.35,1.73,.07,'address enamel white',-1.213)
    for z in (7.49,13.45,22.39,28.35):
        probe('waisted floral panel between storeys',0,31.35,z,.042,ivory,.02)
    # Use the last point of the authored curl, shared by both resolutions.
    for storey in (1,4,8):
        lower=4.64+2.98*storey-1.16
        rad=.17*1.46*(.085+.77)
        offset=-.19*1.46+rad*np.cos(2*np.pi*1.48)
        z=lower+.73*1.04+.77*rad*np.sin(2*np.pi*1.48)
        probe('raised rose coil projects beyond the plaster panel',0,31.35,z,.09,'pale modeled flower plaster',offset)
    probe('recessed frontage on Hengshan',2,10.72,1.67,-.53,'recessed vestibule',.22)
    for f,s in [(0,15.4),(0,40),(1,2),(2,7)]:
        c,t,n,_=segments[f];pt=c+loc(f,s)*t-1.8*n
        test('flat roof of narrow street section',[*pt,40.0],[0,0,-1],20,{'roof bitumen'},40-(33.74-.08))
    for xy in ((0,-3.8),(-5.7,13),(19,10),(-25,52)):
        test('outside bounded model and in original courtyard',[*xy,42],[0,0,-1],43,None,0)
    return results

def run():
    parser=argparse.ArgumentParser()
    for flag in ('project','manifest','decoded','out'):parser.add_argument('--'+flag,type=Path,required=True)
    a=parser.parse_args();manifest=json.loads(a.manifest.read_bytes())
    helper=runpy.run_path(str(a.project/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))
    h=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
    variants=[]
    for role in ['full','lod','raw']:
        rec=manifest['assets'][role];file=a.manifest.parent/rec['file']
        assert h(file)==rec['sha256']
        decoded=file if role=='raw' else a.decoded/(role+'.glb')
        scene=helper['SerialScene'](decoded);probes=check(scene)
        assert len(scene.tri)==rec['triangles']
        variants.append(dict(role=role,triangles=len(scene.tri),sha256=h(file),decoded_sha256=h(decoded),samples=probes))
    data=dict(id=manifest['id'],passed=True,manifest_sha256=h(a.manifest),script_sha256=h(Path(__file__)),
              count=sum(len(v['samples'])for v in variants),variants=variants)
    a.out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':run()

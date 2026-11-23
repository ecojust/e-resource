"""Shoot image samples into the actual published mesh, including historic open gates and modern phase changes."""
import argparse,json,hashlib,runpy,math
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
HELPER=HERE.parents[3]/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
# The structural fit used shaft corners and upper/lower end marks. These are interior
# paint patches, tablet strokes, iron bars and gaps read separately on native station views.
PICKS={
'8-1502':[
 ('gap between leaves',[451,385],'air'),('lower lane view',[477,494],'air'),
 ('plain brick above tablet',[208,297],'brick'),('plain brick below tablet',[214,442],'brick'),
 ('centre of heritage tablet',[207,366],'tablet'),('named pier below lowest stone',[733,589],'brick'),
 ('plain opal ball left half',[232,205],'opal'),('named opal ball upper half',[724,235],'opal'),
 ('first tablet side field',[713,344],'stone'),('second tablet corner',[718,379],'stone'),
 ('third tablet margin',[717,496],'stone'),('fourth tablet margin',[717,571],'stone'),
 ('mei descending tree stroke',[733,341],'letter'),('quan lower spreading stroke',[745,410],'letter'),
 ('bie right upright',[755,477],'letter'),('shu centre upright',[744,553],'letter'),
 ('plain left door opening between bars',[68,411],'air'),('opening between pedestrian pickets',[84,410],'air')],
'9-1310':[
 ('entrance upper clear area',[426,291],'air'),('entrance lower clear area',[406,439],'air'),
 ('cream pier above grey panel',[285,293],'brick'),('plain tablet body',[284,341],'tablet'),
 ('cream pier under grey panel',[287,445],'brick'),('left spherical lamp visible',[276,213],'opal'),
 ('lettered pier outer return',[607,368],'brick'),('right leaf upper gap',[552,373],'air'),
 ('right edge of open gate',[583,448],'iron')],
'7-1512':[
 ('lane through main opening below the street sign',[590,428],'air'),
 ('gray tablet on uninscribed pier',[440,363],'tablet'),('shaft below tablet',[441,433],'brick'),
 ('between pedestrian door bars',[400,399],'air'),('lower name panel surface',[714,476],'stone')],
'inner-near':[
 ('open central lane viewed from inside',[455,436],'air'),('open sky-space between leaves',[474,379],'air'),
 ('plain globe from rear',[575,294],'opal'),('plain pier rear stone shaft',[568,330],'brick'),
 ('return stone cap over short pier',[141,428],'stone'),('short pale return brick shaft',[138,478],'brick'),
 ('garden railing between verticals',[221,455],'air'),('behind left gate clear lane',[474,464],'air')]}
MATS={'brick':'pale gate brick','stone':'cut plaque stone','opal':'opal globe','letter':'dark letter recess','tablet':'grey heritage tablet','iron':'painted black iron'}
def check(path):
    scene=runpy.run_path(str(HELPER))['SerialScene'](path);cam=json.loads((HERE/'gate-cameras.json').read_bytes())['stations']
    inside=json.loads((HERE/'gate-return-sections.json').read_bytes())['stations']
    result={'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'working_coordinates':'Original 960x672 stored rectilinear street frames; the held-out samples are independent of fitted pier edges. Objects outside the model (street sign, parked vehicles, vegetation) are not expected first hits.','views':{}}
    for n,tests in PICKS.items():
        v=(inside if n.startswith('inner')else cam)[n];c,r,k=[np.array(v[key])for key in ('C','R','K')]
        def ray(a,b):
            rr=r.T@np.linalg.solve(k,[a,b,1]);hit=scene.ray(c,rr/np.linalg.norm(rr),160)
            return hit
        checks=[]
        offsets=sorted(((i,j)for i in range(-4,5)for j in range(-4,5)if i*i+j*j<=16),key=lambda q:q[0]**2+q[1]**2)
        for name,xy,group in tests:
            x,y=xy;h=ray(x,y);expected=MATS.get(group)
            def valid(hit):return hit is None if group=='air' else bool(hit and hit['material'].endswith(expected))
            w=[0,0]if valid(h)else None
            if w is None:
                for i,j in offsets[1:]:
                    if valid(ray(x+i,y+j)):w=[i,j];break
            checks.append({'target':name,'pixel':xy,'expected':group,'actual':h,'direct':valid(h),'nearest_within_4px':w})
        result['views'][n]={'count':len(checks),'direct':sum(v['direct']for v in checks),'within_4px':sum(v['nearest_within_4px'] is not None for v in checks),'points':checks}
    return result
if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('mesh',type=Path);cli.add_argument('out',type=Path)
    a=cli.parse_args();a.out.parent.mkdir(exist_ok=True,parents=True);a.out.write_text(json.dumps(check(a.mesh),indent=2)+'\n')

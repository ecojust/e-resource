"""Cast held-out photo rays into a released GLB in its reconstructed coordinate system."""
import argparse,hashlib,json,runpy
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
HELPER=HERE.parents[3]/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
# Work-pixel observations in the same resampling as the fit. These are interior
# patches and gaps. None is a corner or shaft endpoint used in station fitting.
PICKS={
'fayhoo2014':[
 ('first column waist',[281,351],'shaft'),('second column waist',[402,324],'shaft'),
 ('third column waist',[644,357],'shaft'),('fourth column waist',[766,340],'shaft'),
 ('left niche statue torso',[371,328],'figure'),('left draped skirt',[370,351],'figure'),
 ('right niche statue torso',[674,331],'figure'),('right draped skirt',[675,352],'figure'),
 ('left narrow aperture',[443,338],'air'),('central open aperture',[523,338],'air'),
 ('right narrow aperture',[599,341],'air'),('stone pier between central and left openings',[482,342],'screen'),
 ('grey sill beneath central aperture',[525,388],'screen'),('right pier after niche',[723,333],'screen'),
 ('lowest broad step',[552,451],'terrace'),('left flower bowl',[174,354],'urn'),('right flower bowl',[869,354],'urn')],
'district-oblique':[
 ('front left column at waist',[656,510],'shaft'),('second column at waist',[693,508],'shaft'),
 ('third column at waist',[749,500],'shaft'),('fourth column at waist',[767,505],'shaft'),
 ('left-hand marble figure',[519,493],'figure'),('outer flower bowl',[619,526],'urn'),
 ('far flower bowl',[785,527],'urn'),('arched opening clear of near visitor',[576,482],'air'),
 ('front stair landing approach',[713,622],'terrace')],
'district-archive':[
 ('far-left shaft',[36,165],'shaft'),('mid-left shaft',[85,161],'shaft'),
 ('mid-right shaft',[209,150],'shaft'),('near-right shaft',[294,148],'shaft'),
 ('fixed front architrave between midcolumns',[141,92],'beam'),
 ('left side draped figure',[149,167],'figure'),('right side draped figure',[328,159],'figure'),
 ('stage nose',[150,232],'terrace'),('opening flanking centre behind the near column',[260,160],'air')]}
def matches(h,w):
    if w=='air':return h is None
    if h is None:return False
    x,y,z=h['point_enu_m'];m=h['material']
    if w=='terrace':return m.endswith('step and landing stone')
    if w=='screen':return m.endswith('grey screen stone')
    if not m.endswith('pale carved marble'):return False
    return {'shaft':abs(y)<.43 and .60<z<4.6,'figure':3<abs(x)<4.7 and y>3 and z>1.5,
            'urn':abs(x)>7.0 and y<.65,'beam':z>4.32 and abs(y)<.55}[w]
def check(path):
    scene=runpy.run_path(str(HELPER))['SerialScene'](path)
    cams=json.loads((HERE/'pavilion-cameras.json').read_bytes())['stations']
    report={'mesh_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'coordinate_frame':'Working photo pixels as specified in pavilion-observations.json. Tolerance expressed in that frame.','views':{}}
    for key,tests in PICKS.items():
        c=cams[key];k,r,eye=[np.array(c[n])for n in ('K','R','C')]
        def hit(uv):
            v=r.T@np.linalg.solve(k,[*uv,1]);return scene.ray(eye,v/np.linalg.norm(v),120)
        rows=[]
        for name,xy,w in tests:
            first=hit(xy);ok=matches(first,w);nearest=[0,0]if ok else None
            if not ok:
                offsets=sorted(((i,j)for i in range(-4,5)for j in range(-4,5)if 0<i*i+j*j<=16),key=lambda p:p[0]**2+p[1]**2)
                for i,j in offsets:
                    if matches(hit([xy[0]+i,xy[1]+j]),w):nearest=[i,j];break
            rows.append({'target':name,'pixel':xy,'expected':w,'direct':ok,'actual':first,'nearest_within_4_px':nearest})
        report['views'][key]={'direct':sum(v['direct']for v in rows),'within_4_px':sum(v['nearest_within_4_px'] is not None for v in rows),'count':len(rows),'checks':rows}
    return report
if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('mesh',type=Path);cli.add_argument('output',type=Path)
    a=cli.parse_args();a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(check(a.mesh),indent=2)+'\n')

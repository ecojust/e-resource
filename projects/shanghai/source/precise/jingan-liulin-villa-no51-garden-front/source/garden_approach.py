"""The visible granite paving between No.51's outer gate and the front steps."""
from pathlib import Path
import json
import numpy as np
from PIL import Image
from shapely.geometry import Polygon
from shapely.geometry.polygon import orient

SOURCE=Path(__file__).resolve().parent
PAVING='Garden | square stone pavers'
PALETTE={PAVING:dict(color=[1.,1.,1.],texture=str(SOURCE/'garden-pavers.png'),roughness=.88)}

def make_image(path):
    rng=np.random.default_rng(5108)
    y,x=np.mgrid[:192,:192]
    s=x%48;t=y%48
    shade=165+rng.normal(0,3.2,(192,192))+rng.normal(0,4.1,(4,4))[y//48,x//48]
    joint=np.clip((2.4-np.minimum.reduce((s,47-s,t,47-t)))/1.4,0,1)
    stone=np.stack((shade+6,shade+5,shade+1),axis=-1)
    pixels=stone*(1-joint[:,:,None])+np.array([101.,100.,92.])*joint[:,:,None]
    Image.fromarray(pixels.clip(0,255).astype('uint8')).save(path,optimize=True)

def add_approach(b,lod=False):
    b.palette.update(PALETTE)
    # The court extends diagonally from the entrance to the central steps.
    # These edges crop the area visible through the photographed gate.
    placement=json.loads((SOURCE.parent/'measurements/garden-gate-placement.json').read_bytes())
    gate=np.asarray(placement['gate_to_house'],float)
    forecourt_l=(gate@[-4.1,-1.08,0.,1.])[:2]
    forecourt_r=(gate@[4.1,-1.08,0.,1.])[:2]
    points=[(-8.16,1.20),(8.60,1.20),(9.95,-8.70),forecourt_r,
            forecourt_l,(1.05,-12.14),(-6.92,-8.28)]
    b.plan_prism(orient(Polygon(points),sign=1),-.093,-.016,PAVING,'Ground | forecourt paving')
    data=json.loads((SOURCE.parent/'measurements/no51-house-cameras.json').read_bytes())
    P=np.asarray(data['source_poses']['gao05']['P'],float)
    # White masonry crowns are separately visible above the near roof in Gao 05.
    # Their exact distance behind the ridge is an estimate.
    for name,u,v in [('west',478.,85.),('east',930.,63.)]:
        u*=4428/1234;v*=3266/910
        rows=P[:2]-np.outer([u,v],P[2]);y=5.18
        x,z=np.linalg.solve(rows[:,[0,2]],-(rows[:,1]*y+rows[:,3]))
        for j,(half,low,hi) in enumerate([(.34,-1.75,-.19),(.433,-.19,-.095),(.39,-.095,.045),(.456,.045,.103)]):
            b.box((x,y,z+(low+hi)/2),(2*half,2*half,hi-low),'Villa | pale rendered surrounds',label='Roof | '+name+' chimney crown')
if __name__=='__main__':make_image(SOURCE/'garden-pavers.png')

"""The expanding lattice crown in Fayhoo's 2015 photograph of the Xuhui maritime tower."""
from pathlib import Path
import math
import numpy as np
from PIL import Image
ID = 'xuhui-maritime-tower-diamond-lattice-crown'
SILVER = 'Pale silver exterior weave'
EDGE = 'Silver rolled upper edge'
LINER = 'Muted mineral-coloured core'
SHADE = 'Blue-grey shadow behind the upper weave'
LIP = 'Thin grey lipped ring'
PALETTE = {m:dict(color=c,roughness=r) for m,c,r in [(SILVER,[.710,.708,.672],.51),(EDGE,[.737,.737,.708],.51),(LINER,[1,1,1],.9),(SHADE,[.325,.343,.344],.73),(LIP,[.537,.535,.502],.74)]}
MEMBERS=20
HEIGHT=3.32
PROFILE=[(0.,.509),(.14,.530),(.31,.601),(.47,.744),(.65,.900),(.84,1.012),(1.02,1.075),(1.26,1.105),(1.50,1.103),(1.78,1.086),(2.02,1.045),(2.24,.978),(2.46,.876),(2.67,.760),(2.86,.633),(3.04,.495),(3.21,.348),(HEIGHT,.229)]
def radius(z):
    return float(np.interp(z,[k for k,v in PROFILE],[v for k,v in PROFILE]))
def turn(z):
    u=z/HEIGHT
    return .34*u+2.90*u**1.52
def design_xyz(z,idx,hand,offset=0):
    theta=idx*math.tau/MEMBERS+hand*turn(z)
    rad=radius(z)+offset
    return (rad*math.cos(theta),rad*math.sin(theta),z)
def texture():
    f=Path(__file__).with_name('warm-mineral-shell.png')
    if not f.is_file():
        rng=np.random.default_rng(823);col=np.array([184,177,155]);a=col+rng.normal(0,3.4,(512,640,1))
        Image.fromarray(a.clip(0,255).astype('uint8')).quantize(88).save(f)
    PALETTE[LINER]['texture']=str(f)
def add_building(b,far=False):
    texture()
    segments=52 if far else 136
    inner=[(0,.441),(.23,.454),(.53,.498),(.80,.568),(1.06,.684),(1.43,.799),(1.68,.845),(1.91,.858),(2.10,.843),(2.32,.790),(2.57,.686),(2.75,.553),(2.87,.438),(2.91,.327)]
    b.lathe((0,0),inner,LINER,segments,label='Muted solid form seen through the outer diamonds')
    # Use a fully bounded single handmade atlas. It contains no pixels from the source photograph.
    b.parts[-1]['texcoords']=[[(math.atan2(y,x)/math.tau+.5)*.984+.008,z/HEIGHT] for x,y,z in b.parts[-1]['vertices']]
    for lo,hi,rr in [(1.943,2.108,.865),(2.11,2.123,.869),(2.34,2.364,.790)]:
        b.lathe((0,0),[(lo,rr-.009),(lo+.003,rr),(hi-.003,rr),(hi,rr-.009)],SHADE if hi-lo>.06 else LIP,segments,label='Horizontal shadow or ledge seen behind the exterior screen')
    # Straight-edged sections connect consecutive points of each curved diagonal.
    # Keeping the two series as individual members also keeps genuine open diamonds.
    samples=21 if far else 56
    for i in range(MEMBERS):
        for hand in [-1,1]:
            path=[design_xyz(HEIGHT*k/samples,i,hand,.006 if hand>0 else -.004)for k in range(samples+1)]
            b.tube(path,.0175 if hand>0 else .0165,SILVER,5 if far else 8,label=('Ascending'if hand>0 else 'Descending')+' diagonal '+str(i+1))
    cap_r=radius(HEIGHT)
    b.tube([(cap_r*math.cos(a),cap_r*math.sin(a),HEIGHT-.004)for a in np.linspace(0,math.tau,segments+1)],.010,EDGE,6 if far else 9,label='Narrow finishing ring between diagonal ends')

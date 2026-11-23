"""Two original repeating surfaces made for the post-restoration facade."""
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parent
PLASTER='Jiuyuan | yellow roughcast'; TILE='Jiuyuan | green glazed pan tiles'
SAND='Jiuyuan | grey beige coping'; STEEL='Jiuyuan | dark green steel'
GLASS='Jiuyuan | reflected grey blue glazing'; GLASS2='Jiuyuan | shaded olive glazing'
SHADE='Jiuyuan | recessed vent'; DRAIN='Jiuyuan | painted rainwater goods'
def rgb(a):return [(v/255)**2.2 for v in a]
def mat(c,r,m=0):return dict(color=rgb(c),roughness=r,metallic=m)
PALETTE={PLASTER:dict(color=[1,1,1],roughness=.93,texture=str(ROOT/'ochre-roughcast.png')),TILE:dict(color=[1,1,1],roughness=.55,texture=str(ROOT/'green-pan-tile.png')),SAND:mat((174,165,143),.91),STEEL:mat((49,60,54),.50,.25),GLASS:mat((94,110,112),.23,.28),GLASS2:mat((73,84,77),.26,.2),SHADE:mat((49,55,48),.95),DRAIN:mat((73,67,58),.68,.18)}
def generate():
 r=np.random.default_rng(732);h=w=192;v=r.normal(0,2.6,(h,w))+r.normal(0,.9,(32,32)).repeat(6,0).repeat(6,1)
 Image.fromarray(np.uint8(np.clip([226,192,129]+v[:,:,None],0,255))).save(ROOT/'ochre-roughcast.png')
 y,x=np.indices((h,w));rx=x%24;ry=y%32;ridge=8*np.cos(rx*np.pi/12);joint=np.where(ry<2,-14,0)+np.where(rx>21,-11,0)
 v=r.normal(0,2.2,(h,w))+ridge+joint;Image.fromarray(np.uint8(np.clip([112,120,98]+v[:,:,None],0,255))).save(ROOT/'green-pan-tile.png')
if __name__=='__main__':generate()

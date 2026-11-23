"""Nos. 1 and 2. Front coordinates follow the large and small east gables in the architect's album.

On Gao's numbered 2013 frame the No.1 plate is to the right of the odd entrance.
The plated stair to No.2 rises on the viewer's left behind a curved outer cheek.
"""
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
import numpy as np
from materials import *
from joinery import window,door,plaque,segmental
BIG=(-1.19,5.60,7.18,10.53,0.0)
SMALL=(2.58,6.72,5.82,8.34,1.02)
FLOOR=3.43
def gable_face(f,bay,upper,low,number,lod=False):
    a,b,eave,crest,front=bay;m=(a+b)/2
    profile=Polygon([(a,FLOOR),(b,FLOOR),(b,eave),(m,crest),(a,eave)])
    holes=unary_union([box(*w[:4])for w in upper])
    wall=profile.difference(holes)
    f.solid(wall,front-.205,front,CREAM,number+' upper plaster nogging')
    f.solid(box(a,.045,b,FLOOR).difference(unary_union(low)),front-.28,front-.006,BRICK,number+' lower brick and reveals')
    for i,(x0,z0,x1,z1,cols,rows) in enumerate(upper):
        if number=='larger gable' and i==0:
            # The left upper casement swings into the lane in Gao's numbered
            # photograph. At an oblique angle it stands ahead of the deep reveal.
            f.rect(x0,x1,z0,z1,front-.46,front-.405,DARK,'shadow behind open No 1 casement')
            theta=np.radians(32)
            opened=f.face(x0,-front,np.cos(theta),-np.sin(theta))
            window(opened,0,x1-x0,z0,z1,.21,cols,rows,'outward upper casement of No 1',lod,False)
        else:window(f,x0,x1,z0,z1,front,cols,rows,number+' upper casement',lod,False)
    def timber(path,width=.13):
        f.band(path,width,front+.004,front+.063,OAK,number+' structural timber',wall)
    for h,width in [(FLOOR+.073,.145),(4.63,.128),(eave-.065,.132)]:
        timber([(a-.03,h),(b+.03,h)],width)
    fractions=([.018,.177,.304,.445,.727,.986] if number=='larger gable' else [.023,.26,.535,.79,.982])
    for v in fractions:
        x=a+(b-a)*v;timber([(x,FLOOR),(x,crest+.13)],.155 if v<.03 or v>.97 else .125)
    timber([(a,eave),(m,crest),(b,eave)],.175)
    timber([(a+.17,4.62),(a+1.19,FLOOR+.09)],.15)
    if number=='larger gable':
        # A curved lower brace turns up under the main window on Gao's close and oblique views.
        t=np.linspace(0,1,7);points=[(m-1.35+.84*j,FLOOR+.09+1.10*np.sin(j*np.pi/2))for j in t]
        timber(points,.135)
        timber([(m-1.36,crest-1.94),(m-.40,eave+.11)],.12)
        timber([(m+1.41,crest-2.05),(m+.52,eave+.04)],.12)
        timber([(m-1.14,8.84),(m+1.1,8.84)],.125)
    else:
        timber([(a+.49,eave+.54),(m-.11,eave-.02)],.115)
        timber([(m+.13,eave-.02),(b-.50,eave+.58)],.115)
    # Only build the right return up to the eaves. The gabled roofs own the verges.
def add_one_two(f,lod=False):
    entry=segmental(0,.94,.18,2.36,.105)
    lower1=[entry,box(1.072,1.115,1.753,2.39)]
    upper1=[(-.01,4.63,.69,6.08,2,4),(.97,4.63,1.69,6.08,2,4),(1.88,7.82,2.46,8.85,2,3)]
    gable_face(f,BIG,upper1,lower1,'larger gable',lod)
    door(f,0,.94,.18,2.36,.105,0,'number 1',lod)
    f.rect(-.59,.54,.02,.11,-.09,.415,STEP,'No 1 lowest doorstep')
    f.rect(-.52,.5,.11,.19,-.09,.255,STEP,'No 1 upper doorstep')
    plaque(f,.66,2.128,1,.008)
    # The bracket above No.1 is visible in the close oblique view.
    f.rail([(-.17,-.035,2.82),(-.16,-.07,2.97),(-.10,-.15,3.01),(.035,-.28,2.97),(.10,-.33,2.86)],.017,IRON,'curved iron lamp bracket above No 1')
    f.rect(.005,.20,2.79,2.83,.26,.41,IRON,'small shade above numbered arch')
    window(f,1.072,1.753,1.115,2.39,0,2,3,'No 1 lower casement',lod)
    # The smaller gable is forward of the No.1 brick wall. The left return is visible.
    p=SMALL[4];side=f.face(SMALL[0],-p,0,-1)
    ret=box(-p,.045,0,FLOOR);side.solid(ret,-.21,0,BRICK,'small bay south brick return')
    side.rect(-p,0,FLOOR,SMALL[2],-.21,0,CREAM,'small bay south plaster return')
    for y in [FLOOR+.06,SMALL[2]-.08]:side.rect(-p,0,y-.055,y+.06,.006,.063,OAK,'small bay return binding')
    small_door=segmental(4.60,.64,.12,2.35,.074)
    lower2=[box(3.06,1.03,3.53,2.35),small_door,box(5.70,1.02,6.20,2.35)]
    upper2=[(3.35,4.55,3.91,5.71,2,3),(4.94,4.55,5.51,5.71,2,3)]
    gable_face(f,SMALL,upper2,lower2,'lesser gable',lod)
    door(f,4.60,.64,.12,2.35,.074,p,'small gable secondary opening',lod)
    for j,hole in enumerate((lower2[0],lower2[2])):
        x,z,xx,zz=hole.bounds;window(f,x,xx,z,zz,p,2,3,'small bay lower light '+str(j+1),lod)

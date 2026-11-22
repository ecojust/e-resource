"""The two differently finished pairs of open shutters along the street at Gude Fang."""
from pathlib import Path
import numpy as np
from PIL import Image
from shapely.geometry import box,Polygon
ID='xuhui-gude-fang-street-shutter-pair'
RENDER='Grey scored wall';JOINT='Incised render course';WHITE='Ivory-painted shutter frame';RED='Muted red shutter blades';BROWN='Brown-painted shutter blades';TIMBER='Red-brown window frame';GLASS='Deep window glazing';SILL='Light stone sill';HINGE='Dark small fittings';RETURN='Shadowed jamb'
PALETTE={m:dict(color=colour,roughness=r) for m,colour,r in [(RENDER,[1,1,1],.94),(JOINT,[.49,.49,.447],.94),(WHITE,[.821,.80,.704],.81),(RED,[.508,.302,.235],.78),(BROWN,[.422,.267,.198],.82),(TIMBER,[.503,.321,.271],.80),(GLASS,[.196,.203,.195],.38),(SILL,[.704,.691,.625],.91),(HINGE,[.278,.273,.233],.79),(RETURN,[.368,.357,.311],.89)]}
CENTRES=[-.83,.78]
def texture():
    p=Path(__file__).with_name('grey-scored-plaster.png')
    if not p.exists():
        r=np.random.default_rng(791);a=np.array([161,162,148])+r.normal(0,3,(384,640,1))
        Image.fromarray(a.clip(0,255).astype('uint8')).quantize(72).save(p)
    PALETTE[RENDER]['texture']=str(p)
def add_building(b,far=False):
    texture()
    def front(poly,lo,hi,mat,label):b.prism(poly,lo,hi,lambda x,z,d:(x,-d,z),mat,label)
    def block(l,r,z,t,lo,hi,mat,label):front(box(l,z,r,t),lo,hi,mat,label)
    voids=[box(x-.255,.337,x+.255,1.823)for x in CENTRES]
    whole=box(-1.73,0,1.70,2.18);body=whole.difference(voids[0]).difference(voids[1])
    front(body,-.177,0,RENDER,'Rendered street facade cut by two real window openings')
    for z in [.19,.54,.89,1.24,1.59,1.94]:
        front(box(-1.73,z,1.70,z+.006).intersection(body),0,.001,JOINT,'Fine horizontal scored joint')
    for i,x in enumerate(CENTRES):
        frame=WHITE if i==0 else BROWN;slat=RED if i==0 else BROWN
        block(x-.258,x+.258,.292,.342,-.06,.114,SILL,'Projecting shallow sill')
        block(x-.234,x+.234,.246,.292,-.063,.065,SILL,'Flat apron below sill')
        block(x-.255,x-.217,.337,1.823,-.155,.002,RETURN,'Left reveal of window')
        block(x+.217,x+.255,.337,1.823,-.155,.002,RETURN,'Right reveal of window')
        block(x-.217,x+.217,.337,1.823,-.162,-.139,GLASS,'Glazing set back from shutters')
        block(x-.217,x-.186,.344,1.803,-.14,-.104,TIMBER,'Inner timber stile')
        block(x+.186,x+.217,.344,1.803,-.14,-.104,TIMBER,'Inner timber stile')
        block(x-.259,x+.259,1.785,1.827,-.141,.057,TIMBER,'Window head')
        block(x+.054,x+.071,.35,1.791,-.132,-.107,TIMBER,'Narrow glazing upright')
        for z in [.72,1.33]:block(x+.055,x+.214,z,z+.018,-.136,-.106,TIMBER,'Small glazing bars behind the shutter')
        for s in [-1,1]:
            clear=.019;cx=x+s*.372;width=.231;l=cx-width/2;r=cx+width/2;lower=.365;upper=1.767
            block(l,r,lower,upper,.013,.029,slat,'Dark backing within shutter frame')
            for edge in [l,r-.023]:block(edge,edge+.023,lower,upper,.026,.060,frame,'Tall frame of shutter')
            for z in [lower,upper-.041]:block(l,r,z,z+.041,.029,.062,frame,'Top or bottom shutter rail')
            groups=13 if i==0 else 31;step=(upper-lower-.097)/groups
            for k in range(groups):
                z=lower+.046+k*step
                if i==0:block(l+.018,r-.018,z,z+.017,.033,.058,WHITE,'Broad ivory crossing between red louvre pairs')
                for dz in ([.021,.058] if i==0 else [.004]):
                    h=step*.30 if i==0 else step*.76
                    poly=Polygon([(-.033,z+dz+h),(-.049,z+dz+h),(-.076,z+dz+.004),(-.061,z+dz)])
                    b.prism(poly,l+.023,r-.023,lambda y,z,xx:(xx,y,z),slat,'Sloping painted timber blade')
            # A shallow knuckle projects at the edge of each open shutter leaf.
            for zz in [.52,1.53]:
                ox=cx-s*.106
                front(box(ox-.008,zz-.023,ox+.008,zz+.023).buffer(.005,resolution=3 if far else 9),.060,.079,HINGE,'Small shutter hinge')
    for part in b.parts:
        if part['material']==RENDER:part['texcoords']=[[(x+1.73)/3.43,z/2.18] for x,y,z in part['vertices']]

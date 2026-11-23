"""The Zou Taofen memorial in the southern court, including the signed stone plinth.

Local project coordinates in metres. X points east, Y north, and the inscription
faces the south clock passage. The office's 1995 account, 2004 rear photograph
and 2026 oblique and frontal photographs accompany the dimensions in the report.
"""
from pathlib import Path
from math import cos, sin, pi
import json
from shapely.geometry import Polygon, GeometryCollection
from shapely.affinity import scale,translate

X=-.055
Y=26.46
BLACK='polished charcoal granite'
RED='memorial rose granite'
BRONZE='weathered blue-brown bronze'
HAIR='bronze hair and coat recesses'
LETTER='pale cut inscription'
PALETTE={
    BLACK:dict(color=[.115,.125,.13],roughness=.42),
    RED:dict(color=[.43,.195,.146],roughness=.37),
    BRONZE:dict(color=[.245,.265,.25],roughness=.57,metallic=.71),
    HAIR:dict(color=[.185,.205,.191],roughness=.58,metallic=.69),
    LETTER:dict(color=[.81,.74,.61],roughness=.74)}
def rings(b,sections,mat,label):
    """Build a watertight loft through equal-sized horizontal contours."""
    n=len(sections[0]);v=[(x+X,y+Y,z)for r in sections for x,y,z in r]
    face=[tuple(range(n-1,-1,-1))]
    for i in range(len(sections)-1):
        for j in range(n):
            k=(j+1)%n;lo=i*n;up=lo+n
            face.extend([(lo+j,lo+k,up+k),(lo+j,up+k,up+j)])
    face.append(tuple(range(len(v)-n,len(v))))
    b.add(v,face,mat,'Zou Taofen/'+label)
def cut_stone(b,w,d,lo,hi,bevel,mat,label):
    def rect(a,c,z):return [(-a/2,-c/2,z),(a/2,-c/2,z),(a/2,c/2,z),(-a/2,c/2,z)]
    rings(b,[rect(w,d,lo),rect(w,d,hi-bevel),rect(w-2*bevel,d-2*bevel,hi)],mat,label)
def bronze(b,sections,sides,mat,label):
    contours=[]
    for z,xc,yc,rx,ry in sections:
        contours.append([(xc+rx*cos(2*pi*i/sides),yc+ry*sin(2*pi*i/sides),z)for i in range(sides)])
    rings(b,contours,mat,label)
def inscription(b,text,span,z0,height,full_depth,label):
    glyphs=json.loads(Path(__file__).with_name('statue-lettering.json').read_bytes())
    advance=span/len(text);left=-span/2
    for i,char in enumerate(text):
        g=GeometryCollection()
        for contour in glyphs[char]:
            p=Polygon(contour)
            if p.area>0:g=g.symmetric_difference(p.buffer(0))
        xmin,ymin,xmax,ymax=g.bounds
        g=translate(g,-(xmin+xmax)/2,-ymin)
        ratio=height/1000
        g=translate(scale(g,xfact=ratio,yfact=ratio,origin=(0,0)),xoff=left+advance*(i+.5),yoff=z0)
        b.prism(g,0,.002,lambda x,z,d:(X+x,Y-full_depth/2-.001-d,z),LETTER,label)
def add_sculpture(b,lod=False):
    for k,v in PALETTE.items():b.palette.setdefault(k,v)
    last=0
    for name,(w,d,h,edge) in zip(('ground step','second stair','third stair','upper landing'),[(6.64,3.70,.149,.009),(5.80,3.30,.306,.009),(4.99,2.90,.470,.009),(4.14,2.52,.635,.009)]):
        cut_stone(b,w,d,last,h,edge,BLACK,name);last=h
    for label,w,d,h,bevel in [('red stone foot',2.11,1.87,.993,.014),('pedestal lower moulding',1.45,1.28,1.088,.014),('receding stone fillet',1.37,1.20,1.146,.008),('raised lower pedestal',1.27,1.10,1.613,.018),('square inscription die',1.04,.91,2.349,.012)]:
        cut_stone(b,w,d,last,h,bevel,RED,label);last=h
    b.box((X,Y+.456,1.977),(.847,.006,.618),RED,label='Zou Taofen/reverse inscription tablet outline')
    if not lod:
        inscription(b,'鄒韜奮',.715,2.025,.142,.91,'Transcribed front dedication')
        inscription(b,'(1895—1944)',.63,1.836,.068,.91,'Transcribed life dates')
    n=12 if lod else 24
    bronze(b,[(2.348,0,-.008,.40,.308),(2.39,0,-.008,.407,.315),(2.48,-.006,.004,.403,.285),(2.60,-.008,.033,.34,.227),(2.72,-.005,.043,.282,.202),(2.86,-.002,.044,.286,.203),(3.035,.004,.038,.292,.19),(3.13,.009,.028,.282,.171),(3.18,.005,.02,.183,.132),(3.205,.006,.017,.116,.105)],n,BRONZE,'back of jacket and seated waist')
    for sign,side in [(-1,'west'),(1,'east')]:
        bronze(b,[(2.53,sign*.261,-.065,.103,.134),(2.576,sign*.275,-.032,.113,.175),(2.696,sign*.281,.017,.095,.135),(2.91,sign*.284,.034,.089,.113),(3.055,sign*.254,.032,.089,.119),(3.113,sign*.228,.033,.087,.096)],n,BRONZE,side+' hanging upper sleeve')
        bronze(b,[(2.494,sign*.169,-.122,.126,.092),(2.538,sign*.173,-.144,.162,.11),(2.60,sign*.205,-.121,.150,.113),(2.658,sign*.237,-.072,.104,.105)],n,BRONZE,side+' folded forearm')
        bronze(b,[(2.479,sign*.044,-.197,.043,.061),(2.512,sign*.055,-.201,.076,.075),(2.557,sign*.079,-.193,.072,.062),(2.586,sign*.098,-.166,.054,.049)],n,BRONZE,side+' overlapping hand mass')
        if not lod:
            pts=[(sign*.09,-.081,3.167),(sign*.17,-.115,3.04),(sign*.124,-.145,3.008),(sign*.15,-.141,2.958),(sign*.016,-.163,2.724)]
            # A raised closed ribbon describes the jacket lapel visible in the oblique.
            v=[(X+x,Y+y+offset,z) for offset in (0,.021)for x,y,z in pts]
            faces=[(0,1,2),(0,2,4),(2,3,4),(5,7,6),(5,9,7),(7,9,8)]+[(i,5+i,5+(i+1)%5,(i+1)%5)for i in range(5)]
            if sign>0:
                faces=[tuple(reversed(face))for face in faces]
            b.add(v,faces,BRONZE,'Zou Taofen/'+side+' notched lapel')
    bronze(b,[(3.139,.002,.015,.104,.093),(3.193,.004,.014,.113,.104),(3.25,.006,.019,.091,.095),(3.285,.004,.022,.086,.088)],n,BRONZE,'neck above collar')
    # The 2024 frontal and 2026 oblique constrain jaw, temples and parted hair.
    bronze(b,[(3.203,.006,-.04,.053,.067),(3.232,.004,-.025,.091,.099),(3.29,.003,-.001,.113,.126),(3.355,.001,.006,.139,.142),(3.421,0,.013,.148,.151),(3.49,-.004,.013,.144,.142),(3.532,-.01,.019,.110,.110),(3.556,-.014,.021,.064,.073),(3.559,-.015,.021,.027,.031)],n,BRONZE,'documented head silhouette')
    bronze(b,[(3.44,.001,.021,.141,.143),(3.474,-.003,.019,.149,.148),(3.516,-.008,.02,.138,.137),(3.545,-.013,.023,.108,.109),(3.568,-.02,.029,.055,.061),(3.572,-.018,.029,.019,.021)],n,HAIR,'swept hair crown')

    if not lod:
        for sign,side in ((-1,'west'),(1,'east')):
            bronze(b,[(3.315,sign*.139,.008,.010,.020),(3.339,sign*.142,.003,.020,.034),(3.38,sign*.142,.000,.021,.035),(3.394,sign*.140,.007,.012,.025)],12,BRONZE,side+' visible ear outline')
        bronze(b,[(3.304,.001,-.113,.030,.028),(3.325,.000,-.128,.035,.041),(3.341,-.001,-.125,.018,.036),(3.390,.000,-.12,.013,.019)],14,BRONZE,'raised nose silhouette seen in both front views')
        # Closed annuli around the small round spectacle lenses. Lens centres and
        # spacing follow the 2024 frontal, with the temples read in the oblique.
        for sign,side in ((-1,'west'),(1,'east')):
            n=20;cx=sign*.060;cz=3.384
            def contour(rx,rz,y):return [(X+cx+rx*cos(2*pi*i/n),Y+y+sign*.011*cos(2*pi*i/n),cz+rz*sin(2*pi*i/n))for i in range(n)]
            verts=contour(.049,.036,-.142)+contour(.044,.031,-.142)+contour(.049,.036,-.135)+contour(.044,.031,-.135)
            faces=[]
            for i in range(n):
                j=(i+1)%n
                faces.extend([(i,j,n+j,n+i),(2*n+i,3*n+i,3*n+j,2*n+j),(i,2*n+i,2*n+j,j),(n+i,n+j,3*n+j,3*n+i)])
            b.add(verts,faces,HAIR,'Zou Taofen/'+side+' cast spectacle rim')
            b.tube([(X+sign*.107,Y-.134,3.392),(X+sign*.143,Y-.06,3.395),(X+sign*.145,Y+.01,3.382)],.0038,HAIR,sides=6,label=side+' spectacle arm')
        b.tube([(X-.017,Y-.141,3.39),(X,Y-.152,3.4),(X+.017,Y-.141,3.39)],.004,HAIR,sides=6,label='eyeglass bridge')
        b.tube([(X-.112,Y-.212,2.571),(X-.05,Y-.233,2.548),(X+.07,Y-.242,2.522)],.026,BRONZE,sides=12,label='oblique rolled object held at the waist')

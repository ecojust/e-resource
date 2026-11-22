"""Visible faces of the garden bay at no. 14, May Lee Court, Shanghai.

The broad window and the narrow return are fitted separately to the photographed
perspective. Dimensions in metres set a relative scale for the detail study.
"""
from math import pi, sin
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from shapely.geometry import box
from shapely.ops import unary_union

ID = 'jingan-may-lee-court-no14-canted-bay'
BRICK = 'Orange-red facing brick in running bond'
STONE = 'Buff grey cement surround'
LIP = 'Sunlit edge of projecting stone sill'
STEEL = 'Dark-painted steel casements'
MULLION = 'Wide steel casement meeting stile'
RAIL = 'Weathered iron terrace balustrade'
COPING = 'Limestone terrace cap'
SOFFIT = 'Shadowed cement drip'
FLOOR = 'Weathered terrace paving'
GLASS = ('Dark garden reflection', 'Cool blue garden reflection', 'Warm grey reflected light')
PALETTE = {m:{'color':c,'roughness':r} for m,c,r in (
    (BRICK,[1,1,1],.94),(STONE,[.55,.48,.385],.87),(LIP,[.67,.59,.49],.86),
    (STEEL,[.045,.052,.05],.55),(MULLION,[.044,.046,.044],.52),
    (RAIL,[.115,.114,.095],.59),(COPING,[.54,.49,.42],.89),
    (SOFFIT,[.36,.32,.275],.92),(FLOOR,[.30,.27,.22],.89),
    (GLASS[0],[.092,.123,.117],.28),(GLASS[1],[.114,.159,.173],.28),
    (GLASS[2],[.137,.164,.156],.30))}
WIDE, RETURN, HEIGHT = 3.06, 1.52, 6.51
HALF = WIDE/2
# u increases across the broad face left-to-right and from the wall to the corner on its return.
FACES = {
    'wide':(WIDE,[(.533,2.607,.838,2.818),(.470,2.684,4.140,6.197)],6),
    'narrow':(RETURN,[(.151,1.181,.845,2.865),(.170,1.249,4.150,6.116)],2)}
def xyz(face,u,z,outwards):
    return (u-HALF,-outwards,z) if face=='wide' else (-HALF-outwards,RETURN-u,z)

def texture():
    path=Path(__file__).with_name('brick-and-stone.png')
    if not path.exists():
        rng=np.random.default_rng(584);w,h=576,900
        im=Image.new('RGB',(w,h),(180,151,126));draw=ImageDraw.Draw(im)
        for row in range(103):
            y0=int(row*h/102);y1=int((row+1)*h/102)-1
            for col in range(-1,19):
                x0=int((col+.5*(row%2))*w/16);x1=int((col+1+.5*(row%2))*w/16)-2
                tone=rng.normal(0,5.3);glaze=rng.normal(0,2.1)
                c=tuple(int(a+b) for a,b in zip((185,113,78),(tone,tone+glaze,.83*tone+glaze)))
                draw.rectangle((x0,y0+1,x1,y1),fill=c)
                draw.line((x0,y1,x1,y1),fill=tuple(max(0,t-7) for t in c))
        rgb=np.asarray(im).astype(float)
        noise=rng.normal(0,3.3,(h,w,1))
        Image.fromarray(np.clip(rgb+noise,0,255).astype('uint8')).quantize(160).save(path,optimize=True)
    PALETTE[BRICK]['texture']=str(path)

def add_building(b,far=False,*,include_terrace_back=True):
    texture()
    def beam(face,u0,u1,z0,z1,d0,d1,material,label):
        b.prism(box(u0,z0,u1,z1),d0,d1,lambda u,z,d:xyz(face,u,z,d),material,label)
    for face,(span,frames,columns) in FACES.items():
        mapper=lambda u,z,d:xyz(face,u,z,d)
        holes=[box(a+.035,lo+.035,c-.035,hi-.035) for a,c,lo,hi in frames]
        shape=box(0,0,span,HEIGHT-.073).difference(unary_union(holes))
        # The two outer surfaces meet at their full common height. The thickness
        # returns only a short way behind either window, as the photographs show.
        b.prism(shape,-.222,0,mapper,BRICK,face+' brickwork and real window reveals')
        for part in b.parts[-1:]:
            part['texcoords']=[((.015+.965*((x+HALF)/WIDE)) if face=='wide' else (.015+.965*((RETURN-y)/WIDE)),.990-.971*z/7.58) for x,y,z in part['vertices']]
        for storey,(left,right,base,head) in enumerate(frames):
            jamb=.093 if face=='wide' else .077
            sill=.105;lintel=.092
            l,r,lo,hi=left+jamb,right-jamb,base+sill,head-lintel
            slab=lambda a,c,j,k,d,e,m,n:beam(face,a,c,j,k,d,e,m,face+' '+n)
            slab(left,l,base+sill,head-lintel,-.12,.051,STONE,'stone left jamb')
            slab(r,right,base+sill,head-lintel,-.12,.051,STONE,'stone right jamb')
            slab(left,right,head-lintel,head,-.12,.063,STONE,'stone lintel')
            slab(left-.012,right+.012,base,base+sill,-.13,.095,LIP,'outer stone sill')
            if not far:
                slab(left,right,head-.018,head,-.10,.071,LIP,'fine weathering edge')
                slab(left-.006,right+.006,base+.014,base+.031,.060,.102,LIP,'sill drip edge')
            band=.033
            for a,c in ((l,l+band),(r-band,r)):slab(a,c,lo,hi,-.108,-.063,STEEL,'casement outer steel stile')
            for j,k in ((lo,lo+band),(hi-band,hi)):slab(l+band,r-band,j,k,-.108,-.063,STEEL,'casement outer steel rail')
            a,c,j,k=l+band,r-band,lo+band,hi-band
            rows=5
            us=np.linspace(a,c,columns+1);zs=np.linspace(j,k,rows+1)
            for col in range(columns):
                for row in range(rows):
                    material=pane_material(face,storey,col,row)
                    slab(us[col],us[col+1],zs[row],zs[row+1],-.133,-.122,material,'individual reflected pane')
            for i,u in enumerate(us[1:-1],1):
                middle=i==columns//2;t=.016 if middle else .0095
                slab(u-t,u+t,j,k,-.128,-.078 if middle else -.085,
                     MULLION if middle else STEEL,'meeting stile' if middle else 'slender glazing bar')
            for idx,z in enumerate(zs[1:-1],1):
                t=.013 if idx==3 else .0095
                slab(a,c,z-t,z+t,-.118,-.086,STEEL,'horizontal glazing bar')
        # Paired steel pickets are straight on both faces; depth-tested glass remains
        # visible between them. The near photograph also shows small iron curls.
        rail_face=face+' terrace'
        eps=.025; usable=span-2*eps;groups=6 if face=='wide' else 3
        for d0,d1,za,zb,m,n in [
            (-.06,.065,HEIGHT-.139,HEIGHT-.090,SOFFIT,'lower drip'),
            (-.06,.089,HEIGHT-.09,HEIGHT+.015,COPING,'cap and projecting ledge')]:
            beam(face,-.055,span+.055,za,zb,d0,d1,m,rail_face+' '+n)
        for z,t in [(HEIGHT+.10,.018),(HEIGHT+.895,.019),(HEIGHT+.977,.029)]:
            beam(face,eps,span-eps,z-t,z+t,-.050,-.012,RAIL,rail_face+' horizontal rail')
        for g in range(groups+1):
            u=eps+usable*g/groups;hw=.020 if g in (0,groups) else .012
            beam(face,u-hw,u+hw,HEIGHT,HEIGHT+.980,-.047,-.015,RAIL,rail_face+' upright')
        for g in range(groups):
            mid=eps+usable*(g+.5)/groups
            spacing=.065
            for sign in (-1,1):
                u=mid+sign*spacing
                beam(face,u-.008,u+.008,HEIGHT+.10,HEIGHT+.90,-.043,-.019,RAIL,rail_face+' paired slender uprights')
            if not far and g in ((1,4) if face=='wide' else (1,)):
                for sign in (-1,1):
                    t=np.linspace(0,1,12)
                    points=[xyz(face,mid+sign*(spacing-.040*sin(pi*s)),HEIGHT+.22+.36*s,-.015) for s in t]
                    b.tube(points,.008,RAIL,6,rail_face+' paired curved tie')
    b.box((0,RETURN/2,HEIGHT-.040),(WIDE,RETURN,.090),FLOOR,label='Top face of photographed terrace')
    if not include_terrace_back:
        return
    # The garden photograph also shows a recessed upper casement directly behind
    # the railing. Limit this backing panel to the visible strip above the terrace.
    rear_y=RETURN+.035
    def rear(u,z,d):return (u-HALF,rear_y-d,z)
    back=box(-.24,HEIGHT,WIDE+.17,8.67).difference(box(.52,HEIGHT+.015,2.34,8.50))
    b.prism(back,-.18,0,rear,BRICK,'backing wall of the photographed terrace')
    part=b.parts[-1];part['texcoords']=[(.015+.965*min(.999,max(.001,(x+HALF+.24)/(WIDE+.41))),.972-.23*(z-HEIGHT)) for x,y,z in part['vertices']]
    def rear_strip(u,v,z,t,lo,hi,m,n):
        b.prism(box(u,z,v,t),lo,hi,rear,m,n)
    for a,c in ((.52,.575),(2.285,2.34)):
        rear_strip(a,c,HEIGHT+.005,8.50,-.12,-.044,STEEL,'upper casement jamb')
    for z in (HEIGHT+.045,8.467):
        rear_strip(.575,2.285,z-.032,z+.032,-.12,-.044,STEEL,'upper casement sash')
    for i in range(4):
        x0=.575+i*1.71/4
        for j in range(5):
            z0=HEIGHT+.077+j*.372
            rear_strip(x0,x0+1.71/4,z0,z0+.372,-.16,-.14,
                       GLASS[(i//2+j//3)%3],'upper terrace casement glass')
        if i:
            rear_strip(x0-.018,x0+.018,HEIGHT+.077,8.435,-.13,-.064,
                       MULLION if i==2 else STEEL,'upper casement glazing bar')
    for j in range(1,5):
        z=HEIGHT+.077+j*.372
        rear_strip(.575,2.285,z-.013,z+.013,-.126,-.078,STEEL,'upper casement horizontal')

def pane_material(face,storey,col,row):
    offset=0 if face=='wide' else 2
    # Vary sashes in small groups so the garden is suggested without using pixels from a photograph.
    return GLASS[(int(col>=3)+int(row>=3)+storey+offset)%3]

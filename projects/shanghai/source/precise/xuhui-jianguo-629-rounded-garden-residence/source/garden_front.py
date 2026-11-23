"""Garden-facing plaster wall, steel window pairs and the curved east-of-image end."""
from math import ceil,cos,radians,sin
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
from arch_brick_and_glass import add_brick_and_glass,opening_profiles
from garden_plane import SURVEY,flat_single_windows,hit,wide_openings
from garden_sashes import insert_sash,open_casements
from materials import BASE,DARK,FRAME,GLASS,MID_GLASS,RENDER,ROOF,SILL,TRIM

LEFT=-6.40
STEP=-2.19
TANGENT=SURVEY['arc']['tangent_u']
RADIUS=SURVEY['arc']['radius']
ANGLE=59.5
ROOF_Z=10.19
LOW_WING_Z=7.59
COURSES=[3.11,6.37,9.09]

def slab(face,shape,z0,z1,mat,name):
    face.b.prism(shape,z0,z1,lambda u,d,z:face.point(u,d,z),mat,face.label+' | '+name)

def curved_plan(delta,start=0,end=ANGLE,lod=False):
    count=max(1,ceil((end-start)/(7.5 if lod else 2.4)))
    return [(TANGENT+(RADIUS+delta)*sin(radians(a)),RADIUS-(RADIUS+delta)*cos(radians(a)))
            for a in (start+(end-start)*i/count for i in range(count+1))]

def arc_band(face,inner,outer,z0,z1,mat,label,lod):
    plan=Polygon(curved_plan(outer,lod=lod)+curved_plan(inner,lod=lod)[::-1])
    slab(face,plan,z0,z1,mat,label)

def casement_pairs(face,wide,profiles):
    for rev in profiles:
        name=rev['id']
        outer=wide['ground' if name=='lower' else name]
        x0,z0,x1,z1=outer.bounds
        pier=rev['pier'];a,_,b,_=pier.bounds
        clipped=outer.buffer(-.039,join_style=2)
        left=clipped.intersection(box(x0,z0,a-.014,z1))
        right=clipped.intersection(box(b+.014,z0,x1,z1))
        for side,shape in [('left',left),('right',right)]:
            # The masonry pier divides paired windows; each upper light follows the real lintel.
            divs=[.50] if name=='upper' else []
            label=name+' main window '+side
            if name=='middle' or (name=='upper' and side=='left'):
                open_casements(face,shape,label,(46,53) if name=='upper' else (33,43))
            else:
                insert_sash(face,shape,label,divs,[.23,.78],MID_GLASS if side=='left' else GLASS,0)
        panel=outer.difference(unary_union([left,right,pier]))
        face.solid(panel,-.155,-.025,TRIM,name+' casement | rendered fillets around brick and glass')
        outer_rim=outer.buffer(.075,join_style=2).difference(outer)
        face.solid(outer_rim,.003,.038,TRIM,name+' window | masonry architrave')
        face.rect(x0-.08,x1+.08,z0-.09,z0-.022,.006,.078,SILL,name+' window | shared stone sill')

def add_garden_front(face,layout,lod):
    profiles=opening_profiles(layout);wide=wide_openings(lod);single=flat_single_windows()
    holes=unary_union([*wide.values(),*[s for _,s in single],*[p['strip'] for p in profiles]])
    outline=Polygon([(LEFT,0),(TANGENT,0),(TANGENT,ROOF_Z),(STEP,ROOF_Z),(STEP,LOW_WING_Z),(LEFT,LOW_WING_Z)])
    face.solid(outline.difference(holes),-.246,0,RENDER,'continuous garden face with retained stepped silhouette')
    for name,opening in single:
        insert_sash(face,opening,name,[.46],[.69],GLASS)
    casement_pairs(face,wide,profiles)
    add_brick_and_glass(face.b,layout,lod)
    arc_band(face,-.246,0,.0,ROOF_Z,RENDER,'unbroken circular corner',lod)
    for z in COURSES:
        start=LEFT if z<LOW_WING_Z else STEP
        for z0,z1,proj,mat,tag in [(z-.046,z+.010,.080,SILL,'undercut'),(z+.010,z+.065,.133,TRIM,'upper ledge')]:
            field=box(start,z0,TANGENT,z1).difference(holes)
            face.solid(field,.003,proj,mat,'garden cornice | '+tag)
            arc_band(face,0,proj,z0,z1,mat,'garden cornice | curved '+tag,lod)
    for l,r,z in [(LEFT,STEP,LOW_WING_Z),(STEP,TANGENT,ROOF_Z)]:
        face.rect(l,r,z-.075,z-.013,.004,.102,TRIM,'parapet | projecting light edge')
        face.rect(l,r,z-.013,z+.052,.002,.123,ROOF,'parapet | weathered cap')
    arc_band(face,0,.102,ROOF_Z-.075,ROOF_Z-.013,TRIM,'curved parapet edge',lod)
    arc_band(face,0,.123,ROOF_Z-.013,ROOF_Z+.052,ROOF,'curved parapet weathering',lod)
    face.solid(box(LEFT,.020,TANGENT,.26).difference(holes),.001,.033,BASE,'garden plinth')
    arc_band(face,0,.033,.020,.26,BASE,'curved plinth',lod)

    # Rainwater hopper and pipe on the two-storey wing, visible to the left of the inscriptions.
    u,z=hit(207,177)
    face.rect(u-.105,u+.105,z-.12,z+.075,.020,.163,TRIM,'left garden wing | small rainwater hopper')
    face.rect(u-.135,u+.135,z+.063,z+.102,.007,.170,SILL,'left garden wing | flared hopper rim')
    face.rail([(u,-.096,.35),(u,-.096,z-.124)],.042,TRIM,'left garden wing | downpipe',8 if lod else 14)
    for h in [1.06,2.76,4.39,5.65]:
        face.rect(u-.066,u+.066,h-.019,h+.019,.050,.151,SILL,'left garden wing | pipe clip')

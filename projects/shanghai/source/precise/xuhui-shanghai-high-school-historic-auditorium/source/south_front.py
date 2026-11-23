"""Stepped south front of the auditorium. The projecting doorhead is authored separately."""
from pathlib import Path
import json
import numpy as np
from shapely.geometry import Polygon,LineString,box
from shapely.ops import unary_union
from photo_architecture import Facade
from finish_surfaces import WALL,TRIM,STEP

DATA=Path(__file__).absolute().parents[1]/'measurements/hall-envelope.json'
PREFIX='Shanghai High School hall | '
DARK=PREFIX+'dark lower plinth'
GROOVE=PREFIX+'shadow in cast ornament'
FIELD=PREFIX+'recessed facade panels'
COVER=PREFIX+'weathering on flat surfaces'
PALETTE={DARK:dict(color=[.25,.27,.255],roughness=.89),GROOVE:dict(color=[.396,.399,.372],roughness=.90),
         FIELD:dict(color=[.708,.706,.655],roughness=.94),COVER:dict(color=[.383,.395,.370],roughness=.97)}
def strip(face,u,z,width,height,material,label,projection=.07):
    face.box(u,z,width,height,projection+.015,(projection-.015)/2,material,label)

def lozenge(cx,z,w,h):
    return Polygon([(cx-w/2,z),(cx,z+h/2),(cx+w/2,z),(cx,z-h/2)])

def decorative_pier(face,u,width,top,large,lod):
    # The broad-faced blade runs from the raised plinth to the pierced-looking
    # rhombus in the head. A recessed line gives the rhombus a real profile.
    stem=width*.81
    face.box(u,(top-.16)/2,stem,top-.16,.215,.077,TRIM,'pier shaft')
    shoulder=top-2.12
    profile=Polygon([(u-width*.50,shoulder),(u-width*.50,top-.12),(u-width*.42,top),
                     (u+width*.42,top),(u+width*.50,top-.12),(u+width*.50,shoulder),
                     (u+stem*.50,shoulder-.18),(u-stem*.50,shoulder-.18)])
    motif=lozenge(u,top-.99,width*.70,1.64)
    face.prism(profile.difference(motif),.120,.227,TRIM,'pier head with diamond incision')
    face.prism(motif,.120,.166,GROOVE,'shaded diamond bed')
    inner=lozenge(u,top-.99,width*.61,1.46)
    face.prism(inner,.164,.206,TRIM,'raised diamond field')
    if not lod:
        cut=lozenge(u,top-1.15,width*.35,.82).difference(lozenge(u,top-1.15,width*.27,.65))
        face.prism(cut,.205,.217,FIELD,'nested diamond on the pier head')
        for hand in (-1,1):
            rib=LineString([(u+hand*width*.31,top-.44),(u+hand*width*.13,top-1.04),(u,top-1.56)]).buffer(.016,cap_style=2)
            face.prism(rib,.206,.220,TRIM,'fanned incision at the pier cap')
    for z,h,p in [(1.48,.091,.163),(shoulder-.23,.048,.163),(shoulder-.12,.063,.194)]:
        strip(face,u,z,stem+.08,h,TRIM,'framing course across shaft',p)
    if large or not lod:
        for sign in (-1,1):
            face.box(u+sign*(stem/2-.043),(shoulder+1.70)/2,.034,shoulder-1.70,.022,.184,FIELD,'fluted shaft arris')

def relief_band(face,l,r,z,h):
    count=max(2,round((r-l)/.81));pitch=(r-l)/count
    strip(face,(l+r)/2,z+h/2,r-l,h,TRIM,'frieze backing',.087)
    segments=[]
    for i in range(count):
        x=l+i*pitch
        segments.append(LineString([(x+.03,z+.10),(x+pitch*.50,z+h-.06),(x+pitch-.03,z+.10)]).buffer(.023,join_style=2,cap_style=2))
        segments.append(LineString([(x+.08,z+.08),(x+pitch*.50,z+h-.145),(x+pitch-.08,z+.08)]).buffer(.014,join_style=2,cap_style=2))
    face.prism(unary_union(segments),.088,.113,FIELD,'nested folded frieze')
    for hh in [z-.032,z+h+.02]:strip(face,(l+r)/2,hh,r-l,.049,TRIM,'bead around frieze',.13)

def outer_fields(face,l,r,top,lod):
    center=(l+r)/2;width=r-l
    # Ribbed rectangular field below the upper mouldings, visible in the
    # historic photograph at the second pair of bays from each end.
    floor=13.89;head=15.33
    frame=box(l+.11,floor,r-.11,head).difference(box(l+.22,floor+.094,r-.22,head-.10))
    face.prism(frame,.008,.083,TRIM,'surround of ribbed rectangular frieze')
    face.prism(box(l+.22,floor+.094,r-.22,head-.10),.006,.022,FIELD,'recess behind fluting')
    pitch=.209 if lod else .111
    for x in np.arange(l+.27,r-.25,pitch):
        face.box(x,(floor+head)/2,.034 if lod else .024,head-floor-.20,.043,.045,TRIM,'vertical rib')
    strip(face,center,15.53,width,.115,TRIM,'upper sill below narrow frieze',.12)
    relief_band(face,l+.08,r-.08,top-1.39,.46)
    for level in (top-.665,top-.39,top-.136):
        strip(face,center,level,width,.073,TRIM,'stepped horizontal at the parapet',.15 if level==top-.136 else .10)

def wing_panel(face,x,width,z):
    # A triangular point and ribbed panel on either side of the entrance remain
    # visible in the 2020 photo. Other tree-covered openings are left unscheduled.
    lower=box(x-width/2,z,x+width/2,z+1.84)
    triangle=Polygon([(x-width/2,z+1.88),(x,z+3.14),(x+width/2,z+1.88)])
    face.prism(lower,.021,.058,FIELD,'lower rectangular field')
    face.prism(lower.difference(lower.buffer(-.065,join_style=2)),.055,.093,TRIM,'lower field margin')
    face.prism(triangle,.026,.080,TRIM,'pointed head of side panel')
    for sign in (-1,1):
        v=LineString([(x+sign*width*.422,z+2.00),(x,z+2.98)]).buffer(.020,cap_style=2)
        face.prism(v,.079,.098,GROOVE,'diagonal in pointed head')
    for xx in np.arange(x-width*.42,x+width*.43,.11):
        face.box(xx,z+.92,.021,1.68,.016,.063,TRIM,'narrow field striations')
    strip(face,x,z+1.86,width+.15,.109,TRIM,'cap below pointed panel',.148)

def add_current_fields(face,camera,polygons):
    # Convert inclined-photo coordinates back to the articulated masonry plane.
    for name,points in polygons.items():
        outline=Polygon([camera.wall(uv)[[0,2]] for uv in points])
        if name.startswith('fourth_'):
            face.prism(outline,.030,.065,TRIM,name.replace('_',' '))
            for t in (.066,.151):
                inner=outline.buffer(-t,join_style=2)
                bead=inner.difference(inner.buffer(-.022,join_style=2))
                face.prism(bead,.064,.089,FIELD,'fold in outer triangle')
        elif name.startswith('separator_'):
            face.prism(outline,.038,.088,TRIM,'divider between central relief panels')
        else:
            face.prism(outline,.063,.154,TRIM,name.replace('_',' '))

def build_south(b,lod=False):
    d=json.loads(DATA.read_bytes());w=d['estimated_south_wall_width'];half=w/2;axes=d['south_pier_axes_x']
    face=Facade(b,(-half,0),(half,0),'South facade')
    top=d['south_top_z']
    silhouette=unary_union([box(-half,0,half,top),box(axes[2],top-.22,axes[3],top+.61)])
    # A recessed centre is protected by the projecting six-leaf door porch.
    aperture=box(-4.10,-.001,4.10,6.75)
    face.prism(silhouette.difference(aperture),-.36,0,WALL,'main wall and stepped silhouette')
    for l,r in ((-half,-4.10),(4.10,half)):
        strip(face,(l+r)/2,.81,r-l,1.62,DARK,'lower plinth',.038)
        strip(face,(l+r)/2,1.67,r-l,.12,TRIM,'upper plinth edge',.094)
    for i,x in enumerate(axes):
        central=i in (2,3);cap=d['central_pier_top_z'] if central else d['outer_pier_top_z']
        decorative_pier(face,x,1.02 if central else .85,cap,central,lod)
    for idx,(l,r) in enumerate(zip(axes,axes[1:])):
        if idx!=2:outer_fields(face,l+.42,r-.42,top,lod)
    from register_court import Camera
    current=Camera('2020')
    fields=json.loads((DATA.parent/'south-facade-fields.json').read_bytes())
    west,east=fields['lower_plaque_apices_native_2020']
    for pixel,width in zip((west,east),fields['estimated_outer_plaque_widths_m']):
        x,_,point=current.wall(pixel)
        wing_panel(face,x,width,point-3.14)
    add_current_fields(face,current,fields['polygons_native_2020'])
    # Front block visible above the side roofs in both time periods.
    for a,c in [( (-half,d['front_head_depth_y']),(-half,0) ),((half,0),(half,d['front_head_depth_y']))]:
        side=Facade(b,a,c,'South facade | outer return')
        # The east side wall author supplies openings along this plane.
        if a[0]<0:side.box(0,top/2,side.length,top,.31,-.15,WALL,'blind return')
        if a[0]<0:side.box(0,top-.12,side.length,.24,.38,-.09,TRIM,'returned parapet rim')

def porch_structure(b):
    from entrance_planes import APRON_Y,DOOR_Y
    face=Facade(b,(-15.75,APRON_Y),(15.75,APRON_Y),'Portal | monumental jambs')
    # These outer jambs meet the authored apron. Their broad sides return to
    # the door reveal; the two surfaces are visibly separated in the 1934 view.
    sides=[(-6.44,-4.92,-6.36,-5.03,10.66),(4.17,6.12,4.15,6.07,10.84)]
    for l,r,lt,rt,z in sides:
        jamb=Polygon([(l,.055),(r,.055),(rt,z),(lt,z)])
        face.prism(jamb,-(DOOR_Y-APRON_Y+.35),.010,TRIM,'deep cheek beside the doorhead')
        width=r-l;u=(l+r)/2
        face.box(u,.70,width+.025,1.32,.111,.003,DARK,'lower plinth on entrance cheek')
        for dx in (-.33,.33):
            strip(face,u+dx*width,8.07,.036,3.65,FIELD,'fine cutting in the upper cheek',.034)
        # Retain the folded head seen in the historic oblique photograph.
        outer=lozenge((lt+rt)/2,z-.65,(rt-lt)*.59,1.10)
        inner=lozenge((lt+rt)/2,z-.65,(rt-lt)*.51,.91)
        face.prism(outer.difference(inner),.017,.042,FIELD,'thin lozenge in upper end of cheek')
    x0,x1=-6.44,6.12
    # An entrance roof lies back from the embossed apron. The space directly
    # below the front rim exposes a soffit between the large jambs.
    def volume(l,r,y0,y1,z0,z1,mat,label):
        b.box(((l+r)/2,(y0+y1)/2,(z0+z1)/2),(r-l,y1-y0,z1-z0),mat,label='Portal | '+label)
    volume(x0,x1,APRON_Y+.32,.12,8.29,8.46,COVER,'flat roof inside relief parapet')
    for l,r in [(x0,x0+.28),(x1-.28,x1)]:
        volume(l,r,DOOR_Y+.12,.12,.014,8.42,WALL,'side wall returning to the main frontage')
    volume(-4.94,4.22,APRON_Y+.04,DOOR_Y+.12,6.81,6.94,TRIM,'soffit behind front apron')
    volume(x0,x1,DOOR_Y+.24,DOOR_Y+.39,.040,6.86,DARK,'backing behind the closed entrance')
    # A front return reaches the jamb of the six-leaf entrance on both sides.
    for l,r in [(x0,-4.64),(4.846,x1)]:
        volume(l,r,DOOR_Y-.04,DOOR_Y+.31,.025,8.38,WALL,'return to timber frame')

def raised_center(b):
    # In the oblique original the uppermost short parapet is shifted right
    # against the four central windows. It also sits behind their elevation
    # in the independently dated aerial views.
    x0,x1=-5.27,5.27;y0,y1=6.99,7.54
    f=Facade(b,(x0,y0),(x1,y0),'Upper hall | set-back crest')
    # The parapet must bear on both roof slopes. Coping the foot to the
    # pitch leaves the top silhouette unchanged from the two photo stations.
    d=json.loads(DATA.read_bytes())
    crest=d['roof_eave_z']+d['roof_pitch_rise']
    foot_at_end=crest-d['roof_pitch_rise']*x1/d['auditorium_red_roof_half_span']
    seat=Polygon([(x0,foot_at_end-.06),(0.,crest-.06),(x1,foot_at_end-.06),
                  (x1,17.32),(x0,17.32)])
    f.prism(seat,-(y1-y0),0.,WALL,'masonry seat across both roof slopes')
    f.box(0,19.16,f.length,3.77,y1-y0,-(y1-y0)/2,WALL,'upper step in silhouette')
    strip(f,0,20.90,f.length+.08,.16,TRIM,'weathering course over upper step',.14)
    for x in (x0+.13,x1-.13):
        strip(f,x,19.59,.23,2.85,TRIM,'upright at crest edge',.10)

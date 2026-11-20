"""Study of the street elevation of the 1933 Metropol Cinema, from period photographs."""
import json
from functools import lru_cache
from pathlib import Path
import sys

from shapely import affinity
from shapely.geometry import Polygon, box
from shapely.geometry.polygon import orient

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
sys.path.insert(0, str(PROJECT/'tools'))
from package_architectural_model import build
from photo_architecture import Facade, opening
from sign_lettering import lettering_shapes

P = json.loads((HERE/'parameters.json').read_text())
FIN = P['fin_centres_m']
W = P['width_m']
H = P['roof_m']
DEPTH = P['structural_section_depth_m']
CANOPY = P['canopy_top_m']
FONT = HERE/'fonts/MetropolSignSubset.otf'
META = {
    'id': P['id'], 'name':'大上海大戏院历史立面（1933年建筑）',
    'status':'historical-photo-informed-facade-study',
    'scope':'Historical architectural study of the 1933 Metropol Cinema street elevation as photographed in 1934–1937. Demolished historical building. Standalone historical viewing only.',
    'model_scope_zh':'1934—1937年照片中的大上海大戏院临街立面。建于1933年的原影院列入《上海名建筑志》湮没建筑表。模型保留灯柱、侧窗、雨篷、门厅入口与中英文挑牌，尺度和颜色推定。后方观众厅、内部、屋顶和重建后商场均未建模。',
    'viewer_page':'metropol-cinema-history.html', 'audit_directory':'data/audit/metropol-cinema-history-v1/',
    'source_register':'source/precise/'+P['id']+'/reference-review.json',
    'geometry_period_zh':'1934至1937年照片所示的1933年建筑',
    'city_integration':{'period':'historical-only','shown_in_current_city':False,'current_owner_replacement':False,'current_collision':False},
    'coordinate_convention':'GLB local X positive to the observer’s right, Y up, Z toward the historic street; origin at grade along centre of the facade. Metric dimensions are visual estimates.',
    'interiors_modeled':False,'original_geometry':True,'bundled_font_software_license':'SIL OFL 1.1',
    'historic_address_variants':['西藏中路520号（项目保护名录转录）','西藏中路500号（地方志）','500 Thibet Road / 500 Yuyaching Road（历史影像与建筑档案）'],
}
PALETTE = {
    'polished charcoal':{'color':[.125,.123,.117],'roughness':.35},
    'black marble':{'color':[.055,.052,.049],'roughness':.24},
    'lamp glass':{'color':[.68,.70,.65],'roughness':.24,'metallic':.21},
    'lamp collar':{'color':[.26,.27,.24],'roughness':.32,'metallic':.52},
    'ribbed spandrel':{'color':[.20,.20,.185],'roughness':.49},
    'period glazing':{'color':[.19,.23,.22],'roughness':.20,'metallic':.23},
    'dark joinery':{'color':[.087,.087,.079],'roughness':.43,'metallic':.24},
    'silver aluminium':{'color':[.49,.48,.431],'roughness':.38,'metallic':.55},
    'poster backing':{'color':[.51,.46,.36],'roughness':.81},
    'display mount':{'color':[.26,.244,.197],'roughness':.68},
    'section edge':{'color':[.265,.245,.21],'roughness':.88},
    'opal sign':{'color':[.82,.80,.64],'roughness':.32},
}


def glazed_opening(f,shape,label,lod=False):
    """Narrow metal reveals and frames. Sills are modeled by each elevation."""
    perimeter=shape.buffer(-.055,join_style=2)
    x0,z0,x1,z1=shape.bounds
    panes=perimeter if lod else perimeter.difference(box(x0,(z0+z1)*.5-.019,x1,(z0+z1)*.5+.019))
    f.prism(shape.buffer(.009,join_style=2),-.28,-.25,'period glazing',label+'/glass')
    f.prism(shape.difference(panes),-.235,-.19,'dark joinery',label+'/frame')


def wings(builder, lod):
    inner = abs(FIN[-1])+.27
    for side in [-1,1]:
        left,right = sorted((side*inner,side*W/2))
        f = Facade(builder,(left,0),(right,0),'Flanks/'+('left' if side<0 else 'right'))
        holes = [opening(x,z,.88,1.72 if z<10 else 1.61)
                 for z in P['wing_window_bases_m'] for x in (-1.34,0,1.34)]
        f.wall(CANOPY-.14,H,holes,thickness=DEPTH,material='polished charcoal')
        for shape in holes:
            glazed_opening(f,shape,'upper openings',lod)
        for z in P['wing_window_bases_m']:
            f.box(0,z-.05,3.76,.095,.17,.055,'lamp collar','continuous sill')
        if not lod:
            for z in (7.66,12.02,16.40,20.48):
                f.box(0,z,right-left-.025,.020,.013,.008,'black marble','stone joint')


def light_screen(builder,lod):
    fl = Facade(builder,(-6.36,0),(6.36,0),'Central screen')
    fl.wall(CANOPY-.10,H,thickness=DEPTH,material='dark joinery')
    top = H+.28
    for i, x in enumerate(FIN):
        label = f'Shaft {i+1:02}'
        # Picture Ro-n1142 resolves horizontal collars through the square
        # glazed jackets, with unbroken bright faces on each intervening panel.
        fl.box(x,(CANOPY+top)/2,.53,top-CANOPY,.68,.17,'lamp collar',label+'/armature')
        n = 11
        z0=CANOPY+.095
        height=(top-z0)/n
        for j in range(n):
            fl.box(x,z0+(j+.5)*height,.55,height-.035,.64,.22,'lamp glass',label+'/segmented glass')
        fl.box(x,top+.017,.56,.034,.69,.19,'silver aluminium',label+'/cap')
    for i,(a,b) in enumerate(zip(FIN,FIN[1:])):
        x=(a+b)/2
        w=b-a-.53
        label=f'Bay {i+1:02}'
        fl.box(x,5.80,w,3.31,.15,.09,'period glazing',label+'/lower glazed lights')
        for z in (4.51,5.19,5.86,6.52,7.35):
            fl.box(x,z,w,.06,.115,.19,'silver aluminium',label+'/lower transom')
        for dx in (-.30,.30):
            fl.box(x+dx,5.78,.043,3.28,.09,.17,'dark joinery',label+'/lower mullion')
        fl.box(x,8.34,w,1.65,.20,.075,'ribbed spandrel',label+'/solid spandrel')
        fl.box(x,9.92,w,1.46,.15,.065,'period glazing',label+'/square middle window')
        fl.box(x,9.92,.046,1.46,.08,.20,'dark joinery',label+'/middle mullion')
        fl.box(x,10.69,w,.09,.17,.16,'lamp collar',label+'/middle lintel')
        # The seven dark fluted panels are clear in the near-frontal 1937 plate.
        fl.box(x,16.05,w,10.62,.17,.08,'ribbed spandrel',label+'/tall upper infill')
        grooves=4 if lod else 9
        for j in range(grooves):
            u=x-w/2+(j+.5)*w/grooves
            fl.box(u,16.05,.05 if lod else .038,10.58,.062,.185,'dark joinery',label+'/vertical flute')


def porch(builder,lod):
    f = Facade(builder,(-W/2,.70),(W/2,.70),'Entrance')
    doors=[opening(x,.48,.90,2.86) for x in (-2.88,-1.80,-.72,.72,1.8,2.88)]
    f.wall(0,CANOPY-.13,doors,thickness=.50,material='black marble')
    for shape in doors:
        glazed_opening(f,shape,'recessed glazed door')
    for x in (-2.88,-1.80,-.72,.72,1.8,2.88):
        f.box(x+.25,1.68,.047,.44,.10,-.12,'silver aluminium','door pull')
    for x in (-5.14,5.14):
        f.box(x,1.77,1.38,2.02,.15,.085,'silver aluminium','poster frame')
        f.box(x,1.77,1.23,1.86,.045,.182,'poster backing','unlettered poster mount')
        f.box(x,1.77,1.01,1.61,.030,.226,'display mount','display inset')
    for x in (-8.88,8.88):
        f.box(x,2.03,3.66,2.83,.12,.08,'dark joinery','flanking shopfront sash')
        f.box(x,2.03,3.48,2.63,.06,.169,'period glazing','flanking shopfront glazing')
        for dx in (-.85,0,.85):
            f.box(x+dx,2.03,.058,2.65,.08,.22,'silver aluminium','shopfront mullion')
        f.box(x,2.72,3.49,.063,.09,.23,'silver aluminium','shopfront transom')
    for j in range(4):
        height=.12*(4-j)
        builder.box((0,.48-.29*j,height/2),(7.49,.29,height),'granite base',label='Entrance/four stair treads')
    # A projecting centre marquee shelters the entrance. Wing bands are shallower.
    outline=Polygon([(-W/2,.72),(W/2,.72),(W/2,-.88),(6.61,-.88),(6.61,-1.78),
                     (-6.61,-1.78),(-6.61,-.88),(-W/2,-.88)])
    builder.plan_prism(outline,CANOPY-.33,CANOPY,'black marble','Marquee/faceted rain canopy')
    front=Facade(builder,(-6.61,-1.78),(6.61,-1.78),'Marquee')
    for z in (CANOPY-.30,CANOPY-.045):
        front.box(0,z,13.22,.032,.06,.03,'silver aluminium','edge moulding')
    if not lod:
        for x in (-4.75,-2.37,0,2.37,4.75):
            front.box(x,CANOPY-.345,.19,.025,.19,-.67,'opal sign','soffit light')


@lru_cache(maxsize=None)
def glyph(char, width, height):
    return lettering_shapes(char,width,height,font=FONT)[0][1]


def sign(builder,lod):
    # A pair of outward-facing sign facets gives the street approach its two
    # sightlines. The unreadable film title on the marquee is left unlettered.
    x=-10.69
    p=orient(Polygon([(x-.61,-.09),(x+.61,-.09),(x+.10,-1.69),(x-.10,-1.69)]))
    bot,top=4.39,19.02
    builder.plan_prism(p,bot,top,'black marble','Blade/bilingual projecting sign')
    for z in (bot+.04,top-.04):
        builder.plan_prism(p.buffer(.025,join_style=2),z-.04,z+.04,'lamp collar','Blade/rims')
    pts=list(p.exterior.coords)
    for a,b in zip(pts,pts[1:]):
        if abs(a[1]-b[1])<1:continue
        ident='left' if (a[0]+b[0])/2<x else 'right'
        f=Facade(builder,a,b,'Blade/'+ident)
        for j,char in enumerate('大上海大戲院'):
            shape=glyph(char,.84,.81)
            tol=.008 if lod else .0015
            f.prism(affinity.translate(shape.simplify(tol,preserve_topology=True),yoff=top-1.31-j*.99),
                    .007,.038,'opal sign','Chinese title')
        for j,char in enumerate('METROPOL'):
            shape=glyph(char,.79,.71)
            f.prism(affinity.translate(shape.simplify(.006 if lod else .0013,preserve_topology=True),yoff=12.04-j*.91),
                    .007,.039,'opal sign','English title')
        for z in (top-.33,top-.50,bot+.18,bot+.35):
            f.box(0,z,f.length-.12,.044,.042,.026,'silver aluminium','edge stripes')


def assemble(builder,lod):
    wings(builder,lod)
    light_screen(builder,lod)
    porch(builder,lod)
    sign(builder,lod)
    # Label the conventionally closed cut so a rear view can be identified
    # in Blender. No auditorium roof/depth is asserted from the street photo.
    builder.box((0,DEPTH+.03,H/2),(W,.06,H),'section edge',label='Section/plain rear cut')


if __name__=='__main__':
    build(HERE,META,PALETTE,assemble)

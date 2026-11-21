"""A free-standing architectural detail of two rounded eaves on the historic Wuxing Road residence."""
from pathlib import Path
import argparse,math,os,sys
import numpy as np
from shapely import constrained_delaunay_triangles
from shapely.geometry import Polygon

SOURCE=Path(__file__).resolve().parent
PROJECT=next(p for p in SOURCE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(PROJECT/'tools'))
import package_architectural_model
sys.path.insert(0,str(PROJECT/'source/precise/huangpu-somekh-building-street-corner/source'))
from aggregate_mesh import AggregateBuilder
from washed_finish import MATERIAL as WASH,PERIOD,TEXTURE

ID='xuhui-wuxing-96-curved-cornice'
META=dict(id=ID,name='吴兴路96号花园住宅圆角檐口与窗罩',viewer_page='wuxing-96-curved-cornice.html',
          heritage_group='4D043',scope='按建筑史出版图制作的独立历史装饰构件小样。')
GLAZES=['Ochre glazed ceramic','Honey glazed ceramic','Weathered buff glaze','Brown glazed ceramic']
MAIN='Muted tan upper fascia';EDGE='Upper rolled edge';SHADE='Shadowed eave soffit'
JOINT='Weathered lime joint';CUT='Unfinished section';KERF='Dark drip groove'
STEEL='Dark steel window casing';GLASS='Muted blue glass';VENEER='Light ceramic window trim'

def pigment(rgb, roughness=.78, metallic=0.):
    v=np.asarray(rgb,dtype=float)/255.
    return dict(color=np.where(v<=.04045,v/12.92,((v+.055)/1.055)**2.4).tolist(),roughness=roughness,metallic=metallic)

PALETTE={**{n:pigment(c,.37,.05)for n,c in zip(GLAZES,[(135,112,91),(142,116,93),(132,114,96),(128,104,86)])},
         WASH:dict(color=[1.,1.,1.],roughness=.92,texture=str(TEXTURE)),
         MAIN:pigment((186,153,113)),EDGE:pigment((201,171,131)),SHADE:pigment((115,104,91)),
         JOINT:pigment((104,94,82)),CUT:pigment((134,124,113)),KERF:pigment((72,64,53)),
         STEEL:pigment((65,68,62),.52,.29),GLASS:pigment((102,139,150),.3,.16),VENEER:pigment((206,187,156),.51,.06)}
WINDOW_SPLIT=-.045
FRIEZE_TOP=1.067
MAIN_SOFFIT=1.052
RADIUS=.55
TURN=math.pi*RADIUS/2
LEFT=-1.28
RIGHT=TURN+.67

def position(station, offset, z):
    if station<0:return (station,-offset,z)
    if station<=TURN:
        a=station/RADIUS
        return ((RADIUS+offset)*math.sin(a),RADIUS-(RADIUS+offset)*math.cos(a),z)
    return (RADIUS+offset,RADIUS+station-TURN,z)

def stations(a,b,segments):
    # Tangency points stay present even at distance. The two straight returns never kink.
    return sorted({a,b,*[float(t) for t in np.linspace(0,TURN,segments+1)if a<t<b]})

def swept_profile(b,a,c,profile,materials,tag,lod,subdiv=None):
    """Solid profile on a line–quarter-circle–line path, including two true cut faces."""
    values=stations(a,c,subdiv or (14 if lod else 48))
    for j,material in enumerate(materials):
        k=(j+1)%len(profile);r1,z1=profile[j];r2,z2=profile[k]
        vs=[];uv=[];fs=[];previous=None;distance=[0.,0.]
        for t in values:
            p=position(t,r1,z1);q=position(t,r2,z2)
            if previous is not None:
                for i,point in enumerate((p,q)):
                    distance[i]+=math.dist(previous[i],point)
            previous=(p,q)
            vs.extend([p,q])
            uv.extend([(distance[0]/PERIOD,0.),(distance[1]/PERIOD,math.dist(p,q)/PERIOD)])
        for i in range(len(values)-1):fs.append((2*i,2*i+2,2*i+3,2*i+1))
        b.add(vs,fs,material,tag)
        if material==WASH:b.parts[-1]['texcoords']=uv
    section=Polygon(profile)
    assert section.is_valid and section.area>0
    for t,reverse in [(a,True),(c,False)]:
        vertices=[];faces=[]
        for tri in constrained_delaunay_triangles(section).geoms:
            if not section.covers(tri.representative_point()):continue
            idx=len(vertices);vertices.extend([position(t,q,z)for q,z in list(tri.exterior.coords)[:3]])
            faces.append((idx+2,idx+1,idx)if reverse else(idx,idx+1,idx+2))
        b.add(vertices,faces,CUT,tag+' section')

def tiled_band(b,a,c,base,top,rows,pitch,face,label,lod,stagger=False):
    """Individual fired units, with recessed mortar joints and a slight edge bevel."""
    swept_profile(b,a,c,[(face-.072,base),(face-.008,base),
                         (face-.008,top),(face-.072,top)],
                  [CUT,JOINT,CUT,CUT],label+' / lime joints',lod)
    step=(top-base)/rows
    for row in range(rows):
        shift=-pitch/2 if stagger and row%2 else 0.
        count=math.ceil((c-a-shift)/pitch)
        for i in range(count):
            x=max(a,a+shift+i*pitch)+.002
            stop=min(c,a+shift+(i+1)*pitch)-.002
            if stop-x<.008:continue
            z=base+row*step+.002;upper=base+(row+1)*step-.002
            material=GLAZES[(i*3+row+int(i/3))%len(GLAZES)]
            profile=[(face-.008,z),(face-.003,z),(face,z+.002),
                     (face,upper-.002),(face-.003,upper),(face-.008,upper)]
            swept_profile(b,x,stop,profile,[JOINT,material,material,material,JOINT,JOINT],
                          f'{label} / course {row+1}',lod,12 if lod else 42)

def brick_field(b,lod):
    # The published photograph shows a regular grid above the flat window head.
    # The high point of the curved hood hides the bottom courses on the right.
    tiled_band(b,LEFT,RIGHT,.693,FRIEZE_TOP,7,.072,.015,'Frieze',lod)

def upper_eave(b,lod):
    base=MAIN_SOFFIT
    prof=[(-.106,base),(.029,base),(.060,base+.008),(.225,base+.026),
          (.243,base+.024),(.245,base+.036),(.271,base+.035),
          (.284,base+.052),(.296,base+.070),(.301,base+.097),
          (.297,base+.110),(.292,base+.112),(.291,base+.129),
          (.300,base+.135),(.297,base+.170),(.286,base+.189),
          (.268,base+.196),(-.106,base+.196)]
    mats=[SHADE,SHADE,SHADE,SHADE,KERF,KERF,SHADE,MAIN,MAIN,MAIN,KERF,KERF,
          KERF,EDGE,EDGE,EDGE,MAIN,CUT]
    swept_profile(b,LEFT-.020,RIGHT+.012,prof,mats,'Upper eave / broad rounded cornice',lod)

def window_brow(b,lod):
    z=.674
    # Only the rounded window has the projecting exposed-aggregate lip.
    # Below the lip the photograph resolves two small ceramic courses in shade.
    tiled_band(b,WINDOW_SPLIT,RIGHT-.026,z,z+.120,2,.083,.118,
               'Curved window / glazed apron',lod)
    swept_profile(b,WINDOW_SPLIT,RIGHT-.026,[(-.080,z-.009),(.031,z-.009),
                  (.110,z-.002),(.117,z+.004),(.113,z+.010),(-.080,z+.010)],
                  [SHADE,SHADE,SHADE,SHADE,CUT,CUT],'Curved window / recessed underside',lod)
    prof=[(-.082,z+.112),(.127,z+.112),(.137,z+.117),(.139,z+.124),
          (.147,z+.125),(.153,z+.129),(.154,z+.151),(.148,z+.158),
          (.134,z+.161),(-.082,z+.161)]
    mats=[SHADE,SHADE,KERF,KERF,WASH,WASH,WASH,WASH,WASH,CUT]
    swept_profile(b,WINDOW_SPLIT,RIGHT-.026,prof,mats,'Curved window / washed hood lip',lod)
    # The rectangular window at the left has a lower and much flatter lintel.
    flat=[(-.082,.574),(.018,.574),(.039,.580),(.043,.596),(.041,.606),
          (.029,.610),(.032,.621),(.031,.686),(.021,.697),(-.082,.697)]
    swept_profile(b,LEFT+.012,WINDOW_SPLIT,flat,
                  [SHADE,EDGE,EDGE,EDGE,KERF,KERF,MAIN,MAIN,MAIN,CUT],
                  'Flat window / rectangular head',lod)
    # The fragment ends mid-glazing. The blue panes orient the small hood relative to its casing.
    for start,end,head in [(LEFT+.021,WINDOW_SPLIT,.574),(WINDOW_SPLIT,RIGHT-.035,z)]:
        swept_profile(b,start,end,[(-.078,.03),(-.061,.03),(-.061,head),(-.078,head)],
                      [CUT,GLASS,GLASS,CUT],'Window / cropped glass',lod)
        for level,h in [(.035,.036),(.392 if start<WINDOW_SPLIT else .445,.019),(head-.014,.028)]:
            swept_profile(b,start,end,[(-.08,level-h/2),(-.037,level-h/2),
                          (-.037,level+h/2),(-.08,level+h/2)],[STEEL]*4,
                          'Window / horizontal steel bars',lod)
    for t in [LEFT+.029,-.76,-.31,.12,TURN-.14,RIGHT-.054]:
        head=.574 if t<WINDOW_SPLIT else z
        swept_profile(b,t,t+.030,[(-.083,.018),(-.035,.018),(-.035,head),(-.083,head)],
                      [STEEL]*4,'Window / upright steel casing',lod)
    # The cream upright visible at the tangent emphasizes the change of direction.
    swept_profile(b,-.065,.028,[(-.096,.015),(.068,.015),(.134,z+.163),(-.096,z+.163)],
                  [CUT,VENEER,VENEER,CUT],'Window / pale vertical return',lod)

def add_building(b,lod):
    brick_field(b,lod);upper_eave(b,lod);window_brow(b,lod)

if __name__ == '__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--lod',action='store_true')
    parser.add_argument('--blender',default='blender')
    args,rest=parser.parse_known_args()
    if args.output:
        if rest:parser.error('unexpected raw export arguments: '+' '.join(rest))
        builder=AggregateBuilder(PALETTE)
        add_building(builder,args.lod)
        builder.save(args.output,META)
    else:
        if args.lod:parser.error('--lod requires --output')
        os.environ['WUXING_BLENDER']=args.blender
        sys.argv[1:]=[*rest,'--blender',str(SOURCE/'build_blender_source.py')]
        package_architectural_model.Builder=AggregateBuilder
        package_architectural_model.build(SOURCE,META,PALETTE,add_building)

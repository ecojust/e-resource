"""Four sign panels over the open passage and its return at Fumin Xincun."""
from pathlib import Path
import json, random
from shapely.geometry import shape
from shapely import affinity

def color(rgb,roughness=.82,metallic=0):
    def linear(v):return v/3294.6 if v<=10 else ((v/255+.055)/1.055)**2.4
    return dict(color=[linear(v)for v in rgb],roughness=roughness,metallic=metallic)

PALETTE={
    'grey ochre stucco':color((161,151,130)),'sheltered underside':color((131,125,113)),
    'raised stone margin':color((183,174,155)),'scored bottom edge':color((143,134,117)),
    'buff panel':color((176,165,145)),'claret face':color((81,53,61),.61),
    'claret side':color((56,40,45),.70),'quartz light':color((195,181,155)),
    'grey inclusions':color((142,135,124)),'paler ochre':color((182,169,143))
}
SOURCE=Path(__file__).resolve().parent
PANELS=[(-1.80,.80,.72),(-.57,.81,.73),(.67,.80,.745),(1.86,.79,.745)]
BOUNDS=[(130,241,52,151),(305,423,54,156),(480,596,57,163),(648,761,61,169)]

def box(b,x0,x1,y0,y1,z0,z1,material,label):
    b.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),material,label=label)

def ink_geometry(glyph,index):
    cx,width,height=PANELS[index]
    x0,x1,v0,v1=BOUNDS[index]
    p=affinity.translate(shape(glyph['geometry']),-x0,v1-215)
    p=affinity.scale(p,width/(x1-x0),height/(v1-v0),origin=(0,0))
    return affinity.translate(p,cx-width/2,.385)

def pebbles(b,lod,centre,width,height,index):
    rng=random.Random(818+index)
    colours=['quartz light','grey inclusions','paler ochre']
    batches=[([],[])for _ in colours]
    for k in range(72 if lod else 320):
        x=centre+(rng.random()-.5)*(width-.05);z=.404+rng.random()*(height-.05)
        rx=rng.uniform(.001,.0038);rz=rng.uniform(.001,.0036);vertices,faces=batches[k%3];start=len(vertices)
        vertices.extend([(x-rx,-.0444,z),(x-rx*.13,-.0449,z-rz),(x+rx,-.0444,z+.0003),(x+rx*.22,-.0447,z+rz)])
        faces.extend([(start,start+1,start+2),(start,start+2,start+3)])
    for (vertices,faces),mat in zip(batches,colours):
        b.add(vertices,faces,mat,f'fine render panel {index+1} {mat}')

def add_building(b,lod=False):
    box(b,-2.49,2.5,0,.42,.26,1.28,'grey ochre stucco','face of passage lintel')
    box(b,-2.49,2.5,-.009,.52,.223,.26,'scored bottom edge','continuous lower arris')
    box(b,-2.49,2.5,.05,.55,.198,.224,'sheltered underside','passage soffit')
    box(b,-2.49,2.5,-.075,.42,1.28,1.355,'raised stone margin','projecting top edge')
    for k,(x0,x1) in enumerate([(-2.49,-2.29),(2.30,2.50)]):
        box(b,x0,x1,.08,.51,.015,.224,'grey ochre stucco',f'upper jamb at passage {k+1}')
    glyphs=json.loads((SOURCE/'four-letters.json').read_bytes())['glyphs']
    for i,(cx,width,height) in enumerate(PANELS):
        stem=f'panel {i+1} from photo left'
        box(b,cx-width/2-.018,cx+width/2+.018,-.019,.011,.358,.385+height+.008,'scored bottom edge',stem+' back plate')
        box(b,cx-width/2,cx+width/2,-.044,-.014,.385,.385+height,'buff panel',stem+' front')
        box(b,cx-width/2+.008,cx+width/2-.008,-.047,-.025,.385,.400,'raised stone margin',stem+' lower painted bevel')
        pebbles(b,lod,cx,width,height,i)
        outline=ink_geometry(glyphs[i],i).simplify(.0027 if lod else .0007,preserve_topology=True)
        mapper=lambda x,z,depth:(x,-depth,z)
        b.prism(outline,.044,.068,mapper,'claret side',f'cast letter {i+1} sides')
        crown=outline.buffer(-.004,join_style='round',quad_segs=2)
        if not crown.is_empty:b.prism(crown,.067,.072,mapper,'claret face',f'cast letter {i+1} broad face')

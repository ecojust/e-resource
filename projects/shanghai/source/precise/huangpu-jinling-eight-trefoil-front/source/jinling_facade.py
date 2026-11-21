"""Ground-level shop bays, the upper sashes, and the two runs of timber and stone cornice."""
from pathlib import Path
from math import cos,pi,sin
from shapely import set_precision,affinity
from shapely.geometry import box, Polygon,Point
from shapely.ops import unary_union
from trefoil_arch import CHALK,LIMESTONE,FILLET,RECESS,LEAF,TIMBER,GLASS, color
from vestibule import round_lintel, IRON,STEP
from sign_lettering import lettering_shapes

PLINTH='Jinling pale speckled plinth'
SIGN='Jinling red 2021 trade sign'
GILT='Jinling warm sign lettering'
GLAZING='Jinling cool recessed top light'
SHUTTER='Jinling dark shop-window muntins'
PALETTE={k:{'color':color(c),'metallic':m,'roughness':r} for k,c,m,r in [
    (PLINTH,(166,160,143),0,.84),(SIGN,(152,52,46),.10,.68),
    (GILT,(216,187,127),.25,.50),(GLAZING,(115,127,126),.15,.35),
    (SHUTTER,(71,72,63),.25,.65)]}

class Front:
    def __init__(self,builder,extent):
        self.builder=builder
        self.extent=extent
        self.cut=box(extent[0],-.02,extent[1],30.)
    def box(self,name,material,a,b,y0,y1,z0,z1):
        assert a<b and y0<y1 and z0<z1,name
        a=max(a,self.extent[0]);b=min(b,self.extent[1])
        if b<=a:return
        self.builder.box(((a+b)/2,(y0+y1)/2,(z0+z1)/2),(b-a,y1-y0,z1-z0),material,label=name)
    def profile(self,name,material,poly,y0,y1):
        if not poly.is_empty and (poly.bounds[0]<self.extent[0] or poly.bounds[2]>self.extent[1]):
            poly=poly.intersection(self.cut)
        if not poly.is_empty and poly.area>1e-10:
            self.builder.prism(poly,-y1,-y0,lambda x,z,d:(x,-d,z),material,name)

def lettering(front,x,z,y,lod):
    font=Path(__file__).with_name('shop-inscription.otf')
    for char,shape in lettering_shapes('烟酒商行',1.85,.43,font=font):
        # From the pavement the local east-to-west X coordinate reads right to left.
        mapped=affinity.translate(affinity.scale(shape,-1,1,origin=(0,0)),xoff=x,yoff=z)
        simplified=set_precision(mapped.simplify(.0028 if lod else .001),.00018)
        front.profile('Dated shop sign '+char,GILT,simplified,y,y+.018)

def sash(front,name,x,sill,head,w,face,detail,top=False):
    h=head-sill
    hole=box(x-w/2,sill,x+w/2,head)
    front.profile(name+' glass',GLASS,hole,face-.248,face-.218)
    edge=hole.difference(hole.buffer(-.056,join_style='mitre'))
    front.profile(name+' frame',TIMBER,edge,face-.226,face-.128)
    if detail:
        b=head-h*.27
        front.box(name+' top light',GLAZING,x-w/2+.055,x+w/2-.055,face-.218,face-.206,b,head-.055)
        for u in ([x] if top else [x-w*.19,x+w*.19]):
            front.box(name+' mullions',TIMBER,u-.019,u+.019,face-.195,face-.151,sill+.03,head-.03)
        front.box(name+' transom',TIMBER,x-w/2+.04,x+w/2-.04,face-.199,face-.149,b-.019,b+.019)
    else:
        rail=head-h*.27
        front.box(name+' central mullion',TIMBER,x-.020,x+.020,face-.21,face-.153,sill+.04,head-.04)
        front.box(name+' transom',TIMBER,x-w/2+.04,x+w/2-.04,face-.205,face-.15,rail-.019,rail+.019)
    return hole

def hood(front,name,x,w,z,detail):
    a=x-w/2;b=x+w/2
    for j,(over,lo,hi,reach) in enumerate([(.04,0,.11,.10),(.13,.11,.18,.16),(.19,.18,.24,.21)]):
        front.box(name+' upper stepped hood',FILLET,a-over,b+over,-.08,reach,z+lo,z+hi)
    if detail:
        arch=Point(x,z+.186).buffer(.42,quad_segs=15)
        crest=affinity.scale(arch,xfact=1.,yfact=.33,origin=(x,z+.186))
        front.profile(name+' shallow shell crest',LIMESTONE,crest,0,.129)

def upper_storey(front,name,measurements,level,detail,hood_top):
    holes=[]
    for i,(u,sill,head,w) in enumerate(measurements):
        label=name+' light '+str(i+1);hole=sash(front,label,u,sill,head,w,0,detail,top=level==4)
        edge=hole.buffer(.075,join_style='mitre').difference(hole)
        front.profile(label+' stone surround',LIMESTONE,edge,-.115,.053)
        if level==3:
            cap_base=hood_top-.24
            front.box(label+' stucco lintel bed',LIMESTONE,u-w/2-.02,u+w/2+.02,-.09,.041,head,cap_base+.007)
            hood(front,label,u,w,cap_base,detail)
        front.box(label+' sill ledge',FILLET,u-w*.54,u+w*.54,-.09,.12,sill-.06,sill+.015)
        holes.append(hole)
    return holes

def shop(front,name,x,w,z0,head,west,detail):
    hole=round_lintel(x,z0,head,w,.31,True)
    inset=w*(.033 if west else .019)
    returns=hole.difference(box(x-w/2+inset,z0-.01,x+w/2-inset,head+.01))
    front.profile(name+' dressed shop jamb returns',LIMESTONE,returns,-.382,-.018)
    if west:
        # The public-facing tobacco-and-wine sign is legible in the dated photograph.
        front.box('September 2021 red shop fascia',SIGN,x-w*.51,x+w*.51,.035,.152,head-.46,head+.075)
        lettering(front,x-.16,head-.19,.153,not detail)
        pane=box(x-w*.47,.25,x+w*.47,head-.49)
        front.profile(name+' storefront glazing',GLASS,pane,-.37,-.34)
        front.box(name+' counter base',PLINTH,x-w*.50,x+w*.50,-.18,.015,.02,.26)
        for u in [x-w*.46,x-w*.16,x+w*.14,x+w*.46]:
            front.box(name+' shop frame',SHUTTER,u-.029,u+.029,-.34,-.25,.25,head-.49)
    else:
        front.box(name+' plastered lower panel',PLINTH,x-w*.484,x+w*.484,-.09,.017,.04,1.13)
        pane=box(x-w*.485,1.11,x+w*.485,head-.48)
        front.profile(name+' dark shop glazing',GLASS,pane,-.29,-.26)
        infill=hole.difference(unary_union([pane,box(x-w,.0,x+w,1.11)]))
        front.profile(name+' filled street arch',CHALK,infill,-.10,-.016)
        for k in range(1,11 if detail else 5):
            u=x-w*.485+w*.97*k/(11 if detail else 5)
            front.box(name+' iron shop guard',SHUTTER,u-.014,u+.014,-.13,-.096,1.13,head-.49)
        front.box(name+' shop transom',SHUTTER,x-w*.48,x+w*.48,-.14,-.09,head-.80,head-.76)
    surround=hole.buffer(.125,join_style='round').intersection(box(x-w,0,x+w,head+.18)).difference(hole)
    front.profile(name+' segmental shop surround',LIMESTONE,surround,-.11,.055)
    return hole

def upper_frieze(front,start,end,z,detail):
    for off,y,span,mat in [(-.23,.09,.12,LIMESTONE),(-.10,.165,.085,FILLET),(.23,.20,.075,FILLET),(.34,.13,.055,LIMESTONE)]:
        front.box('Street frieze course',mat,start,end,-.15,y,z+off,z+off+span)
    if detail:
        arm=.16
        for k in range(int((end-start)/.43)):
            u=start+.35+k*.43
            outer=Polygon([(u-arm,z+.11),(u,z+.205),(u+arm,z+.11),(u,z+.008)])
            inner=outer.buffer(-.026,join_style='mitre')
            front.profile('Cornice diamond band',FILLET,outer.difference(inner),.003,.038)

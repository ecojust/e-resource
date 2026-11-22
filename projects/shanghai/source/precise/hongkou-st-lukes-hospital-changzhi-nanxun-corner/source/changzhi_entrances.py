"""Street-level arcade, photographed plaque and gable lunette on Changzhi Road.

Coordinates on a face are distance along the street, height, and outward relief.
The dated observations and attribution are in changzhi-ground-photo-observations.json.
"""
from math import cos, hypot, pi, sin
from shapely.geometry import LineString, Polygon, box


def _color(rgb, rough=.82, metallic=0.):
    def linear(n):
        x=n/255.
        return x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4
    return {'color':[linear(c) for c in rgb],'roughness':rough,'metallic':metallic}


STUCCO='Street entrances | ivory rendered plaster'
CREAM='Street entrances | pale moulded dressings'
RETURN='Street entrances | shaded plaster reveals'
INFILL='Street entrances | exhibition infill'
PANEL='Street entrances | inset panel'
SILL='Street entrances | grey sill and terrazzo'
GLASS='Street entrances | aged dark casement glass'
WOOD='Street entrances | dark casement and timber'
GRILLE='Street entrances | painted iron'
BRONZE='Street entrances | black bronze plaque'
BRASS='Street entrances | gilt plaque detail'
PALETTE={STUCCO:_color((208,203,196)),CREAM:_color((223,219,211)),RETURN:_color((169,167,161)),
         INFILL:_color((194,190,182)),PANEL:_color((172,169,161)),SILL:_color((145,143,139)),
         GLASS:_color((52,62,61),.42),WOOD:_color((64,59,55)),GRILLE:_color((89,96,90),.52,.12),
         BRONZE:_color((67,64,61),.48,.25),BRASS:_color((182,160,110),.5,.29)}


def _arch(u,w,z0,spring,rise,n):
    pts=[(u-w/2,z0),(u+w/2,z0)]
    pts += [(u+w*.5*cos(a*pi/n),spring+rise*sin(a*pi/n)) for a in range(n+1)]
    return Polygon(pts)


def _half(u,w,base,rise,n):
    return Polygon([(u+w*.5*cos(i*pi/n),base+rise*sin(i*pi/n)) for i in range(n+1)])


def _face(layout,key):
    faces=layout['faces']
    return faces[key] if isinstance(faces,dict) else next(face for face in faces if face['id']==key)


def _length(face):
    return hypot(face['b'][0]-face['a'][0],face['b'][1]-face['a'][1])


def _frame(face):
    x,y=face['a'];dx=(face['b'][0]-x)/_length(face);dy=(face['b'][1]-y)/_length(face)
    nx,ny=face['out']
    direct=(dy*nx-dx*ny)>0
    def place(s,z,d):
        s=s if direct else -s
        return x+dx*s+nx*d,y+dy*s+ny*d,z
    return place,direct


def _dims(layout):
    """Overrides are metric centre/width, spring, sill and crown heights on the registered face."""
    f=_face(layout,'changzhi');length=_length(f)
    f0=22.719819354750513
    scale=length/f0
    m={'gable_u':18.998*scale,'gable_w':3.7215*scale,'gable_base':3.184,'gable_rise':1.184,
       'arcade_u':[scale*r for r in (10.595,13.026,15.522)],'arcade_w':[scale*r for r in (1.525,1.696,1.557)],
       'arch_spring':1.320,'arch_top':2.130,'ground_windows':[scale*r for r in (17.228,18.913,20.534)],
       'ground_width':[scale*r for r in (.917,1.344,.949)],'square_sill':.354,'square_top':1.881,
       'lower_belt':2.75,'left_panels':[(1.166*scale,1.631*scale),(7.203*scale,1.642*scale)]}
    m.update(layout.get('ground_frontage',{}))
    return m


def opening_profiles(layout):
    """Polygons in (s,z) cut the host wall before the removable infill and inner frames are placed."""
    d=_dims(layout);polys=[_half(d['gable_u'], d['gable_w'],d['gable_base'],d['gable_rise'],48)]
    for u,w in zip(d['arcade_u'],d['arcade_w']):
        polys.append(_arch(u,w,.012,d['arch_spring'],d['arch_top']-d['arch_spring'],40))
    for u,w in zip(d['ground_windows'],d['ground_width']):
        polys.append(box(u-w/2,d['square_sill'],u+w/2,d['square_top']))
    return {'changzhi':polys}


def _pen(points,width):
    return LineString(points).buffer(width/2,cap_style=2,join_style=1,quad_segs=3)


def _title_strokes():
    # Original monoline lettering for the six legible characters on the published plaque.
    return [
      [[(.09,.90),(.09,.08)],[(.09,.90),(.91,.90),(.91,.08),(.77,.08)],[(.24,.70),(.76,.70)],[(.30,.55),(.70,.55),(.70,.24),(.30,.24),(.30,.55)]],
      [[(.36,.94),(.25,.72),(.08,.54)],[(.25,.65),(.25,.08)],[(.48,.75),(.85,.75)],[(.40,.21),(.95,.21)]],
      [[(.87,.90),(.12,.90),(.12,.10),(.91,.10)],[(.43,.83),(.30,.64)],[(.38,.73),(.79,.73)],[(.53,.72),(.53,.57),(.49,.44),(.29,.25)],[(.28,.54),(.82,.54)],[(.55,.51),(.65,.38),(.83,.25)]],
      [[(.07,.07),(.07,.90),(.30,.90),(.21,.66),(.31,.53),(.30,.39),(.19,.36)],[(.56,.93),(.66,.83)],[(.39,.71),(.39,.81),(.92,.81),(.90,.71)],[(.45,.62),(.86,.62)],[(.36,.46),(.93,.46)],[(.55,.45),(.54,.28),(.47,.14),(.35,.07)],[(.73,.45),(.73,.16),(.77,.10),(.91,.10),(.94,.24)]],
      [[(.15,.90),(.15,.09)],[(.35,.83),(.86,.83),(.86,.15),(.35,.15),(.35,.83)],[(.35,.50),(.85,.50)]],
      [[(.23,.88),(.23,.22)],[(.09,.62),(.37,.62)],[(.07,.22),(.38,.33)],[(.67,.90),(.67,.17)],[(.46,.65),(.46,.17)],[(.68,.58),(.90,.58)],[(.35,.16),(.95,.16)]]]


def add_entrances(b,lod=False,layout=None):
    if layout is None:raise ValueError('A registered five-face layout is needed.')
    b.palette.update(PALETTE)
    d=_dims(layout);face=_face(layout,'changzhi');place,direct=_frame(face)
    from shapely.affinity import scale
    def solid(shape,back,front,mat,name):
        if shape.is_empty:return
        if not direct:shape=scale(shape,xfact=-1,origin=(0,0))
        b.prism(shape,back,front,place,mat,'Changzhi entrances / '+name)
    def block(l,r,z,t,back,front,mat,name):
        if r>l and t>z:solid(box(l,z,r,t),back,front,mat,name)
    def stroke(p,width,back,front,mat,name):
        solid(_pen(p,width),back,front,mat,name)
    def reveal(profile,thickness,depth,name):
        ring=profile.buffer(thickness,join_style=2).difference(profile)
        solid(ring,-depth,.004,RETURN,name)
    u=d['gable_u'];w=d['gable_w'];base=d['gable_base'];rise=d['gable_rise'];n=26 if lod else 52
    profile=opening_profiles(layout)['changzhi'][0]
    reveal(profile,.036,.050*w,'large lunette finished jamb and soffit')
    solid(profile,-.057*w,-.050*w,PANEL,'large lunette inner closure')
    # Two broad plaster uprights in all three frontal views separate the centre and flank lights.
    for i,fraction in enumerate((-.244,.244)):
        s=u+fraction*w;zw=base+rise*(1-(2*fraction)**2)**.5
        solid(profile.intersection(box(s-.047*w,base-.02,s+.047*w,zw+.065*w)),
              -.043*w,-.0065*w,CREAM,'lunette inner plaster pier '+str(i+1))
    for idx,(left,right) in enumerate(((-.48,-.292),(-.196,.196),(.292,.48))):
        panel=profile.intersection(box(u+left*w,base+.02*w,u+right*w,base+rise))
        solid(panel,-.050*w,-.044*w,GLASS,'lunette recessed glazed bay '+str(idx+1))
        trim=panel.difference(panel.buffer(-.010*w,join_style=2))
        solid(trim,-.045*w,-.037*w,WOOD,'lunette perimeter sash '+str(idx+1))
        for zfrac in ((.30,.62) if idx==1 else (.30,)):
            bar=panel.intersection(box(u-w,base+zfrac*rise-.007*w,u+w,base+zfrac*rise+.007*w))
            solid(bar,-.044*w,-.034*w,WOOD,'glazing rail '+str(idx+1)+' '+str(zfrac))
        if idx==1:
            for j,xx in enumerate((-.070,.066)):
                solid(panel.intersection(box(u+xx*w-.006*w,base,u+xx*w+.006*w,base+rise)),
                      -.043*w,-.034*w,WOOD,'centre light muntin '+str(j+1))
    # The projecting outer hood stops above the waist course. It is independent of the intrados.
    # Native Fayhoo points independently checked against the near-frontal 2021 panorama.
    # The moulding has a shallower rise and wider span than the deep inner arch.
    trace=[(16.589,3.672),(16.940,3.965),(17.315,4.175),(17.699,4.331),(18.119,4.422),
           (18.584,4.477),(19.064,4.443),(19.486,4.345),(19.798,4.178),(20.109,3.926),(20.402,3.651)]
    outer=[]
    for k in range(len(trace)-1):
        a=trace[max(0,k-1)];p=trace[k];q=trace[k+1];r=trace[min(len(trace)-1,k+2)]
        for h in range(2 if lod else 5):
            t=h/(2 if lod else 5);t2=t*t;t3=t2*t
            x,z=[.5*(2*p[j]+(-a[j]+q[j])*t+(2*a[j]-5*p[j]+4*q[j]-r[j])*t2+
                      (-a[j]+3*p[j]-3*q[j]+r[j])*t3) for j in (0,1)]
            outer.append((u+(x-18.60)*w/3.49,base+(z-3.075)*rise/1.14))
    outer.append((u+(trace[-1][0]-18.60)*w/3.49,base+(trace[-1][1]-3.075)*rise/1.14))
    inner=[(u+(x-u)*.971,z-.041) for x,z in outer]
    solid(Polygon(outer+inner[::-1]),-.018,.074,CREAM,'separate arc moulding')
    for j,(s,z) in enumerate((outer[0],outer[-1])):
        block(s-.045*w,s+.045*w,z-.040*w,z-.002*w,-.012,.086,CREAM,'hood square end '+str(j+1))
    capz=max(z for x,z in outer)
    solid(Polygon([(u-.052*w,capz+.047*w),(u+.052*w,capz+.047*w),(u+.038*w,base+rise-.008*w),
                   (u-.038*w,base+rise-.008*w)]),-.015,.095,CREAM,'elongated central keystone')
    block(u-.51*w,u+.51*w,base-.055*w,base+.004*w,-.09*w,.042,SILL,'lunette lower sill')
    dated_open=layout.get('ground_frontage_state')=='published-2021-open'
    arcs=opening_profiles(layout)['changzhi'][1:4]
    for i,(s,aw,arch) in enumerate(zip(d['arcade_u'],d['arcade_w'],arcs)):
        spring=d['arch_spring'];top=d['arch_top'];depth=(.55 if i==1 else .30)*aw
        reveal(arch,.035,depth,'arcade '+str(i+1)+' thick reveal')
        key=Polygon([(s-.11*aw,top+.24),(s+.11*aw,top+.24),(s+.065*aw,top-.055),(s-.065*aw,top-.055)])
        solid(key,-.020,.077,CREAM,'arcade '+str(i+1)+' tapered upper block')
        block(s-.505*aw,s+.505*aw,.003,.045,-depth,.035,SILL,'arcade '+str(i+1)+' threshold')
        if dated_open and i==1:
            doorway=box(s-.247*aw,.04,s+.235*aw,top*.76)
            surround=arch.difference(doorway)
            solid(surround,-depth-.045,-depth,RETURN,'recessed short porch rear wall')
            solid(doorway,-depth-.085,-depth-.060,WOOD,'dark timber inner leaf')
            trim=doorway.difference(doorway.buffer(-.032,join_style=2))
            solid(trim,-depth-.054,-depth+.013,WOOD,'recessed pedestrian door casing')
            block(s-.225*aw,s+.212*aw,top*.591,top*.724,-depth-.054,-depth-.042,GLASS,'door rectangular fanlight')
            for h in (.594,.654,.725):
                block(s-.235*aw,s+.223*aw,top*h,top*h+.020,-depth-.043,-depth-.024,WOOD,'fanlight rail '+str(h))
        elif dated_open:
            solid(arch,-depth-.040,-depth,GLASS,'arcade '+str(i+1)+' dark framed backing')
            for j in range(1,8):
                xx=s+(j/8.-.5)*aw
                solid(arch.intersection(box(xx-.012,.17,xx+.012,top)),-.128,-.106,GRILLE,'arcade '+str(i+1)+' grille vertical '+str(j))
            for j,z in enumerate((.28,1.15,1.82)):
                block(s-.47*aw,s+.47*aw,z,z+.022,-.124,-.100,GRILLE,'arcade '+str(i+1)+' grille rail '+str(j))
        else:
            solid(arch,-.113,-.091,INFILL,'arcade '+str(i+1)+' recessed exhibition backing')
            # The 2023 photographs fill the inset. Their pixels belong to the original photographers.
            inner=arch.buffer(-.068,join_style=1)
            if not inner.is_empty:solid(inner,-.093,-.082,PANEL,'arcade '+str(i+1)+' plain display area')
    for i,(s,ww) in enumerate(zip(d['ground_windows'],d['ground_width'])):
        z=d['square_sill'];t=d['square_top'];panel=box(s-ww*.5,z,s+ww*.5,t)
        reveal(panel,.027,.16*ww,'rectangular lower reveal '+str(i+1))
        solid(panel,-.19*ww,-.16*ww,INFILL,'rectangular lower infill '+str(i+1))
        block(s-.54*ww,s+.54*ww,z-.056,z+.012,-.09,.080,SILL,'projected rectangular sill '+str(i+1))
        block(s-.095*ww,s+.095*ww,t-.013,t+.27,-.015,.041,CREAM,'window vertical head block '+str(i+1))
        if not dated_open:
            low=_arch(s,ww*.94,z+.012,t-.29,.31,20)
            edge=low.difference(low.buffer(-.040,join_style=1))
            solid(edge,-.045,.035,STUCCO,'later shallow arched display edging '+str(i+1))
    if not dated_open:
        for j,(s,ww) in enumerate(d['left_panels']):
            exhibit=_arch(s,ww,.26,1.69,.36,22)
            solid(exhibit,-.001,.020,STUCCO,'western shallow display frame '+str(j+1))
            inner=exhibit.buffer(-.050,join_style=1)
            solid(inner,.020,.026,PANEL,'western plain display backing '+str(j+1))
            block(s-.09*ww,s+.09*ww,2.03,2.36,-.009,.053,CREAM,'western display head '+str(j+1))
    # Centre plaque sits on the pier between the centre and right arcade bays.
    a,bay=d['arcade_u'][1:];plaque_s=a+.48*(bay-a);wall_z=d['arch_top']*.76
    sw=.33*(bay-a);sh=sw*.62
    silhouette=[(-.50,.25),(-.46,.33),(-.39,.34),(-.36,.41),(-.20,.43),(-.12,.47),(0,.50),
                (.12,.47),(.20,.43),(.36,.41),(.39,.34),(.46,.33),(.50,.25),(.50,-.27),
                (.45,-.37),(.36,-.39),(.32,-.43),(.12,-.44),(0,-.50),(-.12,-.44),
                (-.34,-.43),(-.40,-.38),(-.46,-.34),(-.50,-.26)]
    plaque=Polygon([(plaque_s+x*sw,wall_z+y*sh) for x,y in silhouette])
    solid(plaque,.004,.034,BRONZE,'named hospital plaque scalloped casting')
    border=plaque.buffer(-.015).boundary.buffer(.0035 if not lod else .004,quad_segs=2)
    solid(border,.033,.038,BRASS,'plaque cast border')
    for i,glyph in enumerate(_title_strokes()):
        cw=sw*.109;cx=plaque_s+(-3+i)*cw;cz=wall_z
        for j,stroke_pts in enumerate(glyph):
            stroke([(cx+x*cw,cz+(y-.12)*cw) for x,y in stroke_pts],cw*.072,.033,.0383,BRASS,'plaque name '+str(i+1)+' stroke '+str(j+1))
    _corner(b,layout)


def _corner(b,layout):
    """Shallow plaster apron and tapered drops visible on either side of the street corner."""
    from shapely.affinity import scale
    belt=layout.get('low_fascia',2.75)
    def local(face_name,outline,low,high,material,title):
        face=_face(layout,face_name);place,direct=_frame(face)
        poly=Polygon([(u*_length(face),belt+v) for u,v in outline])
        if not direct:poly=scale(poly,xfact=-1,origin=(0,0))
        b.prism(poly,low,high,place,material,'Changzhi entrances / '+title)
    local('corner-center',[(.07,-.02),(.99,-.02),(.99,-.22),(.97,-.63),(.77,-.63),(.77,-.48),(.25,-.48),(.25,-.63),(.084,-.63),(.084,-.24)],
          -.012,.056,STUCCO,'corner stepped plaster apron with two square drops')
    local('corner-center',[(.055,-.01),(.99,-.01),(.99,-.12),(.965,-.22),(.085,-.22),(.055,-.12)],
          .052,.093,CREAM,'apron upper moulding')
    local('corner-changzhi',[(.29,-.12),(.97,-.12),(.97,-.21),(.91,-.25),(.31,-.25)],
          -.009,.048,STUCCO,'western return small horizontal shoulder')
    local('corner-nanxun',[(.02,-.13),(.79,-.13),(.77,-.21),(.11,-.23),(.06,-.33)],
          -.009,.047,STUCCO,'eastern return small horizontal shoulder')
    for n,(s,w,fall) in enumerate(((1.987,.270,.250),(4.449,.353,.61),(6.870,.384,.57))):
        length=_length(_face(layout,'nanxun'));u=s/length;hw=.5*w/length
        local('nanxun',[(u-hw,-.10),(u+hw,-.10),(u+.55*hw,-fall),(u-.67*hw,-fall)],
              -.009,.068,CREAM,'Nanxun Road fascia corbel '+str(n+1))

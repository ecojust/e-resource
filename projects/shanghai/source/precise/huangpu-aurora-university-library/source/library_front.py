"""The field-facing wall of the 1936 Aurora University library, in metres."""
from pathlib import Path
from shapely.affinity import translate
from sign_lettering import lettering_shapes
from shapely.geometry import box
from shapely.ops import unary_union
from photo_architecture import Facade, opening

# The west and east shallow returns are known from the near-oblique 2020 view.
# The 1-D photograph fit separately recovered each center on the field elevation.
HALF_WIDTH=29.849
END_INNER=21.70
CENTRE_HALF=2.62
WING_WINDOWS=(4.79,8.20,11.59,15.17,18.60)
WINDOW_LEVELS=(5.50,10.00,14.50)
PARAPET=20.10
END_PARAPET=20.88
SECTION_DEPTH=4.62
PALETTE={
    'red face tile':{'color':[.306,.090,.073],'roughness':.82},
    'fired brick red':{'color':[.350,.115,.091],'roughness':.80},
    'weathered red tile':{'color':[.266,.070,.061],'roughness':.84},
    'brick bedding':{'color':[.246,.065,.051],'roughness':.91},
    'pale window spandrels':{'color':[.669,.662,.625],'roughness':.84},
    'grey cement dressings':{'color':[.577,.556,.499],'roughness':.82},
    'aged steel casement':{'color':[.277,.300,.285],'roughness':.46,'metallic':.19},
    'window glass':{'color':[.155,.196,.194],'roughness':.28,'metallic':.18},
    'upper pale reflection':{'color':[.240,.279,.274],'roughness':.30,'metallic':.16},
    'deep frame reveal':{'color':[.216,.228,.217],'roughness':.63},
    'aged sign bronze':{'color':[.660,.463,.195],'roughness':.42,'metallic':.53},
    'flat roof':{'color':[.416,.455,.416],'roughness':.89},
    'neutral section':{'color':[.512,.483,.405],'roughness':.87},
}

def casement(f,outline,lights,rows,lod,label):
    x0,z0,x1,z1=outline.bounds
    w,h=x1-x0,z1-z0
    aperture=outline.buffer(-.063,join_style='mitre')
    bars=[box(x0+w*i/lights-.027,z0,x0+w*i/lights+.027,z1)for i in range(1,lights)]
    bars.extend(box(x0,z0+h*i/rows-.033,x1,z0+h*i/rows+.033)for i in range(1,rows))
    lights_area=aperture.difference(unary_union(bars))
    f.prism(outline.buffer(.01,join_style='mitre'),-.32,-.30,'window glass',label+' glass')
    f.prism(outline.buffer(-.014,join_style='mitre').difference(lights_area),-.25,-.16,'aged steel casement',label+' metal grid')
    if not lod:
        lining=lights_area.difference(lights_area.buffer(-.022,join_style='mitre'))
        f.prism(lining,-.285,-.246,'deep frame reveal',label+' pane rebates')
    transom=lights_area.intersection(box(x0,z1-h/rows+.04,x1,z1+.01))
    if transom.area>.002:
        f.prism(transom,-.297,-.290,'upper pale reflection',label+' upper lights')
    surround=outline.buffer(.115,join_style='mitre').difference(outline)
    f.prism(surround,-.025,.063,'grey cement dressings',label+' surround')
    f.box((x0+x1)/2,z0-.06,w+.23,.12,.26,.02,'grey cement dressings',label+' sill')

def tiled_pier(f,x0,x1,top,lod):
    # Narrow upright red tiles are visible between the pale spandrel bands.
    # Model their bedding only on the photo-visible vertical piers. Dark joints
    # are the exposed backing between separate tile strips. The paired side
    # returns and shadowed ground windows keep their original broad brick tone.
    if lod or x1-x0<.26:return
    z0=.21;z1=top-.44
    f.prism(box(x0,z0,x1,z1),.001,.012,'brick bedding','tiled pier bed')
    width=x1-x0
    cols=max(1,round(width/.22));rows=max(1,round((z1-z0)/.34))
    verts={m:[] for m in ('red face tile','fired brick red','weathered red tile')}
    faces={m:[]for m in verts}
    for j in range(rows):
        for i in range(cols):
            tone=(i*5+j*19+j//5)%18
            mat='fired brick red' if tone<3 else 'weathered red tile' if tone==3 else 'red face tile'
            l=x0+i*width/cols+.007;r=x0+(i+1)*width/cols-.007
            b=z0+j*(z1-z0)/rows+.006;t=z0+(j+1)*(z1-z0)/rows-.006
            # The lower skin is embedded in the wall. Model each exposed tile
            # face and its four returns as a separately editable closed solid.
            vi=verts[mat];index=len(vi)
            vi.extend(f.point(u,z,d) for d in (.010,.021)for u,z in [(l,b),(r,b),(r,t),(l,t)])
            faces[mat].extend(tuple(index+n for n in order) for order in [(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])
    for mat in verts:
        if faces[mat]:f.builder.add(verts[mat],faces[mat],mat,f.label+'/upright red tile courses')

def cornice(f,z,w):
    for h,th,pro,mat in [(z-.43,.11,.08,'grey cement dressings'),(z-.27,.13,.17,'pale window spandrels'),(z-.14,.13,.27,'grey cement dressings'),(z+.025,.13,.20,'pale window spandrels')]:
        f.beam(h,th,pro,mat,width=w,label='stepped parapet cornice')

def upper_row(f,u,width,lod,broad=False):
    holes=[]
    # The light spandrel fills between the three real windows, forming one
    # continuous pale vertical band in the photo instead of separate frames.
    light=3 if broad else 1
    gap=.205 if broad else 0
    net=(width-(light-1)*gap)/light
    for z in WINDOW_LEVELS:
        for j in range(light):
            cx=u+(j-(light-1)/2)*(net+gap)
            p=opening(cx,z,net,3.05);holes.append(p)
            casement(f,p,2 if broad else 3,4 if not lod else 3,lod,'upper casement')
    body=box(u-width/2-.15,WINDOW_LEVELS[0]-.17,u+width/2+.15,WINDOW_LEVELS[-1]+3.22)
    f.prism(body.difference(unary_union(holes)),-.008,.038,'pale window spandrels','three-storey pale panel')
    return holes

def panel(b,x0,x1,y,kind,lod):
    mid=(x0+x1)/2;w=x1-x0
    f=Facade(b,(x0,y),(x1,y),kind)
    top=END_PARAPET if kind.startswith('end') else PARAPET
    holes=[]
    if kind.startswith('end'):
        offset=.62 if kind=='end east' else -.32
        holes=upper_row(f,offset,4.48,lod,True)
        ground=opening(offset,.67,4.50,3.47,.77,segments=20 if lod else 38)
        holes.append(ground);casement(f,ground,3,3,lod,'wide end arch')
        for u in (offset-.75,offset+.75):
            pier=ground.intersection(box(u-.066,.67,u+.066,4.21))
            f.prism(pier,-.19,-.06,'pale window spandrels','three light arch mullions')
        if kind=='end east':
            font=Path(__file__).with_name('fonts')/'AuroraWestOneSubset.otf'
            for char,outline in lettering_shapes('西1',1.01,.44,font=font):
                f.prism(translate(outline,xoff=3.04,yoff=4.37),.043,.078,'aged sign bronze','West One '+char)
        tiled_pier(f,-w/2+.09,offset-2.51,top,lod);tiled_pier(f,offset+2.51,w/2-.09,top,lod)
    elif kind=='central window':
        # Center shaft has uninterrupted steel glazing in place of three
        # opaque spandrels. The photographed lowest portion is partly obscured.
        shaft=opening(0,.79,1.83,16.72);holes.append(shaft)
        casement(f,shaft,3,18 if not lod else 11,lod,'continuous vertical casement')
        for z in [3.97,7.01,10.05,13.09,16.13]:
            f.box(0,z,1.68,.13,.13,-.18,'aged steel casement','central stair rails')
        tiled_pier(f,-w/2+.07,-1.17,top,lod);tiled_pier(f,1.17,w/2-.07,top,lod)
    else:
        sign=1 if x0>0 else -1
        positions=sorted(sign*abs(v)-mid for v in WING_WINDOWS)
        for u in positions:
            holes.extend(upper_row(f,u,1.91,lod))
            opening_at_grade=opening(u,.68,1.92,3.46,.9,segments=18 if lod else 30)
            holes.append(opening_at_grade);casement(f,opening_at_grade,3,3,lod,'round-headed field window')
        edges=[-w/2+.04,*[c for u in positions for c in (u-1.16,u+1.16)],w/2-.04]
        for left,right in zip(edges[::2],edges[1::2]):tiled_pier(f,left,right,top,lod)
    f.wall(0,top,holes,.45,'red face tile')
    fascia=2.04 if kind.startswith('end') else 1.96
    f.box(0,top-fascia/2,w,fascia,.20,-.073,'pale window spandrels','raised pale parapet face')
    cornice(f,top,w)
    b.box((mid,y+.19,.16),(w,.39,.32),'grey cement dressings',label=kind+'/plinth')
    b.box((mid,(SECTION_DEPTH+y)/2,top-.40),(w,SECTION_DEPTH-y,.23),'flat roof',label=kind+'/front roof band')
    b.box((mid,SECTION_DEPTH-.05,(top-.30)/2),(w,.10,top-.30),'neutral section',label=kind+'/plain roof section')
    for x in (x0,x1):
        # Every photographed shallow change in plane has a closed return.
        if abs(x)>HALF_WIDTH-.01:
            b.box((x+(.07 if x<0 else -.07),(SECTION_DEPTH+y)/2,top/2),(.14,SECTION_DEPTH-y,top),'neutral section',label=kind+'/end section')
        elif y<.35:
            b.box((x+(.035 if x==x0 else -.035),y+.21,top/2),(.07,.42,top),'red face tile',label=kind+'/shallow return')

def building(builder,lod):
    for x0,x1,y,name in [(-HALF_WIDTH,-END_INNER,.00,'end east'),(-END_INNER,-CENTRE_HALF,.40,'five bays east'),(-CENTRE_HALF,CENTRE_HALF,.16,'central window'),(CENTRE_HALF,END_INNER,.40,'five bays west'),(END_INNER,HALF_WIDTH,.00,'end west')]:
        panel(builder,x0,x1,y,name,lod)

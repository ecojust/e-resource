"""West-facing street entrance documented in 2011 and in the May 2019 street survey."""
from math import cos, sin, pi, tau
from shapely.geometry import LineString, Polygon, box
from photo_architecture import Facade

PIER_X = 1.92
PIER_WIDTH = .64
OPENING = 3.20
WALL_END = 4.45

PALETTE = {
    'warm gray render': {'color': [.548, .543, .504], 'roughness': .93},
    'gray plinth': {'color': [.382, .378, .361], 'roughness': .91},
    'molded cap': {'color': [.479, .476, .451], 'roughness': .90},
    'globe': {'color': [.755, .741, .671], 'roughness': .78},
    'gate leaves': {'color': [.204, .122, .094], 'roughness': .70},
    'gate recess': {'color': [.162, .095, .077], 'roughness': .80},
    'raised woodwork': {'color': [.269, .163, .125], 'roughness': .68},
    'limestone': {'color': [.623, .598, .530], 'roughness': .96},
    'carved limestone': {'color': [.652, .632, .562], 'roughness': .92},
    'carving hollows': {'color': [.395, .378, .329], 'roughness': .98},
    'paving': {'color': [.491, .484, .455], 'roughness': .94},
    'number enamel': {'color': [.094, .346, .251], 'roughness': .52},
    'enamel lettering': {'color': [.870, .849, .766], 'roughness': .60},
    'weathered tablet': {'color': [.579, .535, .432], 'roughness': .80},
    'bronze': {'color': [.237, .209, .157], 'roughness': .59, 'metallic': .28},
}


def ovoid(b, center, radii, material, name, lod, lean=0):
    cx,cy,cz=center
    rx,ry,rz=radii
    slices,stacks=(10,6) if lod else (18,10)
    vertices=[(cx,cy-lean,cz-rz)]
    for i in range(1,stacks):
        lat=-pi/2+pi*i/stacks
        for j in range(slices):
            lon=tau*j/slices
            vertices.append((cx+rx*cos(lat)*cos(lon),cy+ry*cos(lat)*sin(lon)+lean*sin(lat),cz+rz*sin(lat)))
    last=len(vertices)
    vertices.append((cx,cy+lean,cz+rz))
    faces=[]
    for j in range(slices):
        k=(j+1)%slices
        faces.append((0,1+k,1+j))
        for i in range(stacks-2):
            s=1+i*slices
            faces.append((s+j,s+k,s+k+slices,s+j+slices))
        s=1+(stacks-2)*slices
        faces.append((s+j,s+k,last))
    b.add(vertices,faces,material,name)


def tapered_block(b, x, y, sections, material, label):
    """Square or rectangular profiles, retaining an individual editable named mesh."""
    vertices=[]
    for z,w,d in sections:
        vertices.extend([(x-w/2,y-d/2,z),(x+w/2,y-d/2,z),(x+w/2,y+d/2,z),(x-w/2,y+d/2,z)])
    faces=[(3,2,1,0)]
    for n in range(len(sections)-1):
        a=4*n
        for i in range(4):
            j=(i+1)%4
            faces.append((a+i,a+j,a+j+4,a+i+4))
    b.add(vertices,faces+[tuple(range(len(vertices)-4,len(vertices)))],material,label)


def carved_lion(b, x, sign, lod):
    """Seated stone guardians. Small curls and fur are inferred within the photographed silhouettes."""
    group=('south guardian' if sign>0 else 'north guardian')+'/'
    y=-.52
    def form(pos, scale, part, material='limestone', lean=0):
        px,py,pz=pos
        ovoid(b,(x+sign*px,y+py,pz),scale,material,group+part,lod,lean)
    def line(points,radius,part,mat='carved limestone'):
        b.tube([(x+sign*px,y+py,pz)for px,py,pz in points],radius,mat,5 if lod else 8,group+part)
    tapered_block(b,x,y,[(0,.75,.76),(.07,.76,.77),(.095,.72,.73),(.13,.66,.67),
                         (.575,.64,.66),(.603,.72,.75),(.64,.78,.79),(.72,.78,.80)],
                  'limestone',group+'stepped square stone plinth')
    form((0,.075,1.026),(.264,.294,.312),'seated haunches')
    form((0,.00,1.255),(.243,.212,.382),'upright shoulders',lean=-.052)
    for side in (-1,1):
        form((side*.192,.076,.858),(.123,.199,.143),'rounded rear legs')
        form((side*.178,-.115,1.057),(.090,.119,.252),'straight front shins',lean=.038)
        form((side*.165,-.205,.802),(.089,.123,.079),'forepaws')
        if not lod:
            for toe in (-.043,0,.043):
                form((side*.163+toe,-.280,.790),(.028,.052,.045),'carved claw lobes')
    form((.007,-.056,1.624),(.228,.224,.222),'head and cheeks')
    form((0,-.182,1.487),(.164,.114,.112),'lower jaw')
    for side in (-1,1):
        form((side*.101,-.219,1.585),(.106,.092,.083),'split muzzle')
        form((side*.102,-.247,1.703),(.048,.020,.036),'shadow below brows','carving hollows')
        form((side*.103,-.262,1.707),(.027,.018,.025),'raised eyes')
        form((side*.119,-.213,1.750),(.095,.047,.037),'arching brows','carved limestone')
        form((side*.193,.019,1.771),(.088,.052,.082),'ears')
    form((0,-.282,1.649),(.081,.051,.044),'broad carved nose','carved limestone')
    for side in (-1,1):
        line([(0,-.286,1.554),(side*.058,-.281,1.538),(side*.119,-.261,1.542),(side*.144,-.234,1.556)],
             .009,'mouth incision','carving hollows')
    line([(.169,.182,.886),(.261,.220,.918),(.255,.238,1.066),(.174,.225,1.131)],
         .038,'curved tail')
    form((.139,-.174,.862),(.094,.092,.108),'rounded ornament below outer paw')
    # Three overlapping rows of locks form the differing depth of the mane.
    for row,count in [(0,8),(1,9),(2,10)]:
        for j in range(count):
            angle=tau*(j+.34*row)/count
            if row!=0 and sin(angle)<-.46:continue
            radius=(.118,.207,.228)[row]
            cx=radius*cos(angle);cy=-.034+radius*sin(angle);cz=(1.811,1.698,1.579)[row]+.012*cos(3*angle)
            form((cx,cy,cz),(.064,.058,.076),'mane locks','carved limestone')
            if lod:continue
            spiral=[]
            for i in range(11):
                t=i/10;r=.041*(1-.73*t);theta=t*tau*1.04
                spiral.append((cx+(r*cos(theta))*-sin(angle)+.045*cos(angle),
                               cy+(r*cos(theta))*cos(angle)+.045*sin(angle),cz+r*sin(theta)))
            line(spiral,.009,'curled mane ridges')
    for i in range(3 if lod else 5):
        dx=(i-1 if lod else i-2)*.047
        form((dx,-.155,1.408-.4*abs(dx)),(.044,.046,.097),'chest ruff','carved limestone')


def paneled_leaves(b, face, lod):
    width=OPENING-.085
    for side in (-1,1):
        center=side*(width/4+.012)
        face.box(center,1.53,width/2-.016,2.86,.105,-.084,'gate leaves','two closed door leaves')
        for panel in (-1,1):
            u=center+panel*width/8
            face.box(u,1.53,.625,2.65,.027,-.026,'gate recess','four recessed vertical door fields')
            for z,w,h in ((.39,.64,.24),(.72,.56,.16),(1.71,.52,1.39),(2.56,.55,.21)):
                shape=box(u-w/2,z-h/2,u+w/2,z+h/2)
                rim=shape.difference(shape.buffer(-.034,join_style='mitre'))
                face.prism(rim,-.026,.007,'raised woodwork','beveled rectangular panel molding')
            foot=Polygon([(u-.245,.43),(u+.245,.43),(u+.171,.53),(u-.166,.53)])
            face.prism(foot,-.006,.029,'raised woodwork','flared cushion above lower rail')
            outer=Polygon([(u-.232,2.505), (u+.232,2.505), *[(u+.232*cos(i*pi/18),2.52+.164*sin(i*pi/18)) for i in range(19)]])
            if outer.area>.001:face.prism(outer,-.013,.014,'raised woodwork','arched crest casting')
            for z, w in ((.53, .54), (.76, .50), (.91, .44), (2.29, .48), (2.38, .54), (2.50, .46)):
                face.box(u,z,w,.031,.047,.004,'raised woodwork','door ornament/stepped horizontal fillets')
            # A narrow central cartouche is visible inside each of the four vertical panels.
            cartouche = Polygon([(u-.135,1.16),(u-.202,1.28),(u-.202,1.87),(u-.14,1.99),
                                 (u,2.12),(u+.14,1.99),(u+.202,1.87),(u+.202,1.28),
                                 (u+.135,1.16),(u,1.095)])
            border = cartouche.difference(cartouche.buffer(-.014,join_style='round'))
            face.prism(border,-.015,.006,'raised woodwork','door ornament/relief cartouche')
            for i in range(2 if lod else 4):
                z = 1.32+i*(.48 if lod else .168)
                for petal in range(5):
                    ang = tau*petal/5
                    xx=u+.030*cos(ang);zz=z+.038*sin(ang)
                    ovoid(b,(xx,-.015,zz),(.031,.017,.033),'raised woodwork','door ornament/flower and bead cluster',True)
            for sideleaf in (-1,1):
                curl=[(u+sideleaf*(.02+.11*sin(pi*t/14)), -.018,1.32+t*.034)for t in range(15)]
                b.tube(curl,.012,'raised woodwork',5 if lod else 8,'door ornament/paired low-relief branches')
                for i in range(2 if lod else 4):
                    dz=i*.130
                    face.prism(Polygon([(u+sideleaf*.058,1.38+dz),(u+sideleaf*.149,1.45+dz),
                                        (u+sideleaf*.164,1.515+dz),(u+sideleaf*.083,1.474+dz)]),
                               -.014,.014,'raised woodwork','door ornament/foliage')
        ovoid(b,(center-side*(width/4-.13),-.039,1.43),(.027,.032,.026),'bronze','door hardware/knob',lod)


def number_plate(face):
    face.box(-PIER_X,2.58,.292,.218,.024,.374,'number enamel','151 address plate/green enamel')
    for u,digit in zip([-PIER_X-.083,-PIER_X,-PIER_X+.083], '151'):
        # Raised strokes reproduce only the legible number on both the 2011 and 2019 photographs.
        width=.042;hi=.058;lo=-.057
        if digit=='1':
            strokes=[(-width*.65,.031,.002,hi),(.002,hi,.002,lo),(-.021,lo,.023,lo)]
        else:
            strokes=[(-width*.56,hi,width*.64,hi),(-width*.56,hi,-width*.56,.002),(-width*.56,.002,width*.31,.002),
                     (width*.31,.002,width*.62,-.015),(width*.62,-.015,width*.62,-.042),(width*.62,-.042,width*.34,lo),(width*.34,lo,-width*.53,lo)]
        for x0,z0,x1,z1 in strokes:
            poly=LineString([(u+x0,2.59+z0),(u+x1,2.59+z1)]).buffer(.006,cap_style='square')
            face.prism(poly,.388,.394,'enamel lettering','151 address plate/digits')


def street_gate(b, lod):
    face=Facade(b,(-WALL_END,0),(WALL_END,0),'public street')
    for sign in (-1,1):
        for center,z,width,height,depth,offset,mat in [
            ((WALL_END+PIER_X+.27)/2,1.43,WALL_END-PIER_X-.27,2.86,.286,-.015,'warm gray render'),
            ((WALL_END+PIER_X+.27)/2,.215,WALL_END-PIER_X-.27,.43,.318,.002,'gray plinth'),
            ((WALL_END+PIER_X+.27)/2,2.215,WALL_END-PIER_X-.27,.029,.301,.003,'molded cap'),
            ((WALL_END+PIER_X+.27)/2,2.824,WALL_END-PIER_X-.27,.112,.37,.02,'molded cap'),
            ((WALL_END+PIER_X+.27)/2,2.895,WALL_END-PIER_X-.27,.046,.405,.02,'molded cap')]:
            face.box(sign*center,z,width,height,depth,offset,mat,'wall returns/'+mat)
        x=sign*PIER_X
        tapered_block(b,x,0,[(0,.66,.68),(.14,.66,.68),(.19,.635,.652),(3.226,.617,.65),
                             (3.274,.66,.688),(3.32,.66,.688)],'warm gray render','street piers/square shafts and base')
        tapered_block(b,x,0,[(3.32,.67,.69),(3.36,.714,.735),(3.402,.714,.735),
                             (3.426,.627,.65),(3.505,.394,.414),(3.525,.303,.32)],'molded cap','street piers/sloped caps')
        ovoid(b,(x,0,3.645),(.124,.124,.135),'globe','street piers/2019 ball finials',lod)
        carved_lion(b,sign*3.48,sign,lod)
    paneled_leaves(b,face,lod)
    number_plate(face)
    face.box(-2.645,2.58,.548,.398,.022,.145,'weathered tablet','street tablet/weathered untranscribed panel')
    for u in (-2.862,-2.428):
        for z in (2.435,2.725):
            ovoid(b,(u,-.165,z),(.013,.012,.013),'bronze','street tablet/corner pins',lod)
    for z,width,height,depth in [(1.514,.38,.085,.025),(1.57,.43,.03,.045)]:
        face.box(-2.66,z,width,height,depth,.169,'bronze','street wall/letter slot')
    b.box((0,.004,.032),(OPENING,.59,.064),'paving',label='threshold/door sill')

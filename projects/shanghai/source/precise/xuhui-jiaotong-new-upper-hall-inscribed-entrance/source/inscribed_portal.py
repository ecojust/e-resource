"""South entrance to the New Upper Hall, Shanghai Jiao Tong University.

The registration drawing supplies the width ratio. The face, four steps,
portal recess, rectangular transoms and plaques follow the university's
restoration survey photograph 19 and the 2008 front and oblique photographs.
Coordinates are metres, with X east, Y into the south wing, and Z upwards.
"""
from math import cos, sin, pi
from shapely.geometry import Polygon, LineString, Point, box
from shapely.ops import unary_union

PALETTE = {
    'dressed warm grey stone': {'color':[.49,.465,.419], 'roughness':.87},
    'recessed mortar': {'color':[.31,.296,.267], 'roughness':.94},
    'shadowed grey stone': {'color':[.348,.337,.31], 'roughness':.9},
    'weathered stair nosings': {'color':[.33,.322,.30], 'roughness':.89},
    'title panel limestone': {'color':[.65,.619,.533], 'roughness':.86},
    'carved dark characters': {'color':[.060,.057,.050], 'roughness':.94},
    'deep red door wood': {'color':[.235,.037,.025], 'roughness':.71},
    'raised red panel': {'color':[.32,.049,.033], 'roughness':.66},
    'green grey glass': {'color':[.055,.091,.084], 'metallic':.17, 'roughness':.25},
    'dark bronze': {'color':[.17,.141,.095], 'metallic':.55, 'roughness':.46},
    'brass pull': {'color':[.48,.34,.16], 'metallic':.71, 'roughness':.39},
    'lamp glass': {'color':[.77,.73,.59], 'roughness':.41},
}

def face(b, polygon, outer, inner, material, name):
    b.prism(polygon, -inner, -outer, lambda x,z,d:(x,-d,z), material, name)

def block(b, x, y, z, width, depth, height, material, name):
    b.box((x,y,z),(width,depth,height),material,label=name)

def ring(b, x, z, w, h, band, front, back, material, name):
    shell=box(x-w/2,z-h/2,x+w/2,z+h/2)
    face(b,shell.difference(shell.buffer(-band,join_style=2)),front,back,material,name)

def title_glyphs(b,lod):
    # Each stroke belongs to a handwritten character. Shapes and dimensions
    # are drawn directly in the model; no photograph is projected onto the panel.
    strokes = [
      [[(.16,.94),(.23,.82)],[(.04,.78),(.51,.78)],[(.1,.72),(.17,.59)],[(.43,.72),(.37,.59)],[(.02,.54),(.53,.54)],[(.25,.53),(.25,.05)],[(.03,.39),(.48,.39)],[(.23,.35),(.03,.16)],[(.30,.34),(.48,.20)],[(.93,.94),(.58,.84),(.57,.54),(.54,.28),(.46,.1)],[(.59,.59),(.98,.62)],[(.79,.59),(.78,.02)]],
      [[(.48,.91),(.44,.1)],[(.48,.52),(.86,.56)],[(.05,.11),(.94,.15)]],
      [[(.08,.9),(.30,.91),(.22,.70),(.30,.55),(.29,.43),(.22,.39),(.15,.44)],[(.08,.88),(.08,.04)],[(.66,.96),(.72,.86)],[(.41,.83),(.94,.83),(.89,.72)],[(.40,.82),(.37,.70)],[(.46,.65),(.86,.66)],[(.35,.49),(.97,.50)],[(.56,.47),(.54,.31),(.46,.15),(.32,.06)],[(.73,.47),(.70,.17),(.76,.10),(.90,.10),(.97,.19)]]]
    for i, components in enumerate(strokes):
        center=(-1.15,0.,1.15)[i]
        profiles=[]
        for stroke in components:
            pts=[(center+(u-.5)*.80,5.05+(v-.5)*.62)for u,v in stroke]
            profiles.append(LineString(pts).buffer(.039 if i!=1 else .049,quad_segs=2 if lod else 5,cap_style=3,join_style=1))
        face(b,unary_union(profiles),-.135,-.118,'carved dark characters',['Xin','Shang','Yuan'][i]+' inscription')

def add_portal(b,lod=False):
    stone='dressed warm grey stone';shade='shadowed grey stone';red='deep red door wood'
    # Four lit treads alternate with four dark faces in the near-frontal survey.
    floor=.68
    for i in range(4):
        y=-1.30+i*.32
        block(b,0,y+.16,(i+1)*.085,12.35,.32,(i+1)*.17,'weathered stair nosings','entry stair '+str(i+1))
        block(b,0,y-.014,(i+1)*.17-.035,12.40,.065,.070,stone,'stair projecting lip '+str(i+1))
    block(b,0,.89,floor/2,12.29,1.82,floor,'weathered stair nosings','entrance landing')
    for side,center in [('west',-5.05),('east',5.05)]:
        # Shallow recessed joints separate the coursed stone from the corner returns.
        block(b,center,.83,3.11,2.40,1.66,4.86,'recessed mortar',side+' pier body')
        for row in range(6):
            z=floor+(row+.5)*.694
            for part in range(2 if row%2 else 1):
                count=2 if row%2 else 1
                x=center+(part-(count-1)/2)*2.40/count
                block(b,x,-.012,z,2.40/count-.020,.047,.681,stone,side+' dressed stone course '+str(row+1))
        block(b,center,.80,5.22,2.40,1.64,.78,stone,side+' upper relief field')
        block(b,center,.79,4.86,2.50,1.70,.102,shade,side+' relief lower rail')
        # Survey 19 shows shallow floral knots flanked by small square end marks.
        for j in [-1,0,1]:
            x=center+j*.57
            for turn in range(4):
                a=turn*pi/2;pts=[(x+(u*cos(a)-v*sin(a)),5.27+(u*sin(a)+v*cos(a)))for u,v in [(0,.035),(.077,.14),(.17,.13),(.13,.038)]]
                face(b,Polygon(pts),-.060,-.029,stone,side+' relief leaf '+str(j))
        lamp_x=center
        face(b,Point(lamp_x,3.22).buffer(.086,quad_segs=4 if lod else 9),-.052,-.033,'dark bronze',side+' lamp foot')
        block(b,lamp_x,-.134,3.27,.052,.19,.053,'dark bronze',side+' lamp arm')
        face(b,Point(lamp_x,3.32).buffer(.081,quad_segs=4 if lod else 10),-.233,-.132,'lamp glass',side+' lamp glass')
    # The continuous deep lintel, its shallow carved panels and the overhang.
    block(b,0,.84,5.14,7.70,1.68,1.01,stone,'entrance lintel')
    for x in [-3.10,-2.43,2.43,3.10]:
        ring(b,x,5.08,.51,.60,.024,-.040,-.017,shade,'blind rectangular relief')
    for width,z,h,depth in [(12.52,5.72,.17,1.98),(12.70,5.86,.115,2.06),(12.90,5.99,.165,2.14),(13.07,6.105,.075,2.23)]:
        block(b,0,.805,z,width,depth,h,stone,'stepped cornice')
    # Truncated curved stone brackets leave the central door recess open.
    for sign in [-1,1]:
        path=[(3.85,4.64),(1.96,4.64),(1.98,4.60),(2.15,4.58),(2.33,4.59),(2.47,4.55),(2.61,4.46),(2.82,4.40),(3.,4.22),(3.17,4.04),(3.38,3.99),(3.49,3.89),(3.85,3.88)]
        face(b,Polygon([(sign*x,z)for x,z in path]),-.025,.37,stone,'scrolled spandrel '+('east'if sign>0 else'west'))
    for x in [-1.77,1.77]:
        for z in [4.68,5.52]:
            face(b,Point(x,z).buffer(.11,quad_segs=4 if lod else 9),-.091,-.035,stone,'plaque corner boss')
    plaque=box(-1.66,4.66,1.66,5.52)
    face(b,plaque.buffer(.07,join_style=1),-.078,-.015,shade,'projecting plaque bed')
    face(b,plaque,-.115,-.077,'title panel limestone','New Upper Hall inscription panel')
    # Small pendant ovals are visible immediately beneath the inscription
    # in the university's front elevation photograph. The turned underside
    # joins the plaque into a single projected stone frame.
    for idx in range(13):
        x=(idx-6)*.245
        bead=Point(x,4.66).buffer(.100,quad_segs=4 if lod else 9)
        face(b,bead.intersection(box(-1.67,4.52,1.67,4.68)),-.118,-.063,stone,'plaque underside pendant')
    for x in (-1.71,1.71):
        for z in (4.745,5.39):
            face(b,Point(x,z).buffer(.073,quad_segs=4 if lod else 7),-.130,-.065,stone,'carved frame stud')
    for x in (-2.98,-2.18,2.18,2.98):
        ring(b,x,4.85,.58,.43,.021,-.047,-.023,stone,'lintel lower panel')
    title_glyphs(b,lod)
    # Rear wooden doors are recessed behind the jambs, with an open central leaf pair.
    centers=[-2.50,0.,2.50]
    for x in [-3.75,-1.25,1.25,3.75]:
        block(b,x,1.455,2.63,.38,.63,3.90,stone,'portal intermediate jamb')
    for index,x in enumerate(centers):
        paneltop=3.35
        block(b,x,1.61,3.64,2.08,.12,.53,'green grey glass','transom glass '+str(index+1))
        ring(b,x,3.68,2.17,.66,.075,1.47,1.62,red,'transom frame '+str(index+1))
        for xs in (-.69,0,.69):
            block(b,x+xs,1.50,3.66,.045,.06,.52,red,'transom mullion')
        block(b,x,1.50,3.70,2.01,.06,.053,red,'transom cross rail')
        for sign in [-1,1]:
            if index==1:continue
            leaf=x+sign*.51
            block(b,leaf,1.65,(paneltop+.68)/2,1.005,.13,paneltop-.68,red,'red framed door leaf')
            ring(b,leaf,2.51,.81,1.18,.082,1.558,1.59,'raised red panel','upper door moulding')
            block(b,leaf,1.556,2.51,.65,.030,1.00,'green grey glass','door glazing')
            for dx in (-.19,.19):
                block(b,leaf+dx,1.525,2.51,.041,.04,.99,red,'glazing upright')
            for z in (2.29,2.63):
                block(b,leaf,1.524,z,.65,.04,.045,red,'glazing horizontal rail')
            ring(b,leaf,1.24,.79,.79,.068,1.544,1.60,'raised red panel','lower door relief')
            block(b,leaf-sign*.30,1.515,1.79,.036,.064,.19,'brass pull','brass door pull')
    block(b,5.02,-.04,1.69,.99,.046,.38,'dark bronze','east pier rectangular plaque')

    block(b,0,1.555,4.315,7.56,.28,.616,shade,'rear stone band above transoms')
    for x in (-3.75,-1.25,1.25,3.75):
        block(b,x,1.442,3.99,.48,.66,.11,stone,'portal jamb head')

    # The red head and two open stiles of the central doorway are
    # visible in both the pre-2012 exterior and restored front photograph.
    block(b,0,1.52,3.18,2.14,.14,.36,red,'central doorway red header')
    for x in (-1.03,1.03):
        block(b,x,1.51,1.87,.077,.16,2.41,red,'central red jamb')
        block(b,x,1.415,1.60,.036,.051,.34,'brass pull','central vertical push plate')
    # The tall pale plaque is attached to the eastern intermediate jamb.
    # Its small lettering has no legible transcription in the available image.
    block(b,1.25,1.118,2.29,.29,.05,1.37,'title panel limestone','intermediate pier vertical plaque')
    for x in (1.14,1.36):
        for z in (1.70,2.87):
            face(b,Point(x,z).buffer(.011,quad_segs=4),1.084,1.092,'dark bronze','plaque fixing')

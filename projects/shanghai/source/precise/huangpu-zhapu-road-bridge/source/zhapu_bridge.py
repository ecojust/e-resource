"""Visible concrete beam bridge over Suzhou Creek. X runs east across the deck, Y north along it."""
from pathlib import Path
import math

from photo_architecture import Facade
from sign_lettering import add_facade_lettering

HALF_LENGTH = 71.94 / 2
MAIN_HALF = 36.58 / 2
HALF_ROAD = 12.9 / 2
HALF_DECK = HALF_ROAD + 2.2
CURB_RISE = .16
WALL = .24
PALETTE = {
    'river concrete': {'color':[.57,.55,.50], 'roughness':.91},
    'painted fascia': {'color':[.72,.73,.68], 'roughness':.88},
    'projecting coping': {'color':[.80,.79,.71], 'roughness':.83},
    'recessed moulding': {'color':[.46,.48,.44], 'roughness':.89},
    'sheltered concrete': {'color':[.37,.37,.33], 'roughness':.95},
    'cutwater stone': {'color':[.52,.44,.33], 'roughness':.93},
    'stone coping': {'color':[.64,.55,.40], 'roughness':.9},
    'asphalt': {'color':[.17,.18,.18], 'roughness':.97},
    'paved walk': {'color':[.49,.47,.42], 'roughness':.94},
    'curb stone': {'color':[.67,.65,.57], 'roughness':.94},
    'road marking': {'color':[.76,.75,.65], 'roughness':.93},
    'green name panels': {'color':[.046,.24,.17], 'roughness':.68},
    'panel lettering': {'color':[.83,.87,.77], 'roughness':.74},
}

def deck_height(y):
    return 3.74 + .47 * (1 - (y / HALF_LENGTH) ** 2)

def soffit(y):
    """Fit the visible shallow, haunched lower edge. The structural sections were not measured."""
    distance = abs(y)
    pier_half = .79
    if distance <= MAIN_HALF - pier_half:
        u = distance / (MAIN_HALF - pier_half)
        return 3.38 - 2.48 * u ** 2.65
    if distance <= MAIN_HALF + pier_half:
        return .90
    u = (distance-MAIN_HALF-pier_half)/(HALF_LENGTH-MAIN_HALF-pier_half)
    return .90 + 1.67 * (1 - abs(2*u-1) ** 2.16)

def stations(lo, hi, spacing):
    count = math.ceil((hi-lo)/spacing)
    return [lo+(hi-lo)*i/count for i in range(count+1)]

def band(b, ys, left, right, bottom, top, material, label):
    verts=[]
    for y in ys:
        verts.extend([(left,y,bottom(y)),(right,y,bottom(y)),(right,y,top(y)),(left,y,top(y))])
    faces=[(3,2,1,0)]
    for i in range(len(ys)-1):
        j=4*i
        for k in range(4):
            m=(k+1)%4
            faces.append((j+k,j+m,j+m+4,j+k+4))
    faces.append(tuple(range(len(verts)-4,len(verts))))
    b.add(verts,[tuple(reversed(face)) for face in faces],material,label)

def deck_band(b, ys, left, right, z1,z2,mat,name):
    band(b,ys,left,right,lambda y:deck_height(y)+z1,lambda y:deck_height(y)+z2,mat,name)

def tapered_cutwater(b, y, tiers, material, label):
    """Eight-sided plan with cutwaters that project beyond the pale edge beam on both river faces."""
    vertices=[];faces=[]
    for z,width,half,tip in tiers:
        ring=[(-width,-half),(-width-tip,-.22*half),(-width-tip,.22*half),(-width,half),
              (width,half),(width+tip,.22*half),(width+tip,-.22*half),(width,-half)]
        vertices.extend((x,y+dy,z)for x,dy in ring)
    for t in range(len(tiers)-1):
        for k in range(8):
            j=t*8+k;q=t*8+(k+1)%8
            faces.append((j,j+8,q+8,q))
    faces.extend([tuple(range(8)),tuple(reversed(range(len(vertices)-8,len(vertices))))])
    b.add(vertices,faces,material,label)

def batter(b,side,y,label):
    levels=[(.34,1.17,1.08),(.64,1.04,1.00),(2.87,.32,.33),(3.23,.20,.25)]
    v=[];f=[]
    for z,reach,half in levels:
        inner=side*(HALF_DECK-.24);outer=side*(HALF_DECK+reach)
        v.extend([(inner,y-half,z),(outer,y-half*.70,z),(outer,y+half*.70,z),(inner,y+half,z)])
    for level in range(len(levels)-1):
        for k in range(4):
            j=4*level+k;q=4*level+(k+1)%4
            face=(j,q,q+4,j+4)
            f.append(face if side==1 else tuple(reversed(face)))
    end_faces=[(3,2,1,0),tuple(range(12,16))]
    f.extend(end_faces if side==1 else [tuple(reversed(face)) for face in end_faces])
    b.add(v,f,'cutwater stone',label)

def build_bridge(b,lod=False):
    divisions=[-HALF_LENGTH,-MAIN_HALF,MAIN_HALF,HALF_LENGTH]
    for i,span in enumerate(['south short span','central suspended span','north short span']):
        lo,hi=divisions[i:i+2]
        ys=sorted(set(stations(lo,hi,1.7 if lod else .66)+[a for a in [lo+.79,hi-.79]if lo<a<hi]))
        band(b,ys,-HALF_DECK+.12,HALF_DECK-.12,soffit,lambda y:deck_height(y)-.09,'river concrete',span+'/visible beam underside')
        deck_band(b,ys,-HALF_ROAD,HALF_ROAD,-.10,0,'asphalt',span+'/carriageway')
        for side,label in [(-1,'west'),(1,'east')]:
            prefix=span+'/'+label
            def across(a,c): return sorted([side*a,side*c])
            band(b,ys,*across(HALF_DECK-.17,HALF_DECK+.018),lambda y:soffit(y)-.015,
                 lambda y:deck_height(y)-.03,'painted fascia',prefix+'/haunched fascia')
            band(b,ys,*across(HALF_DECK+.018,HALF_DECK+.058),lambda y:soffit(y)+.10,
                 lambda y:soffit(y)+.19,'projecting coping',prefix+'/curved lower moulding')
            deck_band(b,ys,*across(HALF_ROAD,HALF_DECK),-.10,CURB_RISE,'paved walk',prefix+'/walkway')
            deck_band(b,ys,*across(HALF_ROAD,HALF_ROAD+.13),.006,CURB_RISE+.006,'curb stone',prefix+'/curb')
            deck_band(b,ys,*across(HALF_DECK-WALL,HALF_DECK),CURB_RISE,1.03,'painted fascia',prefix+'/solid parapet')
            deck_band(b,ys,*across(HALF_DECK-.30,HALF_DECK+.06),.99,1.10,'projecting coping',prefix+'/parapet cap')
            deck_band(b,ys,*across(HALF_DECK+.02,HALF_DECK+.105),-.11,-.015,'recessed moulding',prefix+'/fascia drip')
            deck_band(b,ys,*across(HALF_DECK+.015,HALF_DECK+.084),.025,.13,'projecting coping',prefix+'/fascia upper band')
            if not lod:
                for joint in stations(lo,hi,2.45)[1:-1]:
                    deck_band(b,[joint-.009,joint+.009],*across(HALF_ROAD+.15,HALF_DECK-WALL-.02),
                              CURB_RISE-.002,CURB_RISE+.002,'recessed moulding',prefix+'/paving joints')
    for y,label in [(-MAIN_HALF,'south pier'),(MAIN_HALF,'north pier')]:
        tapered_cutwater(b,y,[(-.34,8.24,1.21,.98),(.31,8.24,1.21,.98),(.47,8.13,1.12,.86)],
                          'cutwater stone',label+'/river plinth')
        tapered_cutwater(b,y,[(.42,8.12,1.14,.91),(.62,8.14,1.14,.92),(.69,8.02,1.03,.80)],
                          'stone coping',label+'/stone plinth cap')
        tapered_cutwater(b,y,[(.50,7.82,.92,.47),(1.32,7.73,.81,.35)],
                          'sheltered concrete',label+'/beam bearing')
        for side,title in [(-1,'west'),(1,'east')]:
            batter(b,side,y,label+'/'+title+' battered nose')
    for y in (-HALF_LENGTH,HALF_LENGTH):
        b.box((0,y+(.19 if y<0 else -.19),.38),(2*HALF_DECK-.13,.38,1.02),'river concrete',label='bank abutments')
    # Viewed from upstream, north is on the left of the photographed inscription.
    x = -(HALF_DECK + .094)
    for glyph, y in zip('乍浦路桥', [9.1, 3.05, -3.05, -9.1]):
        z = deck_height(y) - .18
        b.box((x,y,z),(.035,1.11,.70),'green name panels',label='west fascia/name panel '+glyph)
        if not lod:
            outward = x - .0175
            face = Facade(b, (outward,y+1), (outward,y-1), 'west fascia')
            add_facade_lettering(face,glyph,0,z,.50,.48,.002,.012,'panel lettering',
                                 label='bridge name',font=Path(__file__).parent/'fonts/ZhapuBridgeSigns.otf')
    for y in stations(-32,32,6.2):
        for x in [-2.15,2.15]:
            deck_band(b,[y-.93,y+.93],x-.042,x+.042,.007,.012,'road marking','interrupted carriageway paint')

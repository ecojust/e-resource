"""Five copper-clad domes and the recessed arched lights below them, in metres."""
from math import cos, pi, sin
from shapely.geometry import box
from photo_architecture import opening

PLASTER = 'ivory mineral plaster'
MOULDING = 'pale moulded plaster'
COPPER = 'blue painted copper'
FOLD = 'blue copper standing seams'
IRON = 'dark glazing bars'
GLASS = 'smoky recessed glazing'
FINIAL = 'weathered finial metal'
PALETTE = {
    PLASTER: {'color':[.82,.80,.74], 'roughness':.9},
    MOULDING: {'color':[.73,.72,.67], 'roughness':.8},
    COPPER: {'color':[.115,.205,.315], 'roughness':.47,'metallic':.44},
    FOLD: {'color':[.116,.183,.257], 'roughness':.43,'metallic':.53},
    IRON: {'color':[.15,.16,.16], 'roughness':.58,'metallic':.3},
    GLASS: {'color':[.205,.25,.267], 'roughness':.31,'metallic':.26},
    FINIAL:{'color':[.42,.35,.22], 'roughness':.47,'metallic':.59}
}
# Profile in radius/eaves-radius and elevation/crown-height. The source distinguishes
# the slightly pinched foot from the broad lower shoulder of the copper skin.
PROFILE = ((0,.92),(.065,.97),(.15,1.008),(.25,1.018),(.36,.988),(.47,.928),
           (.59,.822),(.70,.679),(.80,.51),(.89,.315),(.955,.155),(1,.038))
def shell(b, centre, rings, count, material, label):
    cx,cy=centre
    vertices=[(cx+r*cos(2*pi*i/count),cy+r*sin(2*pi*i/count),z)
              for z,r in rings for i in range(count)]
    faces=[]
    for j in range(len(rings)-1):
        for i in range(count):
            a=j*count+i;c=j*count+(i+1)%count
            faces.append((a,c,c+count,a+count))
    faces.extend([tuple(reversed(range(count))),tuple((len(rings)-1)*count+i for i in range(count))])
    b.add(vertices,faces,material,label)
def dome(b,centre,base,radius,height,small,lod,label):
    seg=32 if lod else 64
    levels=[(base+k*height,r*radius)for k,r in PROFILE]
    shell(b,centre,levels,seg,COPPER,label+' / formed copper skin')
    ribs=8 if lod else (16 if small else 24)
    for j in range(ribs):
        a=2*pi*j/ribs
        line=[(centre[0]+r*cos(a),centre[1]+r*sin(a),z) for z,r in levels[:-1]]
        b.tube(line,.016 if small else .025,FOLD,4 if lod else 6,label+' / radial seams')
    top=base+height
    shell(b,centre,[(top-.03,radius*.047),(top+.08,radius*.049),
                    (top+.17,radius*.027),(top+.23,radius*.012)],
          8 if lod else 16,FINIAL,label+' / finial')
def drum(b,centre,radius,floor,eaves,bays,lod,label):
    arc=2*pi*radius/bays
    span=eaves-floor
    sill=floor+.13*span
    window_top=eaves-.16*span
    aperture=opening(0,sill,arc*.47,window_top-sill,arc*.235,10 if lod else 20)
    trim=aperture.buffer(.055 if bays<=8 else .075,join_style='round').difference(aperture)
    surround=box(-arc/2,floor,arc/2,eaves)
    for i in range(bays):
        azimuth=(i+.5)*2*pi/bays
        def position(u,z,depth):
            a=azimuth+u/radius
            return (centre[0]+(radius+depth)*cos(a),centre[1]+(radius+depth)*sin(a),z)
        b.prism(surround.difference(aperture),-.27,0,position,PLASTER,label+' / pierced drum')
        b.prism(trim,-.018,.065,position,MOULDING,label+' / arch reveal')
        b.prism(aperture,-.24,-.214,position,GLASS,label+' / recessed panes')
        if not lod:
            for z in (sill+.32*(window_top-sill),sill+.66*(window_top-sill)):
                b.prism(box(-arc*.23,z-.028,arc*.23,z+.028).intersection(aperture),-.204,-.162,position,IRON,label+' / transom')
            b.prism(box(-.026,sill,.026,window_top).intersection(aperture),-.204,-.16,position,IRON,label+' / mullion')
    for z in (floor+.06,eaves-.27,eaves-.04):
        shell(b,centre,[(z-.12,radius+.015),(z-.075,radius+.105),
                        (z+.045,radius+.105),(z+.1,radius+.035)],32 if lod else 64,
              MOULDING,label+' / drum courses')
def add_roof(b,lod):
    # Thirty-five metres is the crown height recorded in the Shanghai local history.
    # Drum diameters and setback are photogrammetric estimates within the 24.35 × 27.06 m registered parcel.
    drum(b,(0,0),4.65,20.4,28.3,12,lod,'central drum')
    dome(b,(0,0),28.28,4.91,6.49,False,lod,'central cupola')
    for x,y,corner in ((-6.25,-7,'southwest'),(6.25,-7,'southeast'),
                       (6.25,7,'northeast'),(-6.25,7,'northwest')):
        centre=(x,y)
        drum(b,centre,2.28,15.85,21.70,8,lod,corner+' drum')
        dome(b,centre,21.68,2.47,3.55,True,lod,corner+' cupola')

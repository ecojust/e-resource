"""Cream balcony screens, corner return and original rail proportions at 50 Shimen No. 2 Road."""


def mat(rgb,rough=.87,metal=0):
    return dict(color=[v/3294.6 if v<=10 else ((v/255+.055)/1.055)**2.4 for v in rgb],roughness=rough,metallic=metal)


PALETTE={'cream render':mat((201,189,162)),'slot reveal':mat((161,148,124)),'coping':mat((211,201,178)),
         'floor concrete':mat((153,143,126),.93),'iron':mat((66,60,49),.70,.16),'rust':mat((92,68,45),.80,.09)}
FRONT=[(.47,1.42),(2.50,3.37),(3.56,4.30),(4.49,5.34)]
RETURN=[(.27,.84)]
ROWS=[(.408,.470),(.543,.605),(.677,.739),(.810,.872)]
LIMIT=5.53


def box(b,h0,h1,d0,d1,z0,z1,axis,material,name):
    centre=((h0+h1)/2,(d0+d1)/2,(z0+z1)/2)
    size=(h1-h0,d1-d0,z1-z0)
    if axis=='end':
        centre=(-centre[1],centre[0],centre[2])
        size=(size[1],size[0],size[2])
    b.box(centre,size,material,label=name)


def pierced_wall(b,begin,end,slots,axis):
    floors=[(0,ROWS[0][0]),*[(ROWS[j][1],ROWS[j+1][0])for j in range(3)],(ROWS[-1][1],.956)]
    for i,(low,high) in enumerate(floors):
        box(b,begin,end,0,.108,low,high,axis,'cream render','horizontal plaster strip '+str((axis,i)))
    for i,(low,high) in enumerate(ROWS):
        piers=[(begin,slots[0][0]),*[(left[1],right[0])for left,right in zip(slots,slots[1:])],(slots[-1][1],end)]
        for j,(l,r) in enumerate(piers):
            box(b,l,r,0,.108,low,high,axis,'cream render','parapet between openings '+str((axis,i,j)))
        for j,(l,r) in enumerate(slots):
            # Thin revealed inner beds and jambs leave a genuine unobstructed opening.
            for lo,hi in ((low,low+.004),(high-.004,high)):
                box(b,l,r,.009,.108,lo,hi,axis,'slot reveal','slot bed '+str((axis,i,j,lo)))
            for a,c in ((l,l+.004),(r-.004,r)):
                box(b,a,c,.009,.108,low,high,axis,'slot reveal','slot jamb '+str((axis,i,j,a)))
    box(b,begin,end,-.012,.121,.956,.981,axis,'coping','projecting coping '+axis)


def add_building(b,lod=False):
    pierced_wall(b,0,LIMIT,FRONT,'front');pierced_wall(b,.108,1.34,RETURN,'end')
    box(b,0,LIMIT,-.016,1.34,-.092,0,'front','floor concrete','balcony slab and flat underside')
    sides=5 if lod else 12
    for z,r in ((1.090,.009),(1.275,.016)):
        b.tube([(0,.057,z),(LIMIT,.057,z)],r,'iron',sides,'front handrail '+str(z))
        b.tube([(0,.057,z),(0,1.34,z)],r,'iron',sides,'return handrail '+str(z))
    for i,x in enumerate((.05,.46,1.44,2.45,3.46,4.41,5.44)):
        b.tube([(x,.057,.975),(x,.057,1.281)],.0105,'iron',sides,'front iron upright '+str(i))
        box(b,x-.024,x+.024,.033,.083,.975,.988,'front','rust','upright foot '+str(i))
    for y in (.34,.81,1.29):
        b.tube([(0,y,.975),(0,y,1.277)],.010,'iron',sides,'return vertical '+str(y))
    for x in (1.56,3.64,5.45):
        v=[(x-.032,0,-.091),(x-.032,.19,-.091),(x-.032,.19,-.177),
           (x+.032,0,-.091),(x+.032,.19,-.091),(x+.032,.19,-.177)]
        b.add(v,[(0,2,1),(3,4,5),(0,3,5,2),(1,2,5,4),(0,1,4,3)],'floor concrete','short bracket below slab '+str(x))

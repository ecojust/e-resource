from stepped_wall import *
def test(t,names,hit):
    qs=[]
    def ray(o,d,valid,l):
        a=hit(t,names,np.array(o),np.array(d))
        assert (a[0] if a else None) in valid,(o,l,valid,a)
        qs.append(dict(label=l,material=a[0] if a else None,point=a[1] if a else None))
    for i,(y,z) in enumerate(ENDS):
        above=.45 if i==0 else 1.46
        for x in (-.14,-.05,.049,.14):
            for dz in (-.161,-.112,-.026,.008):
                ray((x,y-.41,z+dz),(0,1,0),(END,),'Pale front of four stepped courses')
            ray((x,y-.39,z-.202),(0,1,0),(BAND,),'Lower shaded moulding')
            ray((x,y-.41,z+.051),(0,1,0),(END,),'Blank base of triangular relief field')
        for yy in np.linspace(y+.09,y+.61,7):
            for zz in (above,above+.12):ray((.8,yy,zz),(-1,0,0),(LIME,),'Side of stepped plaster wall')
            for x in (-.115,.116):ray((x,yy,3.21),(0,0,-1),(TILE,),'Raised ridge slopes on the two sides')
            ray((.002,yy,3.21),(0,0,-1),(TIP,),'Top of segmented ridge')
        for c in (-.135,-.047,.046,.135):ray((c,y-.41,z+.101-.020),(0,1,0),(ORN,),'Front of one small curved relief')
    return qs

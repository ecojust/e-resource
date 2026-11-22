from numbered_passage import *
def test(tris,mats,hit):
    records=[]
    def mark(o,d,m,label):
        t=hit(tris,mats,np.array(o),np.array(d));assert (t[0] if t else None)==m,(o,m,t)
        if m==SHADE:assert t[1][1]>1.46
        records.append(dict(label=label,material=t[0]if t else None,point=t[1]if t else None))
    for x in (-.235,-.12,.001,.152,.31,.465):
        for z in (.25,.60,1.14,1.57,2.00):mark((x,-.6,z),(0,1,0),SHADE,'Street ray travels through the entrance into deep shade')
    for x in (-.99,-.78,-.45,.667,.979):
        for z in (.77,.98,1.31,1.73,1.91,2.49,2.75):mark((x,-.6,z),(0,1,0),LIME,'Lime plaster flanking the doorway')
    for j in range(4):
        for x in (.641,.772,.969):mark((x,-.6,.056+j*.111),(0,1,0),BRICK,'Street brick course below the broken plaster')
    for y in (.38,.83,1.12):
        for z in (.88,1.28):mark((.04,y,z),(-1,0,0),LIME,'Wall on the left as the entrance turns inward')
    for p in glyphs():
        v=p.representative_point();mark((v.x,-.61,v.y),(0,1,0),LETTER,'Digit or letter of the signed number')
    mark((-.638,-.6,2.17),(0,1,0),NUMBER,'Green enamel around the lettering')
    return records

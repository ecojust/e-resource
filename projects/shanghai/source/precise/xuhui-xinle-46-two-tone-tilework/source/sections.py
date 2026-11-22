"""Sample the two colour courses and recessed joints, soldier head, jambs and returning wall."""
import numpy as np
from facing_tiles import EDGE,REVEAL,STEP,segments,material,RED,IVORY,MORTAR,STONE,CAP,DRIP,GREEN,SLAT,ROWS
def test(tri,names,hit):
    tests=[]
    def sample(label,point,d,expected):
        contact=hit(tri,names,np.array(point,float),np.array(d,float));assert contact and contact[0]==expected,(label,point,expected,contact)
        tests.append(dict(label=label,material=contact[0],point=contact[1]))
    def front(x,z,m,l):sample(l,(x,-.8,z),(0,1,0),m)
    for r in range(ROWS):
        z=(r+.5)*STEP
        for col,u,v in segments(r,REVEAL,EDGE):
            if v-u>.07:front((u+v)/2,z,material(r,col),'Right pier facing centre')
        for col,u,v in segments(r,0,.98):
            if v-u>.08:sample('Side return facing centre',(EDGE+.75,(u+v)/2,z),(-1,0,0),material(r,col+1))
    for r in (3,4,6,9,12,15,17,19,21):
        front(1.87,r*STEP,MORTAR,'Bed joint through solid pier')
    for i in range(31):
        x=-REVEAL+(i+.5)*2*REVEAL/31;front(x,1.62,IVORY if i%2 else RED,'Vertical soldier over opening')
    for x in (-1.39,-.91,-.42,.33,.84,1.34):front(x,1.4,STONE,'Cement head')
    for x in (-1.43,1.43):
        for z in (.18,.5,.86,1.08):front(x,z,STONE,'Projecting pale jamb')
    front(.113,1.39,GREEN,'Green enamel number plate')
    for x in (-.9,0,.9):front(x,.616,SLAT,'Shutter beyond masonry')
    for x in (-1.72,-.6,.95,1.84):
        front(x,2.86,CAP,'Returning orange string');front(x,3.04,DRIP,'Grey drip')
    return tests

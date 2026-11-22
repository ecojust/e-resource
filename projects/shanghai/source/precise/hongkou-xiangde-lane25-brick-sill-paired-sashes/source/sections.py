from sash import *
def test(tri,m,hit):
    reads=[]
    def probe(x,z,mat,why):
        row=hit(tri,m,np.array([x,-1.,z]),np.array([0.,1.,0.]));assert row and row[0] in mat,(x,z,why,row)
        reads.append(dict(label=why,material=row[0],point=row[1]))
    for x in(-.67,-.55,-.31,-.22,.21,.32,.54,.68):
        for z in(.47,.64,1.00,1.13,1.43,1.59):probe(x,z,[TEAL],'Coloured field behind divided sash')
        for z in(.835,1.277,1.72):probe(x,z,[MULL],'Horizontal glazing division')
    for x in(-.832,.832):
        for z in(.49,1.09,1.71):probe(x,z,[REVEAL],'Exposed face of the joint to the side of the visible jamb')
    for x in(-.803,0,.803):
        for z in(.49,.77,1.02,1.53,1.87):probe(x,z,[FRAME],'Meeting or perimeter stile')
    for x in(-.4195,.4195):
        for z in(.49,.74,1.02,1.53,1.87):probe(x,z,[MULL],'Narrow central glazing bar')
    for i in range(19):
        probe(-.929+i*.098+.047,.293,[SILL,DARK],'One projecting soldier brick')
    return reads

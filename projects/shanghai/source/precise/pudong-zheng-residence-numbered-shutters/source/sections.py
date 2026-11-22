from shutter_boards import *
def test(t,names,hit):
    result=[]
    def probe(x,z,m,label):
        a=hit(t,names,np.array([x,-.60,z]),np.array([0.,1.,0]))
        assert (a[0] if a else None)==m,(x,z,m,a)
        result.append(dict(label=label,material=a[0] if a else None,point=a[1] if a else None))
    for i in range(8):
        x=(i-3.5)*PITCH
        for z in (1.18,1.46,1.76,2.04):probe(x+.046,z,WOOD,'Exposed upper shutter surface')
        for z,m in ((.66,WOOD),(.41,PLASTER),(.55,FRAME),(.875,GUIDE),(1.891,FRAME)):
            probe(x,z,m,'Horizontal succession of sill, wall and shutter')
        for u,v in (DIGITS[i][0][0],DIGITS[i][0][1]):
            probe(x+(u-.5)*.042,.985+v*.080,MARK,'Raised outline of the pale shutter number')
    for i in range(7):
        x=(i-3)*PITCH
        for z in (1.431,1.591):probe(x,z,BACK,'Dark groove between the two removable panels')
    for x in (-TOTAL/2-.041,TOTAL/2+.041):
        for z in (.36,.77,1.01,1.8):probe(x,z,FRAME,'Outside jamb')
    return result

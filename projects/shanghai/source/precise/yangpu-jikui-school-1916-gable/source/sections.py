from school_gable import *
def test(tri,names,hit):
    rows=[]
    def check(x,z,m,name):
        ans=hit(tri,names,np.array([x,-.5,z]),np.array([0.,1.,0.]));assert ans and ans[0]==m,(x,z,name,ans)
        rows.append(dict(label=name,material=m,point=ans[1]))
    for x in (-.85,-.72,-.56,.57,.72,.85):
        for z in (.47,.62,.79,.93,1.09,1.22,1.34):check(x,z,PLASTER,'Rendered background flanking the date')
    for z in (1.492,1.555,1.618,1.68,1.739):
        for x in (-.055,0,.055):check(x,z,DARK,'A true individual louvre')
    for i,digit in enumerate('1916'):
        for k,stroke in enumerate(digit_paths(digit)):
            for u,v in stroke[1:-1] or stroke[:1]:
                check(-.37+i*.192+u*.176+(v-.5)*.023,.956+v*.233,STONE,'Raised numeral '+str(i)+' stroke '+str(k))
    for x in (-1.00,-.88,-.76,.75,.88,1.01):check(x,.17,RED,'Jamb window head')
    for x in (-.13,0,.13):check(x,1.434,RED,'Projecting vent sill')
    return rows

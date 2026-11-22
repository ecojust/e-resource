from arched_door import *
def test(t,m,hit):
    r=[]
    def ask(x,z,allowed,what):
        v=hit(t,m,np.array([x,-1.,z]),np.array([0.,1.,0.]));assert v and v[0]in allowed,(what,x,z,v)
        r.append(dict(label=what,material=v[0],point=v[1]))
    for count,rad,mat,description in [(21,.752,BRICK,'Outer red brick arch ring'),(19,.605,INNER,'Recessed second arch order')]:
        for k in range(count):
            a=(k+.5)*pi/count;ask(rad*cos(a),SPRING+rad*sin(a),[mat],description)
            if k:
                a=k*pi/count;ask(rad*cos(a),SPRING+rad*sin(a),[BED],'Recessed joint between individual voussoirs')
    for a in np.linspace(.17,pi-.17,14):ask(.89*cos(a),SPRING+.89*sin(a),[ROUGH],'Pebbled wall outside arch')
    for x in (-.912,.912):
        for j in range(11):ask(x,.035+j*.079,[BASE],'Pale brick courses in pier foot')
    for x in(-.539,0,.539):
        for z in(.24,.51,.765,.987,1.214,1.43):ask(x,z,[GATE],'Paired gate uprights')
    for x in(.806,.932):
        for z in(1.61,1.665,1.782):ask(x,z,[TAG],'Green hut number plaque')
    return r

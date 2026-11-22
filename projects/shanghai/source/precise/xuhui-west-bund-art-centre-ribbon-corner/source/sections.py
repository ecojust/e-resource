from steel_ribbon import *
def test(t,names,hit):
    tests=[]
    def sample(side,u,z,mat,label):
        o=np.array([R+1,u,z]) if side else np.array([u,-1,z])
        d=np.array([-1,0,0]) if side else np.array([0,1,0])
        v=hit(t,names,o,d);assert v and v[0]==mat,(side,u,z,mat,v)
        tests.append(dict(label=label,material=mat,point=v[1]))
    for side,l,r,count in ((False,-1.385,-.181,9),(False,.059,1.264,9),(True,.226,DEPTH,18)):
        for low,high in ((.388,.841),(1.174,1.627)):
            for k in range(count):
                x=l+(k+.5)*(r-l)/count
                for row in (0,2):sample(side,x,low+(row+.47)*(high-low)/4,GLASS,'Open glass area within steel divisions')
            for k in range(1,count):
                sample(side,l+k*(r-l)/count,low+.28*(high-low),HEAVY if k%3==0 else STEEL,'Primary and secondary uprights')
    for x in (-1.45,-.102,.009,1.366,1.448):
        for z in (.54,.92,1.36,1.84):sample(False,x,z,PANELS,'Pale structural pier')
    for z in (.55,1.32):sample(True,.11,z,PANELS,'Closed corner pier on continuous end')
    for x in (-1.051,-.586,.477,.861):sample(False,x,2.313,GLASS,'Inset clerestory glazing')
    return tests

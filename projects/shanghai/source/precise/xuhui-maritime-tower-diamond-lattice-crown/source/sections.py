from diamond_crown import *
def test(tri,names,hit):
    results=[]
    def ray(theta,z,expected,label):
        u=np.array([math.cos(theta),math.sin(theta),0]);r=hit(tri,names,u*1.67+np.array([0,0,z]),-u)
        assert r and r[0] in expected,(z,theta,expected,r)
        results.append(dict(label=label,material=r[0],point=r[1]))
    for j in range(0,MEMBERS,2):
        for hand in [-1,1]:
            for z in [.237,.580,1.037,1.484,1.976,2.442,2.938,3.213]:
                x,y,_=design_xyz(z,j,hand)
                ray(math.atan2(y,x),z,{SILVER},'First intersection with one of the crossed external diagonal members')
    step=math.tau/MEMBERS
    for z,mat in [(.328,LINER),(.615,LINER),(1.702,LINER),(2.029,SHADE),(2.442,LINER)]:
        # Midpoint of the widest clear interval in one diamond course.
        angles=sorted([(-turn(z))%step,turn(z)%step]);a0,a1=angles
        c=(a0+a1)/2 if a1-a0>step-(a1-a0) else (a0+a1+step)/2
        for j in range(0,MEMBERS,2):ray(c+j*step,z,{mat},'Open diamond gives a second sight line to the material behind it')
    return results

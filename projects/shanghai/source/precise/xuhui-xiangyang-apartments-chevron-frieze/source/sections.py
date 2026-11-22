from chevron_frieze import *
def test(tri,names,hit):
    rows=[]
    def sample(x,z,mat,label):
        a=hit(tri,names,np.array([x,-.55,z]),np.array([0.,1.,0.]))
        assert a and a[0]==mat,(x,z,mat,a)
        rows.append(dict(label=label,material=mat,point=a[1]))
    for c in CENTERS:
        for j in range(5):
            mid=.715+j*.076
            sample(c+.075,mid+.046,FILLET,'Front of right leg on a V strip')
            sample(c-.075,mid+.046,FILLET,'Front of left leg on a V strip')
            sample(c+.04,mid+.058,RECESS,'Exposed channel between adjacent raised folds')
        if c == CENTERS[0]:
            sample(c-.184,.87,WALL,'Edge of the outer panel falls behind the end pier')
        else:
            sample(c-.184,.87,FILLET,'Vertical border between the relief panels')
    for a in [-1.40+i*.350 for i in range(9)]:
        sample(a,.56,FILLET,'Separate bracket')
        sample(a+.12,.56,SHADOW,'Setback on the side of each soffit bracket')
    for c in (-1.74,1.74):
        for dx in (-.076,0,.076):sample(c+dx+.015,.716,FILLET,'Pendant raised above the pier')
        sample(c,.272,WALL,'Face below all three pendants')
    return rows

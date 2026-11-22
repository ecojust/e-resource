from brick_windows import *
def test(t,names,hit):
    out=[]
    def check(x,z,mat,note,y=-1.,direction=(0,1,0)):
        v=hit(t,names,np.asarray((x,y,z)),np.asarray(direction));assert v and v[0]==mat,(x,z,mat,v)
        out.append(dict(label=note,material=mat,point=v[1]))
    for cx in CENTERS:
        for dx in (-.332,-.198,.112,.289):
            for z in (.47,.79,1.11,1.42):check(cx+dx,z,GLASS,'Glazing to either side of the middle stile')
        for x in (-.34,-.21,0,.19,.33):
            check(cx+x,.321,EDGE,'Independent projecting sill')
            check(cx+x,.199,TRIM,'Rectangular apron')
            check(cx+x,1.267,FRAME,'High horizontal sash rail')
        for sign in (-1,1):
            for z in (.52,.86,1.29,1.55):check(cx+sign*.488,z,TRIM,'Pale jamb')
            check(cx+sign*.521,1.738,TRIM,'Curved end of lintel')
    for x in (-1.38,-.22,-.09,.015,.19,1.44):
        for z in (.115,.46,.82,1.11,1.51):check(x,z,BRICK,'Exposed mid- and edge-pier brick')
    return out

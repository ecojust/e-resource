from hotel_bays import *
def test(t,names,hit):
    rows=[]
    def take(x,z,mat,label):
        rec=hit(t,names,np.array([x,-2.,z]),np.array([0.,1.,0.]));assert rec and rec[0] in mat,(x,z,mat,rec)
        rows.append(dict(label=label,material=rec[0],point=rec[1]));return -rec[1][1]
    for c in CS:
        for lo in (0,3.17):
            for x in (-.784,-.601,-.115,.383,.699):
                for z in (1.46,1.72,2.08,2.41):assert take(c+x,lo+z,[PANE,REFLECTION],'Glass recessed above the balcony parapet')<-.17
                for z in (.477,.845,1.08,1.245):assert take(c+x,lo+z,[WALL],'Solid balcony face within its edge')>.84
            for x in (-.312,.202):
                for z in (1.78,2.19):take(c+x,lo+z,[FRAME],'Visible thin sash between panes')
            for x in (-.99,-.686,0,.631,.96):
                take(c+x,lo+2.595+.108+.019+arc(x,1.173),[LIP],'Upper curved edge of separate window hood')
            for x in (-.65,-.24,.27,.59):assert take(c+x,lo+.596,[BAND],'Raised ornament on low front panel')>.88
    return rows

"""Independent local-space first-hit checks for the E block, before its site transform."""

def south_cases():
    cases=[]
    def ray(name,xyz,direction,material,interval):
        cases.append(dict(name='E '+name,origin=list(xyz),direction=list(direction),
                          material=material,first_distance_m=interval))
    for label,x in [('east',-20.08),('centre',0),('west',20.12)]:
        for relative in (-.67,0,.67):
            ray(f'{label} open portal {relative:+.2f}',(x+relative,-5,1.35),(0,1,0),None,[0,6.05])
        ray(label+' lintel',(x,-5,2.49),(0,1,0),'E cement coping',[2.9,3.35])
        ray(label+' outer blade',(x+1.25,-5,11.55),(0,1,0),'E warm buff cement',[2.7,3.25])
        for z in (3.82,7.22,10.62):
            ray(f'{label} west stair light {z:.2f}',(x+.32,-5,z),(0,1,0),'E smoked stair lights',[3.40,3.47])
            ray(f'{label} east stair light {z:.2f}',(x-.32,-5,z),(0,1,0),'E smoked stair lights',[3.40,3.47])
        ray(label+' top left opaque infill',(x-.385,-5,14.12),(0,1,0),'E recessed grey stair panels',[3.28,3.36])
        ray(label+' split central fin',(x,-5,15.05),(0,1,0),'E warm buff cement',[2.6,3.20])
        ray(label+' stair landing',(x,-1.,.81),(0,0,-1),'E dark plinth',[.72,.74])
    for floor,z in enumerate((4.10,7.50,10.90),start=2):
        for x in (2.85,7.72,11.69):
            ray(f'north room window {floor}/{x}',(x,-4,z),(0,1,0),'E courtyard glazing',[4.25,4.29])
        ray(f'court window pier {floor}',(9.91,-4,z),(0,1,0),'Chestnut and warm ochre horizontal render',[3.99,4.01])
        ray(f'court ribbed spandrel {floor}',(7.91,-4,z-.49),(0,1,0),'E cement coping',[3.84,3.9])
        ray(f'south room window {floor}',(8.68,13,z),(0,-1,0),'E courtyard glazing',[3.21,3.27])
    for x in (-26,26):
        ray(f'open roof terrace {x}',(x,5,15),(0,0,-1),'E weathered flat roof',[5.10,5.14])
        ray(f'short terrace wall {x}',(x,-2,10.26),(0,1,0),'E warm buff cement',[1.9,1.98])
    ray('middle roof membrane',(5,5,17),(0,0,-1),'E weathered flat roof',[3.70,3.74])
    ray('garage recess',(9.92,-4,1.55),(0,1,0),'E deep reveal',[5.11,5.16])
    ray('projecting south balcony rail',(-9.73,15,3.50),(0,-1,0),'E warm buff cement',[4.29,4.37])
    ray('terrace top-storey east door',(-25,5.50,10.74),(1,0,0),'E courtyard glazing',[4.97,5.16])
    return cases

"""Recreate the three photographed strips of trailing greenery on the upper gallery."""
import math
import numpy as np
def add(b,lod):
    shades=[('garden foliage dark',[.034,.083,.018]),('garden foliage midtone',[.065,.137,.026]),('garden foliage light',[.112,.194,.038])]
    for s,color in shades:b.palette[s]={'color':color,'roughness':.80}
    rng=np.random.default_rng(868032);xface=7.43
    for i,(a,c)in enumerate(zip([.40,2.95,5.46],[2.95,5.46,7.87])):
        for g,(mat,col)in enumerate(shades):
            vertices=[];faces=[]
            for stem in range(3 if lod else 9):
                y0=a+.12+(c-a-.24)*(stem+rng.uniform(.04,.96))/(3 if lod else 9)
                drop=rng.uniform(.17,.57);side=rng.uniform(-.11,.11);phase=rng.uniform(-3,3)
                sample=np.linspace(0,1,4 if lod else 8);segments=[]
                for t in sample:
                    segments.append((xface+.025+.065*math.sin(t*math.pi)+.018*math.cos(t*6+phase),y0+side*t+.042*math.sin(t*5+phase),5.99-drop*t))
                b.tube(segments,.005 if lod else .004,mat,4 if lod else 5,f'gallery planting {i+1}/stem {g+1}-{stem+1}')
                for j in range(6 if lod else 15):
                    t=rng.uniform(0,1);y=y0+t*side+.054*math.sin(t*5+phase)+rng.uniform(-.059,.059)
                    z=5.99-drop*t+rng.uniform(-.023,.043);x=xface+.039+.065*math.sin(t*math.pi)+rng.uniform(-.014,.036)
                    θ=rng.uniform(-1.35,1.35);u=np.array([.10,math.sin(θ),math.cos(θ)]);v=np.array([.13,math.cos(θ),-math.sin(θ)])
                    n=np.cross(u,v);n/=np.linalg.norm(n);o=np.array([x,y,z]);l=rng.uniform(.030,.062);h=rng.uniform(.011,.026);offset=len(vertices)
                    vertices.extend([o-l*u,o-h*v,o+l*u,o+h*v,o+.005*n,o-.002*n])
                    for q in range(4):
                        nxt=(q+1)%4;faces.extend([(offset+q,offset+nxt,offset+4),(offset+nxt,offset+q,offset+5)])
            b.add(vertices,faces,mat,f'gallery planting {i+1}/leaves {g+1}')
    return b

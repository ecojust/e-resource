"""Model each clear glass unit's worn bevel and the balcony guard's staggered bridges."""
def glass_field(b,xyz,width,bottom,head,material,name):
    columns,rows=10,14
    du=width/columns;dz=(head-bottom)/rows;points=[];faces=[]
    for row in range(rows):
        for col in range(columns):
            u=(col+.5)*du-width/2;z=bottom+(row+.5)*dz;ix=len(points)
            for depth,s in [(-.143,1.),(-.119,1.),(-.106,.75)]:
                for x,y in [(-1,-1),(1,-1),(1,1),(-1,1)]:
                    points.append(xyz(u+s*x*(du*.5-.0086),z+s*y*(dz*.5-.0086),depth))
            faces.append(tuple(ix+k for k in [3,2,1,0]))
            for k in range(4):
                h=(k+1)%4
                faces.extend([(ix+k,ix+h,ix+4+h,ix+4+k),(ix+4+k,ix+4+h,ix+8+h,ix+8+k)])
            faces.append((ix+8,ix+9,ix+10,ix+11))
    b.add(points,faces,material,name)
def guard(bar,width,bottom,top,central,material):
    # Three fields have the same alternating short bridges. The central field is wider.
    count=11 if central else 9
    centres=[(k/count-.5)*(width-.048)for k in range(count+1)]
    for k,u in enumerate(centres):
        bar('garden guard / upright '+str(k),u-.012,u+.012,bottom+.075,top-.026,-.027,.010,material)
    for k,(u,v) in enumerate(zip(centres,centres[1:])):
        for part,relative in enumerate((.18,.55)if k%2 else (.37,.76)):
            z=bottom+relative*(top-bottom)
            bar('garden guard / short bridge '+str(k)+'-'+str(part),u+.012,v-.012,z-.012,z+.012,-.023,.006,material)

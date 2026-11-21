"""Small fittings visible between the two balcony groups in the February 2020 street survey."""
from porthole_wall import block,circle,facade


def outdoor_units(builder,d,lod):
    for i,z in enumerate(d['centres']):
        floor=i+2
        # The bottom storey has a pale fan unit; both upper units sit inside ageing slatted guards.
        x=-1.04
        bottom=z-0.52
        name=f'{floor}F condenser'
        block(builder,x-0.48,x+0.47,-0.45,-0.045,bottom,bottom+0.55,'AC enamel',name+' case')
        block(builder,x-0.52,x+0.51,-0.50,0.0,bottom-0.07,bottom-0.026,'AC brackets',name+' shelf')
        for x_at in [x-0.39,x+0.36]:
            builder.tube([(x_at,-0.44,bottom-0.065),(x_at,-0.033,bottom-0.30)],
                         0.018,'AC brackets',5 if lod else 8,name+' shelf brackets')
        fan_x,fan_z=x-0.14,bottom+0.272
        if i==0:
            shape=circle(fan_x,fan_z,0.217,16 if lod else 36)
            facade(builder,shape,-0.458,-0.450,'Fan vent',name+' circular inlet')
            if not lod:
                # Straight guard wires are clipped at the circular perimeter.
                for k in range(-3,4):
                    y=k*0.047
                    half=(0.21**2-y*y)**0.5
                    builder.tube([(fan_x-half,-0.466,fan_z+y),(fan_x+half,-0.466,fan_z+y)],
                                 0.004,'AC brackets',5,name+' fan wires')
                block(builder,x+0.23,x+0.40,-0.459,-0.451,bottom+0.427,bottom+0.484,
                      'Small blue service mark',name+' blue service mark')
        else:
            # Shallow cages stand in front of each of the two more distant units.
            block(builder,x-0.428,x+0.416,-0.461,-0.450,bottom+0.033,bottom+0.512,'Fan vent',name+' shaded air grille')
            for k in range(1,5 if lod else 9):
                h=bottom+0.030+k*(0.46/(5 if lod else 9))
                block(builder,x-0.421,x+0.416,-0.476,-0.459,h,h+0.013,'AC brackets',name+' louvers')
            for pos in [x-0.476,x-0.04,x+0.456]:
                block(builder,pos-0.012,pos+0.012,-0.485,-0.445,bottom-0.005,bottom+0.55,
                      'AC brackets',name+' guard uprights')
        if not lod:
            # A short, insulated line returns immediately to the wall behind each unit.
            builder.tube([(x+0.46,-0.16,bottom+0.14),(x+0.52,-0.13,bottom+0.11),
                          (x+0.54,-0.065,bottom-0.055),(x+0.55,-0.008,bottom-0.080)],
                         0.019,'Service insulation',8,name+' short pipe')
        if floor<4:
            block(builder,1.39,1.57,-0.089,-0.012,z-0.22,z+0.046,'AC enamel',name+' small wall fixture')
            block(builder,1.41,1.55,-0.101,-0.088,z-0.19,z+0.016,'Fan vent',name+' fixture face')

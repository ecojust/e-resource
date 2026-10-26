"""Replace only the two front arched-window frame grids, keeping all glass.

The 2025 image distinguishes three thick transoms from fine blind slats.
The selected top row36% / lower rows64%/3 are photograph-proportioned estimates.
"""
from shapely.geometry import box
from shapely.ops import unary_union

def replace_front_arch_frame(facade,shape,label):
    builder=facade.builder;full_label=facade.label+'/'+label+'-frame-grid'
    indices=[i for i,p in enumerate(builder.parts) if p['label']==full_label];assert len(indices)==1
    target=indices[0];previous=builder.parts[target];assert previous['material']=='bronze window frame'
    x0,z0,x1,z1=shape.bounds;inner=shape.buffer(-.09,join_style=2);outer=shape.buffer(-.025,join_style=2)
    bars=[box(x0+(x1-x0)*k/4-.028,z0,x0+(x1-x0)*k/4+.028,z1) for k in [1,2,3]]
    for fraction in [(.64/3),(.64*2/3),.64]:
        z=z0+(z1-z0)*fraction;bars.append(box(x0,z-.027,x1,z+.027))
    # Match the frozen common algorithm; do not clip intersecting bars first.
    panes=inner.difference(unary_union(bars));frame=outer.difference(panes)
    before=len(builder.parts);facade.prism(frame,-.27,-.16,'bronze window frame',label+'-frame-grid')
    assert len(builder.parts)==before+1
    builder.parts[target]=builder.parts.pop()

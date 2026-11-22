"""Model the external stair and two photographed openings at the west return.

The west edge is directed from north to south in the frozen footprint. Distances
below are measured inwards from its south end. The May 2015 photographs show
the iron railing, level landing and two window transoms. The February 2020
and January 2021 street photographs show light exposed treads. The earlier
green covering is recorded in the dated references. Metric sizes and the
total number of risers are estimates.
"""
from math import cos, pi, sin

from shapely.geometry import Polygon, box
from photo_architecture import opening


def west_windows(facade, u, build_window):
    width = 1.25
    sill = 1.48
    transom = 3.20
    lower = box(u - width / 2, sill, u + width / 2, transom - 0.13)
    upper = opening(u, transom + 0.14, width, 1.00, 0.62, 26)
    for shape, columns, rows, label in (
        (lower, 2, 3, 'west-stair-lower-sash'),
        (upper, 2, 1, 'west-stair-arched-transom'),
    ):
        first = len(facade.builder.parts)
        build_window(facade, shape, columns, rows, trim=False, label=label)
        # The original helper also adds a projected horizontal sill. On this
        # wall the stone member between upper and lower lights is flush.
        components = facade.builder.parts[first:]
        sills = [part for part in components if part['label'].endswith('/'+label+'-sill')]
        assert len(sills) == 1
        facade.builder.parts[first:] = [part for part in components if part is not sills[0]]
        seat = shape.buffer(.004,join_style=2).difference(shape.buffer(-.081,join_style=2))
        facade.prism(seat,-.35,-.175,'bronze window frame',label+'-perimeter-seat')
    # The stone bridge between the two wall holes is part of the continuous wall.
    facade.box(u, transom, width + .12, .20, .12, .04,
               'carved pale stone', 'west-stair-transom')
    facade.box(u, sill - .13, width + .26, .17, .49, .16,
               'plinth stone', 'west-stair-projected-sill')
    return [lower, upper]


def add_west_stair(facade):
    builder = facade.builder
    builder.palette['pale stone stair treads'] = {
        'color': [.60, .59, .55], 'roughness': .90
    }
    half = facade.length / 2
    foot = .53
    count = 14
    going = .286
    rise = .155
    height = count * rise
    landing_end = foot + count * going + 1.05
    wall_depth = .10
    outer_depth = 1.77

    def station(distance):
        return half - distance

    # A single closed stepped stringer retains true riser faces and a free
    # passage alongside the open railing. The dark recess at the photo edge
    # does not establish the path or location of an interior doorway.
    flight = [(station(foot), 0), (station(foot), rise)]
    for index in range(count):
        end = station(foot + (index + 1) * going)
        top = (index + 1) * rise
        flight.append((end, top))
        if index + 1 < count:
            flight.append((end, top + rise))
    flight += [(station(landing_end), height), (station(landing_end), 0)]
    facade.prism(Polygon(flight), wall_depth, outer_depth, 'plinth stone',
                 'west-stair-closed-flight')
    surface = 'pale stone stair treads'
    for index in range(count):
        start = station(foot + (index + .5) * going)
        facade.box(station(foot + index * going) + .003, (index + .5) * rise,
                   .006, rise-.002, outer_depth-wall_depth-.004,
                   (outer_depth+wall_depth)/2, surface, 'west-stair-riser')
        facade.box(start, (index + 1) * rise + .009, going - .008, .018,
                   outer_depth - wall_depth, (outer_depth + wall_depth) / 2,
                   surface, 'west-stair-tread')
    run_end = foot + count * going
    facade.box((station(run_end)+station(landing_end))/2, height + .009,
               landing_end-run_end-.008, .018, outer_depth-wall_depth,
               (outer_depth+wall_depth)/2,surface,'west-stair-landing')
    plane = outer_depth - .07
    post_distances = [foot + going*.5, foot+going*5.5, foot+going*10.5,
                      foot+going*(count-.5), landing_end-.09]
    heights = [rise, rise*6, rise*11, height, height]
    for distance, floor in zip(post_distances, heights):
        u = station(distance)
        facade.box(u,floor+.49,.072,.98,.072,plane,'wrought iron','west-stair-iron-post')
        facade.box(u,floor+.985,.09,.045,.09,plane,'wrought iron','west-stair-post-cap')
    for (a,b),(za,zb) in zip(zip(post_distances,post_distances[1:]),zip(heights,heights[1:])):
        for level,radius in ((.91,.035),(.22,.015)):
            facade.line((station(a),za+level,plane),(station(b),zb+level,plane),
                        radius,'wrought iron',8,'west-stair-iron-rail')
        for division in range(1,5):
            t=division/5
            u=station(a+(b-a)*t);z=za+(zb-za)*t
            facade.line((u,z+.23,plane),(u,z+.90,plane),.013,'wrought iron',
                        8,'west-stair-rail-bar')
        # Two linked open curls occupy each interval between the upright bars.
        # The ironwork is clear in silhouette. The radii describe that rhythm,
        # without assigning a historic maker or tracing a particular casting.
        span = (b-a)/4
        for interval in range(4):
            middle = a + (interval+.5)*span
            for sign in (-1, 1):
                coordinates = []
                for step in range(17):
                    t = step/16
                    angle = sign*(pi*.70+t*pi*2.12)
                    scale = .20 + .80*t
                    distance = middle + (span*.36)*scale*cos(angle)
                    local = (distance-a)/(b-a)
                    z = za + (zb-za)*local + .55 + sign*.15 + .135*scale*sin(angle)
                    coordinates.append(facade.point(station(distance),z,plane+.021))
                builder.tube(coordinates,.014,'wrought iron',6,
                             facade.label+'/west-stair-open-iron-scroll')

"""The two open arches and the balcony directly above them in villa 2's lawn photograph."""
import json
from pathlib import Path

import numpy as np
from shapely.geometry import Polygon
from lawn import DATA, front_poly, plane_world

FRONT = -.98
REAR = .65

PIER = 'Cypress loggia shaded render'
BOARD = 'Cypress loggia brown upright'
RIM = 'Cypress balcony dark edge'
SOFFIT = 'Cypress balcony soffit'
PLASTER = 'Cypress recessed warm infill'
GLASS = 'Cypress shaded rear glazing'
DARK = 'Cypress loggia rear timber'

def pigment(rgb, roughness):
    value = np.asarray(rgb, dtype=float) / 255
    return {'color': np.where(value <= .04045, value / 12.92, ((value+.055)/1.055)**2.4).tolist(),
            'roughness': roughness}

PALETTE = {PIER: pigment((150,127,104), .86), BOARD: pigment((89,75,62), .71),
           RIM: pigment((74,63,52), .72), SOFFIT: pigment((117,97,77), .85),
           PLASTER: pigment((182,174,149), .88), GLASS: pigment((68,87,86), .38),
           DARK: pigment((64,54,49), .78)}

def solid(builder, pixels, front_y, thickness, material, name):
    shape = front_poly(pixels, front_y)
    builder.prism(shape, -thickness, 0., lambda x,z,d: (x,front_y-d,z),
                  material, 'Garden loggia/'+name)

def add_loggia(builder, lod):
    survey = json.loads((DATA/'loggia-arch-and-railing-pixels.json').read_bytes())
    arches = [item['trace_left_to_right'] for item in survey['inner_arch_edges']]
    # The jambs end at the last unoccluded part of each pier. The opening below
    # each arch is actual space. The shaded rear features use a different plane.
    left, right = arches
    if lod:
        left = [*left[:-1:2],left[-1]]
        right = [*right[:-1:2],right[-1]]
    arch_face = [(538,310.5),(665,306.2),(665,332),(658.5,333),
                 *reversed(right),(603,377),(596,377),*reversed(left),
                 (545.5,342),(539,344)]
    solid(builder,arch_face,FRONT,.30,PIER,'two shallow arches and three square piers')
    # The horizontal balcony slab terminates at this two-bay study's cut section.
    solid(builder,[(535.8,306),(665.6,301.3),(665.5,306.5),(536,311.2)],
          FRONT-.014, REAR-FRONT+.04, SOFFIT,'balcony floor and soffit')
    solid(builder,[(535.5,305.8),(665.8,301.1),(665.8,303.7),(535.5,308.5)],
          FRONT-.058,.066,RIM,'projecting floor fascia')
    # The upper edge is reconstructed only to the section cut; the vegetation over
    # the continuation to the right does not establish a third opening.
    rail_y = FRONT+.068
    for x in [548,556,564,572,585,594,607.5,614.5,622.5,630.5,644,654,662]:
        y_top = 286.8-(x-539)*.038
        y_foot = 306.3-(x-539)*.036
        width = 2.2 if x in (585,594,622.5) else 1.7
        solid(builder,[(x-width,y_top),(x+width,y_top-.13),(x+width,y_foot-.13),(x-width,y_foot)],
              rail_y,.078,BOARD,'upright at image x '+str(x))
    solid(builder,[(538.5,285.3),(665.4,280.6),(665.4,283.1),(538.5,288.1)],
          FRONT+.024,.145,RIM,'timber handrail')
    # Only areas of the rear wall which appear between the posts, rails and
    # foliage are restated. The two pale infill fields have separate returns.
    for i, field in enumerate([
        [(563.7,255.0),(581.9,253.4),(582.2,304),(563.1,304.5)],
        [(611,254.1),(631.5,252.2),(631.0,302.3),(611,302.9)],
        [(663.3,259.2),(664.8,259.1),(664.8,299.6),(663.3,299.7)]]):
        solid(builder,field,REAR,.105,PLASTER,'recessed pale panel '+str(i+1))
    for i,field in enumerate([
        [(584.7,254.4),(605.3,252.1),(605.1,302.8),(584.8,303.4)],
        [(549,331.1),(593.7,329.9),(593.6,349.5),(549.1,349.8)]]):
        solid(builder,field,REAR+.035,.026,GLASS,'glazing seen behind opening '+str(i+1))
    solid(builder,[(565,256.2),(568.1,256),(579.7,284.3),(577.5,284.7)],
          REAR-.035,.07,DARK,'visible diagonal brace on rear panel')
    for x in [550,569.4,592.5]:
        solid(builder,[(x,332.0),(x+1.1,332),(x+1.1,348.5),(x,348.7)],
              REAR-.005,.034,DARK,'rear lower glazed bar '+str(x))
    solid(builder,[(548,330.4),(594.5,329),(594.5,330.6),(548,332)],
          REAR-.017,.072,DARK,'rear lower transom')
    solid(builder,[(607,330.1),(654.5,328.8),(654.5,330.3),(607,331.6)],
          REAR-.017,.072,DARK,'right rear horizontal in shade')

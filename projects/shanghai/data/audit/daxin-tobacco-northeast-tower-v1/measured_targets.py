from math import cos, radians, sin

# The central upper face has blind brick arches. Its flanks have real recessed sashes.
RADIUS = 3.2813
GLAZING = ['Grey blue courtyard glazing', 'Dark varnished window joinery']
MOULDING = ['Dark red molded brick', 'Burnt orange arch brick', 'Deep kiln flash']


def facet(index, height, offset=0, outward=0):
    angle = radians(225 + 60 * index)
    radius = RADIUS * cos(radians(30)) + outward
    return (radius*cos(angle)-offset*sin(angle), radius*sin(angle)+offset*cos(angle), height)


TARGETS = [
    ('Tower left upper arched window', facet(0, 13.40), (.94, .85, 1.11), GLAZING),
    ('Tower right upper arched window', facet(2, 13.41), (.80, .88, 1.14), GLAZING),
    ('Central pair of blind brick arches', facet(1, 14.36, -.54), (.9, .34, .67), MOULDING),
    ('Central middle sash', facet(1, 7.24), (.86, .32, 1.20), GLAZING),
    ('Central lower sash and grille', facet(1, 2.42), (.66, .38, .86), GLAZING + ['Cast iron and rainwater fittings']),
    ('Flat-topped grey coping', facet(1, 16.59, .03, .08), (1.0, .43, .67), ['Weathered coping stone']),
    ('First short-wing arch sash', (4.94, -1.77, 7.39), (.97, .29, 1.05), GLAZING),
    ('Second short-wing arch sash', (8.37, -1.77, 7.39), (.91, .29, 1.05), GLAZING),
    ('First radial brick arch', (4.94, -1.88, 9.01), (.91, .25, .43), MOULDING),
    ('Second radial brick arch', (8.37, -1.88, 9.01), (.91, .25, .43), MOULDING),
    ('Short-wing parapet coping', (6.93, -1.85, 11.17), (1.02, .31, .32), ['Weathered coping stone']),
    ('Courtyard equipment casing by second window', (8.54, -2.04, 5.22), (.61, .36, .47), ['Stone-grey equipment case'])
]

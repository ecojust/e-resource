"""Entrance lintel and transverse ceiling return in the refurbished passage."""
from gate_passage import material, rings

INTRADOS = 'Entry beam / exposed grey plaster'
RETURN = 'Entry beam / recessed plaster'
BOARD = 'Entry beam / blue-grey inner face'
PALETTE = {INTRADOS: material((172, 172, 168)),
           RETURN: material((126, 126, 123)),
           BOARD: material((146, 154, 153))}


def add_soffit(b, lod=False, layout=None):
    """Fit the street intrados, ceiling closure and inward-facing downstand."""
    if layout is None:
        import json
        from pathlib import Path
        layout = json.loads(Path(__file__).with_name('gatehouse-layout.json').read_bytes())
    if str(layout.get('period', '2022')).startswith('2018'):
        return
    port = layout['portal']
    spec = layout.get('passage', {})
    floor = spec.get('floor_z', 0.)
    pitch = spec.get('bay_pitch', 1.55)
    ceiling = floor + spec.get('soffit_z', 2.46 * pitch)
    head = floor + port['head']
    midpoint = (port['left'] + port['right']) / 2
    half_width = spec.get('inner_clear_width', 1.55 * 4.55 / 1.77198221136) / 2
    street = layout.get('front_y', {}).get('tower', 0.)
    casing = street + spec.get('decorated_start_y', .32)
    front = street - .127
    back = casing + .52
    curtain = casing + .37
    drop = floor + 3.07
    x0, x1 = port['left'] - .018, port['right'] + .018
    inner_l, inner_r = midpoint - half_width - .022, midpoint + half_width + .022

    def section(y, left, right, base, top):
        return [(left,y,base),(right,y,base),(right,y,top),(left,y,top)]

    # The grey strip changes width with the receding edge at the east pier.
    # Its visible face is underneath the red pediment. The buried backing
    # thickness and the construction within the closed ceiling are estimates.
    rings(b, [section(front, x0, x1, head - .005, head + .018),
              section(street + .012, x0, x1, head - .005, head + .080),
              section(casing, x0, x1, head - .005, head + .080)],
          INTRADOS, 'South entrance | street lintel soffit')
    # Close the spandrels immediately above both sloping jamb returns.
    # Their lower edges follow the existing entrance splays, not the floor.
    for side, edge, lining, sign in (('west', port['left'], inner_l + .022, -1),
                                     ('east', port['right'], inner_r - .022, 1)):
        def cheek(y, face_x, low):
            outer = face_x + sign * .104
            return section(y, min(face_x, outer), max(face_x, outer), low, head + .050)
        rings(b, [cheek(street + .11, edge, head - .019),
                  cheek(casing, lining, ceiling - .016)],
              RETURN, 'South entrance | ' + side + ' upper jamb return')
    rings(b, [section(casing, x0, x1, ceiling - .012, head + .080),
              section(casing + .095, inner_l, inner_r, ceiling - .012, head + .080)],
          RETURN, 'South entrance | recessed ceiling closure')
    # The documented ceiling surface already fills the lower 120 mm behind
    # the entrance. The backing seats into that panel by 1 mm.
    rings(b, [section(casing + .095, inner_l, inner_r, ceiling + .119, head + .080),
              section(back, inner_l, inner_r, ceiling + .119, head + .080)],
          RETURN, 'South entrance | concealed lintel backing')
    rings(b, [section(curtain, inner_l, inner_r, drop, ceiling + .006),
              section(back, inner_l, inner_r, drop, ceiling + .006)],
          BOARD, 'South entrance | inward transverse downstand')

"""Local metres from the northwestern end: X to the street, Y towards the bridge, Z up."""
WIDTH = 18.7
LENGTH = 56.5

def point(face, along, inward, height):
    """Along grows to the right while looking squarely at the named wall."""
    if face == 'northwest': return [along, inward, height]
    if face == 'southeast': return [WIDTH-along, LENGTH-inward, height]
    if face == 'canal': return [inward,LENGTH-along,height]
    if face == 'street': return [WIDTH-inward,along,height]
    raise ValueError(face)

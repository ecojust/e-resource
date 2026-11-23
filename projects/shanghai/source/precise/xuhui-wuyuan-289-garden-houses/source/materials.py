"""Original finishes for the lane-289 maisonettes."""
from pathlib import Path
BASE=Path(__file__).resolve().parent
BRICK='Maresca | red facing brick'
CREAM='Maresca | pale lime plaster'
TILE='Maresca | red brown roof tile'
OAK='Maresca | tarred timber'
BARGE='Maresca | light weathered verge'
SASH='Maresca | dark casement frame'
GLASS='Maresca | grey blue glazing'
GLINT='Maresca | shaded glazing'
DOOR='Maresca | jointed wood door'
STEP='Maresca | worn brick stair tread'
SILL='Maresca | red sill and coping'
IRON='Maresca | blackened iron'
LEAD='Maresca | gutter and flashing'
DARK='Maresca | passage shadow'
BOARD='Maresca | green enamel'
LETTER='Maresca | enamel lettering'
PAVE='Maresca | lane paving'
GROUND='Maresca | planted ground'
def rgb(values,rough=.87):
    return {'color':[((v/255+.055)/1.055)**2.4 if v>10.315 else v/3294.6 for v in values], 'roughness':rough}
def tiled(name):
    return {'texture':str(BASE/name),'color':[1,1,1],'roughness':.91}
PALETTE={BRICK:tiled('red-facing-brick.png'),CREAM:tiled('lime-plaster.png'),TILE:tiled('clay-roof.png'),
 OAK:rgb((52,43,35)),BARGE:rgb((151,142,123)),SASH:rgb((59,57,46),.54),GLASS:rgb((110,125,123),.34),
 GLINT:rgb((84,97,93),.39),DOOR:rgb((89,66,47)),STEP:rgb((153,105,82)),SILL:rgb((146,78,63)),
 IRON:rgb((60,59,52),.58),LEAD:rgb((127,126,116),.65),DARK:rgb((58,54,44)),BOARD:rgb((42,88,69),.48),
 LETTER:rgb((226,224,199)),PAVE:rgb((135,132,120)),GROUND:rgb((133,133,102))}

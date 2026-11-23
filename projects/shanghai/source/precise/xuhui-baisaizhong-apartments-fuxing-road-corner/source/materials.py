from pathlib import Path
HERE=Path(__file__).resolve().parent
STUCCO='Boissezon | ivory mineral render'
PALE='Boissezon | warm limestone grey'
BASE='Boissezon | weathered granite toe'
BAND='Boissezon | stone-grey cement'
ROOF='Boissezon | red pressed clay tile'
RIDGE='Boissezon | clay ridge cap'
TERRAZZO='Boissezon | fine aggregate terrazzo'
IRON='Boissezon | black iron'
WOOD='Boissezon | dark polished timber'
GREEN='Boissezon | deep green stair dado'
WHITE='Boissezon | limewashed stairs'
GLASS='Boissezon | blue grey glass'
FRAME='Boissezon | dark green steel'
DARK='Boissezon | interior shadow'
ZINC='Boissezon | aged zinc'
def rgb(rgb,rough=.88):
    return {'color':[((a/255+.055)/1.055)**2.4 if a>10.315 else a/(255*12.92) for a in rgb],'roughness':rough}
def texture(name):
    return {'texture':str(HERE/name),'color':[1,1,1],'roughness':.93}
PALETTE={STUCCO:texture('original-stucco.png'),ROOF:texture('aged-red-roof.png'),TERRAZZO:texture('stair-terrazzo.png'),
         PALE:rgb((211,205,189)),BASE:rgb((102,99,91)),BAND:rgb((154,149,135)),RIDGE:rgb((131,85,67)),IRON:rgb((47,48,46),.48),
         WOOD:rgb((81,62,49),.50),GREEN:rgb((50,70,63)),WHITE:rgb((222,219,209)),GLASS:rgb((124,143,143),.34),
         FRAME:rgb((59,70,65),.58),DARK:rgb((54,57,52)),ZINC:rgb((129,131,123),.65)}

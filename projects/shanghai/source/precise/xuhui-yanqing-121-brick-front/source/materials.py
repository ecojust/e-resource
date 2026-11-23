from brick_finishes import PALETTE as BRICKS
from western_bay import finish
WHITE='121 front | pale painted joinery'
BROWN='121 front | brown timber'
CREAM='121 front | cream lime render'
PALE='121 front | grey rendered parapet'
STONE='121 front | grey sill stone'
DARK='121 front | deep shade'
GLASS='121 front | smoky glass'
GREEN='121 front | dark green wood'
PALETTE={**BRICKS,**{k:finish(c,r) for k,c,r in [(WHITE,(203,209,205),.79),(BROWN,(100,63,52),.84),(CREAM,(192,181,153),.88),(PALE,(160,158,147),.91),(STONE,(102,102,95),.9),(DARK,(48,43,38),.92),(GLASS,(58,68,69),.31),(GREEN,(37,67,51),.78)]}}

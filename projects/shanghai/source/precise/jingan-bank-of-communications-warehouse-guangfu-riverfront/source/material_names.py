"""Procedural exterior surfaces embedded in both warehouse deliveries."""
from pathlib import Path
S=Path(__file__).resolve().parent
PLASTER='Guangfu | grey washed aggregate'
TEXTURES={PLASTER:S/'guangfu-washed-aggregate.jpg',
          'River entrance | grey washed aggregate':S/'guangfu-washed-aggregate.jpg',
          'Guanger terrace | jointed stone paving':S/'roof-terrace-paving.png'}
for name in ['Guanger | blue grey window glass','Guanger | pale reflective window glass','Guanger | lower shop glass']:
    TEXTURES[name]=S/'warehouse-window-glass.png'

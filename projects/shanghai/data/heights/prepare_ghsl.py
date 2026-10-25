"""Rebuild Shanghai GHSL from the official eastern and western source tiles.

This entry point delegates to alternatives/extend_ghsl_west.py. Run --help for
portable --east, --west, --boundaries, --output, and optional --previous inputs.
Default output is under rebuilt/, leaving the locked release raster intact.
"""
from alternatives.extend_ghsl_west import main

if __name__ == '__main__':
    main()

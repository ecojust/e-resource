#!/usr/bin/env python3
"""Carry both meshopt geometry and its exact FLOAT32 fallback in one GLB."""
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import os
import struct
import subprocess
import sys

PROJECT = Path(__file__).resolve().parents[4]
DECODER = PROJECT / 'vendor/meshopt_decoder.module.js'
UNPACK = PROJECT / 'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'

def chunks(path):
    blob = path.read_bytes()
    magic, version, length, text_size, chunk_type = struct.unpack_from('<5I', blob)
    assert (magic, version, length, chunk_type) == (0x46546c67, 2, len(blob), 0x4e4f534a)
    body_length, bin_type = struct.unpack_from('<2I', blob, 20 + text_size)
    start = 28 + text_size
    assert bin_type == 0x004e4942 and start + body_length == len(blob)
    return json.loads(blob[20:20 + text_size]), blob[start:]

def carry_fallback(output):
    compressed, compressed_data = chunks(output)
    with TemporaryDirectory(dir=output.parent) as scratch:
        unpacked = Path(scratch) / 'fallback.glb'
        subprocess.run(['node', UNPACK, output, unpacked, DECODER], check=True,
                       stdout=subprocess.DEVNULL)
        decoded, fallback_data = chunks(unpacked)
    assert len(compressed['bufferViews']) == len(decoded['bufferViews'])
    assert any('EXT_meshopt_compression' in v.get('extensions', {}) for v in compressed['bufferViews'])
    offset = len(compressed_data)
    assert offset % 4 == 0
    for source, fallback in zip(compressed['bufferViews'], decoded['bufferViews'], strict=True):
        assert source['byteLength'] == fallback['byteLength'] and fallback['buffer'] == 0
        source['byteOffset'] = offset + fallback.get('byteOffset', 0)
        source['buffer'] = 0
        ext = source.get('extensions', {}).get('EXT_meshopt_compression')
        if ext:
            assert ext['buffer'] == 0 and ext.get('byteOffset', 0) + ext['byteLength'] <= offset
    binary = compressed_data + fallback_data
    compressed['buffers'] = [{'byteLength': len(binary)}]
    required = [e for e in compressed.get('extensionsRequired', []) if e != 'EXT_meshopt_compression']
    if required:
        compressed['extensionsRequired'] = required
    else:
        compressed.pop('extensionsRequired', None)
    text = json.dumps(compressed, ensure_ascii=False, separators=(',', ':')).encode()
    text += b' ' * (-len(text) % 4)
    header = struct.pack('<5I', 0x46546c67, 2, 28 + len(text) + len(binary), len(text), 0x4e4f534a)
    output.write_bytes(header + text + struct.pack('<2I', len(binary), 0x004e4942) + binary)

if __name__ == '__main__':
    args = sys.argv[1:]
    if args in (['-v'], ['--version']):
        raise SystemExit(subprocess.call([os.environ.get('JOFFRE_GLTFPACK', 'gltfpack'), '-v']))
    output = Path(args[args.index('-o') + 1])
    subprocess.run([os.environ.get('JOFFRE_GLTFPACK', 'gltfpack'), *args], check=True)
    carry_fallback(output)

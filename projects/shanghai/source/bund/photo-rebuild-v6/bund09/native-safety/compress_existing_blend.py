#!/usr/bin/env python3
"""Losslessly wrap an existing uncompressed .blend, without invoking Blender.

Use only if a normal Blender save already exists (including an over100MB save).
The new native file decodes byte-for-byte to the unchanged source .blend.
"""
from pathlib import Path
import argparse,hashlib,json,os
import zstandard
from validate_native_storage import validate,sha256_file,DEFAULT_DECODED_LIMIT


def compress(source,target):
    source=source.resolve();target=target.resolve()
    if source==target or target.exists():raise ValueError('Use a new distinct output path')
    if source.stat().st_size>DEFAULT_DECODED_LIMIT:raise ValueError('Source exceeds512MiB decoded limit')
    with source.open('rb') as f:
        if not f.read(12).startswith(b'BLENDER'):raise ValueError('Input must be an uncompressed Blender file')
    source_sha=sha256_file(source);target.parent.mkdir(parents=True,exist_ok=True)
    temporary=target.with_name(target.name+'.partial')
    if temporary.exists():raise ValueError('Partial output already exists')
    try:
        c=zstandard.ZstdCompressor(level=6,write_checksum=True,write_content_size=True)
        with source.open('rb') as inp,temporary.open('xb') as out:
            c.copy_stream(inp,out,size=source.stat().st_size)
        report=validate(temporary)
        if report['decoded_sha256']!=source_sha or report['decoded_bytes']!=source.stat().st_size:raise ValueError('Compressed native does not decode to exact source bytes')
        if sha256_file(source)!=source_sha:raise ValueError('Source changed during compression')
        os.replace(temporary,target)
        report.update({'file':str(target),'source_uncompressed_file':str(source),'source_uncompressed_bytes':source.stat().st_size,'source_uncompressed_sha256':source_sha,'source_uncompressed_bytes_unchanged':True,'decoded_bytes_identical_to_uncompressed_native':True,'compression_only_no_geometry_or_photo_change':True,'requires_parent_blender_reopen':True})
        return report
    except BaseException:
        temporary.unlink(missing_ok=True);raise


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--input',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--report',type=Path,required=True);a=ap.parse_args()
    r=compress(a.input,a.output);a.report.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))

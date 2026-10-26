#!/usr/bin/env python3
"""Read-only bounded validation of plain/gzip/zstd .blend storage and BHeads.

This is structural file validation, not a Blender scene/geometry validation.
Decoded bytes are streamed and hashed, never materialized as a second file.
"""
from pathlib import Path
from contextlib import ExitStack
import argparse,gzip,hashlib,json,struct

LIMIT=100_000_000
DEFAULT_DECODED_LIMIT=512*1024*1024
DEFAULT_WINDOW_LIMIT=128*1024*1024


def sha256_file(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def validate(path,max_decoded=DEFAULT_DECODED_LIMIT,max_window=DEFAULT_WINDOW_LIMIT):
    path=Path(path).resolve();size=path.stat().st_size
    if not 0<size<LIMIT:raise ValueError('Stored .blend must be strictly smaller than100,000,000 bytes')
    if max_decoded<32 or max_window<1024:raise ValueError('Invalid safety limits')
    original_sha=sha256_file(path);decoded_sha=hashlib.sha256();total=0
    with ExitStack() as stack:
        raw=stack.enter_context(path.open('rb'));signature=raw.read(4);raw.seek(0)
        if signature.startswith(b'\x1f\x8b'):
            stream=stack.enter_context(gzip.GzipFile(fileobj=raw,mode='rb'));compression='gzip'
        elif signature==b'\x28\xb5\x2f\xfd':
            import zstandard
            # zstandard0.25's installed C/CFFI backend forwards this value to
            # ZSTD_DCtx_setMaxWindowSize in bytes. The fixture test probes the
            # bound instead of relying on stale KiB wording in its docstring.
            decoder=zstandard.ZstdDecompressor(max_window_size=max_window)
            stream=stack.enter_context(decoder.stream_reader(raw,read_across_frames=True));compression='zstandard'
        else:stream=raw;compression='none'
        def read_exact(n):
            nonlocal total
            if n<0 or total+n>max_decoded:raise ValueError('Decoded-byte safety limit exceeded')
            parts=[];left=n
            while left:
                chunk=stream.read(min(left,1024*1024))
                if not chunk:raise ValueError('Truncated decompressed .blend stream')
                decoded_sha.update(chunk);total+=len(chunk);left-=len(chunk);parts.append(chunk)
            return b''.join(parts)
        header=read_exact(12)
        if header[:7]!=b'BLENDER' or header[7:8] not in (b'-',b'_') or header[8:9] not in (b'v',b'V') or not header[9:12].isdigit():raise ValueError('Invalid decompressed Blender header')
        pointer=8 if header[7:8]==b'-' else 4;endian='<' if header[8:9]==b'v' else '>'
        layout=endian+'4si'+('Q' if pointer==8 else 'I')+'ii';headsize=struct.calcsize(layout)
        blocks=0;dna_seen=False;largest=0;end_seen=False
        while not end_seen:
            code,length,address,sdna,count=struct.unpack(layout,read_exact(headsize));blocks+=1
            if length<0 or count<0 or sdna<0:raise ValueError('Negative Blender block field')
            if total+length>max_decoded:raise ValueError('Declared block exceeds decoded-byte safety limit')
            largest=max(largest,length)
            if code==b'ENDB':
                if length!=0:raise ValueError('ENDB must have no payload')
                end_seen=True;break
            first=True;remaining=length
            while remaining:
                chunk=read_exact(min(remaining,1024*1024));remaining-=len(chunk)
                if code==b'DNA1' and first:
                    if not chunk.startswith(b'SDNA'):raise ValueError('DNA1 does not start with SDNA')
                    dna_seen=True
                first=False
        if not dna_seen:raise ValueError('Missing SDNA block')
        # Forces gzip CRC/end checks and zstd final frame processing. Never drain
        # arbitrarily large untrusted trailing content after the end block.
        if stream.read(1):raise ValueError('Unexpected decoded data after ENDB')
    if sha256_file(path)!=original_sha:raise ValueError('Input changed during read-only validation')
    return {'schema':'bounded-native-storage-v1','passed':True,'file':str(path),'stored_bytes':size,'stored_sha256':original_sha,'compression':compression,'decompressed_header':header.decode('ascii'),'decoded_bytes':total,'decoded_sha256':decoded_sha.hexdigest(),'decoded_byte_limit':max_decoded,'zstd_window_limit_bytes':max_window,'block_count':blocks,'largest_block_bytes':largest,'sdna_seen':dna_seen,'end_block_seen':end_seen,'input_bytes_unchanged':True,'scope':'Full bounded decode, stream integrity, recognizable header and well-sized BHead sequence through SDNA/ENDB. Does not interpret SDNA structures, validate geometry, evaluate images or replace a Blender reopen.'}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--input',type=Path,required=True);ap.add_argument('--report',type=Path);ap.add_argument('--max-decoded-bytes',type=int,default=DEFAULT_DECODED_LIMIT);ap.add_argument('--max-window-bytes',type=int,default=DEFAULT_WINDOW_LIMIT);a=ap.parse_args()
    result=validate(a.input,a.max_decoded_bytes,a.max_window_bytes)
    text=json.dumps(result,indent=2)+'\n'
    if a.report:a.report.write_text(text)
    print(text,end='')

"""Synchronous, serial Popen client for gltfpack_server.mjs.

Drop-in execution alternative to subprocess.run([gltfpack,*args],check=True).
The caller still supplies exactly the same arguments and validates its output.
"""
from pathlib import Path
import json
import os
import selectors
import subprocess
import tempfile
import time


class PackFailure(RuntimeError):
    def __init__(self,response):
        self.response=response
        super().__init__(response.get('error','gltfpack request failed'))


class GltfpackService:
    def __init__(self,library,server=None,node='node',timeout=120):
        self.timeout=timeout;self.buffer=b'';self.sequence=0;self.closed=False
        self.stderr=tempfile.TemporaryFile()
        self.process=subprocess.Popen([node,str(server or Path(__file__).with_name('gltfpack_server.mjs')),str(library)],
            stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=self.stderr,bufsize=0)
        self.selector=selectors.DefaultSelector();self.selector.register(self.process.stdout,selectors.EVENT_READ)
        try:
            self.ready=self._read(timeout)
            if self.ready.get('type')!='ready' or self.ready.get('protocol')!=1:
                raise RuntimeError('Invalid gltfpack service handshake')
        except BaseException:
            self.close();raise

    def _read(self,timeout):
        deadline=time.monotonic()+timeout
        while b'\n' not in self.buffer:
            remaining=deadline-time.monotonic()
            if remaining<=0 or not self.selector.select(remaining):
                raise TimeoutError('Timed out waiting for gltfpack service response')
            chunk=os.read(self.process.stdout.fileno(),65536)
            if not chunk:
                self.stderr.seek(0)
                raise RuntimeError('gltfpack service exited: '+self.stderr.read().decode(errors='replace')[-8000:])
            self.buffer+=chunk
            if len(self.buffer)>10*1024*1024:
                raise RuntimeError('Unexpectedly large gltfpack service response')
        line,self.buffer=self.buffer.split(b'\n',1)
        return json.loads(line)

    def pack(self,args,timeout=None):
        if self.closed:
            raise RuntimeError('gltfpack service is closed')
        self.sequence+=1
        request={'id':self.sequence,'args':[str(a) for a in args]}
        try:
            self.process.stdin.write((json.dumps(request,separators=(',',':'))+'\n').encode())
            self.process.stdin.flush()
            result=self._read(timeout or self.timeout)
            if result.get('id')!=self.sequence:
                raise RuntimeError('gltfpack service response ID mismatch')
        except BaseException:
            self.close();raise
        if not result.get('ok'):
            raise PackFailure(result)
        return result

    def close(self):
        if self.closed:
            return
        self.closed=True
        try:
            self.process.stdin.close()
            self.process.wait(timeout=3)
        except (BrokenPipeError,subprocess.TimeoutExpired):
            self.process.kill();self.process.wait()
        finally:
            self.selector.close();self.process.stdout.close();self.stderr.close()

    def __enter__(self):
        return self

    def __exit__(self,*args):
        self.close()

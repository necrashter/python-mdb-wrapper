# Preprocessing steps: loading files, breakpoints, etc.
import pathlib
from .exceptions import *

PROJECT_NAME = pathlib.Path().absolute().parent.name

if PROJECT_NAME.endswith(".X"):
    ELF_FILE = f"../dist/default/production/{PROJECT_NAME}.production.elf"
    CMF_FILE = f"../dist/default/production/{PROJECT_NAME}.production.cmf"
    ASM_FILE = "../main.s"
else:
    print(f"Parent directory ({PROJECT_NAME}) doesn't end with .X")
    print("You are probably running the script in the wrong directory.")

def load_breakpoints(sfile: str, cmffile: str, bps: list[str]):
    line2bp = {}
    bp2line = {}
    with open(sfile, 'r') as f:
        for n, line in enumerate(f.readlines()):
            for bp in bps:
                if line.startswith(bp + ":"):
                    if bp in bp2line:
                        raise MdbException("Label \"" + bp + "\" was defined multiple times")
                    bp2line[bp] = n + 1
                    line2bp[n + 1] = bp
    bp2addr = {}
    addr2bp = {}
    with open(cmffile, 'r') as f:
        for line in f.readlines():
            # 1FDAA resetVec CODE >67:/home/
            splitted = line.split(None, 1)
            if len(splitted) < 2:
                continue
            addr, info = splitted
            if not info.startswith("resetVec CODE"):
                continue
            n = int(info[info.index('>')+1:info.index(':')])
            if n in line2bp:
                bp = line2bp[n]
                bp2addr[bp] = addr
                addr2bp[addr] = bp
    assert len(bp2addr) == len(bps)
    return bp2addr, addr2bp

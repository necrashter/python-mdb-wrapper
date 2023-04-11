# Preprocessing steps: loading files, breakpoints, etc.
import os
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

def check_files():
    """
    Check if .elf, .cmf, and .s files exist.
    """
    if not os.path.isfile(ASM_FILE):
        # Testing setup is wrong if no ASM file
        raise MdbException("ASM_FILE not found!")
    if not os.path.isfile(ELF_FILE) or not os.path.isfile(CMF_FILE):
        # This must be because compile failed
        raise TestFailed("Compile failed!")

def load_breakpoints(sfile: str, cmffile: str, bps: list):
    line2bp = {}
    bp2line = {}
    with open(sfile, 'r') as f:
        for n, line in enumerate(f.readlines()):
            for bp in bps:
                if line.startswith(bp + ":"):
                    if bp in bp2line:
                        raise TestFailed("Label " + bp + " was defined multiple times")
                    bp2line[bp] = n + 1
                    line2bp[n + 1] = bp
    undefined_labels = [label for label in bps if label not in bp2line]
    if undefined_labels:
        raise TestFailed("Following labels were undefined: " + ", ".join(undefined_labels))
    bp2addr = {}
    addr2bp = {}
    with open(cmffile, 'r') as f:
        lines = f.readlines()
        line_tab_i = lines.index("%LINETAB\n")
        sym_tab_i = lines.index("%SYMTAB\n")
        lines = [line for line in lines[line_tab_i+2:sym_tab_i] if not line.startswith("#")]
        for line in lines:
            # 1FDAA resetVec CODE >67:/home/
            # 34 CODE ABS >93:/home/
            splitted = line.split(None, 1)
            if len(splitted) < 2:
                continue
            addr, info = splitted
            try:
                n = int(info[info.index('>')+1:info.index(':')])
            except ValueError:
                continue
            if n in line2bp:
                bp = line2bp[n]
                bp2addr[bp] = addr
                addr2bp[addr] = bp
    return bp2addr, addr2bp

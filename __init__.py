import subprocess

class MdbException(Exception):
    pass

def load_breakpoints(sfile: str, cmffile: str, bps: list):
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

def get_breakpoint(output):
    for line in output:
        if line.startswith("\taddress:"):
            return line[11:-1].upper()
    return None

class Mdb:
    """
    Python Wrapper around MDB, Microchip debugger.
    """

    def __init__(self):
        print("Initializing MDB Python Wrapper")
        self.p = subprocess.Popen(
                "mdb", stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        while True:
            line = self.p.stderr.readline().decode()
            if line.startswith("WARNING: Unable to create a system terminal, creating a dumb terminal"):
                break
        print("MDB Python Wrapper is ready")
        # Output of last command
        self.last = []
        self.running = False

    def exec(self, command):
        """
        Execute a given command, return output.
        """
        if (exitcode := self.p.poll()) != None:
            raise MdbException("MDP process is dead with exit code " + str(exitcode))
        command += "\necho DONE\n"
        self.p.stdin.write(command.encode())
        self.p.stdin.flush()
        lines = []
        while True:
            line = self.p.stdout.readline().decode()
            if line.startswith(">/*DONE"):
                break
            lines.append(line)
        return lines

    def prelude(self, prelude):
        """
        Prelude commands: adjust settings and load a program.
        """
        lines = self.exec(prelude)
        for line in lines:
            if line.startswith("Program succeeded."):
                return
        raise MdbException("Couldn't load program. Output:\n" + "".join(lines))

    def quit(self):
        """
        Send quit command and wait until exit.
        Returns the exit code.
        """
        if (exitcode := self.p.poll()) != None:
            raise MdbException("MDP process is dead with exit code " + str(exitcode))
        # We cannot receive confirmation like other commands
        command = "quit\n"
        self.p.stdin.write(command.encode())
        self.p.stdin.flush()
        return self.p.wait()

    def cont_timeout(self, timeout = 15000):
        """
        Run until a breakpoint is reached or timeout (15 seconds).
        """
        if self.running:
            return self.exec("continue\nwait " + str(timeout))
        else:
            return self.exec("run\nwait " + str(timeout))

    def cont(self, timeout = 15000):
        """
        Run until a breakpoint is reached and raise an exception if timeout (15 seconds).
        Returns the address of breakpoint.
        """
        lines = self.cont_timeout(timeout)
        bp = get_breakpoint(lines)
        if not bp:
            raise MdbException("Timeout is reached while waiting for a breakpoint")
        return bp

    def stopwatch(self):
        """
        Returns stopwatch cycle count.
        """
        for line in self.exec("stopwatch"):
            # Output looks like:
            # ['>Stopwatch cycle count = 4440176 (444.0176 ms)\n']
            if "Stopwatch cycle count" in line:
                return int(line[line.index('=')+2:line.index('(')-1])

    def bp(self, bp):
        """
        BreakPoint.
        """
        return self.exec("break *" + bp)

    def obp(self, bp):
        """
        Only BreakPoint. Clears all breakpoints and enables the given breakpoint.
        """
        return self.exec("delete\nbreak *" + bp)

    def clearbp(self):
        """
        Clear BreakPoints.
        """
        return self.exec("delete")

# Wrapper for MDB
import subprocess
from .exceptions import *

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
        self.p = subprocess.Popen(
                "mdb", stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        while True:
            line = self.p.stderr.readline().decode()
            if line.startswith("WARNING: Unable to create a system terminal, creating a dumb terminal"):
                break
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

    def run_timeout(self, timeout = 15000):
        """
        Run until a breakpoint is reached or timeout (15 seconds).
        """
        if self.running:
            return self.exec("continue\nwait " + str(timeout))
        else:
            return self.exec("run\nwait " + str(timeout))

    def run(self, timeout = 15000):
        """
        Run until a breakpoint is reached and raise an exception if timeout (15 seconds).
        Returns the address of breakpoint.
        """
        lines = self.run_timeout(timeout)
        bp = get_breakpoint(lines)
        if not bp:
            raise TestFailed("Timeout is reached while waiting for a breakpoint")
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

    def breakpoint(self, bp):
        """
        Add a new breakpoint.
        """
        return self.exec("break *" + bp)

    def only_breakpoint(self, bp):
        """
        Clears all breakpoints and enables the given breakpoint.
        """
        return self.exec("delete\nbreak *" + bp)

    def clear_breakpoints(self):
        """
        Clear all Breakpoints.
        """
        return self.exec("delete")

    def watch(self, watchpoint):
        """
        Set watch point.
        Argument must be of form: "address breakonType[:value]"
        address can be a variable name.
        breakonType: W or RW
        """
        return self.exec("watch " + watchpoint)

    def get(self, name):
        """
        Get a variable by name or address.
        """
        out = self.exec("print " + name)
        line = out[0].strip()
        return int(line[line.rindex('=')+1:])

    def reset(self):
        """
        Halt the execution and reset the simulator (including hardware reset).
        Also clears breakpoints.
        """
        return self.exec("halt\ndelete\nreset MCLR")

    def step(self):
        """
        Step program until it reaches a different source line.
        Only enters a function if there is line number information for the function.
        """
        return self.exec("step")

    def next(self):
        """
        Equivalent to the step command but treats subroutine calls as one instruction.
        """
        return self.exec("next")

    def stepi(self, n: int = 1):
        """
        Execute the given number of machine instructions.
        """
        return self.exec("stepi " + str(n))

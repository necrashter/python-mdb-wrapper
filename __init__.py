from .wrapper import Mdb
from .preprocess import *

class MdbTester:
    def __init__(self, prelude: str, breakpoints: list[str]):
        self.prelude = prelude.strip() + "\nprogram " + ELF_FILE
        self.breakpoints = breakpoints
        self.bp2addr, self.addr2bp = None, None
        self.m = None

    def run(self, tests: list):
        self.bp2addr, self.addr2bp = load_breakpoints(ASM_FILE, CMF_FILE, self.breakpoints)
        self.m = Mdb()
        self.m.prelude(self.prelude)
        for test in tests:
            try:
                test(self.m, self.bp2addr, self.addr2bp)
            except TestFailed as e:
                print("Test failed:", test.__name__)
                print(e)
            # TODO: reset
        self.m.quit()


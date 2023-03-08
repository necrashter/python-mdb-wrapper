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
            print("\nRUNNING TEST:", test.__name__)
            if test.__doc__ is not None:
                print("\t" + test.__doc__.strip())
            try:
                test(self.m, self.bp2addr, self.addr2bp)
            except TestFailed as e:
                print("TEST FAILED:", e)
            finally:
                self.m.reset()
        self.m.quit()


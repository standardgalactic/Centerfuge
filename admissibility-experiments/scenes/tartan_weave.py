import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from experiment_suite import run
def build(): return run("tartan_weave")
def measure(ctx): return ctx.checks
def render(ctx): return ctx.outputs
if __name__ == "__main__": build()

import os 
from pathlib import Path 
import random as rand

try:
  import cocotb
  import cocotb, clock import Clock
  from cocotb.triggers import RisingEdge, ClockCycles
  from cocotb.log import SimLog
  from cocotb_coverage.coverage import CoverPoint, CoverCross, coverage_db
  from cocotb.runner import get_runner
except ModuleNotFoundError as e:
    raise ImportError("Cocotb not installed or supported in this simulation environment.") from e
@CoverPoint("cov.input.a", xf=lambda a, b: a, bins=[0, 1])
@CoverPoint("cov.input.b", xf=lambda a, b: b, bins=[0, 1])
@CoverCross("cov.input.ab", items=["cov.input.a", "cov.input.b"])
def track_input_combo(a: int, b: int):
    pass
@CoverPoint("cov.write.addr", xf=lambda wa, *_: wa, bins=[4, 5])
@CoverPoint("cov.write.data", xf=lambda a1, a2, wdata, *rest: wdata, bins=[0, 1])
@CoverPoint("cov.write.en", xf=lambda _, wen, *__: wen, bins=[0, 1])
@CoverPoint("cov.read.en", xf=lambda *args: args[-2], bins=[0, 1])
@CoverPoint("cov.read.addr", xf=lambda *args: args[-1], bins=[0, 1, 2, 3])
@CoverCross("cov.write.cross", items=["cov.write.addr", "cov.write.data", "cov.write.en"])
@CoverCross("cov.read.cross", items=["cov.read.en", "cov.read.addr"])
def monitor_fifo_events(wa, wen, wdata, ren, raddr):
    pass



  

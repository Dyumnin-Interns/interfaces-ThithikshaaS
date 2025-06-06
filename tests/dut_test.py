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


class FIFOTest:
    def __init__(self, dut):
        self.dut = dut
        self.logger = SimLog("fifo_tb")

    async def launch_clock(self, ns=2):
        cocotb.start_soon(Clock(self.dut.CLK, ns, units="ns").start())

    async def do_reset(self):
        self.dut.RST_N.value = 1
        await ClockCycles(self.dut.CLK, 4)
        self.dut.RST_N.value = 0
        await ClockCycles(self.dut.CLK, 4)
        self.dut.RST_N.value = 1
        await RisingEdge(self.dut.CLK)
        self.logger.info("Reset done")

    async def write_data(self, addr: int, val: int):
        await RisingEdge(self.dut.CLK)
        while not self.dut.write_rdy.value.integer:
            await RisingEdge(self.dut.CLK)
        self.dut.write_address.value = addr
        self.dut.write_data.value = val
        self.dut.write_en.value = 1
        await RisingEdge(self.dut.CLK)
        self.dut.write_en.value = 0

    async def read_data(self, addr: int) -> int:
        await RisingEdge(self.dut.CLK)
        while not self.dut.read_rdy.value.integer:
            await RisingEdge(self.dut.CLK)
        self.dut.read_address.value = addr
        self.dut.read_en.value = 1
        await RisingEdge(self.dut.CLK)
        self.dut.read_en.value = 0
        await RisingEdge(self.dut.CLK)
        return self.dut.read_data.value.integer





  

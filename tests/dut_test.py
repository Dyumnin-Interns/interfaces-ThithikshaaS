import asyncio
import os 
import sys    
from pathlib import Path 
import cocotb 
from cocotb import runner 
from cocotb.runner import get_runner 
from cocotb.triggers import Timer, ClockCycles, RisingEdge, Event , ReadOnly 
from cocotb.clock import Clock  
from cocotb.log import logging, SimLog 
from cocotb_bus.drivers import BusDriver 
from cocotb_bus.monitors import BusMonitor 
from cocotb_bus.scoreboard import Scoreboard 
from cocotb_coverage.coverage import CoverPoint, CoverCross, coverage_db  
import random as rand 
import constraint  

@CoverPoint("top.x",             
            xf = lambda x,y:x,             
            bins=[0,1]) 
@CoverPoint("top.z",             
            xf = lambda x,y:y,             
            bins=[0,1]) 
@CoverCross("top.cross.xz",             
            items=['top.x','top.z']) 
def basic_sample(x,y):     
    pass   

@CoverPoint("top.wr.wr_addr",             
            xf = lambda wr_addr,wr_en, wr_data, rd_en, rd_addr: wr_addr,             
            bins=[4,5]) 
@CoverPoint("top.wr.wr_data",             
            xf = lambda wr_addr,wr_en, wr_data, rd_en, rd_addr: wr_data,             
            bins=[0,1]) 
@CoverPoint("top.wr.wr_en",             
            xf = lambda wr_addr,wr_en, wr_data, rd_en, rd_addr: wr_en,             
            bins=[0,1]) 
@CoverPoint("top.rd.rd_addr",             
            xf = lambda wr_addr,wr_en, wr_data, rd_en, rd_addr: rd_addr,             
            bins=[0,1,2,3]) 
@CoverPoint("top.rd.rd_en",             
            xf = lambda wr_addr,wr_en, wr_data, rd_en, rd_addr: rd_en,             
            bins=[0,1]) 
@CoverCross("top.cross.wr",             
            items=['top.wr.wr_addr', 'top.wr.wr_data', 'top.wr.wr_en']              
            ) 
@CoverCross("top.cross.rd",             
            items=["top.rd.rd_en", "top.rd.rd_addr"]) 
def mem_cv(wr_addr, wr_en, wr_data, rd_en, rd_addr):     
    pass      

class wr_Driver(BusDriver):     
    _signals=["CLK", "RST_N", "write_address", "write_data", "write_en", "write_rdy", "read_address", "read_en", "read_rdy", "read_data"]     
    def __init__(self, name, entity):         
        self.name = name         
        self.entity= entity         
        self.CLK = entity.CLK      

    async def _driver_send(self, transaction, sync = True):         
        await RisingEdge(self.CLK)         
        if (self.entity.write_rdy.value.integer != 1):             
            await RisingEdge(self.entity.write_rdy)         
        self.entity.write_en.value = 1         
        self.entity.write_address.value = transaction.get('addr')         
        self.entity.write_data.value = transaction.get('val')         
        await RisingEdge(self.CLK)         
        self.entity.write_en.value = 0  

class rd_Driver(BusDriver):      
    _signals=["CLK", "RST_N", "write_address", "write_data", "write_en", "write_rdy", "read_address", "read_en", "read_rdy", "read_data"]     
    def __init__(self, name, entity):         
        self.name = name         
        self.entity= entity         
        self.CLK = entity.CLK      

    async def _driver_send(self, transaction, sync= True):         
        await RisingEdge(self.CLK)         
        if (self.entity.read_rdy.value.integer != 1):             
            await RisingEdge(self.entity.read_rdy)         
        self.entity.read_en.value = 1         
        self.entity.read_address.value = transaction.get('addr')         
        await RisingEdge(self.CLK)         
        self.entity.read_en.value = 0  

class TestBench:     
    def __init__(self, name, entity, log):         
        self.log = log          
        self.name = name          
        self.entity = entity         
        self.CLK=self.entity.CLK          
        self.x_ls = []         
        self.z_ls = []         
        self.result_ls = []         
        self.stats=[]         
        self.wr_event= Event()         
        self.rd_event = Event()         
        self.address_ref={'A_status':0,'B_status':1,'Y_status':2, 'Y_output':3 , 'A_data':4, 'B_data':5}         
        self.wr_drv = wr_Driver("Write fifo", entity)         
        self.rd_drv = rd_Driver("Read fifo", entity)          

    async def dut_reset(self):         
        await RisingEdge(self.CLK)         
        self.entity.write_address.value=0         
        self.entity.write_data.value=0         
        self.entity.write_en.value=0         
        self.entity.read_en.value=0         
        self.entity.read_data.value=0         
        self.entity.read_address.value=0         
        # apply negative reset          
        self.entity.RST_N.value=1         
        await ClockCycles(self.CLK, 4)         
        self.entity.RST_N.value=0         
        await ClockCycles(self.CLK, 4)         
        self.entity.RST_N.value=1         
        await RisingEdge(self.CLK)         
        print("\t\t reset completed")      

    def decode_stat(self,addr, val):         
        if addr ==  3:             
            self.stats.append({'name':'yr','val':val})         
        elif addr == 4:             
            self.stats.append({'name':'aw', 'val':val})         
        elif addr == 5:             
            self.stats.append({'name':'bw', 'val':val})         
        elif addr == 0:             
            self.stats.append({'name':'as', 'val':(f"{'full' if val == 0 else 'empty'}")})         
        elif addr == 1:             
            self.stats.append({'name':'bs', 'val':(f"{'full' if val == 0 else 'empty'}")})         
        elif addr == 2:             
            self.stats.append({'name':'ys', 'val':(f"{'full' if val == 1 else 'empty'}")})       

    def constraint_setup(self):         
        self.prob = constraint.Problem()         
        self.prob.addVariable('write_en',[0,1])         
        self.prob.addVariable('read_en', [0,1])         
        self.prob.addVariable('write_address', [4,5]) # max 5          
        self.prob.addVariable('read_address', [0,1,2,3]) # max 5         
        self.prob.addVariable('write_data', [0,1])         
        self.prob.addVariable('write_rdy', [1])         
        self.prob.addVariable('read_rdy', [1])              
        self.prob.addConstraint(lambda rd_en, wr_en, rd_rdy: rd_en == 1 if wr_en == 0 and rd_rdy == 1 else rd_en == 0, ['read_en', 'write_en', 'read_rdy']) # read when write not active and rd_rdy asserted         
        self.prob.addConstraint(lambda rd_en, wr_en, wr_rdy: wr_en == 1 if rd_en == 0 and wr_rdy == 1 else wr_en == 0, ['read_en', 'write_en', 'write_rdy']) # write when read not active and wr_rdy asserted         
        

    def get_solutions(self):         
        self.constraint_obj = self.constraint_setup()         
        self.solutions = self.prob.getSolutions()      

    def pick_solution(self):         
        return rand.choice(self.solutions) if self.solutions else None    

@cocotb.test() 
async def dut_test(dut):     
    cocotb.start_soon(Clock(dut.CLK, 2, "ns").start())     
    log = SimLog("interface_test")     
    logging.getLogger().setLevel(logging.INFO)      
    
    tb_inst = TestBench(name="tb inst", entity=dut, log=log)          
    await tb_inst.dut_reset()      

    
    await tb_inst.wr_drv._driver_send(transaction={'addr':4,'val':0})     
    await tb_inst.wr_drv._driver_send(transaction={'addr':5,'val':0})     
    basic_sample(0,0)     
    await tb_inst.rd_drv._driver_send({'addr':3,'val':0})     
    log.debug(f"[functional] a:0 b:0 y:{dut.read_data.value.integer}")     
    
    await tb_inst.wr_drv._driver_send(transaction={'addr':4,'val':0})     
    await tb_inst.wr_drv._driver_send(transaction={'addr':5,'val':1})      
    basic_sample(0,1)     
    await tb_inst.rd_drv._driver_send({'addr':3,'val':0})     
    log.debug(f"[functional] a:0 b:1 y:{dut.read_data.value.integer}")     
    
    await tb_inst.wr_drv._driver_send(transaction={'addr':4,'val':1})     
    await tb_inst.wr_drv._driver_send(transaction={'addr':5,'val':0})      
    basic_sample(1,0)     
    await tb_inst.rd_drv._driver_send({'addr':3,'val':0})     
    log.debug(f"[functional] a:1 b:0 y:{dut.read_data.value.integer}")     
    
    await tb_inst.wr_drv._driver_send(transaction={'addr':4,'val':1})     
    await tb_inst.wr_drv._driver_send(transaction={'addr':5,'val':1})      
    basic_sample(1,1)     
    await tb_inst.rd_drv._driver_send({'addr':3,'val':0})     
    log.debug(f"[functional] a:1 b:1 y:{dut.read_data.value.integer}")      

    tb_inst.get_solutions()     
    for i in range(32):         
        solution = tb_inst.pick_solution()         
        mem_cv(solution.get("write_address"), solution.get("write_data"), solution.get("write_en"), solution.get("read_en"), solution.get("read_address"))         
        
        if solution.get('read_en') == 1:             
            await tb_inst.rd_drv._driver_send(transaction={'addr':solution.get('read_address'), 'val':0 })             
            log.debug(f"[{i}][read  operation] address: {solution.get('read_address')} got data: {dut.read_data.value.integer}")             
            tb_inst.decode_stat(solution.get('read_address'), dut.read_data.value.integer)         
        elif solution.get('write_en') == 1:             
            await tb_inst.wr_drv._driver_send(transaction={'addr':solution.get('write_address'), 'val': solution.get('write_data') })             
            log.debug(f"[{i}][write operation] address: {solution.get('write_address')} put data: {solution.get('write_data')}")             
            tb_inst.decode_stat(solution.get('write_address'), solution.get('write_data'))         
        await RisingEdge(dut.CLK)      

    for i in tb_inst.stats:         
        log.debug(f"{i}")      

    coverage_db.report_coverage(log.info,bins=True)     
    log.info(f"Functional Coverage: {coverage_db['top.cross.xz'].cover_percentage:.2f} %")     
    log.info(f"Write Coverage: {coverage_db['top.cross.wr'].cover_percentage:.2f} %")     
    log.info(f"Read Coverage: {coverage_db['top.cross.rd'].cover_percentage:.2f} %")         

def build_and_run():     
    sim = os.getenv("SIM","verilator")     
    project_dir = Path(__file__).resolve().parent.parent     
    project_dir = f"{project_dir}/hdl"     
    hdl_top="dut"     
    verilog_files = [f"{project_dir}/{hdl_top}.v", f"{project_dir}/FIFO1.v",f"{project_dir}/FIFO2.v"]     
    build_options = ["--trace", "--trace-fst"]          
    
    test_runner = get_runner(sim)      
    test_runner.build(         
        hdl_toplevel=hdl_top,         
        verilog_sources=verilog_files,         
        build_args=build_options,         
        waves=True,         
        always=True     
    )      

    test_runner.test(     
        test_module="dut_test",         
        hdl_toplevel=hdl_top,         
        waves=True     
    )  

if __name__ == "__main__":     
    build_and_run()

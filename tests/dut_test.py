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

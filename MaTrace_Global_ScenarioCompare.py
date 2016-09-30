# -*- coding: utf-8 -*-
"""
Created on Thur June 18, 2015
Last modified: February, 2016

@author: pauliuk
"""

"""
# Script MaTrace_Global_ScenarioCompare.py

# Standalone script for cross-comparing scenarios for the global multiregional version of MaTrace model (Nakamura et al. 2014)
# Import required libraries:
#%%
"""

# import os

import logging
import os
import xlrd, xlwt
import numpy as np
import time
import datetime
import scipy.io
import scipy.stats   
import matplotlib.pyplot as plt 
import matplotlib.patches as mpatches   
#import matplotlib.colors as col
import pylab
import shutil 
import uuid

#%%
#import dynamic_stock_model  # If this model is not installed, check https://github.com/stefanpauliuk/dynamic_stock_model for an installation guide.
#################
#     Functions #
#################

def function_logger(file_level, Name_Scenario, Path_Result, console_level): # Set up logger
    # remove all handlers from logger
    logger = logging.getLogger()
    logger.handlers = [] # required if you don't want to exit the shell
    logger.setLevel(logging.DEBUG) #By default, logs all messages

    if console_level != None:
        console_log = logging.StreamHandler() #StreamHandler logs to console
        console_log.setLevel(console_level)
        console_log_format = logging.Formatter('%(message)s') # ('%(asctime)s - %(message)s')
        console_log.setFormatter(console_log_format)
        logger.addHandler(console_log)

    file_log = logging.FileHandler(Path_Result + '\\' + Name_Scenario + '.html', mode='w', encoding=None, delay=False)
    file_log.setLevel(file_level)
    #file_log_format = logging.Formatter('%(asctime)s - %(lineno)d - %(levelname)-8s - %(message)s<br>')
    file_log_format = logging.Formatter('%(message)s<br>')
    file_log.setFormatter(file_log_format)
    logger.addHandler(file_log)

    return logger, console_log, file_log
    
    
def ensure_dir(f): # Checks whether a given directory f exists, and creates it if not
    d = os.path.dirname(f)
    if not os.path.exists(d):
        os.makedirs(d) 
        
def greyfade(color_triple,greyfactor): # returns a color triple (RGB) that is between the original color triple and and equivalent grey value, linear scaling: greyfactor = 0: original, greyfactor = 1: grey
    return (1 - greyfactor) * color_triple + greyfactor * color_triple.sum() / 3

#%%    
#################
#     MAIN      #
#################
"""
Set main path
"""    

# For Stefan:
Project_MainPath = 'C:\\Users\\spauliuk\\FILES\\ARBEIT\\PROJECTS\\MaTrace_Global\\'    
Name_User        = 'Stefan'

# For Yasushi:
#Project_MainPath = ''
#Name_User        = 'Yasushi'

Project_DataPath   = Project_MainPath + 'Data\\'
Project_ResultPath = Project_MainPath + 'Results\\'
    
"""
Read configuration data
"""    
#Read Configuration file and fetch user name and projects
Project_DataFileName = 'MaTrace_Global_Indata.xlsx'
Project_DataFilePath = Project_DataPath + Project_DataFileName 
Project_DataFile_WB  = xlrd.open_workbook(Project_DataFilePath)
Project_Configsheet  = Project_DataFile_WB.sheet_by_name('Scenario_Overview')

Name_Scenario      = Project_Configsheet.cell_value(5,2)
StartTime          = datetime.datetime.now()
TimeString         = str(StartTime.year) + '_' + str(StartTime.month) + '_' + str(StartTime.day) + '__' + str(StartTime.hour) + '_' + str(StartTime.minute) + '_' + str(StartTime.second)
DateString         = str(StartTime.year) + '_' + str(StartTime.month) + '_' + str(StartTime.day)
Path_Result        = Project_ResultPath + '_ScenarioCompare_' + TimeString + '\\'

# Read control and selection parameters into dictionary
ScriptConfig = {'Scenario_Description': Project_Configsheet.cell_value(6,2)}
ScriptConfig['Scenario Name'] = Name_Scenario
for m in range(9,21): # add all defined control parameters to dictionary
    try:
        ScriptConfig[Project_Configsheet.cell_value(m,1)] = np.int(Project_Configsheet.cell_value(m,2))
    except:
        ScriptConfig[Project_Configsheet.cell_value(m,1)] = str(Project_Configsheet.cell_value(m,2))
        
ScriptConfig['Current_UUID'] = str(uuid.uuid4())

# Create scenario folder
ensure_dir(Path_Result)
#Copy script and Config file into that folder
shutil.copy(Project_DataFilePath, Path_Result + Project_DataFileName)
shutil.copy(Project_MainPath + 'Scripts\\MaTrace_Global_ScenarioCompare.py', Path_Result + 'MaTrace_Global_ScenarioCompare.py')
# Initialize logger    
[Mylog,console_log,file_log] = function_logger(logging.DEBUG, Name_Scenario + '_' + TimeString, Path_Result, logging.DEBUG) 

# log header and general information
Mylog.info('<html>\n<head>\n</head>\n<body bgcolor="#ffffff">\n<br>')
Mylog.info('<font "size=+5"><center><b>Script ' + 'MaTrace_Global_ScenarioCompare' + '.py</b></center></font>')
Mylog.info('<font "size=+5"><center><b>Version: 2016-02-18 or later.</b></center></font>')
Mylog.info('<font "size=+4"> <b>Current User: ' + Name_User + '.</b></font><br>')
Mylog.info('<font "size=+4"> <b>Current Path: ' + Project_MainPath + '.</b></font><br>')
Mylog.info('<font "size=+4"> <b>Current Scenario: Cross-comparison of scenarios.</b></font><br>')
Mylog.info(ScriptConfig['Scenario_Description'])
Mylog.info('Unique ID of scenario run: <b>' + ScriptConfig['Current_UUID'] + '</b>')

Time_Start = time.time()
Mylog.info('<font "size=+4"> <b>Start of simulation: ' + time.asctime() + '.</b></font><br>')

#%%
"""
Read model data and define system variables
""" 
Mylog.info('<p><b>Reading model parameters.</b></p>')
Project_DefSheet  = Project_DataFile_WB.sheet_by_name('Definitions')
Def_RegionsNames   = []
Def_RegionsSymbols = []
for m in range (0,25):
    Def_RegionsNames.append(Project_DefSheet.cell_value(m+2,3))
    Def_RegionsSymbols.append(Project_DefSheet.cell_value(m+2,4))

Def_ProductNames      = []
Def_ProductShortNames = []
for m in range (0,10):
    Def_ProductNames.append(Project_DefSheet.cell_value(m+2,5))    
    Def_ProductShortNames.append(Project_DefSheet.cell_value(m+2,6))    
    
Def_RegionsNames_agg = []
for m in range(0,10):
    Def_RegionsNames_agg.append(Project_DefSheet.cell_value(m+2,11))    
    
Def_RegionAgg_Vector = []
for m in range(0,25):
    Def_RegionAgg_Vector.append(Project_DefSheet.cell_value(m+2,12))       
    
Def_Application_Weighting = np.zeros((3,1))    
for m in range(0,3):
    Def_Application_Weighting[m] = Project_DefSheet.cell_value(m+2,13)
    
Project_Datasheet  = Project_DataFile_WB.sheet_by_name('Parameter_MaTrace')

Par_NoOfProducts  = 10
Mylog.info('<p>Number of products: ' + str(Par_NoOfProducts) + '.</p>')
Par_NoOfRegions   = 25
Mylog.info('<p>Number of regions: ' + str(Par_NoOfRegions) + '.</p>')
Par_NoOfYears     = 86 #[2015;2100]
Mylog.info('<p>Number of years: ' + str(Par_NoOfYears) + '.</p>')
Par_NoOfScraps    = 2 #[0: new scrap, 1: old scrap]
Mylog.info('<p>Number of scrap types: ' + str(Par_NoOfScraps) + '.</p>')
Par_NoOfSecMetals = 2 #[0: BOF route, 1: EAF route]
Mylog.info('<p>Number of refinement processes: ' + str(Par_NoOfSecMetals) + '.</p>')

Mylog.info('<br> Define List of scenarios from which to read data. <br>')

ScenList = ['US_Car_Base_2016_4_4__15_32_52', # 0
            'US_Car_Sensitivity_Lifetime_2016_4_4__15_33_14',
            'US_Car_Sensitivity_ProcessRouteEoL_2016_4_4__15_33_37',
            'US_Car_Sensitivity_SectorSplit1_2016_4_4__15_33_54',
            'US_Car_Sensitivity_SectorSplit2_2016_4_4__15_34_9',
            'US_Car_Sensitivity_FabYield_2016_4_4__15_34_22', # 5
            'US_Car_Sensitivity_FabScrapRec_2016_4_4__15_34_35',
            'US_Car_Sensitivity_EoLRecovery_2016_4_4__15_34_49',
            'US_Car_Sensitivity_RemeltingYield_2016_4_4__15_35_29',
            'US_Car_Sensitivity_NoTrade_2016_4_4__15_35_51',
            'US_Car_Sensitivity_NoEoLTrade_2016_4_4__15_36_12', # 10
            'US_Car_Sensitivity_NoScrapTrade_2016_4_4__15_36_40', # 11
            'US_Car_Sensitivity_NoMetalTrade_2016_4_4__15_36_52', # 12
            'US_Car_Sensitivity_NoProductTrade_2016_4_4__15_37_8', # 13
            'US_Car_ClosedLoop_2016_4_4__15_37_20', # 14
            'US_Car_ClosedLoop_HighRec_2016_4_4__15_37_33',
            'US_Car_HighRecovery_2016_4_4__15_37_45', # 16
            'US_Car_HighRecovery_Lifetime_2016_4_4__15_37_59',
            'US_Car_ClosedLoop_Lt_2016_4_4__15_38_12',
            'US_Car_ClosedLoop_HighRec_Lt_2016_4_4__15_38_24',
            'US_Car_NoTrade_LowLoss_2016_4_4__16_30_7',
            'US_Car_NoScrapTrade_2016_4_4__15_38_48', # 21
            'US_Car_NoMetalProductTrade_2016_4_4__15_39_1', # 22

            'Japan_Car_Base_2016_4_4__16_31_30', #23
            'Japan_Car_Sensitivity_Lifetime_2016_4_4__16_31_43',
            'Japan_Car_Sensitivity_ProcessRouteEoL_2016_4_4__16_31_56',
            'Japan_Car_Sensitivity_SectorSplit1_2016_4_4__16_32_8',
            'Japan_Car_Sensitivity_SectorSplit2_2016_4_4__16_32_29',
            'Japan_Car_Sensitivity_FabYield_2016_4_4__16_38_35',
            'Japan_Car_Sensitivity_FabScrapRec_2016_4_4__16_38_48',
            'Japan_Car_Sensitivity_EoLRecovery_2016_4_4__16_39_1',
            'Japan_Car_Sensitivity_RemeltingYield_2016_4_4__16_39_14',
            'Japan_Car_Sensitivity_NoTrade_2016_4_4__16_39_27', # 32
            'Japan_Car_Sensitivity_NoEoLTrade_2016_4_4__16_39_40',
            'Japan_Car_Sensitivity_NoScrapTrade_2016_4_4__16_39_58',
            'Japan_Car_Sensitivity_NoMetalTrade_2016_4_4__16_40_12',
            'Japan_Car_Sensitivity_NoProductTrade_2016_4_4__16_40_25',
            'Japan_Car_ClosedLoop_2016_4_4__16_40_37',
            'Japan_Car_ClosedLoop_HighRec_2016_4_4__16_40_49',
            'Japan_Car_HighRecovery_2016_4_4__16_41_2',
            'Japan_Car_HighRecovery_Lifetime_2016_4_4__16_41_14',
            'Japan_Car_ClosedLoop_Lt_2016_4_4__16_41_27',
            'Japan_Car_ClosedLoop_HighRec_Lt_2016_4_4__16_41_40', # 42
            'Japan_Car_NoTrade_LowLoss_2016_4_4__16_41_59',
            'Japan_Car_NoScrapTrade_2016_4_4__16_42_12',
            'Japan_Car_NoMetalProductTrade_2016_4_4__16_42_50', # 45

            'Germany_Car_Base_2016_4_4__16_44_11', # 46
            'Germany_Car_Sensitivity_Lifetime_2016_4_4__16_44_23',
            'Germany_Car_Sensitivity_ProcessRouteEoL_2016_4_4__16_44_36',
            'Germany_Car_Sensitivity_SectorSplit1_2016_4_4__16_44_50',
            'Germany_Car_Sensitivity_SectorSplit2_2016_4_4__16_45_3',
            'Germany_Car_Sensitivity_FabYield_2016_4_4__16_45_15',
            'Germany_Car_Sensitivity_FabScrapRec_2016_4_4__16_45_28',
            'Germany_Car_Sensitivity_EoLRecovery_2016_4_4__16_45_41',
            'Germany_Car_Sensitivity_RemeltingYield_2016_4_4__16_45_57',
            'Germany_Car_Sensitivity_NoTrade_2016_4_4__16_46_15',
            'Germany_Car_Sensitivity_NoEoLTrade_2016_4_4__16_46_32',
            'Germany_Car_Sensitivity_NoScrapTrade_2016_4_4__16_46_50',
            'Germany_Car_Sensitivity_NoMetalTrade_2016_4_4__16_47_5',
            'Germany_Car_Sensitivity_NoProductTrade_2016_4_4__16_47_18', # 59
            'Germany_Car_ClosedLoop_2016_4_4__16_47_32', #60
            'Germany_Car_ClosedLoop_HighRec_2016_4_4__16_47_44',
            'Germany_Car_HighRecovery_2016_4_4__16_47_57',
            'Germany_Car_HighRecovery_Lifetime_2016_4_4__16_48_10',
            'Germany_Car_ClosedLoop_Lt_2016_4_4__16_48_26',
            'Germany_Car_ClosedLoop_HighRec_Lt_2016_4_4__16_48_38',
            'Germany_Car_NoTrade_LowLoss_2016_4_4__16_48_51',
            'Germany_Car_NoScrapTrade_2016_4_4__16_49_4',
            'Germany_Car_NoMetalProductTrade_2016_4_4__16_49_16' # 68
            ]

            
ScenList_Names_Plot = ['Baseline', # US
                       'S_lifetime', # US
                       'S_BOF_route', # US
                       'S_SectorSplit_static', # US
                       'S_SectorSplit_dynamic', # US
                       'S_fab_yield', # US
                       'S_yield_loss_recov.', # US
                       'S_EoL_recovery', # US
                       'S_RemeltingYield', # US
                       'S_no_trade', # US
                       'S_no_EoL_trade', # US
                       'S_no_Scrap_trade', # US
                       'S_no_Metal_trade', # US
                       'S_no_Product_trade', # US
                       'ClosedLoop', # US
                       'ClosedLoop_HighRec', # US
                       'HighRecovery', # US
                       'HighRecovery_lifetime', # US
                       'ClosedLoop_lifetime', # US
                       'ClosedLoop_lt_HighRec', # US
                       'NoTrade_LowLoss', # US
                       'No_EoL_Scrap_Trade', # US
                       'No_Metal_Product_Trade', # US

                       'Baseline', # Japan
                       'S_lifetime', # Japan
                       'S_BOF_route', # Japan
                       'S_SectorSplit_static', # Japan
                       'S_SectorSplit_dynamic', # Japan
                       'S_fab_yield', # Japan
                       'S_yield_loss_recov.', # Japan
                       'S_EoL_recovery', # Japan
                       'S_RemeltingYield', # Japan
                       'S_no_trade', # Japan
                       'S_no_EoL_trade', # Japan
                       'S_no_Scrap_trade', # Japan
                       'S_no_Metal_trade', # Japan
                       'S_no_Product_trade', # Japan
                       'ClosedLoop', # Japan
                       'ClosedLoop_HighRec', # Japan
                       'HighRecovery', # Japan
                       'HighRecovery_lifetime', # Japan
                       'ClosedLoop_lifetime', # Japan
                       'ClosedLoop_lt_HighRec', # Japan
                       'NoTrade_LowLoss', # Japan
                       'No_EoL_Scrap_Trade', # Japan
                       'No_Metal_Product_Trade', # Japan
                       
                       'Baseline', # Germany
                       'S_lifetime', # Germany
                       'S_BOF_route', # Germany
                       'S_SectorSplit_static', # Germany
                       'S_SectorSplit_dynamic', # Germany
                       'S_fab_yield', # Germany
                       'S_yield_loss_recov.', # Germany
                       'S_EoL_recovery', # Germany
                       'S_RemeltingYield', # Germany
                       'S_no_trade', # Germany
                       'S_no_EoL_trade', # Germany
                       'S_no_Scrap_trade', # Germany
                       'S_no_Metal_trade', # Germany
                       'S_no_Product_trade', # Germany
                       'ClosedLoop', # Germany
                       'ClosedLoop_HighRec', # Germany
                       'HighRecovery', # Germany
                       'HighRecovery_lifetime', # Germany
                       'ClosedLoop_lifetime', # Germany
                       'ClosedLoop_lt_HighRec', # Germany
                       'NoTrade_LowLoss', # Germany
                       'No_EoL_Scrap_Trade', # Germany
                       'No_Metal_Product_Trade', # Germany
                       ]            
            
Mylog.info(ScenList)

Stock_Product_2015   = np.zeros((14,len(ScenList))) # 0:10: products, 10-13: obs, eol, remelting, manuf. losses
Stock_Product_2050   = np.zeros((14,len(ScenList)))
Stock_Product_2100   = np.zeros((14,len(ScenList)))

Stock_Region_2015_f  = np.zeros((50,len(ScenList))) # first 25: in use, second 25: losses
Stock_Region_2050_f  = np.zeros((50,len(ScenList)))
Stock_Region_2100_f  = np.zeros((50,len(ScenList)))

Circ_2100            = np.zeros((len(ScenList)))

ScenList_Names_Script = []

m = 0
for ThisScen in ScenList:
    Mylog.info('<br> Read results results from  scenario  ' + ThisScen + ' <br>')
    Filestring_Matlab_in      = Project_ResultPath + ThisScen + '\\MaTraceGlobal_' + ThisScen[0:ThisScen.find('__')] + '.mat' 
    S_1_temp  = scipy.io.loadmat(Filestring_Matlab_in)['S_1']
    S_1a_temp = scipy.io.loadmat(Filestring_Matlab_in)['S_1a']
    S_3a_temp = scipy.io.loadmat(Filestring_Matlab_in)['S_3a']
    S_5a_temp = scipy.io.loadmat(Filestring_Matlab_in)['S_5a']
    S_7a_temp = scipy.io.loadmat(Filestring_Matlab_in)['S_7a']
    SC_temp   = scipy.io.loadmat(Filestring_Matlab_in)['ScriptConfig']
    
    Stock_Product_2015[0:Par_NoOfProducts,m]    = S_1_temp[0,:,:].sum(axis =0)
    Stock_Product_2015[Par_NoOfProducts,m]      = S_1a_temp[0,:,:].sum()
    Stock_Product_2015[Par_NoOfProducts +1,m]   = S_3a_temp[0,:,:].sum()
    Stock_Product_2015[Par_NoOfProducts +2,m]   = S_5a_temp[0,:].sum()
    Stock_Product_2015[Par_NoOfProducts +3,m]   = S_7a_temp[0,:].sum()
    
    Stock_Product_2050[0:Par_NoOfProducts,m]    = S_1_temp[36,:,:].sum(axis =0)
    Stock_Product_2050[Par_NoOfProducts,m]      = S_1a_temp[36,:,:].sum()
    Stock_Product_2050[Par_NoOfProducts +1,m]   = S_3a_temp[36,:,:].sum()
    Stock_Product_2050[Par_NoOfProducts +2,m]   = S_5a_temp[36,:].sum()
    Stock_Product_2050[Par_NoOfProducts +3,m]   = S_7a_temp[36,:].sum()

    Stock_Product_2100[0:Par_NoOfProducts,m]    = S_1_temp[-1,:,:].sum(axis =0)
    Stock_Product_2100[Par_NoOfProducts,m]      = S_1a_temp[-1,:,:].sum()
    Stock_Product_2100[Par_NoOfProducts +1,m]   = S_3a_temp[-1,:,:].sum()
    Stock_Product_2100[Par_NoOfProducts +2,m]   = S_5a_temp[-1,:].sum()
    Stock_Product_2100[Par_NoOfProducts +3,m]   = S_7a_temp[-1,:].sum()
    
    Stock_Region_2015_f[0:Par_NoOfRegions,m]  = S_1_temp[0,:,:].sum(axis =1)
    Stock_Region_2015_f[Par_NoOfRegions::,m]  = S_1a_temp[0,:,:].sum(axis =1) + S_3a_temp[0,:,:].sum(axis =1) + S_5a_temp[0,0:Par_NoOfRegions] + S_5a_temp[0,Par_NoOfRegions::] + S_7a_temp[0,0:Par_NoOfRegions] + S_7a_temp[0,Par_NoOfRegions::]
          
    Stock_Region_2050_f[0:Par_NoOfRegions,m]  = S_1_temp[36,:,:].sum(axis =1)
    Stock_Region_2050_f[Par_NoOfRegions::,m]  = S_1a_temp[36,:,:].sum(axis =1) + S_3a_temp[36,:,:].sum(axis =1) + S_5a_temp[36,0:Par_NoOfRegions] + S_5a_temp[36,Par_NoOfRegions::] + S_7a_temp[36,0:Par_NoOfRegions] + S_7a_temp[36,Par_NoOfRegions::]

    Stock_Region_2100_f[0:Par_NoOfRegions,m]  = S_1_temp[-1,:,:].sum(axis =1)
    Stock_Region_2100_f[Par_NoOfRegions::,m]  = S_1a_temp[-1,:,:].sum(axis =1) + S_3a_temp[-1,:,:].sum(axis =1) + S_5a_temp[-1,0:Par_NoOfRegions] + S_5a_temp[-1,Par_NoOfRegions::] + S_7a_temp[-1,0:Par_NoOfRegions] + S_7a_temp[-1,Par_NoOfRegions::]
    
    # Determine circular economy performance index
    for year in range(0,Par_NoOfYears):
        Circ_2100[m] = Circ_2100[m] + (Def_Application_Weighting[0] * S_1_temp[year,:,0:9].sum() + Def_Application_Weighting[1] * S_1_temp[year,:,9].sum() + Def_Application_Weighting[2] * (S_1a_temp[year,:,:].sum() + S_3a_temp[year,:,:].sum() + S_5a_temp[year,:].sum() + S_7a_temp[year,:].sum()))/(Par_NoOfYears -1)
    
    ScenList_Names_Script.append(SC_temp[0][0][3][0])

    m +=1

# aggregate and resort regional split:
Stock_Region_2015_use_loss_a  = np.zeros((20,len(ScenList))) # in use and loss alternating. First: in-use, then loss, the repeat for next region
Stock_Region_2050_use_loss_a  = np.zeros((20,len(ScenList)))
Stock_Region_2100_use_loss_a  = np.zeros((20,len(ScenList)))

for m in range(0,Par_NoOfRegions):
    TargetRegionIndex = Def_RegionAgg_Vector[m]
    Stock_Region_2015_use_loss_a[2*TargetRegionIndex +1,:]    = Stock_Region_2015_use_loss_a[2*TargetRegionIndex +1,:]   + Stock_Region_2015_f[m,:]
    Stock_Region_2015_use_loss_a[2*TargetRegionIndex,:] = Stock_Region_2015_use_loss_a[2*TargetRegionIndex,:] + Stock_Region_2015_f[m + Par_NoOfRegions,:]

    Stock_Region_2050_use_loss_a[2*TargetRegionIndex +1,:]    = Stock_Region_2050_use_loss_a[2*TargetRegionIndex +1,:]   + Stock_Region_2050_f[m,:]
    Stock_Region_2050_use_loss_a[2*TargetRegionIndex,:] = Stock_Region_2050_use_loss_a[2*TargetRegionIndex,:] + Stock_Region_2050_f[m + Par_NoOfRegions,:]

    Stock_Region_2100_use_loss_a[2*TargetRegionIndex +1,:]    = Stock_Region_2100_use_loss_a[2*TargetRegionIndex +1,:]   + Stock_Region_2100_f[m,:]
    Stock_Region_2100_use_loss_a[2*TargetRegionIndex,:] = Stock_Region_2100_use_loss_a[2*TargetRegionIndex,:] + Stock_Region_2100_f[m + Par_NoOfRegions,:]

#%%        
"""
Plot results
""" 
#%% define color maps
MyColorCycle_prod = np.zeros((14,4))
MyColorCycle_prod[0:10,:] = pylab.cm.Paired(np.arange(0,1,0.1)) # select 10 colors from the 'Paired' color map.
MyColorCycle_prod[10,:]   = [0.7,0.7,0.7,1]    
MyColorCycle_prod[11,:]   = [0.5,0.5,0.5,1]
MyColorCycle_prod[12,:]   = [0.3,0.3,0.3,1]
MyColorCycle_prod[13,:]   = [0.2,0.2,0.2,1]

MyColorCycle_10Reg = np.zeros((10,4))  
MyColorCycle_10Reg[0,:]   = [141,180,226,255] 
MyColorCycle_10Reg[1,:]   = [197,217,241,255] 
MyColorCycle_10Reg[2,:]   = [226,107, 10,255] 
MyColorCycle_10Reg[3,:]   = [249,173,111,255] 
MyColorCycle_10Reg[4,:]   = [252,213,180,255] 
MyColorCycle_10Reg[5,:]   = [118,147, 60,255] 
MyColorCycle_10Reg[6,:]   = [166,194,102,255] 
MyColorCycle_10Reg[7,:]   = [216,228,188,255] 
MyColorCycle_10Reg[8,:]   = [177,160,199,255] 
MyColorCycle_10Reg[9,:]   = [125, 95,159,255] 
MyColorCycle_10Reg        = MyColorCycle_10Reg/255

StockLabels = Def_ProductShortNames.copy()
StockLabels.append('Obsolete products')
StockLabels.append('Recovery losses')
StockLabels.append('Remelting losses')
StockLabels.append('Fabrication losses')

# shorten Stocklabels:
StockLabels[1] = 'Machinery, nonelectr.'
StockLabels[4] = 'Communication'
StockLabels[5] = 'Medical & optical'

Mylog.info('<p>Create plots.</p>')

Figurecounter = 1

#%% Plot data for US

ScenSel_2015 = [0]
ScenSel_2050 = [0,1,2,3,4,5,6,7,8,9,10,11,12,13]
ScenSel_2100 = [0,1,2,3,4,5,6,7,8,9,10,11,12,13]
fig_name = 'Steel_Stock_Sensitivity_US.png'

#%% Steel stock by product (top) and region (bottom)
ind = np.arange(0,(len(ScenSel_2015) +len(ScenSel_2050) +len(ScenSel_2100)+ 2)/2,0.5)  
width = 0.4       # the width of the bars
xticks = np.concatenate((np.arange(0.2,len(ScenSel_2015)/2,0.5),np.arange(0.2 + len(ScenSel_2015)/2 + 0.5,0.2 + len(ScenSel_2015)/2 + 0.5 + len(ScenSel_2050)/2,0.5),np.arange(0.2 + len(ScenSel_2015)/2 + 0.5 + len(ScenSel_2050)/2 + 0.5,0.2 + len(ScenSel_2015)/2 + 0.5 + len(ScenSel_2050)/2 + 0.5 + len(ScenSel_2100)/2,0.5)), axis = 0)
xticklabels = []
xticklabels.append(['All scenarios'])#Alternative: xticklabels.append([ScenList_Names_Plot[i] for i in ScenSel_2015])
xticklabels.append([ScenList_Names_Plot[i] for i in ScenSel_2050])
xticklabels.append([ScenList_Names_Plot[i] for i in ScenSel_2100])
xticklabels_flat = [item for sublist in xticklabels for item in sublist]

xticklabels_flat_2 = []
for m in range(0,len(xticklabels_flat)):
    xticklabels_flat_2.append('')

Gen_Linewidth = 0.5

# Start plotting
fig, axs = plt.subplots(2,1,figsize=(12,8))
axs = axs.ravel()
gs = plt.GridSpec(2, 1)
gs.update(hspace=0.2)#, wspace=0.4)

# create x lables for upper axis:
xticklabels_flat_3 = xticklabels_flat_2.copy()
xticklabels_flat_3[len(ScenSel_2015) -1 + len(ScenSel_2050) -0] = 'Circ_2100:'
for m in range(0,len(ScenSel_2100)):
    xticklabels_flat_3[len(ScenSel_2015) -1 + len(ScenSel_2050) +1 +m] = str("%.2f" %Circ_2100[ScenSel_2100[m]])


# plot bars for product split first
axs[0] = plt.subplot(gs[0])#, sharey=True, sharex=True)
axs[0].set_color_cycle(MyColorCycle_prod)
ProxyHandlesList = []   # For legend 
for m in range(0,14):
    p1 = plt.bar(ind[0:len(ScenSel_2015)], Stock_Product_2015[m,ScenSel_2015], width, color=MyColorCycle_prod[m,:], 
    label = StockLabels[m], bottom = Stock_Product_2015[0:m,ScenSel_2015].sum(axis=0), linewidth = Gen_Linewidth)
    ProxyHandlesList.append(plt.Rectangle((0, 0), 1, 1, fc=MyColorCycle_prod[m,:], linewidth = Gen_Linewidth)) # create proxy artist for legend
       
    p1 = plt.bar(ind[len(ScenSel_2015)+1:len(ScenSel_2015)+1 + len(ScenSel_2050)], Stock_Product_2050[m,ScenSel_2050], width, color=MyColorCycle_prod[m,:], 
    bottom = Stock_Product_2050[0:m,ScenSel_2050].sum(axis=0), linewidth = Gen_Linewidth)
   
    p1 = plt.bar(ind[len(ScenSel_2015)+1 + len(ScenSel_2050) +1 ::], Stock_Product_2100[m,ScenSel_2100], width, color=MyColorCycle_prod[m,:], 
    bottom = Stock_Product_2100[0:m,ScenSel_2100].sum(axis=0), linewidth = Gen_Linewidth)

plt_lgd  = plt.legend(reversed(ProxyHandlesList),reversed(StockLabels),shadow = False, prop={'size':8.0},loc='upper left', bbox_to_anchor=(1.02, 1))  

axs[0].set_ylim([     0, 1.10])
axs[0].set_xlim([     -0.1, ind.max() + 0.6])
axs[0].set_ylabel('Total steel in system, %', fontsize =15)
axs[0].set_yticks(np.arange(0,1.01,0.2))
axs[0].set_yticklabels(['0','20','40','60','80','100'], fontsize =15)
axs[0].set_xticks(xticks)
axs[0].set_xticklabels(xticklabels_flat_3, fontsize =8, rotation = 0)
axs[0].text(0.25 * (len(ScenSel_2015)) - 0.25, 1.03, '2015', fontsize=10, fontweight='bold') #alternative fontweight: bold
axs[0].text(0.50 * (len(ScenSel_2015) +1) +0.25 * len(ScenSel_2050) - 0.25, 1.03, '2050', fontsize=10, fontweight='bold') #alternative fontweight: bold
axs[0].text(0.50 * (len(ScenSel_2015) +1 +len(ScenSel_2050) +1)  + 0.25 * len(ScenSel_2100) - 0.25, 1.03, '2100', fontsize=10, fontweight='bold') #alternative fontweight: bold

# plot bars for regional split afterwards
axs[1] = plt.subplot(gs[1])#, sharey=True, sharex=True)
axs[1].set_color_cycle(MyColorCycle_10Reg)
ProxyHandlesList = []   # For legend 
for m in range(0,10*2):
    if m % 2 == 0:
        p1 = plt.bar(ind[0:len(ScenSel_2015)], Stock_Region_2015_use_loss_a[m,ScenSel_2015], width, hatch = '//', color=MyColorCycle_10Reg[m//2,:], 
        label = Def_RegionsNames_agg[m//2], bottom = Stock_Region_2015_use_loss_a[0:m,ScenSel_2015].sum(axis=0), linewidth = 0.0)
        ProxyHandlesList.append(plt.Rectangle((0, 0), 1, 1, fc=MyColorCycle_10Reg[m//2,:])) # create proxy artist for legend
    else:
        p1 = plt.bar(ind[0:len(ScenSel_2015)], Stock_Region_2015_use_loss_a[m,ScenSel_2015], width, color=MyColorCycle_10Reg[(m -1)//2,:], 
        label = Def_RegionsNames_agg[(m -1)//2], bottom = Stock_Region_2015_use_loss_a[0:m,ScenSel_2015].sum(axis=0), linewidth = 0.0)        
        
    if m % 2 == 0:
        p1 = plt.bar(ind[len(ScenSel_2015)+1:len(ScenSel_2015)+1 + len(ScenSel_2050)], Stock_Region_2050_use_loss_a[m,ScenSel_2050], width, hatch = '//', color=MyColorCycle_10Reg[m//2,:], 
        label = Def_RegionsNames_agg[m//2], bottom = Stock_Region_2050_use_loss_a[0:m,ScenSel_2050].sum(axis=0), linewidth = 0.0)
    else:
        p1 = plt.bar(ind[len(ScenSel_2015)+1:len(ScenSel_2015)+1 + len(ScenSel_2050)], Stock_Region_2050_use_loss_a[m,ScenSel_2050], width, color=MyColorCycle_10Reg[(m -1)//2,:], 
        label = Def_RegionsNames_agg[(m -1)//2], bottom = Stock_Region_2050_use_loss_a[0:m,ScenSel_2050].sum(axis=0), linewidth = 0.0)
               
    if m % 2 == 0:
        p1 = plt.bar(ind[len(ScenSel_2015)+1 + len(ScenSel_2050) +1 ::], Stock_Region_2100_use_loss_a[m,ScenSel_2100], width, hatch = '//', color=MyColorCycle_10Reg[m//2,:], 
        label = Def_RegionsNames_agg[m//2], bottom = Stock_Region_2100_use_loss_a[0:m,ScenSel_2100].sum(axis=0), linewidth = 0.0)
    else:
        p1 = plt.bar(ind[len(ScenSel_2015)+1 + len(ScenSel_2050) +1 ::], Stock_Region_2100_use_loss_a[m,ScenSel_2100], width, color=MyColorCycle_10Reg[(m -1)//2,:], 
        label = Def_RegionsNames_agg[(m -1)//2], bottom = Stock_Region_2100_use_loss_a[0:m,ScenSel_2100].sum(axis=0), linewidth = 0.0)
        # plot horizontal bar boundary
        
for xx in xticks:
    plt.plot([xx - 0.2, xx - 0.2], [0,1], color='k', linestyle='-', linewidth = Gen_Linewidth)    
    plt.plot([xx + 0.2, xx + 0.2], [0,1], color='k', linestyle='-', linewidth = Gen_Linewidth)    
    
for xx in range(0,len(ScenSel_2015)):
    for yy in range(0,10):
        plt.plot([xx/2, xx/2 + 0.4], [Stock_Region_2015_use_loss_a[0:2*yy,ScenSel_2015[xx]].sum(axis=0), Stock_Region_2015_use_loss_a[0:2*yy,ScenSel_2015[xx]].sum(axis=0)], color='k', linestyle='-', linewidth = Gen_Linewidth)    

for xx in range(0,len(ScenSel_2050)):
    for yy in range(0,10):
        plt.plot([len(ScenSel_2015)/2 + 0.5 + xx/2, len(ScenSel_2015)/2 + 0.5 + xx/2 + 0.4], [Stock_Region_2050_use_loss_a[0:2*yy,ScenSel_2050[xx]].sum(axis=0), Stock_Region_2050_use_loss_a[0:2*yy,ScenSel_2050[xx]].sum(axis=0)], color='k', linestyle='-', linewidth = Gen_Linewidth)    

for xx in range(0,len(ScenSel_2100)):
    for yy in range(0,10):
        plt.plot([len(ScenSel_2015)/2 + 0.5 + len(ScenSel_2050)/2 + 0.5 + xx/2, len(ScenSel_2015)/2 + 0.5 + len(ScenSel_2050)/2 + 0.5 + xx/2 + 0.4], [Stock_Region_2100_use_loss_a[0:2*yy,ScenSel_2100[xx]].sum(axis=0), Stock_Region_2100_use_loss_a[0:2*yy,ScenSel_2100[xx]].sum(axis=0)], color='k', linestyle='-', linewidth = Gen_Linewidth)    
    
# add hatch to legend
ProxyHandlesList.insert(0,plt.Rectangle((0, 0), 1, 1, fc='w', hatch = '//')) # create proxy artist for legend  
Def_RegionsNames_agg.insert(0,'Losses')
                 
plt_lgd  = plt.legend(reversed(ProxyHandlesList),reversed(Def_RegionsNames_agg),shadow = False, prop={'size':9.0},loc='upper left', bbox_to_anchor=(1.02, 1))                     

axs[1].set_ylim([     0, 1.10])
axs[1].set_xlim([     -0.1, ind.max() + 0.6])
axs[1].set_ylabel('Total steel in system, %', fontsize =15)
axs[1].set_yticks(np.arange(0,1.01,0.2))
axs[1].set_yticklabels(['0','20','40','60','80','100'], fontsize =15)
axs[1].set_xlabel('Scenario name', fontsize =15)
axs[1].set_xticks(xticks)
axs[1].set_xticklabels(xticklabels_flat, fontsize =10, rotation = 90)
axs[1].text(0.25 * (len(ScenSel_2015)) - 0.25, 1.03, '2015', fontsize=10, fontweight='bold') #alternative fontweight: bold
axs[1].text(0.50 * (len(ScenSel_2015) +1) +0.25 * len(ScenSel_2050) - 0.25, 1.03, '2050', fontsize=10, fontweight='bold') #alternative fontweight: bold
axs[1].text(0.50 * (len(ScenSel_2015) +1 +len(ScenSel_2050) +1)  + 0.25 * len(ScenSel_2100) - 0.25, 1.03, '2100', fontsize=10, fontweight='bold') #alternative fontweight: bold

plt.show()

fig.savefig(Path_Result + fig_name, dpi = 400,bbox_extra_artists=(plt_lgd,), bbox_inches='tight') 
# include figure in logfile:
Mylog.info('<center><img src="'+ fig_name +'" width="857" height="600" alt="'+ fig_name +'"></center>')
Mylog.info('<font "size=+3"><center><b><i>Figure '+ str(Figurecounter) + ': '+ fig_name +'.</i></b></center></font><br>')
Figurecounter += 1    



ScenSel_2015 = [0]
ScenSel_2050 = [0,16,17,14,15,18,19,20,21,22]
ScenSel_2100 = [0,16,17,14,15,18,19,20,21,22]
fig_name = 'Steel_Stock_Development_USA.png'

#%% Steel stock by product (top) and region (bottom)
ind = np.arange(0,(len(ScenSel_2015) +len(ScenSel_2050) +len(ScenSel_2100)+ 2)/2,0.5)  
width = 0.4       # the width of the bars
xticks = np.concatenate((np.arange(0.2,len(ScenSel_2015)/2,0.5),np.arange(0.2 + len(ScenSel_2015)/2 + 0.5,0.2 + len(ScenSel_2015)/2 + 0.5 + len(ScenSel_2050)/2,0.5),np.arange(0.2 + len(ScenSel_2015)/2 + 0.5 + len(ScenSel_2050)/2 + 0.5,0.2 + len(ScenSel_2015)/2 + 0.5 + len(ScenSel_2050)/2 + 0.5 + len(ScenSel_2100)/2,0.5)), axis = 0)
xticklabels = []
xticklabels.append(['All scenarios'])#Alternative: xticklabels.append([ScenList_Names_Plot[i] for i in ScenSel_2015])
xticklabels.append([ScenList_Names_Plot[i] for i in ScenSel_2050])
xticklabels.append([ScenList_Names_Plot[i] for i in ScenSel_2100])
xticklabels_flat = [item for sublist in xticklabels for item in sublist]

Gen_Linewidth = 0.5

# Start plotting
fig, axs = plt.subplots(2,1,figsize=(12,8))
axs = axs.ravel()
gs = plt.GridSpec(2, 1)
gs.update(hspace=0.2)#, wspace=0.4)

# create x lables for upper axis:
xticklabels_flat_3 = xticklabels_flat_2.copy()
xticklabels_flat_3[len(ScenSel_2015) -1 + len(ScenSel_2050) -0] = 'Circ_2100:'
for m in range(0,len(ScenSel_2100)):
    xticklabels_flat_3[len(ScenSel_2015) -1 + len(ScenSel_2050) +1 +m] = str("%.2f" %Circ_2100[ScenSel_2100[m]])

# plot bars for product split first
axs[0] = plt.subplot(gs[0])#, sharey=True, sharex=True)
axs[0].set_color_cycle(MyColorCycle_prod)
ProxyHandlesList = []   # For legend 
for m in range(0,14):
    p1 = plt.bar(ind[0:len(ScenSel_2015)], Stock_Product_2015[m,ScenSel_2015], width, color=MyColorCycle_prod[m,:], 
    label = StockLabels[m], bottom = Stock_Product_2015[0:m,ScenSel_2015].sum(axis=0), linewidth = Gen_Linewidth)
    ProxyHandlesList.append(plt.Rectangle((0, 0), 1, 1, fc=MyColorCycle_prod[m,:], linewidth = Gen_Linewidth)) # create proxy artist for legend
       
    p1 = plt.bar(ind[len(ScenSel_2015)+1:len(ScenSel_2015)+1 + len(ScenSel_2050)], Stock_Product_2050[m,ScenSel_2050], width, color=MyColorCycle_prod[m,:], 
    bottom = Stock_Product_2050[0:m,ScenSel_2050].sum(axis=0), linewidth = Gen_Linewidth)
   
    p1 = plt.bar(ind[len(ScenSel_2015)+1 + len(ScenSel_2050) +1 ::], Stock_Product_2100[m,ScenSel_2100], width, color=MyColorCycle_prod[m,:], 
    bottom = Stock_Product_2100[0:m,ScenSel_2100].sum(axis=0), linewidth = Gen_Linewidth)

plt_lgd  = plt.legend(reversed(ProxyHandlesList),reversed(StockLabels),shadow = False, prop={'size':8.0},loc='upper left', bbox_to_anchor=(1.02, 1))  

axs[0].set_ylim([     0, 1.10])
axs[0].set_xlim([     -0.1, ind.max() + 0.6])
axs[0].set_ylabel('Total steel in system, %', fontsize =15)
axs[0].set_yticks(np.arange(0,1.01,0.2))
axs[0].set_yticklabels(['0','20','40','60','80','100'], fontsize =15)
axs[0].set_xticks(xticks)
axs[0].set_xticklabels(xticklabels_flat_3, fontsize =10, rotation = 0)
axs[0].text(0.25 * (len(ScenSel_2015)) - 0.25, 1.03, '2015', fontsize=10, fontweight='bold') #alternative fontweight: bold
axs[0].text(0.50 * (len(ScenSel_2015) +1) +0.25 * len(ScenSel_2050) - 0.25, 1.03, '2050', fontsize=10, fontweight='bold') #alternative fontweight: bold
axs[0].text(0.50 * (len(ScenSel_2015) +1 +len(ScenSel_2050) +1)  + 0.25 * len(ScenSel_2100) - 0.25, 1.03, '2100', fontsize=10, fontweight='bold') #alternative fontweight: bold

# plot bars for regional split afterwards
axs[1] = plt.subplot(gs[1])#, sharey=True, sharex=True)
axs[1].set_color_cycle(MyColorCycle_10Reg)
ProxyHandlesList = []   # For legend 
for m in range(0,10*2):
    if m % 2 == 0:
        p1 = plt.bar(ind[0:len(ScenSel_2015)], Stock_Region_2015_use_loss_a[m,ScenSel_2015], width, hatch = '//', color=MyColorCycle_10Reg[m//2,:], 
        label = Def_RegionsNames_agg[m//2], bottom = Stock_Region_2015_use_loss_a[0:m,ScenSel_2015].sum(axis=0), linewidth = 0.0)
        ProxyHandlesList.append(plt.Rectangle((0, 0), 1, 1, fc=MyColorCycle_10Reg[m//2,:])) # create proxy artist for legend
    else:
        p1 = plt.bar(ind[0:len(ScenSel_2015)], Stock_Region_2015_use_loss_a[m,ScenSel_2015], width, color=MyColorCycle_10Reg[(m -1)//2,:], 
        label = Def_RegionsNames_agg[(m -1)//2], bottom = Stock_Region_2015_use_loss_a[0:m,ScenSel_2015].sum(axis=0), linewidth = 0.0)        
        
    if m % 2 == 0:
        p1 = plt.bar(ind[len(ScenSel_2015)+1:len(ScenSel_2015)+1 + len(ScenSel_2050)], Stock_Region_2050_use_loss_a[m,ScenSel_2050], width, hatch = '//', color=MyColorCycle_10Reg[m//2,:], 
        label = Def_RegionsNames_agg[m//2], bottom = Stock_Region_2050_use_loss_a[0:m,ScenSel_2050].sum(axis=0), linewidth = 0.0)
    else:
        p1 = plt.bar(ind[len(ScenSel_2015)+1:len(ScenSel_2015)+1 + len(ScenSel_2050)], Stock_Region_2050_use_loss_a[m,ScenSel_2050], width, color=MyColorCycle_10Reg[(m -1)//2,:], 
        label = Def_RegionsNames_agg[(m -1)//2], bottom = Stock_Region_2050_use_loss_a[0:m,ScenSel_2050].sum(axis=0), linewidth = 0.0)
               
    if m % 2 == 0:
        p1 = plt.bar(ind[len(ScenSel_2015)+1 + len(ScenSel_2050) +1 ::], Stock_Region_2100_use_loss_a[m,ScenSel_2100], width, hatch = '//', color=MyColorCycle_10Reg[m//2,:], 
        label = Def_RegionsNames_agg[m//2], bottom = Stock_Region_2100_use_loss_a[0:m,ScenSel_2100].sum(axis=0), linewidth = 0.0)
    else:
        p1 = plt.bar(ind[len(ScenSel_2015)+1 + len(ScenSel_2050) +1 ::], Stock_Region_2100_use_loss_a[m,ScenSel_2100], width, color=MyColorCycle_10Reg[(m -1)//2,:], 
        label = Def_RegionsNames_agg[(m -1)//2], bottom = Stock_Region_2100_use_loss_a[0:m,ScenSel_2100].sum(axis=0), linewidth = 0.0)
        # plot horizontal bar boundary
        
for xx in xticks:
    plt.plot([xx - 0.2, xx - 0.2], [0,1], color='k', linestyle='-', linewidth = Gen_Linewidth)    
    plt.plot([xx + 0.2, xx + 0.2], [0,1], color='k', linestyle='-', linewidth = Gen_Linewidth)    
    
for xx in range(0,len(ScenSel_2015)):
    for yy in range(0,10):
        plt.plot([xx/2, xx/2 + 0.4], [Stock_Region_2015_use_loss_a[0:2*yy,ScenSel_2015[xx]].sum(axis=0), Stock_Region_2015_use_loss_a[0:2*yy,ScenSel_2015[xx]].sum(axis=0)], color='k', linestyle='-', linewidth = Gen_Linewidth)    

for xx in range(0,len(ScenSel_2050)):
    for yy in range(0,10):
        plt.plot([len(ScenSel_2015)/2 + 0.5 + xx/2, len(ScenSel_2015)/2 + 0.5 + xx/2 + 0.4], [Stock_Region_2050_use_loss_a[0:2*yy,ScenSel_2050[xx]].sum(axis=0), Stock_Region_2050_use_loss_a[0:2*yy,ScenSel_2050[xx]].sum(axis=0)], color='k', linestyle='-', linewidth = Gen_Linewidth)    

for xx in range(0,len(ScenSel_2100)):
    for yy in range(0,10):
        plt.plot([len(ScenSel_2015)/2 + 0.5 + len(ScenSel_2050)/2 + 0.5 + xx/2, len(ScenSel_2015)/2 + 0.5 + len(ScenSel_2050)/2 + 0.5 + xx/2 + 0.4], [Stock_Region_2100_use_loss_a[0:2*yy,ScenSel_2100[xx]].sum(axis=0), Stock_Region_2100_use_loss_a[0:2*yy,ScenSel_2100[xx]].sum(axis=0)], color='k', linestyle='-', linewidth = Gen_Linewidth)    
    
# add hatch to legend
ProxyHandlesList.insert(0,plt.Rectangle((0, 0), 1, 1, fc='w', hatch = '//')) # create proxy artist for legend  
Def_RegionsNames_agg.insert(0,'Losses')
                 
plt_lgd  = plt.legend(reversed(ProxyHandlesList),reversed(Def_RegionsNames_agg),shadow = False, prop={'size':9.0},loc='upper left', bbox_to_anchor=(1.02, 1))                     

axs[1].set_ylim([     0, 1.10])
axs[1].set_xlim([     -0.1, ind.max() + 0.6])
axs[1].set_ylabel('Total steel in system, %', fontsize =15)
axs[1].set_yticks(np.arange(0,1.01,0.2))
axs[1].set_yticklabels(['0','20','40','60','80','100'], fontsize =15)
axs[1].set_xlabel('Scenario name', fontsize =15)
axs[1].set_xticks(xticks)
axs[1].set_xticklabels(xticklabels_flat, fontsize =10, rotation = 90)
axs[1].text(0.25 * (len(ScenSel_2015)) - 0.25, 1.03, '2015', fontsize=10, fontweight='bold') #alternative fontweight: bold
axs[1].text(0.50 * (len(ScenSel_2015) +1) +0.25 * len(ScenSel_2050) - 0.25, 1.03, '2050', fontsize=10, fontweight='bold') #alternative fontweight: bold
axs[1].text(0.50 * (len(ScenSel_2015) +1 +len(ScenSel_2050) +1)  + 0.25 * len(ScenSel_2100) - 0.25, 1.03, '2100', fontsize=10, fontweight='bold') #alternative fontweight: bold

plt.show()

fig.savefig(Path_Result + fig_name, dpi = 400,bbox_extra_artists=(plt_lgd,), bbox_inches='tight') 
# include figure in logfile:
Mylog.info('<center><img src="'+ fig_name +'" width="857" height="600" alt="'+ fig_name +'"></center>')
Mylog.info('<font "size=+3"><center><b><i>Figure '+ str(Figurecounter) + ': '+ fig_name +'.</i></b></center></font><br>')
Figurecounter += 1 

#%% Plot data for Japan

ScenSel_2015 = [23]
ScenSel_2050 = [23,24,25,26,27,28,29,30,31,32,33,34,35,36]
ScenSel_2100 = [23,24,25,26,27,28,29,30,31,32,33,34,35,36]
fig_name = 'Steel_Stock_Sensitivity_Japan.png'

#%% Steel stock by product (top) and region (bottom)
ind = np.arange(0,(len(ScenSel_2015) +len(ScenSel_2050) +len(ScenSel_2100)+ 2)/2,0.5)  
width = 0.4       # the width of the bars
xticks = np.concatenate((np.arange(0.2,len(ScenSel_2015)/2,0.5),np.arange(0.2 + len(ScenSel_2015)/2 + 0.5,0.2 + len(ScenSel_2015)/2 + 0.5 + len(ScenSel_2050)/2,0.5),np.arange(0.2 + len(ScenSel_2015)/2 + 0.5 + len(ScenSel_2050)/2 + 0.5,0.2 + len(ScenSel_2015)/2 + 0.5 + len(ScenSel_2050)/2 + 0.5 + len(ScenSel_2100)/2,0.5)), axis = 0)
xticklabels = []
xticklabels.append(['All scenarios'])#Alternative: xticklabels.append([ScenList_Names_Plot[i] for i in ScenSel_2015])
xticklabels.append([ScenList_Names_Plot[i] for i in ScenSel_2050])
xticklabels.append([ScenList_Names_Plot[i] for i in ScenSel_2100])
xticklabels_flat = [item for sublist in xticklabels for item in sublist]

xticklabels_flat_2 = []
for m in range(0,len(xticklabels_flat)):
    xticklabels_flat_2.append('')

Gen_Linewidth = 0.5

# Start plotting
fig, axs = plt.subplots(2,1,figsize=(12,8))
axs = axs.ravel()
gs = plt.GridSpec(2, 1)
gs.update(hspace=0.2)#, wspace=0.4)

# create x lables for upper axis:
xticklabels_flat_3 = xticklabels_flat_2.copy()
xticklabels_flat_3[len(ScenSel_2015) -1 + len(ScenSel_2050) -0] = 'Circ_2100:'
for m in range(0,len(ScenSel_2100)):
    xticklabels_flat_3[len(ScenSel_2015) -1 + len(ScenSel_2050) +1 +m] = str("%.2f" %Circ_2100[ScenSel_2100[m]])


# plot bars for product split first
axs[0] = plt.subplot(gs[0])#, sharey=True, sharex=True)
axs[0].set_color_cycle(MyColorCycle_prod)
ProxyHandlesList = []   # For legend 
for m in range(0,14):
    p1 = plt.bar(ind[0:len(ScenSel_2015)], Stock_Product_2015[m,ScenSel_2015], width, color=MyColorCycle_prod[m,:], 
    label = StockLabels[m], bottom = Stock_Product_2015[0:m,ScenSel_2015].sum(axis=0), linewidth = Gen_Linewidth)
    ProxyHandlesList.append(plt.Rectangle((0, 0), 1, 1, fc=MyColorCycle_prod[m,:], linewidth = Gen_Linewidth)) # create proxy artist for legend
       
    p1 = plt.bar(ind[len(ScenSel_2015)+1:len(ScenSel_2015)+1 + len(ScenSel_2050)], Stock_Product_2050[m,ScenSel_2050], width, color=MyColorCycle_prod[m,:], 
    bottom = Stock_Product_2050[0:m,ScenSel_2050].sum(axis=0), linewidth = Gen_Linewidth)
   
    p1 = plt.bar(ind[len(ScenSel_2015)+1 + len(ScenSel_2050) +1 ::], Stock_Product_2100[m,ScenSel_2100], width, color=MyColorCycle_prod[m,:], 
    bottom = Stock_Product_2100[0:m,ScenSel_2100].sum(axis=0), linewidth = Gen_Linewidth)

plt_lgd  = plt.legend(reversed(ProxyHandlesList),reversed(StockLabels),shadow = False, prop={'size':8.0},loc='upper left', bbox_to_anchor=(1.02, 1))  

axs[0].set_ylim([     0, 1.10])
axs[0].set_xlim([     -0.1, ind.max() + 0.6])
axs[0].set_ylabel('Total steel in system, %', fontsize =15)
axs[0].set_yticks(np.arange(0,1.01,0.2))
axs[0].set_yticklabels(['0','20','40','60','80','100'], fontsize =15)
axs[0].set_xticks(xticks)
axs[0].set_xticklabels(xticklabels_flat_3, fontsize =8, rotation = 0)
axs[0].text(0.25 * (len(ScenSel_2015)) - 0.25, 1.03, '2015', fontsize=10, fontweight='bold') #alternative fontweight: bold
axs[0].text(0.50 * (len(ScenSel_2015) +1) +0.25 * len(ScenSel_2050) - 0.25, 1.03, '2050', fontsize=10, fontweight='bold') #alternative fontweight: bold
axs[0].text(0.50 * (len(ScenSel_2015) +1 +len(ScenSel_2050) +1)  + 0.25 * len(ScenSel_2100) - 0.25, 1.03, '2100', fontsize=10, fontweight='bold') #alternative fontweight: bold

# plot bars for regional split afterwards
axs[1] = plt.subplot(gs[1])#, sharey=True, sharex=True)
axs[1].set_color_cycle(MyColorCycle_10Reg)
ProxyHandlesList = []   # For legend 
for m in range(0,10*2):
    if m % 2 == 0:
        p1 = plt.bar(ind[0:len(ScenSel_2015)], Stock_Region_2015_use_loss_a[m,ScenSel_2015], width, hatch = '//', color=MyColorCycle_10Reg[m//2,:], 
        label = Def_RegionsNames_agg[m//2], bottom = Stock_Region_2015_use_loss_a[0:m,ScenSel_2015].sum(axis=0), linewidth = 0.0)
        ProxyHandlesList.append(plt.Rectangle((0, 0), 1, 1, fc=MyColorCycle_10Reg[m//2,:])) # create proxy artist for legend
    else:
        p1 = plt.bar(ind[0:len(ScenSel_2015)], Stock_Region_2015_use_loss_a[m,ScenSel_2015], width, color=MyColorCycle_10Reg[(m -1)//2,:], 
        label = Def_RegionsNames_agg[(m -1)//2], bottom = Stock_Region_2015_use_loss_a[0:m,ScenSel_2015].sum(axis=0), linewidth = 0.0)        
        
    if m % 2 == 0:
        p1 = plt.bar(ind[len(ScenSel_2015)+1:len(ScenSel_2015)+1 + len(ScenSel_2050)], Stock_Region_2050_use_loss_a[m,ScenSel_2050], width, hatch = '//', color=MyColorCycle_10Reg[m//2,:], 
        label = Def_RegionsNames_agg[m//2], bottom = Stock_Region_2050_use_loss_a[0:m,ScenSel_2050].sum(axis=0), linewidth = 0.0)
    else:
        p1 = plt.bar(ind[len(ScenSel_2015)+1:len(ScenSel_2015)+1 + len(ScenSel_2050)], Stock_Region_2050_use_loss_a[m,ScenSel_2050], width, color=MyColorCycle_10Reg[(m -1)//2,:], 
        label = Def_RegionsNames_agg[(m -1)//2], bottom = Stock_Region_2050_use_loss_a[0:m,ScenSel_2050].sum(axis=0), linewidth = 0.0)
               
    if m % 2 == 0:
        p1 = plt.bar(ind[len(ScenSel_2015)+1 + len(ScenSel_2050) +1 ::], Stock_Region_2100_use_loss_a[m,ScenSel_2100], width, hatch = '//', color=MyColorCycle_10Reg[m//2,:], 
        label = Def_RegionsNames_agg[m//2], bottom = Stock_Region_2100_use_loss_a[0:m,ScenSel_2100].sum(axis=0), linewidth = 0.0)
    else:
        p1 = plt.bar(ind[len(ScenSel_2015)+1 + len(ScenSel_2050) +1 ::], Stock_Region_2100_use_loss_a[m,ScenSel_2100], width, color=MyColorCycle_10Reg[(m -1)//2,:], 
        label = Def_RegionsNames_agg[(m -1)//2], bottom = Stock_Region_2100_use_loss_a[0:m,ScenSel_2100].sum(axis=0), linewidth = 0.0)
        # plot horizontal bar boundary
        
for xx in xticks:
    plt.plot([xx - 0.2, xx - 0.2], [0,1], color='k', linestyle='-', linewidth = Gen_Linewidth)    
    plt.plot([xx + 0.2, xx + 0.2], [0,1], color='k', linestyle='-', linewidth = Gen_Linewidth)    
    
for xx in range(0,len(ScenSel_2015)):
    for yy in range(0,10):
        plt.plot([xx/2, xx/2 + 0.4], [Stock_Region_2015_use_loss_a[0:2*yy,ScenSel_2015[xx]].sum(axis=0), Stock_Region_2015_use_loss_a[0:2*yy,ScenSel_2015[xx]].sum(axis=0)], color='k', linestyle='-', linewidth = Gen_Linewidth)    

for xx in range(0,len(ScenSel_2050)):
    for yy in range(0,10):
        plt.plot([len(ScenSel_2015)/2 + 0.5 + xx/2, len(ScenSel_2015)/2 + 0.5 + xx/2 + 0.4], [Stock_Region_2050_use_loss_a[0:2*yy,ScenSel_2050[xx]].sum(axis=0), Stock_Region_2050_use_loss_a[0:2*yy,ScenSel_2050[xx]].sum(axis=0)], color='k', linestyle='-', linewidth = Gen_Linewidth)    

for xx in range(0,len(ScenSel_2100)):
    for yy in range(0,10):
        plt.plot([len(ScenSel_2015)/2 + 0.5 + len(ScenSel_2050)/2 + 0.5 + xx/2, len(ScenSel_2015)/2 + 0.5 + len(ScenSel_2050)/2 + 0.5 + xx/2 + 0.4], [Stock_Region_2100_use_loss_a[0:2*yy,ScenSel_2100[xx]].sum(axis=0), Stock_Region_2100_use_loss_a[0:2*yy,ScenSel_2100[xx]].sum(axis=0)], color='k', linestyle='-', linewidth = Gen_Linewidth)    
    
# add hatch to legend
ProxyHandlesList.insert(0,plt.Rectangle((0, 0), 1, 1, fc='w', hatch = '//')) # create proxy artist for legend  
Def_RegionsNames_agg.insert(0,'Losses')
                 
plt_lgd  = plt.legend(reversed(ProxyHandlesList),reversed(Def_RegionsNames_agg),shadow = False, prop={'size':9.0},loc='upper left', bbox_to_anchor=(1.02, 1))                     

axs[1].set_ylim([     0, 1.10])
axs[1].set_xlim([     -0.1, ind.max() + 0.6])
axs[1].set_ylabel('Total steel in system, %', fontsize =15)
axs[1].set_yticks(np.arange(0,1.01,0.2))
axs[1].set_yticklabels(['0','20','40','60','80','100'], fontsize =15)
axs[1].set_xlabel('Scenario name', fontsize =15)
axs[1].set_xticks(xticks)
axs[1].set_xticklabels(xticklabels_flat, fontsize =10, rotation = 90)
axs[1].text(0.25 * (len(ScenSel_2015)) - 0.25, 1.03, '2015', fontsize=10, fontweight='bold') #alternative fontweight: bold
axs[1].text(0.50 * (len(ScenSel_2015) +1) +0.25 * len(ScenSel_2050) - 0.25, 1.03, '2050', fontsize=10, fontweight='bold') #alternative fontweight: bold
axs[1].text(0.50 * (len(ScenSel_2015) +1 +len(ScenSel_2050) +1)  + 0.25 * len(ScenSel_2100) - 0.25, 1.03, '2100', fontsize=10, fontweight='bold') #alternative fontweight: bold

plt.show()

fig.savefig(Path_Result + fig_name, dpi = 400,bbox_extra_artists=(plt_lgd,), bbox_inches='tight') 
# include figure in logfile:
Mylog.info('<center><img src="'+ fig_name +'" width="857" height="600" alt="'+ fig_name +'"></center>')
Mylog.info('<font "size=+3"><center><b><i>Figure '+ str(Figurecounter) + ': '+ fig_name +'.</i></b></center></font><br>')
Figurecounter += 1    



ScenSel_2015 = [23]
ScenSel_2050 = [23,39,40,37,38,41,42,43,44,45]
ScenSel_2100 = [23,39,40,37,38,41,42,43,44,45]
fig_name = 'Steel_Stock_Development_Japan.png'

#%% Steel stock by product (top) and region (bottom)
ind = np.arange(0,(len(ScenSel_2015) +len(ScenSel_2050) +len(ScenSel_2100)+ 2)/2,0.5)  
width = 0.4       # the width of the bars
xticks = np.concatenate((np.arange(0.2,len(ScenSel_2015)/2,0.5),np.arange(0.2 + len(ScenSel_2015)/2 + 0.5,0.2 + len(ScenSel_2015)/2 + 0.5 + len(ScenSel_2050)/2,0.5),np.arange(0.2 + len(ScenSel_2015)/2 + 0.5 + len(ScenSel_2050)/2 + 0.5,0.2 + len(ScenSel_2015)/2 + 0.5 + len(ScenSel_2050)/2 + 0.5 + len(ScenSel_2100)/2,0.5)), axis = 0)
xticklabels = []
xticklabels.append(['All scenarios'])#Alternative: xticklabels.append([ScenList_Names_Plot[i] for i in ScenSel_2015])
xticklabels.append([ScenList_Names_Plot[i] for i in ScenSel_2050])
xticklabels.append([ScenList_Names_Plot[i] for i in ScenSel_2100])
xticklabels_flat = [item for sublist in xticklabels for item in sublist]

Gen_Linewidth = 0.5

# Start plotting
fig, axs = plt.subplots(2,1,figsize=(12,8))
axs = axs.ravel()
gs = plt.GridSpec(2, 1)
gs.update(hspace=0.2)#, wspace=0.4)

# create x lables for upper axis:
xticklabels_flat_3 = xticklabels_flat_2.copy()
xticklabels_flat_3[len(ScenSel_2015) -1 + len(ScenSel_2050) -0] = 'Circ_2100:'
for m in range(0,len(ScenSel_2100)):
    xticklabels_flat_3[len(ScenSel_2015) -1 + len(ScenSel_2050) +1 +m] = str("%.2f" %Circ_2100[ScenSel_2100[m]])

# plot bars for product split first
axs[0] = plt.subplot(gs[0])#, sharey=True, sharex=True)
axs[0].set_color_cycle(MyColorCycle_prod)
ProxyHandlesList = []   # For legend 
for m in range(0,14):
    p1 = plt.bar(ind[0:len(ScenSel_2015)], Stock_Product_2015[m,ScenSel_2015], width, color=MyColorCycle_prod[m,:], 
    label = StockLabels[m], bottom = Stock_Product_2015[0:m,ScenSel_2015].sum(axis=0), linewidth = Gen_Linewidth)
    ProxyHandlesList.append(plt.Rectangle((0, 0), 1, 1, fc=MyColorCycle_prod[m,:], linewidth = Gen_Linewidth)) # create proxy artist for legend
       
    p1 = plt.bar(ind[len(ScenSel_2015)+1:len(ScenSel_2015)+1 + len(ScenSel_2050)], Stock_Product_2050[m,ScenSel_2050], width, color=MyColorCycle_prod[m,:], 
    bottom = Stock_Product_2050[0:m,ScenSel_2050].sum(axis=0), linewidth = Gen_Linewidth)
   
    p1 = plt.bar(ind[len(ScenSel_2015)+1 + len(ScenSel_2050) +1 ::], Stock_Product_2100[m,ScenSel_2100], width, color=MyColorCycle_prod[m,:], 
    bottom = Stock_Product_2100[0:m,ScenSel_2100].sum(axis=0), linewidth = Gen_Linewidth)

plt_lgd  = plt.legend(reversed(ProxyHandlesList),reversed(StockLabels),shadow = False, prop={'size':8.0},loc='upper left', bbox_to_anchor=(1.02, 1))  

axs[0].set_ylim([     0, 1.10])
axs[0].set_xlim([     -0.1, ind.max() + 0.6])
axs[0].set_ylabel('Total steel in system, %', fontsize =15)
axs[0].set_yticks(np.arange(0,1.01,0.2))
axs[0].set_yticklabels(['0','20','40','60','80','100'], fontsize =15)
axs[0].set_xticks(xticks)
axs[0].set_xticklabels(xticklabels_flat_3, fontsize =10, rotation = 0)
axs[0].text(0.25 * (len(ScenSel_2015)) - 0.25, 1.03, '2015', fontsize=10, fontweight='bold') #alternative fontweight: bold
axs[0].text(0.50 * (len(ScenSel_2015) +1) +0.25 * len(ScenSel_2050) - 0.25, 1.03, '2050', fontsize=10, fontweight='bold') #alternative fontweight: bold
axs[0].text(0.50 * (len(ScenSel_2015) +1 +len(ScenSel_2050) +1)  + 0.25 * len(ScenSel_2100) - 0.25, 1.03, '2100', fontsize=10, fontweight='bold') #alternative fontweight: bold

# plot bars for regional split afterwards
axs[1] = plt.subplot(gs[1])#, sharey=True, sharex=True)
axs[1].set_color_cycle(MyColorCycle_10Reg)
ProxyHandlesList = []   # For legend 
for m in range(0,10*2):
    if m % 2 == 0:
        p1 = plt.bar(ind[0:len(ScenSel_2015)], Stock_Region_2015_use_loss_a[m,ScenSel_2015], width, hatch = '//', color=MyColorCycle_10Reg[m//2,:], 
        label = Def_RegionsNames_agg[m//2], bottom = Stock_Region_2015_use_loss_a[0:m,ScenSel_2015].sum(axis=0), linewidth = 0.0)
        ProxyHandlesList.append(plt.Rectangle((0, 0), 1, 1, fc=MyColorCycle_10Reg[m//2,:])) # create proxy artist for legend
    else:
        p1 = plt.bar(ind[0:len(ScenSel_2015)], Stock_Region_2015_use_loss_a[m,ScenSel_2015], width, color=MyColorCycle_10Reg[(m -1)//2,:], 
        label = Def_RegionsNames_agg[(m -1)//2], bottom = Stock_Region_2015_use_loss_a[0:m,ScenSel_2015].sum(axis=0), linewidth = 0.0)        
        
    if m % 2 == 0:
        p1 = plt.bar(ind[len(ScenSel_2015)+1:len(ScenSel_2015)+1 + len(ScenSel_2050)], Stock_Region_2050_use_loss_a[m,ScenSel_2050], width, hatch = '//', color=MyColorCycle_10Reg[m//2,:], 
        label = Def_RegionsNames_agg[m//2], bottom = Stock_Region_2050_use_loss_a[0:m,ScenSel_2050].sum(axis=0), linewidth = 0.0)
    else:
        p1 = plt.bar(ind[len(ScenSel_2015)+1:len(ScenSel_2015)+1 + len(ScenSel_2050)], Stock_Region_2050_use_loss_a[m,ScenSel_2050], width, color=MyColorCycle_10Reg[(m -1)//2,:], 
        label = Def_RegionsNames_agg[(m -1)//2], bottom = Stock_Region_2050_use_loss_a[0:m,ScenSel_2050].sum(axis=0), linewidth = 0.0)
               
    if m % 2 == 0:
        p1 = plt.bar(ind[len(ScenSel_2015)+1 + len(ScenSel_2050) +1 ::], Stock_Region_2100_use_loss_a[m,ScenSel_2100], width, hatch = '//', color=MyColorCycle_10Reg[m//2,:], 
        label = Def_RegionsNames_agg[m//2], bottom = Stock_Region_2100_use_loss_a[0:m,ScenSel_2100].sum(axis=0), linewidth = 0.0)
    else:
        p1 = plt.bar(ind[len(ScenSel_2015)+1 + len(ScenSel_2050) +1 ::], Stock_Region_2100_use_loss_a[m,ScenSel_2100], width, color=MyColorCycle_10Reg[(m -1)//2,:], 
        label = Def_RegionsNames_agg[(m -1)//2], bottom = Stock_Region_2100_use_loss_a[0:m,ScenSel_2100].sum(axis=0), linewidth = 0.0)
        # plot horizontal bar boundary
        
for xx in xticks:
    plt.plot([xx - 0.2, xx - 0.2], [0,1], color='k', linestyle='-', linewidth = Gen_Linewidth)    
    plt.plot([xx + 0.2, xx + 0.2], [0,1], color='k', linestyle='-', linewidth = Gen_Linewidth)    
    
for xx in range(0,len(ScenSel_2015)):
    for yy in range(0,10):
        plt.plot([xx/2, xx/2 + 0.4], [Stock_Region_2015_use_loss_a[0:2*yy,ScenSel_2015[xx]].sum(axis=0), Stock_Region_2015_use_loss_a[0:2*yy,ScenSel_2015[xx]].sum(axis=0)], color='k', linestyle='-', linewidth = Gen_Linewidth)    

for xx in range(0,len(ScenSel_2050)):
    for yy in range(0,10):
        plt.plot([len(ScenSel_2015)/2 + 0.5 + xx/2, len(ScenSel_2015)/2 + 0.5 + xx/2 + 0.4], [Stock_Region_2050_use_loss_a[0:2*yy,ScenSel_2050[xx]].sum(axis=0), Stock_Region_2050_use_loss_a[0:2*yy,ScenSel_2050[xx]].sum(axis=0)], color='k', linestyle='-', linewidth = Gen_Linewidth)    

for xx in range(0,len(ScenSel_2100)):
    for yy in range(0,10):
        plt.plot([len(ScenSel_2015)/2 + 0.5 + len(ScenSel_2050)/2 + 0.5 + xx/2, len(ScenSel_2015)/2 + 0.5 + len(ScenSel_2050)/2 + 0.5 + xx/2 + 0.4], [Stock_Region_2100_use_loss_a[0:2*yy,ScenSel_2100[xx]].sum(axis=0), Stock_Region_2100_use_loss_a[0:2*yy,ScenSel_2100[xx]].sum(axis=0)], color='k', linestyle='-', linewidth = Gen_Linewidth)    
    
# add hatch to legend
ProxyHandlesList.insert(0,plt.Rectangle((0, 0), 1, 1, fc='w', hatch = '//')) # create proxy artist for legend  
Def_RegionsNames_agg.insert(0,'Losses')
                 
plt_lgd  = plt.legend(reversed(ProxyHandlesList),reversed(Def_RegionsNames_agg),shadow = False, prop={'size':9.0},loc='upper left', bbox_to_anchor=(1.02, 1))                     

axs[1].set_ylim([     0, 1.10])
axs[1].set_xlim([     -0.1, ind.max() + 0.6])
axs[1].set_ylabel('Total steel in system, %', fontsize =15)
axs[1].set_yticks(np.arange(0,1.01,0.2))
axs[1].set_yticklabels(['0','20','40','60','80','100'], fontsize =15)
axs[1].set_xlabel('Scenario name', fontsize =15)
axs[1].set_xticks(xticks)
axs[1].set_xticklabels(xticklabels_flat, fontsize =10, rotation = 90)
axs[1].text(0.25 * (len(ScenSel_2015)) - 0.25, 1.03, '2015', fontsize=10, fontweight='bold') #alternative fontweight: bold
axs[1].text(0.50 * (len(ScenSel_2015) +1) +0.25 * len(ScenSel_2050) - 0.25, 1.03, '2050', fontsize=10, fontweight='bold') #alternative fontweight: bold
axs[1].text(0.50 * (len(ScenSel_2015) +1 +len(ScenSel_2050) +1)  + 0.25 * len(ScenSel_2100) - 0.25, 1.03, '2100', fontsize=10, fontweight='bold') #alternative fontweight: bold

plt.show()

fig.savefig(Path_Result + fig_name, dpi = 400,bbox_extra_artists=(plt_lgd,), bbox_inches='tight') 
# include figure in logfile:
Mylog.info('<center><img src="'+ fig_name +'" width="857" height="600" alt="'+ fig_name +'"></center>')
Mylog.info('<font "size=+3"><center><b><i>Figure '+ str(Figurecounter) + ': '+ fig_name +'.</i></b></center></font><br>')
Figurecounter += 1 

#%% Plot data for Germany

ScenSel_2015 = [46]
ScenSel_2050 = [46,47,48,49,50,51,52,53,54,55,56,57,58,59]
ScenSel_2100 = [46,47,48,49,50,51,52,53,54,55,56,57,58,59]
fig_name = 'Steel_Stock_Sensitivity_Germany.png'

#%% Steel stock by product (top) and region (bottom)
ind = np.arange(0,(len(ScenSel_2015) +len(ScenSel_2050) +len(ScenSel_2100)+ 2)/2,0.5)  
width = 0.4       # the width of the bars
xticks = np.concatenate((np.arange(0.2,len(ScenSel_2015)/2,0.5),np.arange(0.2 + len(ScenSel_2015)/2 + 0.5,0.2 + len(ScenSel_2015)/2 + 0.5 + len(ScenSel_2050)/2,0.5),np.arange(0.2 + len(ScenSel_2015)/2 + 0.5 + len(ScenSel_2050)/2 + 0.5,0.2 + len(ScenSel_2015)/2 + 0.5 + len(ScenSel_2050)/2 + 0.5 + len(ScenSel_2100)/2,0.5)), axis = 0)
xticklabels = []
xticklabels.append(['All scenarios'])#Alternative: xticklabels.append([ScenList_Names_Plot[i] for i in ScenSel_2015])
xticklabels.append([ScenList_Names_Plot[i] for i in ScenSel_2050])
xticklabels.append([ScenList_Names_Plot[i] for i in ScenSel_2100])
xticklabels_flat = [item for sublist in xticklabels for item in sublist]

xticklabels_flat_2 = []
for m in range(0,len(xticklabels_flat)):
    xticklabels_flat_2.append('')

Gen_Linewidth = 0.5

# Start plotting
fig, axs = plt.subplots(2,1,figsize=(12,8))
axs = axs.ravel()
gs = plt.GridSpec(2, 1)
gs.update(hspace=0.2)#, wspace=0.4)

# create x lables for upper axis:
xticklabels_flat_3 = xticklabels_flat_2.copy()
xticklabels_flat_3[len(ScenSel_2015) -1 + len(ScenSel_2050) -0] = 'Circ_2100:'
for m in range(0,len(ScenSel_2100)):
    xticklabels_flat_3[len(ScenSel_2015) -1 + len(ScenSel_2050) +1 +m] = str("%.2f" %Circ_2100[ScenSel_2100[m]])


# plot bars for product split first
axs[0] = plt.subplot(gs[0])#, sharey=True, sharex=True)
axs[0].set_color_cycle(MyColorCycle_prod)
ProxyHandlesList = []   # For legend 
for m in range(0,14):
    p1 = plt.bar(ind[0:len(ScenSel_2015)], Stock_Product_2015[m,ScenSel_2015], width, color=MyColorCycle_prod[m,:], 
    label = StockLabels[m], bottom = Stock_Product_2015[0:m,ScenSel_2015].sum(axis=0), linewidth = Gen_Linewidth)
    ProxyHandlesList.append(plt.Rectangle((0, 0), 1, 1, fc=MyColorCycle_prod[m,:], linewidth = Gen_Linewidth)) # create proxy artist for legend
       
    p1 = plt.bar(ind[len(ScenSel_2015)+1:len(ScenSel_2015)+1 + len(ScenSel_2050)], Stock_Product_2050[m,ScenSel_2050], width, color=MyColorCycle_prod[m,:], 
    bottom = Stock_Product_2050[0:m,ScenSel_2050].sum(axis=0), linewidth = Gen_Linewidth)
   
    p1 = plt.bar(ind[len(ScenSel_2015)+1 + len(ScenSel_2050) +1 ::], Stock_Product_2100[m,ScenSel_2100], width, color=MyColorCycle_prod[m,:], 
    bottom = Stock_Product_2100[0:m,ScenSel_2100].sum(axis=0), linewidth = Gen_Linewidth)

plt_lgd  = plt.legend(reversed(ProxyHandlesList),reversed(StockLabels),shadow = False, prop={'size':8.0},loc='upper left', bbox_to_anchor=(1.02, 1))  

axs[0].set_ylim([     0, 1.10])
axs[0].set_xlim([     -0.1, ind.max() + 0.6])
axs[0].set_ylabel('Total steel in system, %', fontsize =15)
axs[0].set_yticks(np.arange(0,1.01,0.2))
axs[0].set_yticklabels(['0','20','40','60','80','100'], fontsize =15)
axs[0].set_xticks(xticks)
axs[0].set_xticklabels(xticklabels_flat_3, fontsize =8, rotation = 0)
axs[0].text(0.25 * (len(ScenSel_2015)) - 0.25, 1.03, '2015', fontsize=10, fontweight='bold') #alternative fontweight: bold
axs[0].text(0.50 * (len(ScenSel_2015) +1) +0.25 * len(ScenSel_2050) - 0.25, 1.03, '2050', fontsize=10, fontweight='bold') #alternative fontweight: bold
axs[0].text(0.50 * (len(ScenSel_2015) +1 +len(ScenSel_2050) +1)  + 0.25 * len(ScenSel_2100) - 0.25, 1.03, '2100', fontsize=10, fontweight='bold') #alternative fontweight: bold

# plot bars for regional split afterwards
axs[1] = plt.subplot(gs[1])#, sharey=True, sharex=True)
axs[1].set_color_cycle(MyColorCycle_10Reg)
ProxyHandlesList = []   # For legend 
for m in range(0,10*2):
    if m % 2 == 0:
        p1 = plt.bar(ind[0:len(ScenSel_2015)], Stock_Region_2015_use_loss_a[m,ScenSel_2015], width, hatch = '//', color=MyColorCycle_10Reg[m//2,:], 
        label = Def_RegionsNames_agg[m//2], bottom = Stock_Region_2015_use_loss_a[0:m,ScenSel_2015].sum(axis=0), linewidth = 0.0)
        ProxyHandlesList.append(plt.Rectangle((0, 0), 1, 1, fc=MyColorCycle_10Reg[m//2,:])) # create proxy artist for legend
    else:
        p1 = plt.bar(ind[0:len(ScenSel_2015)], Stock_Region_2015_use_loss_a[m,ScenSel_2015], width, color=MyColorCycle_10Reg[(m -1)//2,:], 
        label = Def_RegionsNames_agg[(m -1)//2], bottom = Stock_Region_2015_use_loss_a[0:m,ScenSel_2015].sum(axis=0), linewidth = 0.0)        
        
    if m % 2 == 0:
        p1 = plt.bar(ind[len(ScenSel_2015)+1:len(ScenSel_2015)+1 + len(ScenSel_2050)], Stock_Region_2050_use_loss_a[m,ScenSel_2050], width, hatch = '//', color=MyColorCycle_10Reg[m//2,:], 
        label = Def_RegionsNames_agg[m//2], bottom = Stock_Region_2050_use_loss_a[0:m,ScenSel_2050].sum(axis=0), linewidth = 0.0)
    else:
        p1 = plt.bar(ind[len(ScenSel_2015)+1:len(ScenSel_2015)+1 + len(ScenSel_2050)], Stock_Region_2050_use_loss_a[m,ScenSel_2050], width, color=MyColorCycle_10Reg[(m -1)//2,:], 
        label = Def_RegionsNames_agg[(m -1)//2], bottom = Stock_Region_2050_use_loss_a[0:m,ScenSel_2050].sum(axis=0), linewidth = 0.0)
               
    if m % 2 == 0:
        p1 = plt.bar(ind[len(ScenSel_2015)+1 + len(ScenSel_2050) +1 ::], Stock_Region_2100_use_loss_a[m,ScenSel_2100], width, hatch = '//', color=MyColorCycle_10Reg[m//2,:], 
        label = Def_RegionsNames_agg[m//2], bottom = Stock_Region_2100_use_loss_a[0:m,ScenSel_2100].sum(axis=0), linewidth = 0.0)
    else:
        p1 = plt.bar(ind[len(ScenSel_2015)+1 + len(ScenSel_2050) +1 ::], Stock_Region_2100_use_loss_a[m,ScenSel_2100], width, color=MyColorCycle_10Reg[(m -1)//2,:], 
        label = Def_RegionsNames_agg[(m -1)//2], bottom = Stock_Region_2100_use_loss_a[0:m,ScenSel_2100].sum(axis=0), linewidth = 0.0)
        # plot horizontal bar boundary
        
for xx in xticks:
    plt.plot([xx - 0.2, xx - 0.2], [0,1], color='k', linestyle='-', linewidth = Gen_Linewidth)    
    plt.plot([xx + 0.2, xx + 0.2], [0,1], color='k', linestyle='-', linewidth = Gen_Linewidth)    
    
for xx in range(0,len(ScenSel_2015)):
    for yy in range(0,10):
        plt.plot([xx/2, xx/2 + 0.4], [Stock_Region_2015_use_loss_a[0:2*yy,ScenSel_2015[xx]].sum(axis=0), Stock_Region_2015_use_loss_a[0:2*yy,ScenSel_2015[xx]].sum(axis=0)], color='k', linestyle='-', linewidth = Gen_Linewidth)    

for xx in range(0,len(ScenSel_2050)):
    for yy in range(0,10):
        plt.plot([len(ScenSel_2015)/2 + 0.5 + xx/2, len(ScenSel_2015)/2 + 0.5 + xx/2 + 0.4], [Stock_Region_2050_use_loss_a[0:2*yy,ScenSel_2050[xx]].sum(axis=0), Stock_Region_2050_use_loss_a[0:2*yy,ScenSel_2050[xx]].sum(axis=0)], color='k', linestyle='-', linewidth = Gen_Linewidth)    

for xx in range(0,len(ScenSel_2100)):
    for yy in range(0,10):
        plt.plot([len(ScenSel_2015)/2 + 0.5 + len(ScenSel_2050)/2 + 0.5 + xx/2, len(ScenSel_2015)/2 + 0.5 + len(ScenSel_2050)/2 + 0.5 + xx/2 + 0.4], [Stock_Region_2100_use_loss_a[0:2*yy,ScenSel_2100[xx]].sum(axis=0), Stock_Region_2100_use_loss_a[0:2*yy,ScenSel_2100[xx]].sum(axis=0)], color='k', linestyle='-', linewidth = Gen_Linewidth)    
    
# add hatch to legend
ProxyHandlesList.insert(0,plt.Rectangle((0, 0), 1, 1, fc='w', hatch = '//')) # create proxy artist for legend  
Def_RegionsNames_agg.insert(0,'Losses')
                 
plt_lgd  = plt.legend(reversed(ProxyHandlesList),reversed(Def_RegionsNames_agg),shadow = False, prop={'size':9.0},loc='upper left', bbox_to_anchor=(1.02, 1))                     

axs[1].set_ylim([     0, 1.10])
axs[1].set_xlim([     -0.1, ind.max() + 0.6])
axs[1].set_ylabel('Total steel in system, %', fontsize =15)
axs[1].set_yticks(np.arange(0,1.01,0.2))
axs[1].set_yticklabels(['0','20','40','60','80','100'], fontsize =15)
axs[1].set_xlabel('Scenario name', fontsize =15)
axs[1].set_xticks(xticks)
axs[1].set_xticklabels(xticklabels_flat, fontsize =10, rotation = 90)
axs[1].text(0.25 * (len(ScenSel_2015)) - 0.25, 1.03, '2015', fontsize=10, fontweight='bold') #alternative fontweight: bold
axs[1].text(0.50 * (len(ScenSel_2015) +1) +0.25 * len(ScenSel_2050) - 0.25, 1.03, '2050', fontsize=10, fontweight='bold') #alternative fontweight: bold
axs[1].text(0.50 * (len(ScenSel_2015) +1 +len(ScenSel_2050) +1)  + 0.25 * len(ScenSel_2100) - 0.25, 1.03, '2100', fontsize=10, fontweight='bold') #alternative fontweight: bold

plt.show()

fig.savefig(Path_Result + fig_name, dpi = 400,bbox_extra_artists=(plt_lgd,), bbox_inches='tight') 
# include figure in logfile:
Mylog.info('<center><img src="'+ fig_name +'" width="857" height="600" alt="'+ fig_name +'"></center>')
Mylog.info('<font "size=+3"><center><b><i>Figure '+ str(Figurecounter) + ': '+ fig_name +'.</i></b></center></font><br>')
Figurecounter += 1    



ScenSel_2015 = [46]
ScenSel_2050 = [46,62,63,60,61,64,65,66,67,68]
ScenSel_2100 = [46,62,63,60,61,64,65,66,67,68]
fig_name = 'Steel_Stock_Development_Germany.png'

#%% Steel stock by product (top) and region (bottom)
ind = np.arange(0,(len(ScenSel_2015) +len(ScenSel_2050) +len(ScenSel_2100)+ 2)/2,0.5)  
width = 0.4       # the width of the bars
xticks = np.concatenate((np.arange(0.2,len(ScenSel_2015)/2,0.5),np.arange(0.2 + len(ScenSel_2015)/2 + 0.5,0.2 + len(ScenSel_2015)/2 + 0.5 + len(ScenSel_2050)/2,0.5),np.arange(0.2 + len(ScenSel_2015)/2 + 0.5 + len(ScenSel_2050)/2 + 0.5,0.2 + len(ScenSel_2015)/2 + 0.5 + len(ScenSel_2050)/2 + 0.5 + len(ScenSel_2100)/2,0.5)), axis = 0)
xticklabels = []
xticklabels.append(['All scenarios'])#Alternative: xticklabels.append([ScenList_Names_Plot[i] for i in ScenSel_2015])
xticklabels.append([ScenList_Names_Plot[i] for i in ScenSel_2050])
xticklabels.append([ScenList_Names_Plot[i] for i in ScenSel_2100])
xticklabels_flat = [item for sublist in xticklabels for item in sublist]

Gen_Linewidth = 0.5

# Start plotting
fig, axs = plt.subplots(2,1,figsize=(12,8))
axs = axs.ravel()
gs = plt.GridSpec(2, 1)
gs.update(hspace=0.2)#, wspace=0.4)

# create x lables for upper axis:
xticklabels_flat_3 = xticklabels_flat_2.copy()
xticklabels_flat_3[len(ScenSel_2015) -1 + len(ScenSel_2050) -0] = 'Circ_2100:'
for m in range(0,len(ScenSel_2100)):
    xticklabels_flat_3[len(ScenSel_2015) -1 + len(ScenSel_2050) +1 +m] = str("%.2f" %Circ_2100[ScenSel_2100[m]])

# plot bars for product split first
axs[0] = plt.subplot(gs[0])#, sharey=True, sharex=True)
axs[0].set_color_cycle(MyColorCycle_prod)
ProxyHandlesList = []   # For legend 
for m in range(0,14):
    p1 = plt.bar(ind[0:len(ScenSel_2015)], Stock_Product_2015[m,ScenSel_2015], width, color=MyColorCycle_prod[m,:], 
    label = StockLabels[m], bottom = Stock_Product_2015[0:m,ScenSel_2015].sum(axis=0), linewidth = Gen_Linewidth)
    ProxyHandlesList.append(plt.Rectangle((0, 0), 1, 1, fc=MyColorCycle_prod[m,:], linewidth = Gen_Linewidth)) # create proxy artist for legend
       
    p1 = plt.bar(ind[len(ScenSel_2015)+1:len(ScenSel_2015)+1 + len(ScenSel_2050)], Stock_Product_2050[m,ScenSel_2050], width, color=MyColorCycle_prod[m,:], 
    bottom = Stock_Product_2050[0:m,ScenSel_2050].sum(axis=0), linewidth = Gen_Linewidth)
   
    p1 = plt.bar(ind[len(ScenSel_2015)+1 + len(ScenSel_2050) +1 ::], Stock_Product_2100[m,ScenSel_2100], width, color=MyColorCycle_prod[m,:], 
    bottom = Stock_Product_2100[0:m,ScenSel_2100].sum(axis=0), linewidth = Gen_Linewidth)

plt_lgd  = plt.legend(reversed(ProxyHandlesList),reversed(StockLabels),shadow = False, prop={'size':8.0},loc='upper left', bbox_to_anchor=(1.02, 1))  

axs[0].set_ylim([     0, 1.10])
axs[0].set_xlim([     -0.1, ind.max() + 0.6])
axs[0].set_ylabel('Total steel in system, %', fontsize =15)
axs[0].set_yticks(np.arange(0,1.01,0.2))
axs[0].set_yticklabels(['0','20','40','60','80','100'], fontsize =15)
axs[0].set_xticks(xticks)
axs[0].set_xticklabels(xticklabels_flat_3, fontsize =10, rotation = 0)
axs[0].text(0.25 * (len(ScenSel_2015)) - 0.25, 1.03, '2015', fontsize=10, fontweight='bold') #alternative fontweight: bold
axs[0].text(0.50 * (len(ScenSel_2015) +1) +0.25 * len(ScenSel_2050) - 0.25, 1.03, '2050', fontsize=10, fontweight='bold') #alternative fontweight: bold
axs[0].text(0.50 * (len(ScenSel_2015) +1 +len(ScenSel_2050) +1)  + 0.25 * len(ScenSel_2100) - 0.25, 1.03, '2100', fontsize=10, fontweight='bold') #alternative fontweight: bold

# plot bars for regional split afterwards
axs[1] = plt.subplot(gs[1])#, sharey=True, sharex=True)
axs[1].set_color_cycle(MyColorCycle_10Reg)
ProxyHandlesList = []   # For legend 
for m in range(0,10*2):
    if m % 2 == 0:
        p1 = plt.bar(ind[0:len(ScenSel_2015)], Stock_Region_2015_use_loss_a[m,ScenSel_2015], width, hatch = '//', color=MyColorCycle_10Reg[m//2,:], 
        label = Def_RegionsNames_agg[m//2], bottom = Stock_Region_2015_use_loss_a[0:m,ScenSel_2015].sum(axis=0), linewidth = 0.0)
        ProxyHandlesList.append(plt.Rectangle((0, 0), 1, 1, fc=MyColorCycle_10Reg[m//2,:])) # create proxy artist for legend
    else:
        p1 = plt.bar(ind[0:len(ScenSel_2015)], Stock_Region_2015_use_loss_a[m,ScenSel_2015], width, color=MyColorCycle_10Reg[(m -1)//2,:], 
        label = Def_RegionsNames_agg[(m -1)//2], bottom = Stock_Region_2015_use_loss_a[0:m,ScenSel_2015].sum(axis=0), linewidth = 0.0)        
        
    if m % 2 == 0:
        p1 = plt.bar(ind[len(ScenSel_2015)+1:len(ScenSel_2015)+1 + len(ScenSel_2050)], Stock_Region_2050_use_loss_a[m,ScenSel_2050], width, hatch = '//', color=MyColorCycle_10Reg[m//2,:], 
        label = Def_RegionsNames_agg[m//2], bottom = Stock_Region_2050_use_loss_a[0:m,ScenSel_2050].sum(axis=0), linewidth = 0.0)
    else:
        p1 = plt.bar(ind[len(ScenSel_2015)+1:len(ScenSel_2015)+1 + len(ScenSel_2050)], Stock_Region_2050_use_loss_a[m,ScenSel_2050], width, color=MyColorCycle_10Reg[(m -1)//2,:], 
        label = Def_RegionsNames_agg[(m -1)//2], bottom = Stock_Region_2050_use_loss_a[0:m,ScenSel_2050].sum(axis=0), linewidth = 0.0)
               
    if m % 2 == 0:
        p1 = plt.bar(ind[len(ScenSel_2015)+1 + len(ScenSel_2050) +1 ::], Stock_Region_2100_use_loss_a[m,ScenSel_2100], width, hatch = '//', color=MyColorCycle_10Reg[m//2,:], 
        label = Def_RegionsNames_agg[m//2], bottom = Stock_Region_2100_use_loss_a[0:m,ScenSel_2100].sum(axis=0), linewidth = 0.0)
    else:
        p1 = plt.bar(ind[len(ScenSel_2015)+1 + len(ScenSel_2050) +1 ::], Stock_Region_2100_use_loss_a[m,ScenSel_2100], width, color=MyColorCycle_10Reg[(m -1)//2,:], 
        label = Def_RegionsNames_agg[(m -1)//2], bottom = Stock_Region_2100_use_loss_a[0:m,ScenSel_2100].sum(axis=0), linewidth = 0.0)
        # plot horizontal bar boundary
        
for xx in xticks:
    plt.plot([xx - 0.2, xx - 0.2], [0,1], color='k', linestyle='-', linewidth = Gen_Linewidth)    
    plt.plot([xx + 0.2, xx + 0.2], [0,1], color='k', linestyle='-', linewidth = Gen_Linewidth)    
    
for xx in range(0,len(ScenSel_2015)):
    for yy in range(0,10):
        plt.plot([xx/2, xx/2 + 0.4], [Stock_Region_2015_use_loss_a[0:2*yy,ScenSel_2015[xx]].sum(axis=0), Stock_Region_2015_use_loss_a[0:2*yy,ScenSel_2015[xx]].sum(axis=0)], color='k', linestyle='-', linewidth = Gen_Linewidth)    

for xx in range(0,len(ScenSel_2050)):
    for yy in range(0,10):
        plt.plot([len(ScenSel_2015)/2 + 0.5 + xx/2, len(ScenSel_2015)/2 + 0.5 + xx/2 + 0.4], [Stock_Region_2050_use_loss_a[0:2*yy,ScenSel_2050[xx]].sum(axis=0), Stock_Region_2050_use_loss_a[0:2*yy,ScenSel_2050[xx]].sum(axis=0)], color='k', linestyle='-', linewidth = Gen_Linewidth)    

for xx in range(0,len(ScenSel_2100)):
    for yy in range(0,10):
        plt.plot([len(ScenSel_2015)/2 + 0.5 + len(ScenSel_2050)/2 + 0.5 + xx/2, len(ScenSel_2015)/2 + 0.5 + len(ScenSel_2050)/2 + 0.5 + xx/2 + 0.4], [Stock_Region_2100_use_loss_a[0:2*yy,ScenSel_2100[xx]].sum(axis=0), Stock_Region_2100_use_loss_a[0:2*yy,ScenSel_2100[xx]].sum(axis=0)], color='k', linestyle='-', linewidth = Gen_Linewidth)    
    
# add hatch to legend
ProxyHandlesList.insert(0,plt.Rectangle((0, 0), 1, 1, fc='w', hatch = '//')) # create proxy artist for legend  
Def_RegionsNames_agg.insert(0,'Losses')
                 
plt_lgd  = plt.legend(reversed(ProxyHandlesList),reversed(Def_RegionsNames_agg),shadow = False, prop={'size':9.0},loc='upper left', bbox_to_anchor=(1.02, 1))                     

axs[1].set_ylim([     0, 1.10])
axs[1].set_xlim([     -0.1, ind.max() + 0.6])
axs[1].set_ylabel('Total steel in system, %', fontsize =15)
axs[1].set_yticks(np.arange(0,1.01,0.2))
axs[1].set_yticklabels(['0','20','40','60','80','100'], fontsize =15)
axs[1].set_xlabel('Scenario name', fontsize =15)
axs[1].set_xticks(xticks)
axs[1].set_xticklabels(xticklabels_flat, fontsize =10, rotation = 90)
axs[1].text(0.25 * (len(ScenSel_2015)) - 0.25, 1.03, '2015', fontsize=10, fontweight='bold') #alternative fontweight: bold
axs[1].text(0.50 * (len(ScenSel_2015) +1) +0.25 * len(ScenSel_2050) - 0.25, 1.03, '2050', fontsize=10, fontweight='bold') #alternative fontweight: bold
axs[1].text(0.50 * (len(ScenSel_2015) +1 +len(ScenSel_2050) +1)  + 0.25 * len(ScenSel_2100) - 0.25, 1.03, '2100', fontsize=10, fontweight='bold') #alternative fontweight: bold

plt.show()

fig.savefig(Path_Result + fig_name, dpi = 400,bbox_extra_artists=(plt_lgd,), bbox_inches='tight') 
# include figure in logfile:
Mylog.info('<center><img src="'+ fig_name +'" width="857" height="600" alt="'+ fig_name +'"></center>')
Mylog.info('<font "size=+3"><center><b><i>Figure '+ str(Figurecounter) + ': '+ fig_name +'.</i></b></center></font><br>')
Figurecounter += 1 
                       
#%%
"""
End script
""" 
Mylog.info('Script is finished. Terminating logging process and closing all log files.<br>')
Time_End = time.time()
Time_Duration = Time_End - Time_Start
Mylog.info('<font "size=+4"> <b>End of simulation: ' + time.asctime() + '.</b></font><br>')
Mylog.info('<font "size=+4"> <b>Duration of simulation: %.1f seconds.</b></font><br>' % Time_Duration)
logging.shutdown()
# remove all handlers from logger
root = logging.getLogger()
root.handlers = [] # required if you don't want to exit the shell
#
#
# The End
#%%
# -*- coding: utf-8 -*-
"""
Created on Thur June 18, 2015
Last modified: April, 2016

@author: pauliuk
"""

"""
# Script MaTrace_Global_Main.py

# Standalone script for global multiregional version of MaTrace model (Nakamura et al. 2014)
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
Path_Result        = Project_ResultPath + Name_Scenario + '_' + TimeString + '\\'

# Read control and selection parameters into dictionary
ScriptConfig = {'Scenario_Description': Project_Configsheet.cell_value(6,2)}
ScriptConfig['Scenario Name'] = Name_Scenario
for m in range(9,22): # add all defined control parameters to dictionary
    try:
        ScriptConfig[Project_Configsheet.cell_value(m,1)] = np.int(Project_Configsheet.cell_value(m,2))
    except:
        ScriptConfig[Project_Configsheet.cell_value(m,1)] = str(Project_Configsheet.cell_value(m,2))
        
ScriptConfig['Current_UUID'] = str(uuid.uuid4())

# Create scenario folder
ensure_dir(Path_Result)
#Copy script and Config file into that folder
shutil.copy(Project_DataFilePath, Path_Result + Project_DataFileName)
shutil.copy(Project_MainPath + 'Scripts\\MaTrace_Global_Main.py', Path_Result + 'MaTrace_Global_Main.py')
# Initialize logger    
[Mylog,console_log,file_log] = function_logger(logging.DEBUG, Name_Scenario + '_' + TimeString, Path_Result, logging.DEBUG) 

# log header and general information
Mylog.info('<html>\n<head>\n</head>\n<body bgcolor="#ffffff">\n<br>')
Mylog.info('<font "size=+5"><center><b>Script ' + 'MaTrace_Global_Main' + '.py</b></center></font>')
Mylog.info('<font "size=+5"><center><b>Version: 2016-02-17 or later.</b></center></font>')
Mylog.info('<font "size=+4"> <b>Current User: ' + Name_User + '.</b></font><br>')
Mylog.info('<font "size=+4"> <b>Current Path: ' + Project_MainPath + '.</b></font><br>')
Mylog.info('<font "size=+4"> <b>Current Scenario: ' + Name_Scenario + '.</b></font><br>')
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

Par_Time = [] # Time vector of the model, unit: year
for m in range(19,105):
    Par_Time.append(np.int(Project_Datasheet.cell_value(m,1)))
    
Par_Tau = np.zeros((Par_NoOfRegions,Par_NoOfProducts)) # Mean lifetime array, region by product, unit: year
for m in range(0,Par_NoOfRegions):
    for n in range(0,Par_NoOfProducts):
        Par_Tau[m,n] = Project_Datasheet.cell_value(m +4,n +4)

# increase lifetime if lifetime flag is set:
if ScriptConfig['Lifetime extension 30%'] == 'yes':
    Par_Tau = 1.3 * Par_Tau
        
Par_Sigma = 0.3 * Par_Tau # Standard deviation of lifetime array, region by product, unit: year       

Mylog.info('Define lifetime distribution.<br>')
MaTrace_pdf = np.zeros((Par_NoOfYears,Par_NoOfYears,Par_NoOfRegions,Par_NoOfProducts)) # Par: pdf
AgeMatrix   = np.zeros((Par_NoOfYears,Par_NoOfYears))
for c in range(0, Par_NoOfYears):  # cohort index
    for y in range(c + 1, Par_NoOfYears):
        AgeMatrix[y,c] = y-c
for R in range(0,Par_NoOfRegions):
    for P in range(0,Par_NoOfProducts):
        MaTrace_pdf[:,:,R,P] = scipy.stats.norm(Par_Tau[R,P], Par_Sigma[R,P]).pdf(AgeMatrix)  # Call scipy's Norm function with Mean, StdDev, and Age
# No discard in historic years and year 0:
for m in range(0,Par_NoOfYears):
    MaTrace_pdf[0:m+1,m,:,:] = 0

Mylog.info('Read and format parameters for obsolete products and waste management industries.<br>')
Par_Omega_ObsoleteStocks = np.zeros((Par_NoOfYears,Par_NoOfRegions,Par_NoOfProducts)) # Par: Ω
for m in range(0,Par_NoOfYears):
    for n in range(0,Par_NoOfRegions):
        for o in range(0,Par_NoOfProducts):
            Par_Omega_ObsoleteStocks[m,n,o] = Project_Datasheet.cell_value(5 + 29*o,n +16)

Par_E_EoL_Product_Trade_Static = np.zeros((Par_NoOfProducts,Par_NoOfRegions,Par_NoOfRegions)) # Par: E, Static (no time dimension) shares of EoL product fate, by product, region of obsolescene, and target region.
for m in range(0,Par_NoOfProducts):
    for n in range(0,Par_NoOfRegions):
        for o in range(0,Par_NoOfRegions):
            Par_E_EoL_Product_Trade_Static[m,n,o] = Project_Datasheet.cell_value(o +6 + 29*m,n +16)
            
Par_EComplement_EoL_Treatment_Share_Static = np.zeros((Par_NoOfProducts,Par_NoOfRegions)) # Par: J-Ω-E. Shares of EoL product flows to waste management industries, by product and region of obsolescene
for m in range(0,Par_NoOfProducts):
    for n in range(0,Par_NoOfRegions):
        Par_EComplement_EoL_Treatment_Share_Static[m,n] = Project_Datasheet.cell_value(4 + 29*m,n +16)
              
# Choose more ambitious EoL recovery efficiency (Γ) if EoL flag is set:
Par_Gamma_EoL_Recovery_Efficiency_Steel = np.zeros((Par_NoOfYears,Par_NoOfRegions,Par_NoOfProducts))        
if ScriptConfig['End-of-life recovery rate'] == 'Basic':       
    for m in range(0,Par_NoOfYears):
        for n in range(0,Par_NoOfProducts):
            Par_Gamma_EoL_Recovery_Efficiency_Steel[m,:,n] = Project_Datasheet.cell_value(m + 19,n +43)

if ScriptConfig['End-of-life recovery rate'] == 'Improve':       
    for m in range(0,Par_NoOfYears):
        for n in range(0,Par_NoOfProducts):
            Par_Gamma_EoL_Recovery_Efficiency_Steel[m,:,n] = Project_Datasheet.cell_value(m + 19,n +55)
#Note: EoL scrap is old scrap, that is why there is no explicit scrap index here. This will be introduced later, for the vector version of flow F_3_4 and F_7_4.            
            
Mylog.info('Read and format parameters for scrap trade and refining.<br>')        
Par_B_ScrapToRecycling = np.zeros((Par_NoOfRegions*Par_NoOfSecMetals,Par_NoOfRegions*Par_NoOfScraps)) # Par: B. rows: outer index: refinement process, inner index: destination region. columns: outer index: scrap type, inner index: origin region.
for m in range(0,Par_NoOfRegions):
    for n in range(0,Par_NoOfRegions):
        Par_B_ScrapToRecycling[n,m] = Project_Datasheet.cell_value(m + 4,n +67) # new scrap is traded to BOF recyclers, transpose from Excel sheet!
if ScriptConfig['Process route'] == 'BOF': # old scrap is traded to BOF recyclers
    for m in range(0,Par_NoOfRegions):
        for n in range(0,Par_NoOfRegions):
            Par_B_ScrapToRecycling[n,m +25] = Project_Datasheet.cell_value(m + 4,n +67) # transpose from Excel sheet!
if ScriptConfig['Process route'] == 'EAF': # old scrap is traded to EAF recyclers
    for m in range(0,Par_NoOfRegions):
        for n in range(0,Par_NoOfRegions):
            Par_B_ScrapToRecycling[n +25,m +25] = Project_Datasheet.cell_value(m + 4,n +67) # transpose from Excel sheet!            

Par_Theta_RemeltingYield = np.zeros((Par_NoOfRegions*Par_NoOfSecMetals,Par_NoOfRegions*Par_NoOfSecMetals)) # Par: Theta. Diagonal matrix rows and columns have the same meaning: outer index: refinement process, inner index: region.
if ScriptConfig['RemeltingYield'] == 'Basic':
    for m in range(0,25):
        Par_Theta_RemeltingYield[m,m]         = Project_Datasheet.cell_value(4,99)
        Par_Theta_RemeltingYield[m +25,m +25] = Project_Datasheet.cell_value(4,98)
if ScriptConfig['RemeltingYield'] == 'Improve':
    for m in range(0,25):
        Par_Theta_RemeltingYield[m,m]         = Project_Datasheet.cell_value(6,99)
        Par_Theta_RemeltingYield[m +25,m +25] = Project_Datasheet.cell_value(6,98)

Mylog.info('Read and format parameters for manufacturing.<br>')                
Par_D_AllocationSteelToProducts = np.zeros((Par_NoOfYears,Par_NoOfRegions * Par_NoOfProducts,Par_NoOfSecMetals * Par_NoOfRegions)) # This is the D-matrix

if ScriptConfig['Sector split select'] == 'BOF_EAF_static': # Use D calculated from CREEA data disaggregated with Info from the Japanese IOT.
    # Read C matrices and y vector
    C_mp_BOF_transpose = np.zeros((Par_NoOfRegions * Par_NoOfProducts, Par_NoOfRegions))
    C_mp_EAF_transpose = np.zeros((Par_NoOfRegions * Par_NoOfProducts, Par_NoOfRegions))
    for m in range(0,Par_NoOfProducts): # product index
        for n in range(0,Par_NoOfRegions): # destination region index
            for o in range(0,Par_NoOfRegions): # origin region index
                C_mp_BOF_transpose[n * Par_NoOfProducts +m, o] = Project_Datasheet.cell_value(n * Par_NoOfProducts +m +4, o +210)
                C_mp_EAF_transpose[n * Par_NoOfProducts +m, o] = Project_Datasheet.cell_value(n * Par_NoOfProducts +m +4, o +235)
                
    Y_Total_Agg = np.zeros(250)
    for m in range(0,Par_NoOfProducts): # product index
        for n in range(0,Par_NoOfRegions): # consumption region index               
            Y_Total_Agg[n * Par_NoOfProducts +m] = Project_Datasheet.cell_value(n * Par_NoOfProducts +m +4, 261)

    TotalMat =  Y_Total_Agg.transpose().dot(C_mp_BOF_transpose)
    TotalMat_inv = np.linalg.inv(np.diag(TotalMat))    
    D_BOF = np.diag(Y_Total_Agg).dot(C_mp_BOF_transpose.dot(TotalMat_inv))
    D_BOF_Check = D_BOF.sum(axis =0) # must be all 1, mass balance of distribution  
    
    TotalMat =  Y_Total_Agg.transpose().dot(C_mp_EAF_transpose)
    TotalMat_inv = np.linalg.inv(np.diag(TotalMat))    
    D_EAF = np.diag(Y_Total_Agg).dot(C_mp_EAF_transpose.dot(TotalMat_inv))
    D_EAF_Check = D_EAF.sum(axis =0) # must be all 1, mass balance of distribution  
    
    for m in range(0,Par_NoOfYears):
        Par_D_AllocationSteelToProducts[m,:,0:Par_NoOfRegions] = D_BOF
        Par_D_AllocationSteelToProducts[m,:,Par_NoOfRegions::] = D_EAF
            
if ScriptConfig['Sector split select'] == 'BOF_EAF_dynamic': # Use D calculated from CREEA data disaggregated with Info from the Japanese IOT. Recalculate D to build time series D(t) using the raw data C and Y(t) on the separate sheet Parameter_Original
    # Read C matrices and y vector for base year (2007)
    C_mp_BOF_transpose = np.zeros((Par_NoOfRegions * Par_NoOfProducts, Par_NoOfRegions))
    C_mp_EAF_transpose = np.zeros((Par_NoOfRegions * Par_NoOfProducts, Par_NoOfRegions))
    for m in range(0,Par_NoOfProducts): # product index
        for n in range(0,Par_NoOfRegions): # destination region index
            for o in range(0,Par_NoOfRegions): # origin region index
                C_mp_BOF_transpose[n * Par_NoOfProducts +m, o] = Project_Datasheet.cell_value(n * Par_NoOfProducts +m +4, o +210)
                C_mp_EAF_transpose[n * Par_NoOfProducts +m, o] = Project_Datasheet.cell_value(n * Par_NoOfProducts +m +4, o +235)
                
    Y_Total_Agg = np.zeros(Par_NoOfRegions * Par_NoOfProducts)
    for m in range(0,Par_NoOfProducts): # product index
        for n in range(0,Par_NoOfRegions): # consumption region index               
            Y_Total_Agg[n * Par_NoOfProducts +m] = Project_Datasheet.cell_value(n * Par_NoOfProducts +m +4, 261)


    Y_GrowthRates = np.zeros((Par_NoOfYears +15,Par_NoOfRegions))
    for m in range(0,Par_NoOfYears +15): # time index
        for n in range(0,Par_NoOfRegions): # consumption region index               
            Y_GrowthRates[m,n] = Project_Datasheet.cell_value(m +4, 264 + n)
    
    # Determine growth before 2015, start in 2007:
    Y_Total_Agg_TimeSeries = np.zeros((Par_NoOfRegions * Par_NoOfProducts,Par_NoOfYears + 9))
    Y_Total_Agg_TimeSeries[:,0] = Y_Total_Agg
    for m in range(1,8):
        for n in range(0,Par_NoOfRegions):
            Y_Total_Agg_TimeSeries[n:n*Par_NoOfProducts + Par_NoOfProducts,m] = Y_Total_Agg_TimeSeries[n:n*Par_NoOfProducts + Par_NoOfProducts,m -1] * Y_GrowthRates[m +7,n]
    
    for m in range(0,Par_NoOfYears):
        for n in range(0,Par_NoOfRegions):
            Y_Total_Agg_TimeSeries[n:n*Par_NoOfProducts + Par_NoOfProducts,m +8] = Y_Total_Agg_TimeSeries[n:n*Par_NoOfProducts + Par_NoOfProducts,m +8 -1] * Y_GrowthRates[m +15,n]
        Y_Total_ThisYear = Y_Total_Agg_TimeSeries[:,m +8]
        TotalMat =  Y_Total_ThisYear.transpose().dot(C_mp_BOF_transpose)
        TotalMat_inv = np.linalg.inv(np.diag(TotalMat))    
        D_BOF = np.diag(Y_Total_ThisYear).dot(C_mp_BOF_transpose.dot(TotalMat_inv))
        D_BOF_Check = D_BOF.sum(axis =0) # must be all 1, mass balance of distribution  
        
        TotalMat =  Y_Total_ThisYear.transpose().dot(C_mp_EAF_transpose)
        TotalMat_inv = np.linalg.inv(np.diag(TotalMat))    
        D_EAF = np.diag(Y_Total_ThisYear).dot(C_mp_EAF_transpose.dot(TotalMat_inv))
        D_EAF_Check = D_EAF.sum(axis =0) # must be all 1, mass balance of distribution  

        Par_D_AllocationSteelToProducts[m,:,0:Par_NoOfRegions] = D_BOF
        Par_D_AllocationSteelToProducts[m,:,Par_NoOfRegions::] = D_EAF
        
if ScriptConfig['Sector split select'] == 'AverageSteel_static': # Use static D, Sector split from CREEA MRIO table, plus all secondary steel going into construction
    for m in range(0,Par_NoOfProducts): # product index
        for n in range(0,Par_NoOfRegions): # destination region index
            for o in range(0,Par_NoOfRegions): # origin region index
                for p in range(0, Par_NoOfSecMetals): # secondary metal type index
                    Par_D_AllocationSteelToProducts[:,n * Par_NoOfProducts +m, p * Par_NoOfRegions +o] = Project_Datasheet.cell_value(n * Par_NoOfProducts +m +4, p * Par_NoOfRegions +o +103)

Par_Lambda_FabricationYield = np.zeros((Par_NoOfYears,Par_NoOfProducts * Par_NoOfRegions,Par_NoOfProducts * Par_NoOfRegions))
if ScriptConfig['Fabrication yield loss'] == 'Basic': # Lambda is a diagonal matrix
    for tt in range(0,Par_NoOfYears):
        for m in range(0,Par_NoOfProducts): # product index
            for n in range(0,Par_NoOfRegions): # region index
                Par_Lambda_FabricationYield[tt,n * Par_NoOfProducts +m,n * Par_NoOfProducts +m] = Project_Datasheet.cell_value(n + 4,m +155)
if ScriptConfig['Fabrication yield loss'] == 'Improve': # Lambda is a diagonal matrix
    for tt in range(0,Par_NoOfYears):
        if tt <=35:
            for m in range(0,Par_NoOfProducts): # product index
                for n in range(0,Par_NoOfRegions): # region index
                    Par_Lambda_FabricationYield[tt,n * Par_NoOfProducts +m,n * Par_NoOfProducts +m] = Project_Datasheet.cell_value(n + 4,m +155) + tt/35 * (Project_Datasheet.cell_value(n + 33,m +155) - Project_Datasheet.cell_value(n + 4,m +155))
        if tt >35:
            for m in range(0,Par_NoOfProducts): # product index
                for n in range(0,Par_NoOfRegions): # region index
                    Par_Lambda_FabricationYield[tt,n * Par_NoOfProducts +m,n * Par_NoOfProducts +m] = Project_Datasheet.cell_value(n + 33,m +155)
                
                
Par_Xi_FabricationYieldLossRecovery            = np.zeros((Par_NoOfYears,Par_NoOfScraps * Par_NoOfRegions,Par_NoOfRegions * Par_NoOfProducts))
Par_Xi_FabricationYieldLossRecovery_complement = np.zeros((Par_NoOfYears,Par_NoOfScraps * Par_NoOfRegions,Par_NoOfRegions * Par_NoOfProducts))
if ScriptConfig['Fabrication scrap recovery rate'] == 'Basic': # Only the upper part (for new scrap) is filled
    for tt in range(0,Par_NoOfYears):    
        for m in range(0,Par_NoOfProducts):
            for n in range(0,Par_NoOfRegions):
                Par_Xi_FabricationYieldLossRecovery[tt,n,n * Par_NoOfProducts + m]            = Project_Datasheet.cell_value(n + 4,m +167)
                Par_Xi_FabricationYieldLossRecovery_complement[tt,n,n * Par_NoOfProducts + m] = 1 - Project_Datasheet.cell_value(n + 4,m +167)

if ScriptConfig['Fabrication scrap recovery rate'] == 'Improve': # Only the upper part (for new scrap) is filled
    for tt in range(0,Par_NoOfYears):  
        if tt <=35:
            for m in range(0,Par_NoOfProducts):
                for n in range(0,Par_NoOfRegions):
                    Par_Xi_FabricationYieldLossRecovery[tt,n,n * Par_NoOfProducts + m]            = Project_Datasheet.cell_value(n + 4,m +167) + tt/35 * (Project_Datasheet.cell_value(n + 33,m +167) - Project_Datasheet.cell_value(n + 4,m +167))
                    Par_Xi_FabricationYieldLossRecovery_complement[tt,n,n * Par_NoOfProducts + m] = 1 - Project_Datasheet.cell_value(n + 4,m +167) - tt/35 * (Project_Datasheet.cell_value(n + 33,m +167) - Project_Datasheet.cell_value(n + 4,m +167))
        if tt >35:
            for m in range(0,Par_NoOfProducts):
                for n in range(0,Par_NoOfRegions):
                    Par_Xi_FabricationYieldLossRecovery[tt,n,n * Par_NoOfProducts + m]            = Project_Datasheet.cell_value(n + 33,m +167)
                    Par_Xi_FabricationYieldLossRecovery_complement[tt,n,n * Par_NoOfProducts + m] = 1 - Project_Datasheet.cell_value(n + 33,m +167)
            
Mylog.info('Read and format parameters for trade of finished products.<br>')        
Par_M_FinishedProductsTradeShares_Static = np.zeros((Par_NoOfRegions * Par_NoOfProducts,Par_NoOfRegions * Par_NoOfProducts))
for m in range(0,Par_NoOfProducts): # product index
    for n in range(0,Par_NoOfRegions): # destination region index
        for o in range(0,Par_NoOfRegions): # origin region index
            Par_M_FinishedProductsTradeShares_Static[n * Par_NoOfProducts +m,o * Par_NoOfProducts +m] = Project_Datasheet.cell_value(o * Par_NoOfProducts +m +4, n+180)
        
        

Mylog.info('Check whether trade remove parameter is set and collapse trade flows in exisiting parameters.')        
if ScriptConfig['Trade_remove'].find('E') != -1: # if 'E' appears in the control parameter
    Par_E_EoL_Product_Trade_Static = np.zeros((Par_NoOfProducts,Par_NoOfRegions,Par_NoOfRegions)) # no trade of EoL products
    Par_EComplement_EoL_Treatment_Share_Static = 1 - Par_Omega_ObsoleteStocks[0,:,:].transpose() # All EoL products that do not accumulate as obsolete stocks are sent to DOMESTIC treatment/srap recovery

if ScriptConfig['Trade_remove'].find('B') != -1: # if 'B' appears in the control parameter
    Par_B_ScrapToRecycling = np.zeros((Par_NoOfRegions*Par_NoOfSecMetals,Par_NoOfRegions*Par_NoOfScraps)) # Par: B. rows: outer index: refinement process, inner index: destination region. columns: outer index: scrap type, inner index: origin region.
    Par_B_ScrapToRecycling[0:Par_NoOfRegions,0:Par_NoOfRegions] = np.eye(Par_NoOfRegions) # All fabrication scrap allocated to BOF route, no trade.
    if ScriptConfig['Process route'] == 'BOF': # old scrap is traded to BOF recyclers
        Par_B_ScrapToRecycling[0:Par_NoOfRegions,Par_NoOfRegions::] = np.eye(Par_NoOfRegions) # All post-consumer scrap allocated to BOF route, no trade.
    if ScriptConfig['Process route'] == 'EAF': # old scrap is traded to EAF recyclers
        Par_B_ScrapToRecycling[Par_NoOfRegions::,Par_NoOfRegions::] = np.eye(Par_NoOfRegions) # All post-consumer scrap allocated to EAF route, no trade.
        
if ScriptConfig['Trade_remove'].find('D') != -1: # if 'D' appears in the control parameter
    for Thisyear in range(0,Par_NoOfYears):
        for Origin in range (0,Par_NoOfRegions):
            for Destination in range(0,Par_NoOfRegions):
                if Origin != Destination:
                    # add all allocation to foreign regions to domestic region, remove allocation to foreign regions. For BOF steel.
                    Par_D_AllocationSteelToProducts[Thisyear,Origin * Par_NoOfProducts:Origin * Par_NoOfProducts + Par_NoOfProducts, Origin] = Par_D_AllocationSteelToProducts[Thisyear,Origin * Par_NoOfProducts:Origin * Par_NoOfProducts + Par_NoOfProducts, Origin] + Par_D_AllocationSteelToProducts[Thisyear,Destination * Par_NoOfProducts:Destination * Par_NoOfProducts + Par_NoOfProducts, Origin]
                    Par_D_AllocationSteelToProducts[Thisyear,Destination * Par_NoOfProducts:Destination * Par_NoOfProducts + Par_NoOfProducts, Origin] = 0
                    # add all allocation to foreign regions to domestic region, remove allocation to foreign regions. For EAF steel.
                    Par_D_AllocationSteelToProducts[Thisyear,Origin * Par_NoOfProducts:Origin * Par_NoOfProducts + Par_NoOfProducts, Origin + Par_NoOfRegions] = Par_D_AllocationSteelToProducts[Thisyear,Origin * Par_NoOfProducts:Origin * Par_NoOfProducts + Par_NoOfProducts, Origin + Par_NoOfRegions] + Par_D_AllocationSteelToProducts[Thisyear,Destination * Par_NoOfProducts:Destination * Par_NoOfProducts + Par_NoOfProducts, Origin + Par_NoOfRegions]
                    Par_D_AllocationSteelToProducts[Thisyear,Destination * Par_NoOfProducts:Destination * Par_NoOfProducts + Par_NoOfProducts, Origin + Par_NoOfRegions] = 0

if ScriptConfig['Trade_remove'].find('M') != -1: # if 'M' appears in the control parameter
    Par_M_FinishedProductsTradeShares_Static = np.eye((Par_NoOfRegions * Par_NoOfProducts))
    
#%%        
Mylog.info('Define system variables.<br>')
# Define external input vector F_0_8(t,r,p):
F_0_8  = np.zeros((Par_NoOfYears,Par_NoOfRegions,Par_NoOfProducts))
# Define final consumption vector F_8_1(t,r,p):
F_8_1  = np.zeros((Par_NoOfYears,Par_NoOfRegions,Par_NoOfProducts))
# Define flow of obsolete steel F_y(t,r,p) (internal flow, not visible in system definition!):
F_y    = np.zeros((Par_NoOfYears,Par_NoOfRegions,Par_NoOfProducts))
# Define addition to obsolete stocks, F_1_1a(t,r,p):
F_1_1a = np.zeros((Par_NoOfYears,Par_NoOfRegions,Par_NoOfProducts))
# Define flow of obsolete products from use phase to market for EoL products, F_1_2(t,r,p):
F_1_2  = np.zeros((Par_NoOfYears,Par_NoOfRegions,Par_NoOfProducts))
# Define flow of exports for re-use, to be inserted into stocks in other regions, F_2_8(t,r,p):
F_2_8  = np.zeros((Par_NoOfYears,Par_NoOfRegions,Par_NoOfRegions,Par_NoOfProducts))
# Define flow of domestic EoL products treatment, F_2_3(t,r,p):
F_2_3  = np.zeros((Par_NoOfYears,Par_NoOfRegions,Par_NoOfProducts)) 
# Define flow of recovery losses to landfills, F_3_3a(t,r,p):
F_3_3a = np.zeros((Par_NoOfYears,Par_NoOfRegions,Par_NoOfProducts)) 
# Define flow of (old) scrap from EoL treatment to scrap market, F_3_4(t,[s,r]): # NOTE: For every year t, this variable is a column vector with outer index s and inner index r.
F_3_4  = np.zeros((Par_NoOfYears,Par_NoOfRegions*Par_NoOfScraps)) 

# The flow F_3_4 is the driver of the recycling loop, for which we now define the variables:
#Define flow of total material for remelting, by remelting route and region, F_4_5(t,[m,r]):
F_4_5  = np.zeros((Par_NoOfYears,Par_NoOfSecMetals * Par_NoOfRegions))
#Define flow of total material lost during remelting, by producer and region, F_5_5a(t,[m,r]):
F_5_5a = np.zeros((Par_NoOfYears,Par_NoOfSecMetals * Par_NoOfRegions)) 
#Define flow of total remelted material, by producer and region, F_5_6(t,[m,r]):
F_5_6  = np.zeros((Par_NoOfYears,Par_NoOfSecMetals * Par_NoOfRegions)) 
#Define flow of total secondary material consumed, F_6_7(t,[m,r]):
F_6_7  = np.zeros((Par_NoOfYears,Par_NoOfProducts * Par_NoOfRegions)) 
#Define flow of losses during  manufacturing, F_7_7a(t,[m,r]):
F_7_7a = np.zeros((Par_NoOfYears,Par_NoOfSecMetals * Par_NoOfRegions)) 
# Define fabrication scrap, f_7_4(t,[s,r])
F_7_4  = np.zeros((Par_NoOfYears,Par_NoOfScraps*Par_NoOfRegions)) 

# Define flow of steel in recycled products, by producing region, F_7_8(t,[r,p]):
F_7_8  = np.zeros((Par_NoOfYears,Par_NoOfRegions * Par_NoOfProducts)) 


# Define stocks
# In use stock
S_1  = np.zeros((Par_NoOfYears,Par_NoOfRegions,Par_NoOfProducts))
# Obsolete stock
S_1a = np.zeros((Par_NoOfYears,Par_NoOfRegions,Par_NoOfProducts))
# Recovery loss stock (landfills)
S_3a = np.zeros((Par_NoOfYears,Par_NoOfRegions,Par_NoOfProducts))
# Remelting loss stock (landfills)
S_5a = np.zeros((Par_NoOfYears,Par_NoOfSecMetals * Par_NoOfRegions))
# Fabrication loss stock (landfills)
S_7a = np.zeros((Par_NoOfYears,Par_NoOfSecMetals * Par_NoOfRegions))
# Total amount of steel in the system
S_Tot = np.zeros(Par_NoOfYears)

# Define process balances
# Define Balance of use phase
Bal_1                = np.zeros((Par_NoOfYears,Par_NoOfRegions,Par_NoOfProducts))
# Define Balance of EoL flows
Bal_ObsoleteProducts = np.zeros((Par_NoOfYears,Par_NoOfRegions,Par_NoOfProducts))
# Define Balance of Waste management industries:
Bal_3                = np.zeros((Par_NoOfYears,Par_NoOfRegions))
# Define Balance of the remelting industries
Bal_5                = np.zeros((Par_NoOfYears,Par_NoOfSecMetals * Par_NoOfRegions))
# Define Balance of the fabrication sectors:
Bal_7                = np.zeros((Par_NoOfYears,Par_NoOfRegions))

# Define market balances
#Define Balance of Final products market
Bal_8    = np.zeros((Par_NoOfYears,Par_NoOfProducts))
#Define Balance of EoL products market
Bal_2    = np.zeros((Par_NoOfYears,Par_NoOfProducts))
#Define balance of scrap markets
Bal_4    = np.zeros((Par_NoOfYears,1))
#Define balance of material markets
Bal_6    = np.zeros((Par_NoOfYears,1))

#Define system-wide mass balance:
Bal_System           = np.zeros(Par_NoOfYears)

#%%
"""
Perform calculations
""" 
Mylog.info('<p><b>Performing model calculations.</b></p>')
if ScriptConfig['Modus'] == 'Trace single product': # this is the only modus currently implemented
    if ScriptConfig['TestProduct'] == 'Car':
        PI =  6 # index for cars
    if ScriptConfig['TestProduct'] == 'Building':
        PI =  9 # index for buildings
    if ScriptConfig['TestProduct'] == 'Machine':
        PI =  1 # index for machine    
    if ScriptConfig['TestProduct'] == 'ElMachine':
        PI =  3 # index for electrical machinery      
    CI = ScriptConfig['Country of discard'] -1 # index for country
    SY = ScriptConfig['StartYear no.'] -2015 # index for start year
    EY = ScriptConfig['Time horizon']  -2015 # index for start year
    Mylog.info('<p>Modus: Trace fate of single product.</p>')
    Mylog.info('<p>Tracing fate of a ton of steel in ' + Def_ProductShortNames[PI] + ' in ' + Def_RegionsNames[CI] + ' starting in year ' + str(Par_Time[SY]) + ', ending in year ' + str(Par_Time[EY]) + '.</p>')
    # initialize x in the start year:
    F_0_8[SY,CI,PI] = 1

    # perform a year-by-year computation of the outflow, recycling, and inflow
    Mylog.info('<p>MaTrace global was successfully initialized. Starting to calculate the future material distribution.</p>')
    for CY in range(0,EY+1): # CY stands for 'current year'
        Mylog.info('<p>Performing calculations for year ' + str(Par_Time[CY]) + '.</p>')

        Mylog.info('Step 1: Determine flow of steel in obsolete products from historic inflow.<br>')
        # Use dynamic stock model, determine outflow as convolution.    
        for m in range(0,Par_NoOfRegions):
            for n in range(0,Par_NoOfProducts):
                # Use MaTrace_pdf to determine convolution of historic inflow with lifetime distribution
                F_y[CY,m,n] = (F_8_1[0:CY,m,n] * MaTrace_pdf[CY,0:CY,m,n]).sum()
                #Outflow in CY= hist. inflow until CY element-wise multiplied with probability of discard in year CY

        Mylog.info('Step 2: Obsolete stocks, trade of obsolete products, and material sent to the waste management industries.<br>')
        # Determine obsolete stocks:
        F_1_1a[CY,:,:] = F_y[CY,:,:] * Par_Omega_ObsoleteStocks[CY,:,:]
        # Determine export for re-use:
        F_2_8[CY,:,:,:] = np.tile(np.expand_dims(F_y[CY,:,:],axis =1),(1,25,1)) * Par_E_EoL_Product_Trade_Static.transpose(1,2,0) 
        # Determine domestic treatment
        F_2_3[CY,:,:]  = F_y[CY,:,:] * Par_EComplement_EoL_Treatment_Share_Static.transpose()
        # Determine mass balance of market for obsolete products
        Bal_ObsoleteProducts[CY,:,:] = F_y[CY,:,:] - F_1_1a[CY,:,:] - F_2_8[CY,:,:,:].sum(axis = 1) - F_2_3[CY,:,:]
        # Determine EoL Product balance:
        Bal_2[CY,:] = F_y[CY,:,:].sum(axis = 0) - F_1_1a[CY,:,:].sum(axis = 0) - F_2_8[CY,:,:,:].sum(axis = 1).sum(axis =0) - F_2_3[CY,:,:].sum(axis = 0)

        Mylog.info('Step 3: EoL material recovery and lossed to landfills.<br>')
        # Determine flow of old scrap from EoL treatment to scrap market, aggregate over products    
        F_3_4[CY,Par_NoOfRegions::] = (Par_Gamma_EoL_Recovery_Efficiency_Steel[CY,:,:] * F_2_3[CY,:,:]).sum(axis =1)
        # Determine flow of recovery losses to landfills
        F_3_3a[CY,:,:] = F_2_3[CY,:,:] * (1 - Par_Gamma_EoL_Recovery_Efficiency_Steel[CY,:,:])
        # Determine mass balance of scrap recovery process
        Bal_3[CY,:] = F_2_3[CY,:,:].sum(axis=1) - F_3_4[CY,Par_NoOfRegions::] - F_3_3a[CY,:,:].sum(axis =1)
        
        Mylog.info('Step 4: Refining, manufacturing, and re-distribution into products.<br>')
        #   #Delta_wo_Lambda = np.linalg.inv(np.eye(Par_NoOfRegions * Par_NoOfProducts) - Par_AllocationSteelToProducts.dot(Par_RemeltingYield[CY,:,:]).dot(Par_AllocationScrapToRefinement).dot(Par_FabricationYieldLossRecovery).dot(np.eye(Par_NoOfRegions * Par_NoOfProducts) - Par_FabricationYield))
        # Delta_wo_Lambda = (I - Xi*(I-Lambda)*D*Theta*B)^-1:
        Delta_wo_Lambda = np.linalg.inv(np.eye(Par_NoOfScraps * Par_NoOfRegions) - Par_Xi_FabricationYieldLossRecovery[CY,:,:].dot(np.eye(Par_NoOfRegions * Par_NoOfProducts) - Par_Lambda_FabricationYield[CY,:,:]).dot(Par_D_AllocationSteelToProducts[CY,:,:]).dot(Par_Theta_RemeltingYield[:,:]).dot(Par_B_ScrapToRecycling))
        # Determine fabrication scrap
        F_7_4[CY,:]  = Delta_wo_Lambda.dot(Par_Xi_FabricationYieldLossRecovery[CY,:,:]).dot(np.eye(Par_NoOfRegions * Par_NoOfProducts) - Par_Lambda_FabricationYield[CY,:,:]).dot(Par_D_AllocationSteelToProducts[CY,:,:]).dot(Par_Theta_RemeltingYield[:,:]).dot(Par_B_ScrapToRecycling).dot(F_3_4[CY,:])
        # Determine supply of secondary material
        F_5_6[CY,:]  = Par_Theta_RemeltingYield.dot(Par_B_ScrapToRecycling).dot(F_3_4[CY,:] + F_7_4[CY,:])
        # Determine consumption of secondary material
        F_6_7[CY,:]  = Par_D_AllocationSteelToProducts[CY,:,:].dot(F_5_6[CY,:])
        # Determine net production of goods from recycled material:
        F_7_8[CY,:]  = Par_Lambda_FabricationYield[CY,:,:].dot(Par_D_AllocationSteelToProducts[CY,:,:]).dot(Par_Theta_RemeltingYield).dot(Par_B_ScrapToRecycling).dot(F_3_4[CY,:] + F_7_4[CY,:])
        #Determine losses during remelting
        F_5_5a[CY,:] = (np.eye(Par_NoOfSecMetals * Par_NoOfRegions) - Par_Theta_RemeltingYield).dot(Par_B_ScrapToRecycling).dot(F_3_4[CY,:] + F_7_4[CY,:])
        #Determine losses during manufacturing
        F_7_7a[CY,:] = Par_Xi_FabricationYieldLossRecovery_complement[CY,:,:].dot(np.eye(Par_NoOfProducts * Par_NoOfRegions) - Par_Lambda_FabricationYield[CY,:,:]).dot(Par_D_AllocationSteelToProducts[CY,:,:]).dot(Par_Theta_RemeltingYield).dot(Par_B_ScrapToRecycling).dot(F_3_4[CY,:] + F_7_4[CY,:])
        # Determine mass balance of the refining/manufacturing subystem.        
        Bal_5[CY,:]  = Par_B_ScrapToRecycling.dot(F_3_4[CY,:] + F_7_4[CY,:]) - F_5_5a[CY,:] - F_5_6[CY,:]
        # Determine mass balance of markets for secondary metal.
        Bal_6[CY,:]  = F_5_6[CY,:].sum() - F_6_7[CY,:].sum()
        # Determine scrap market balance for old and new scrap
        Bal_4[CY,:]  = F_3_4[CY,:].sum() + F_7_4[CY,:].sum() - Par_B_ScrapToRecycling.dot(F_3_4[CY,:] + F_7_4[CY,:]).sum()
        # Determine balance of manufacturing processes:
        Bal_7[CY,:]  = F_6_7[CY,:].reshape(Par_NoOfRegions,Par_NoOfProducts).sum(axis =1) - F_7_4[CY,:].reshape(Par_NoOfScraps,Par_NoOfRegions).transpose().sum(axis =1) - F_7_7a[CY,:].reshape(Par_NoOfScraps,Par_NoOfRegions).transpose().sum(axis =1) - F_7_8[CY,:].reshape(Par_NoOfRegions,Par_NoOfProducts).sum(axis =1)
        
        Mylog.info('Step 5: Re-insert recycled and re-used goods into the stock.<br>')
        # Determine the total consumption of products as sum of external input x_in, re-used products from all regions, and recycled products from all regions
        F_8_1[CY,:,:] = F_0_8[CY,:,:] + F_2_8[CY,:,:,:].sum(axis = 0) + Par_M_FinishedProductsTradeShares_Static.dot(F_7_8[CY,:]).reshape(Par_NoOfRegions,Par_NoOfProducts)
        # Determine final products balance:
        Bal_8[CY,:]   = F_8_1[CY,:,:].sum(axis = 0) - F_0_8[CY,:,:].sum(axis = 0) - F_2_8[CY,:,:,:].sum(axis = 0).sum(axis =0) - Par_M_FinishedProductsTradeShares_Static.dot(F_7_8[CY,:]).reshape(Par_NoOfRegions,Par_NoOfProducts).sum(axis = 0)
        
        Mylog.info('Step 6: Determine stocks and overall system balance.')
        if CY == 0:
            S_1[0,:,:]         = F_8_1[0,:,:] - F_y[0,:,:]
            S_1a[0,:,:]        = F_1_1a[0,:,:]
            S_3a[0,:,:]        = F_3_3a[0,:,:]
            S_5a[0,:]          = F_5_5a[0,:]
            S_7a[0,:]          = F_7_7a[0,:]

        else:
            S_1[CY,:,:]   = S_1[CY-1,:,:]  + F_8_1[CY,:,:] - F_y[CY,:,:]
            S_1a[CY,:,:]  = S_1a[CY-1,:,:] + F_1_1a[CY,:,:]
            S_3a[CY,:,:]  = S_3a[CY-1,:,:] + F_3_3a[CY,:,:]
            S_5a[CY,:]    = S_5a[CY-1,:]   + F_5_5a[CY,:]
            S_7a[CY,:]    = S_7a[CY-1,:]   + F_7_7a[CY,:]        
            Bal_1[CY,:,:] = F_8_1[CY,:,:]  - F_y[CY,:,:] - (S_1[CY,:,:] - S_1[CY-1,:,:]) 
            
        Mylog.info('Step 7: Report balance checks for flows.<br>')
        Bal_Process_UsePhase_Total = np.abs(Bal_1[CY,:,:]).sum()
        Mylog.info('Total imbalance for use phase |Bal_Process_UsePhase|.sum(): ' + str(Bal_Process_UsePhase_Total) + '.<br>')
        Bal_ObsoleteProducts_Total = np.abs(Bal_ObsoleteProducts[CY,:,:]).sum()
        Mylog.info('Total imbalance for obsolete products |Bal_ObsoleteProducts|.sum(): ' + str(Bal_ObsoleteProducts_Total) + '.<br>')
        Bal_Market_EolProducts_Total = np.abs(Bal_2[CY,:]).sum()
        Mylog.info('Total imbalance for EoL products market |Bal_Market_EolProducts|.sum(): ' + str(Bal_Market_EolProducts_Total) + '.<br>')
        Bal_Process_WasteMgt_Total = np.abs(Bal_3[CY,:]).sum()
        Mylog.info('Total imbalance for waste mgt. industries |Bal_Process_WasteMgt|.sum(): ' + str(Bal_Process_WasteMgt_Total) + '.<br>')
        Mylog.info('Total imbalance for scrap trade |Bal_Market_Scrap|.sum(): ' + str(np.abs(Bal_4[CY].sum())) + '.<br>')
        Bal_Process_Refining_Total = np.abs(Bal_5[CY,:]).sum()
        Mylog.info('Total imbalance for scrap remelting industries |Bal_Process_Refining|.sum(): ' + str(Bal_Process_Refining_Total) + '.<br>')
        Bal_Market_Steel_Total = np.abs(Bal_6[CY,:]).sum()
        Mylog.info('Total imbalance for secondary steel market |Bal_Market_Steel|.sum(): ' + str(Bal_Market_Steel_Total) + '.<br>')
        Bal_Process_Manufacturing_Total = np.abs(Bal_7[CY,:]).sum()
        Mylog.info('Total imbalance for manufacturing industries |Bal_Process_Manufacturing|.sum(): ' + str(Bal_Process_Manufacturing_Total) + '.<br>')
        Bal_FinalProducts_Total = np.abs(Bal_8[CY,:]).sum()
        Mylog.info('Total imbalance for final products market |Bal_FinalProducts|.sum(): ' + str(Bal_FinalProducts_Total) + '.<br>')

            
Var_Stock_Tot = (S_1.sum(axis =2) + S_1a.sum(axis =2) + S_3a.sum(axis =2) + S_5a[:,0:Par_NoOfRegions] + S_5a[:,Par_NoOfRegions::] + S_7a[:,0:Par_NoOfRegions] + S_7a[:,Par_NoOfRegions::]).sum(axis = 1)
Bal_System = Var_Stock_Tot - np.cumsum(F_0_8.sum(axis =2).sum(axis =1))
Mylog.info('<br><br><b>Total imbalance in entire system, all years: |Bal_System|.sum(): ' + str(np.abs(Bal_System).sum()) + '.</b><br>')

# Determine circular economy performance index
Circ_2100 = 0
for year in range(0,Par_NoOfYears):
    Circ_2100 = Circ_2100 + (Def_Application_Weighting[0] * S_1[year,:,0:9].sum() + Def_Application_Weighting[1] * S_1[year,:,9].sum() + Def_Application_Weighting[2] * (S_1a[year,:,:].sum() + S_3a[year,:,:].sum() + S_5a[year,:].sum() + S_7a[year,:].sum()))/(Par_NoOfYears -1)
    
#%%        

"""
Plot results
""" 
Mylog.info('<p>Determine ancillary results for plots.</p>')
Steel_Consumption_ByRegion = F_8_1.sum(axis =2)
Steel_Consumption_ByRegion_Stacked = np.cumsum(Steel_Consumption_ByRegion, axis =1)

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

Mylog.info('<p>Create plots.</p>')
Figurecounter = 1
if ScriptConfig['Modus'] == 'Trace single product':    
   
    StockLabels = Def_RegionsSymbols.copy()
    StockLabels.append('Obsolete products')
    StockLabels.append('Recovery losses')
    StockLabels.append('Remelting losses')
    StockLabels.append('Fabrication losses')
    
    Steel_Consumption_ByRegion = F_8_1.sum(axis =2) - F_0_8.sum(axis =2)
    Steel_Fate = np.concatenate((Steel_Consumption_ByRegion,F_1_1a.sum(axis=2).sum(axis=1).reshape(86,1),F_3_3a.sum(axis=2).sum(axis=1).reshape(86,1),F_5_5a.sum(axis=1).reshape(86,1),F_7_7a.sum(axis=1).reshape(86,1)), axis =1)
    Steel_Fate_Stacked = np.cumsum(Steel_Fate, axis =1)
    
    fig, ax = plt.subplots()   
    MyColorCycle = np.zeros((29,4))  
    MyColorCycle[0:25,:] = pylab.cm.hot(np.arange(0,1,0.04)) # select 25 colors from the 'hot' color map.
    MyColorCycle[25,:]   = [0.7,0.7,0.7,1]    
    MyColorCycle[26,:]   = [0.5,0.5,0.5,1]
    MyColorCycle[27,:]   = [0.3,0.3,0.3,1]
    MyColorCycle[28,:]   = [0.2,0.2,0.2,1]
    ax.set_color_cycle(MyColorCycle)

#%% Final consumption of steel by regions, aggregated over products
    # plot bars
    ProxyHandlesList = []
    for m in range(0,Par_NoOfRegions+4):
        if m == 0:
            ax.fill_between(Par_Time, 0,      Steel_Fate_Stacked[:,m], facecolor=MyColorCycle[m,:], alpha=1.0, label = StockLabels[m],linewidth = 0.3)
        else:            
            ax.fill_between(Par_Time, Steel_Fate_Stacked[:,m-1], Steel_Fate_Stacked[:,m], facecolor=MyColorCycle[m,:], alpha=1.0, label = StockLabels[m], linewidth = 0.3)
        ProxyHandlesList.append(plt.Rectangle((0, 0), 1, 1, fc=MyColorCycle[m,:])) # create proxy artist for legend
        
    
    plt.ylabel('Final consumption of steel, tons/year.')
    plt.xlabel('Year')
    #plt.title('Global average material content of final products')
    plt.axis([2010, 2100, 0, 0.12])
    plt.grid
    
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
    # Put a legend to the right of the current axis
    plt_lgd  = plt.legend(reversed(ProxyHandlesList),reversed(StockLabels),shadow = False, prop={'size':5.0},loc='upper left', bbox_to_anchor=(1.05, 1))  
    
    # add text    
    plt.title('1 ton of steel in ' + Def_ProductShortNames[PI] + ',originally consumed in ' + Def_RegionsNames[CI] + ', ' + str(Par_Time[SY]) + '.'   ,fontsize=10, fontweight='normal', color = 'k')   
    plt.text(2030, 0.11,  'Recycled steel entering the use phase, by region.'   ,fontsize=8, fontweight='normal', color = 'k')   
    plt.show()
    fig_name = 'Steel_FinalConsumption_RegionAggregate_2_' + Name_Scenario + '.png'
    fig.savefig(Path_Result + fig_name, dpi = 400,bbox_extra_artists=(plt_lgd,), bbox_inches='tight') 
    # include figure in logfile:
    Mylog.info('<center><img src="'+ fig_name +'" width="857" height="600" alt="'+ fig_name +'"></center>')
    Mylog.info('<font "size=+3"><center><b><i>Figure '+ str(Figurecounter) + ': '+ fig_name +'.</i></b></center></font><br>')
    Figurecounter += 1 

     
#%% Final consumption of steel by products, aggregated over regions
    StockLabels1 = Def_ProductShortNames.copy()
    StockLabels1.append('Obsolete products')
    StockLabels1.append('Recovery losses')
    StockLabels1.append('Remelting losses')
    StockLabels1.append('Fabrication losses')

    Steel_Consumption_ByProduct = F_8_1.sum(axis =1) - F_0_8.sum(axis =1)
    Steel_Fate2 = np.concatenate((Steel_Consumption_ByProduct,F_1_1a.sum(axis=2).sum(axis=1).reshape(86,1),F_3_3a.sum(axis=2).sum(axis=1).reshape(86,1),F_5_5a.sum(axis=1).reshape(86,1),F_7_7a.sum(axis=1).reshape(86,1)), axis =1)
    Steel_Fate_Stacked2 = np.cumsum(Steel_Fate2, axis =1)
    
    fig, ax = plt.subplots()   
    MyColorCycle = np.zeros((14,4))
    MyColorCycle[0:10,:] = pylab.cm.Paired(np.arange(0,1,0.1)) # select 10 colors from the 'Paired' color map.
    MyColorCycle[10,:]   = [0.7,0.7,0.7,1]    
    MyColorCycle[11,:]   = [0.5,0.5,0.5,1]
    MyColorCycle[12,:]   = [0.3,0.3,0.3,1]
    MyColorCycle[13,:]   = [0.2,0.2,0.2,1]
    ax.set_color_cycle(MyColorCycle)
    
    # plot bars
    ProxyHandlesList = []
    for m in range(0,Par_NoOfProducts+4):
        if m == 0:
            ax.fill_between(Par_Time, 0,      Steel_Fate_Stacked2[:,m], facecolor=MyColorCycle[m,:], alpha=1.0, label = StockLabels1[m],linewidth = 0.3)
        else:            
            ax.fill_between(Par_Time, Steel_Fate_Stacked2[:,m-1], Steel_Fate_Stacked2[:,m], facecolor=MyColorCycle[m,:], alpha=1.0, label = StockLabels1[m], linewidth = 0.3)
        ProxyHandlesList.append(plt.Rectangle((0, 0), 1, 1, fc=MyColorCycle[m,:])) # create proxy artist for legend
        
    
    plt.ylabel('Final consumption of steel, tons/year.')
    plt.xlabel('Year')
    #plt.title('Global average material content of final products')
    plt.axis([2010, 2100, 0, 0.12])
    plt.grid
    
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
    # Put a legend to the right of the current axis
    plt_lgd  = plt.legend(reversed(ProxyHandlesList),reversed(StockLabels1),shadow = False, prop={'size':6.0},loc='upper left', bbox_to_anchor=(1.05, 1))  
    
    # add text    
    plt.title('1 ton of steel in ' + Def_ProductShortNames[PI] + ', consumed in ' + Def_RegionsNames[CI] + ', ' + str(Par_Time[SY]) + '.'   ,fontsize=10, fontweight='normal', color = 'k')   
    plt.text(2028, 0.11,  'Recycled steel entering the use phase, by product.'   ,fontsize=8, fontweight='normal', color = 'k')   
    plt.show()
    fig_name = 'Steel_FinalConsumption_ProductAggregate_' + Name_Scenario + '.png'
    fig.savefig(Path_Result + fig_name, dpi = 400,bbox_extra_artists=(plt_lgd,), bbox_inches='tight') 
    # include figure in logfile:
    Mylog.info('<center><img src="'+ fig_name +'" width="857" height="600" alt="'+ fig_name +'"></center>')
    Mylog.info('<font "size=+3"><center><b><i>Figure '+ str(Figurecounter) + ': '+ fig_name +'.</i></b></center></font><br>')
    Figurecounter += 1    



#%% Steel stock by product
    Var_Stock_Use_Prod = S_1.sum(axis =1)
    Var_Stock_Obs_Tot  = S_1a.sum(axis =2).sum(axis =1)
    Var_Stock_Rec_Tot  = S_3a.sum(axis =2).sum(axis =1)
    Var_Stock_Rem_Tot  = S_5a.sum(axis =1)
    Var_Stock_Fab_Tot  = S_7a.sum(axis =1)
    
    Var_Stock_Tot      = np.concatenate((Var_Stock_Use_Prod,Var_Stock_Obs_Tot.reshape(86,1),Var_Stock_Rec_Tot.reshape(86,1),Var_Stock_Rem_Tot.reshape(86,1),Var_Stock_Fab_Tot.reshape(86,1)),axis =1)    
    
    Var_Stock_ByProduct_Stacked = np.cumsum(Var_Stock_Tot, axis =1)

    fig, ax = plt.subplots()   
    MyColorCycle = np.zeros((14,4))
    MyColorCycle[0:10,:] = pylab.cm.Paired(np.arange(0,1,0.1)) # select 10 colors from the 'Paired' color map.
    MyColorCycle[10,:]   = [0.7,0.7,0.7,1]    
    MyColorCycle[11,:]   = [0.5,0.5,0.5,1]
    MyColorCycle[12,:]   = [0.3,0.3,0.3,1]
    MyColorCycle[13,:]   = [0.2,0.2,0.2,1]
    
    ax.set_color_cycle(MyColorCycle)
    
    # plot bars
    ProxyHandlesList = []
    for m in range(0,Par_NoOfProducts+4):
        if m == 0:
            ax.fill_between(Par_Time, 0,      Var_Stock_ByProduct_Stacked[:,m], facecolor=MyColorCycle[m,:], alpha=1.0, label = StockLabels1[m],linewidth = 0.3)
        else:            
            ax.fill_between(Par_Time, Var_Stock_ByProduct_Stacked[:,m-1], Var_Stock_ByProduct_Stacked[:,m], facecolor=MyColorCycle[m,:], alpha=1.0, label = StockLabels1[m], linewidth = 0.3)
        ProxyHandlesList.append(plt.Rectangle((0, 0), 1, 1, fc=MyColorCycle[m,:])) # create proxy artist for legend
        
    
    plt.ylabel('Total stock of steel by product, tons.')
    plt.xlabel('Year')
    #plt.title('Global average material content of final products')
    plt.axis([2010, 2100, 0, 1.1])
    plt.grid
    
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
    # Put a legend to the right of the current axis
    plt_lgd  = plt.legend(reversed(ProxyHandlesList),reversed(StockLabels1),shadow = False, prop={'size':6.0},loc='upper left', bbox_to_anchor=(1.05, 1))  
    
    # add text    
    plt.title('1 ton of steel in ' + Def_ProductShortNames[PI] + ', consumed in ' + Def_RegionsNames[CI] + ', ' + str(Par_Time[SY]) + '.'   ,fontsize=10, fontweight='normal', color = 'k')   
    plt.show()
    fig_name = 'Steel_Stock_Product_' + Name_Scenario + '.png'
    fig.savefig(Path_Result + fig_name, dpi = 500,bbox_extra_artists=(plt_lgd,), bbox_inches='tight') 
    # include figure in logfile:
    Mylog.info('<center><img src="'+ fig_name +'" width="857" height="600" alt="'+ fig_name +'"></center>')
    Mylog.info('<font "size=+3"><center><b><i>Figure '+ str(Figurecounter) + ': '+ fig_name +'.</i></b></center></font><br>')
    Figurecounter += 1    





#%% Total steel stock, by region, including losses

    Var_Stock_Use_Region = S_1.sum(axis =2)
    Var_Stock_Lost_Region = S_1a.sum(axis =2) + S_3a.sum(axis =2) + S_5a[:,0:Par_NoOfRegions] + S_5a[:,Par_NoOfRegions::] + S_7a[:,0:Par_NoOfRegions] + S_7a[:,Par_NoOfRegions::]
    
    #Var_Stock_Tot      = np.concatenate((Var_Stock_Use_Region,Var_Stock_Lost_Region),axis =1)    
    Var_Stock_Tot2 = np.zeros((86,50))
    for m in range(0,50):
        if m % 2 == 0:
            Var_Stock_Tot2[:,m] = Var_Stock_Lost_Region[:,m // 2]
        else:
            Var_Stock_Tot2[:,m] = Var_Stock_Use_Region[:,m // 2 ]
            
    Var_Stock_ByProduct_Stacked2 = np.cumsum(Var_Stock_Tot2, axis =1)

    fig, ax = plt.subplots()    
    MyColorCycleHelp = pylab.cm.hot(np.arange(0,1,0.04)) # select 25 colors from the 'hot' color map.
    MyColorCycle = np.zeros((50,4))
    MyColorCycle[:,3] = 1
    for m in range(0,50):
        if m % 2 == 0:
            MyColorCycle[m,0:3] = greyfade(MyColorCycleHelp[m // 2,0:3],0.42)
        else:
            MyColorCycle[m,0:3] = MyColorCycleHelp[m // 2,0:3]
    ax.set_color_cycle(MyColorCycle)
   
    StockLabels2 = Def_RegionsNames.copy()

    # plot bars
    ProxyHandlesList = []
    for m in range(0,Par_NoOfRegions*2):
        if m == 0:
            ax.fill_between(Par_Time, 0,      Var_Stock_ByProduct_Stacked2[:,m], facecolor=MyColorCycle[m,:], alpha=1.0,linewidth = 0.3)
        else:  
            if m % 2 == 0: # is not part of legend
                ax.fill_between(Par_Time, Var_Stock_ByProduct_Stacked2[:,m-1], Var_Stock_ByProduct_Stacked2[:,m], facecolor=MyColorCycle[m,:], alpha=1.0, linewidth = 0.0, edgecolor = 'none')
            else:
                ax.fill_between(Par_Time, Var_Stock_ByProduct_Stacked2[:,m-1], Var_Stock_ByProduct_Stacked2[:,m], facecolor=MyColorCycle[m,:], alpha=1.0, label = StockLabels2[m // 2], linewidth = 0.0, linestyle = '-',edgecolor = 'none')
                ProxyHandlesList.append(plt.Rectangle((0, 0), 1, 1, fc=MyColorCycle[m,:])) # create proxy artist for legend        
    for m in range(0,Par_NoOfRegions):
        ax.plot(Par_Time, Var_Stock_ByProduct_Stacked2[:,2*m+1], color='k', alpha=1.0, linewidth = 0.3, linestyle = '-')
    
    plt.ylabel('Total stock of steel by region, tons.')
    plt.xlabel('Year')
    #plt.title('Global average material content of final products')
    plt.axis([2010, 2100, 0, 1.1])
    plt.grid
    
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
    # Put a legend to the right of the current axis
    plt_lgd  = plt.legend(reversed(ProxyHandlesList[0:25]),reversed(StockLabels2[0:25]),shadow = False, prop={'size':6.0},loc='upper left', bbox_to_anchor=(1.05, 1))  
    
    # add text    
    plt.title('1 ton of steel in ' + Def_ProductShortNames[PI] + ', consumed in ' + Def_RegionsNames[CI] + ', ' + str(Par_Time[SY]) + '.'   ,fontsize=10, fontweight='normal', color = 'k')   
    plt.text(2057, 1.03,  'Shaded areas indicate losses.'   ,fontsize=8, fontweight='normal', color = 'k')   
    plt.show()
    fig_name = 'Steel_Stock_Region_' + Name_Scenario + '.png'
    fig.savefig(Path_Result + fig_name, dpi = 500,bbox_extra_artists=(plt_lgd,), bbox_inches='tight') 
    # include figure in logfile:
    Mylog.info('<center><img src="'+ fig_name +'" width="857" height="600" alt="'+ fig_name +'"></center>')
    Mylog.info('<font "size=+3"><center><b><i>Figure '+ str(Figurecounter) + ': '+ fig_name +'.</i></b></center></font><br>')
    Figurecounter += 1   
    


#%% Total steel stock, by 10 aggregated regions, including losses

    Var_Stock_Use_Region  = S_1.sum(axis =2)
    Var_Stock_Lost_Region = S_1a.sum(axis =2) + S_3a.sum(axis =2) + S_5a[:,0:Par_NoOfRegions] + S_5a[:,Par_NoOfRegions::] + S_7a[:,0:Par_NoOfRegions] + S_7a[:,Par_NoOfRegions::]
    
    Var_Stock_Use_10Region  = np.zeros((Par_NoOfYears,10))
    Var_Stock_Lost_10Region = np.zeros((Par_NoOfYears,10))
    
    for m in range(0,Par_NoOfRegions):
        TargetRegionIndex = Def_RegionAgg_Vector[m]
        Var_Stock_Use_10Region[:,TargetRegionIndex]  = Var_Stock_Use_10Region[:,TargetRegionIndex]  + Var_Stock_Use_Region[:,m]
        Var_Stock_Lost_10Region[:,TargetRegionIndex] = Var_Stock_Lost_10Region[:,TargetRegionIndex] + Var_Stock_Lost_Region[:,m]
    
    #Var_Stock_Tot      = np.concatenate((Var_Stock_Use_Region,Var_Stock_Lost_Region),axis =1)    
    Var_Stock_Tot_10 = np.zeros((86,20))
    for m in range(0,20):
        if m % 2 == 0:
            Var_Stock_Tot_10[:,m] = Var_Stock_Lost_10Region[:,m // 2]
        else:
            Var_Stock_Tot_10[:,m] = Var_Stock_Use_10Region[:,m // 2 ]
            
    Var_Stock_ByProduct_Stacked_10 = np.cumsum(Var_Stock_Tot_10, axis =1)

    fig, ax = plt.subplots()   
    MyColorCycle = np.zeros((20,4))
    for m in range(0,20):
        if m % 2 == 0:
            MyColorCycle[m,0:3] = MyColorCycle_10Reg[m // 2,0:3]
        else:
            MyColorCycle[m,0:3] = MyColorCycle_10Reg[m // 2,0:3]
    ax.set_color_cycle(MyColorCycle)
   
    StockLabels3 = Def_RegionsNames_agg.copy()

    # plot bars
    ProxyHandlesList = []
    for m in range(0,10*2):
        if m == 0:
            ax.fill_between(Par_Time, 0,      Var_Stock_ByProduct_Stacked_10[:,m], facecolor=MyColorCycle[m+1,:], hatch='///', alpha=1.0,linewidth = 0.0)
        else:  
            if m % 2 == 0: # is not part of legend
                ax.fill_between(Par_Time, Var_Stock_ByProduct_Stacked_10[:,m-1], Var_Stock_ByProduct_Stacked_10[:,m], facecolor=MyColorCycle[m+1,:], hatch='///', alpha=1.0, linewidth = 0.0, edgecolor = 'none')
            else:
                ax.fill_between(Par_Time, Var_Stock_ByProduct_Stacked_10[:,m-1], Var_Stock_ByProduct_Stacked_10[:,m], facecolor=MyColorCycle[m,:], alpha=1.0, label = StockLabels2[m // 2], linewidth = 0.0, linestyle = '-',edgecolor = 'none')
                #ProxyHandlesList.append(plt.Rectangle((0, 0), 1, 1, fc=MyColorCycle[m,0:2])) # create proxy artist for legend        
                ProxyHandlesList.append(mpatches.Patch(color=MyColorCycle[m,0:3], label=StockLabels3[m//2]))
    for m in range(0,10):
        ax.plot(Par_Time, Var_Stock_ByProduct_Stacked_10[:,2*m+1], color='k', alpha=1.0, linewidth = 0.6, linestyle = '-')
    
    plt.ylabel('Total stock of steel by region, tons.')
    plt.xlabel('Year')
    #plt.title('Global average material content of final products')
    plt.axis([2010, 2100, 0, 1.1])
    plt.grid
    
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
    # Put a legend to the right of the current axis
    plt_lgd  = plt.legend(handles = ProxyHandlesList[-1::-1],shadow = False, prop={'size':6.0},loc='upper left', bbox_to_anchor=(1.05, 1))  
    # add text    
    plt.title('1 ton of steel in ' + Def_ProductShortNames[PI] + ', consumed in ' + Def_RegionsNames[CI] + ', ' + str(Par_Time[SY]) + '.'   ,fontsize=10, fontweight='normal', color = 'k')   
    plt.text(2057, 1.03,  'Hatched areas indicate losses.'   ,fontsize=8, fontweight='normal', color = 'k')   
    plt.show()
    fig_name = 'Steel_Stock_10Region_' + Name_Scenario + '.png'
    fig.savefig(Path_Result + fig_name, dpi = 500,bbox_extra_artists=(plt_lgd,), bbox_inches='tight') 
    # include figure in logfile:
    Mylog.info('<center><img src="'+ fig_name +'" width="857" height="600" alt="'+ fig_name +'"></center>')
    Mylog.info('<font "size=+3"><center><b><i>Figure '+ str(Figurecounter) + ': '+ fig_name +'.</i></b></center></font><br>')
    Figurecounter += 1   
    
    

#%%    
"""
Store results
""" 
Mylog.info('<br> Write main results to .mat file. <br>')
Filestring_Matlab_out      = Path_Result + 'MaTraceGlobal_' + Name_Scenario + '_' + DateString + '.mat' 
scipy.io.savemat(Filestring_Matlab_out, 
                 mdict={'ScriptConfig':ScriptConfig,
                        'F_0_8':F_0_8,
                        'F_8_1':F_8_1,
                        'F_y':F_y,
                        'F_1_1a':F_1_1a,
                        'F_1_2':F_1_2,
                        'F_2_8':F_2_8,
                        'F_2_3':F_2_3,
                        'F_3_3a':F_3_3a,
                        'F_3_4':F_3_4,
                        'F_4_5':F_4_5,
                        'F_5_5a':F_5_5a,
                        'F_5_6':F_5_6,
                        'F_6_7':F_6_7,
                        'F_7_7a':F_7_7a,
                        'F_7_4':F_7_4,
                        'F_7_8':F_7_8,
                        'S_1':S_1,
                        'S_1a':S_1a,
                        'S_3a':S_3a,
                        'S_5a':S_5a,
                        'S_7a':S_7a,
                        'S_Tot':S_Tot,
                        'Var_Stock_Use_10Region':Var_Stock_Use_10Region,
                        'Var_Stock_Lost_10Region':Var_Stock_Lost_10Region,
                        'Circ_2100':Circ_2100})
                        

Mylog.info('<br> Write main results to Excel file. <br>')

myfont = xlwt.Font()
myfont.bold = True
mystyle = xlwt.XFStyle()
mystyle.font = myfont

Result_workbook  = xlwt.Workbook(encoding = 'ascii') 
Result_worksheet = Result_workbook.add_sheet('Steel_Consumption_ByRegion')

Result_worksheet.write(0, 0, label = 'Final consumption of recycled steel, t/yr.', style = mystyle)
Result_worksheet.write(1, 0, label = 'Year', style = mystyle)
for m in range(0,29):
    Result_worksheet.write(1, m +1, label = StockLabels[m], style = mystyle)

for m in range(0,86):
    Result_worksheet.write(m +2, 0, label = Par_Time[m], style = mystyle)
    for n in range(0,29):
        Result_worksheet.write(m +2, n +1, label = Steel_Fate[m,n])

Result_worksheet = Result_workbook.add_sheet('Steel_Consumption_ByProduct')

Result_worksheet.write(0, 0, label = 'Final consumption of recycled steel, t/yr.', style = mystyle)
Result_worksheet.write(1, 0, label = 'Year', style = mystyle)
for m in range(0,14):
    Result_worksheet.write(1, m +1, label = StockLabels1[m], style = mystyle)

for m in range(0,86):
    Result_worksheet.write(m +2, 0, label = Par_Time[m], style = mystyle)
    for n in range(0,14):
        Result_worksheet.write(m +2, n +1, label = Steel_Fate2[m,n])
        
Result_worksheet = Result_workbook.add_sheet('Steel_Stock_ByRegion')

Result_worksheet.write(0, 0, label = 'Stock of steel by region, t.', style = mystyle)
Result_worksheet.write(1, 0, label = 'Year', style = mystyle)
for m in range(0,50):
    if m % 2 == 0:
        Result_worksheet.write(1, m +1, label = StockLabels2[m // 2] + ', lossses', style = mystyle)
    else:
        Result_worksheet.write(1, m +1, label = StockLabels2[m // 2] + ', in use', style = mystyle)
        
for m in range(0,86):
    Result_worksheet.write(m +2, 0, label = Par_Time[m], style = mystyle)
    for n in range(0,50):
        Result_worksheet.write(m +2, n +1, label = Var_Stock_Tot2[m,n])         
        
Result_worksheet = Result_workbook.add_sheet('Steel_Stock_ByProduct')

Result_worksheet.write(0, 0, label = 'Stock of steel by product, t.', style = mystyle)
Result_worksheet.write(1, 0, label = 'Year', style = mystyle)
for m in range(0,14):
    Result_worksheet.write(1, m +1, label = StockLabels1[m], style = mystyle)

for m in range(0,86):
    Result_worksheet.write(m +2, 0, label = Par_Time[m], style = mystyle)
    for n in range(0,14):
        Result_worksheet.write(m +2, n +1, label = Var_Stock_Tot[m,n])        

Result_workbook.save(Path_Result + 'PlotData.xls')    
Mylog.info('<br> Write main results to Excel file finished. <br>')
                       
#%%
"""
End script
""" 
Mylog.info('Circ_2100 index: ' + str(Circ_2100[0]) + '.<br>')
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
# -*- coding: utf-8 -*-

import os 
import sys
import pandas as pd
from SESAMI.SESAMI_1.betan import BETAn

def calculation_runner(MAIN_PATH, plotting_information):

    minlinelength = 4
    
    p0 = 1e5 # TODO adjust later
    temperature = 77 # TODO adjust later
    gas = plotting_information['gas']

    # changing some variable types
    plotting_information['font size'] = int(plotting_information['font size'])
    plotting_information['R2 cutoff'] = float(plotting_information['R2 cutoff'])
    plotting_information['R2 min'] = float(plotting_information['R2 min'])
    plotting_information['dpi'] = float(plotting_information['dpi'])

    # The R^2 information from the GUI supersedes the input.txt content R^2   
    b = BETAn(gas, temperature, minlinelength, plotting_information)

    column_names = ['Pressure', 'Loading']
    data = pd.read_table(f'{MAIN_PATH}user_0/input.txt', skiprows=1, sep='\t', names=column_names) # TODO change from user_0 to specific user ID down the line
    data = b.prepdata(data, p0=p0)

    BET_dict, BET_ESW_dict = b.generatesummary(data, plotting_information, sumpath=f'{MAIN_PATH}user_0/', ) # TODO change from user_0 to specific user ID down the line

    return BET_dict, BET_ESW_dict
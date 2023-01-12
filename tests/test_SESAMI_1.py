import os
import pytest
import shutil
import math
import pandas as pd
from SESAMI.SESAMI_1.SESAMI_1 import calculation_runner

MAIN_PATH = os.path.abspath(".") + "/"
# MAIN_PATH = str(current_path.parent.absolute()) + "/" # the main directory

# All the following lists must have a length of ten (ten test cases)
R2_cutoffs = ['0.9995', '0.9995', '0.995', '0.995', '0.9995'] * 2
R2_mins = ['0.998', '0.99', '0.99', '0.97', '0.998'] * 2
gases = ['Argon'] * 5 + ['Nitrogen'] * 5
scopes = (['BET and BET+ESW'] * 4 + ['BET'] * 1) * 2

# List of length ten where each entry is a tuple of (BET dictionary, BET+ESW dictionary)
benchmark_values_list = [({'C': 201.07820437891343, 'qm': 28.42284930790741, 'A_BET': 2430.9096636176737, 'con3': 'Yes', 'con4': 'Yes', 'length': 9, 'R2': 0.9996471530103053},
        {'C': 248.13040372760412, 'qm': 27.438654967829116, 'A_BET': 2346.7348679715333, 'con3': 'No', 'con4': 'Yes', 'length': 9, 'R2': 0.9984668760492631}),
    ({'C': 201.07820437891343, 'qm': 28.42284930790741, 'A_BET': 2430.9096636176737, 'con3': 'Yes', 'con4': 'Yes', 'length': 9, 'R2': 0.9996471530103053},
        {'C': 215.3771852683996, 'qm': 27.631618378374007, 'A_BET': 2363.238372399842, 'con3': 'No', 'con4': 'Yes', 'length': 10, 'R2': 0.9929475457250563}),
    ({'C': 139.65914181288488, 'qm': 29.429697336541643, 'A_BET': 2517.021952223462, 'con3': 'Yes', 'con4': 'Yes', 'length': 10, 'R2': 0.9984582095624193},
        {'C': 215.3771852683996, 'qm': 27.631618378374007, 'A_BET': 2363.238372399842, 'con3': 'No', 'con4': 'Yes', 'length': 10, 'R2': 0.9929475457250563}),
    ({'C': 139.65914181288488, 'qm': 29.429697336541643, 'A_BET': 2517.021952223462, 'con3': 'Yes', 'con4': 'Yes', 'length': 10, 'R2': 0.9984582095624193},
        {'C': 215.3771852683996, 'qm': 27.631618378374007, 'A_BET': 2363.238372399842, 'con3': 'No', 'con4': 'Yes', 'length': 10, 'R2': 0.9929475457250563}),
    ({'C': 201.07820437891343, 'qm': 28.42284930790741, 'A_BET': 2430.9096636176737, 'con3': 'Yes', 'con4': 'Yes', 'length': 9, 'R2': 0.9996471530103053},
        None),
    ({'C': 201.07820437891343, 'qm': 28.42284930790741, 'A_BET': 2773.2913063807264, 'con3': 'Yes', 'con4': 'Yes', 'length': 9, 'R2': 0.9996471530103053},
        {'C': 248.13040372760412, 'qm': 27.438654967829116, 'A_BET': 2677.260905714003, 'con3': 'No', 'con4': 'Yes', 'length': 9, 'R2': 0.9984668760492631}),
    ({'C': 201.07820437891343, 'qm': 28.42284930790741, 'A_BET': 2773.2913063807264, 'con3': 'Yes', 'con4': 'Yes', 'length': 9, 'R2': 0.9996471530103053},
        {'C': 215.3771852683996, 'qm': 27.631618378374007, 'A_BET': 2696.088847385736, 'con3': 'No', 'con4': 'Yes', 'length': 10, 'R2': 0.9929475457250563}),
    ({'C': 139.65914181288488, 'qm': 29.429697336541643, 'A_BET': 2871.532086339443, 'con3': 'Yes', 'con4': 'Yes', 'length': 10, 'R2': 0.9984582095624193},
        {'C': 215.3771852683996, 'qm': 27.631618378374007, 'A_BET': 2696.088847385736, 'con3': 'No', 'con4': 'Yes', 'length': 10, 'R2': 0.9929475457250563}),
    ({'C': 139.65914181288488, 'qm': 29.429697336541643, 'A_BET': 2871.532086339443, 'con3': 'Yes', 'con4': 'Yes', 'length': 10, 'R2': 0.9984582095624193},
        {'C': 215.3771852683996, 'qm': 27.631618378374007, 'A_BET': 2696.088847385736, 'con3': 'No', 'con4': 'Yes', 'length': 10, 'R2': 0.9929475457250563}),
    ({'C': 201.07820437891343, 'qm': 28.42284930790741, 'A_BET': 2773.2913063807264, 'con3': 'Yes', 'con4': 'Yes', 'length': 9, 'R2': 0.9996471530103053},
        None)
    ]

inputs = [] # Populated below
for i in range(10): # Ten test cases
	inputs.append((MAIN_PATH, 
		{'dpi': '300', 'font size': '10', 'font type': 'sans-serif', 'legend': 'Yes', 'R2 cutoff': R2_cutoffs[i], 'R2 min': R2_mins[i], 'gas': gases[i], 'scope': scopes[i], 'ML': 'No'},
		'test', # all session_ID set to 'test'
		i,
        benchmark_values_list[i])) # session_plot_num

# Getting the example file ready
if not os.path.exists(f'{MAIN_PATH}user_test'):
	os.mkdir(f'{MAIN_PATH}user_test')
shutil.copyfile(
    f"{MAIN_PATH}example_input/example_input.txt",
    f'{MAIN_PATH}user_test/input.txt', # Use an ID of 'test' for the purposes of the test
)

@pytest.mark.parametrize("MAIN_PATH, user_options, session_ID, session_plot_num, benchmark_values", inputs)
def test_SESAMI_1(MAIN_PATH, user_options, session_ID, session_plot_num, benchmark_values):
    BET_dict, BET_ESW_dict = calculation_runner(
        MAIN_PATH, user_options, session_ID, session_plot_num
    )

    # # Getting the benchmarks. Plug into benchmark_values_list above, then comment out this code block.
    # with open(f'/Users/gianmarcoterrones/Downloads/temp_{session_plot_num}.txt', 'w') as f:
    #     f.write('BET_dict\n')
    #     f.write(str(BET_dict) + '\n')
    #     f.write('BET_ESW_dict\n')
    #     f.write(str(BET_ESW_dict))

    for key in BET_dict:
        if type(BET_dict[key]) == int or type(BET_dict[key]) == float: # Comparing numbers (e.g. for qm)
            assert math.isclose(BET_dict[key], benchmark_values[0][key])
            assert math.isclose(BET_ESW_dict[key], benchmark_values[1][key])
        else: # Comparing strings (e.g. for con3)
            assert BET_dict[key] == benchmark_values[0][key]
            assert BET_ESW_dict[key] == benchmark_values[1][key]

    # assert BET_dict == benchmark_values[0]    
    # assert BET_ESW_dict == benchmark_values[1]
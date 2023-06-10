# The goal of this script is to calculate the mean absolute percent error between Zeo++ areas and areas calculated by different programs.
# Across the 13 MOFs (I exclude SIFSIX-3 due to its poor GCMC isotherm).

import numpy as np

# Mean absolute percentage error. From https://www.askpython.com/python/examples/mape-mean-absolute-percentage-error
def MAPE(Y_actual,Y_Predicted):
    mape = np.mean(np.abs((Y_actual - Y_Predicted)/Y_actual))*100
    return mape

# Using the data from calculated_areas.xlsx

BET_a = [2001, 3502, 2107, 3828, 1239, 1429, 1221, 2386, 1828, 44, 2439, 2711, 3543] # BET SESAMI
BET_b = [1933, 3543, 1853, 2862, 1239, 1386, 1168, 2438, 1834, np.NAN, 2181, 934, 3594] # BET+ESW SESAMI
BET_c = [2089, 3123, 2111, 2944, 1443, 1575, 1405, 2203, 1902, 1275, 2633, 2601, 3111] # SESAMI ML
pyGAPS = [1902, 3504, 1852, 2939, 1242, 1390, 1183, 82, 1839, np.NAN, 2144, 1073, 3758]
beatmap_a = [1933, np.NAN, 1905, 2343, 1332, 1420, 1223, 82, 1830, 38, 2178, 2915, 2866] # beatmap option set 1
beatmap_b = [1980, np.NAN, 2094, 3331, 1304, 1414, 1212, 2423, 1791, 1147, 2672, 2930, 3492] # beatmap option set 2
zeo_167 = [2397, 3722, 1957, 3164, 1289, 1588, 1510, 1933, 1796, 1690, 3050, 3192, 3944]
zeo_227 = [1768, 3338, 1783, 2617, 0, 0, 703, 1826, 1496, 1571, 2689, 2306, 3350]
betsi_c = [1962, 3519, np.NAN, np.NAN, np.NAN, 1381, 1164, 2426, np.NAN, np.NAN, np.NAN, np.NAN, np.NAN] # BETSI option set 3
betsi_new = [1962, 3519, 1799, 2879, 1201, 1381, 1164, 2426, 1815, 1172, 2082, 1077, 3756] # newer BETSI version, option set 3

# Will loop through the program generated areas and compare to Zeo++
print('1.67 A probe first')
areas_to_compare = [BET_a, BET_b, BET_c, pyGAPS, beatmap_a, beatmap_b, betsi_c, betsi_new]
software_names = ['SESAMI 1 BET', 'SESAMI 1 BET+ESW', 'SESAMI 2 LASSO', 'pyGAPS', 'BEaTmap 1', 'BEaTmap 2', 'BETSI', 'BETSI_new']
for i, my_list in enumerate(areas_to_compare):
	software_predictions = np.array(my_list)
	pseudo_ground_truth = np.array(zeo_167)
	# Getting rid of NaN values
	pseudo_ground_truth_clean = pseudo_ground_truth[np.logical_not(np.isnan(software_predictions))] # Only keep the non NAN values
	software_predictions_clean = software_predictions[np.logical_not(np.isnan(software_predictions))] # Only keep the non NAN values
	print(f'MAPE for {software_names[i]} is {MAPE(pseudo_ground_truth_clean, software_predictions_clean)}')

print('\n2.27 A probe next')
for i, my_list in enumerate(areas_to_compare):
	software_predictions = np.array(my_list)
	pseudo_ground_truth = np.array(zeo_227)
	# Getting rid of NaN values
	pseudo_ground_truth_clean = pseudo_ground_truth[np.logical_not(np.logical_or(np.isnan(software_predictions),pseudo_ground_truth == 0))] # Only keep the non NAN values and non zero values (zero values are present from Zeo++ output)
	software_predictions_clean = software_predictions[np.logical_not(np.logical_or(np.isnan(software_predictions),pseudo_ground_truth == 0))] # Only keep the non NAN values and non zero values
	print(f'MAPE for {software_names[i]} is {MAPE(pseudo_ground_truth_clean, software_predictions_clean)}')

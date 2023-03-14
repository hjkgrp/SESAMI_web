# The goal of this script is to load in isotherms and to calculate BET areas with pyGAPS.

import pygaps as pg
import pandas as pd
import pygaps.characterisation as pgc

MOFs = [
'HKUST-1',
'Mg-MOF-74',
'MOF-808',
'NU-1000',
'NU-1200',
'NU-1500(Fe)',
'SIFSIX-Ni',
'UiO-66',
'ZIF-8'
]

for i, MOF in enumerate(MOFs):
	df = pd.read_csv(f'../experimental_N2_77K_isotherms_SESAMI_web_format/{MOF}.csv')

	isotherm = pg.PointIsotherm(
		isotherm_data=df,
		pressure_key='Pressure (Pa)',
		loading_key='Loading (mol/kg)',
		material=MOF,
		adsorbate='N2',
		temperature=77,
		pressure_unit='Pa',
		pressure_mode='absolute',
		temperature_unit='K',
		loading_basis='molar',
		loading_unit='mol',
		material_basis='mass',
		material_unit='kg')

	print(f'isotherm #{i+1}:')
	print(isotherm)

	try:
		result_dict = pgc.area_BET(isotherm, verbose=True)
		# print(f'result_dict #{i+1}:')
		# print(result_dict)

		# area is originally in m2/kg because material_unit is kg. https://pygaps.readthedocs.io/en/master/reference/characterisation/area_bet.html

		print(f'BET area #{i+1} is {result_dict["area"] / 1000} in m2/g') # Divide by 1000 to convert from m2/kg to m2/g
	except:
		print('Issue with this isotherm')
		# For MOF-808 and SIFSIX-3-Ni, got this error: pygaps.utilities.exceptions.CalculationError: The isotherm does not have enough points (at least 3) in the BET region. Unable to calculate BET area.

	print()
	print('************************************')
	print()
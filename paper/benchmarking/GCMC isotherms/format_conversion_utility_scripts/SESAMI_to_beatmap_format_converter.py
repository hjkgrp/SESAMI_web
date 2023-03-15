# The goal of this script is to convert the CSV files in GCMC_N2_77K_isotherms_SESAMI_web_format into a format compatible with beatmap.
# Will drop these new files into GCMC_N2_77K_isotherms_beatmap_format

import pandas as pd

MOFs = [
'Cu-BTC',
'IRMOF-1',
'MIL-100_Cr',
'MIL-101',
'UIO-66',
'ZIF-8',
'MIL-53_Al',
'MIL-100_Fe',
'MgMOF-74_opt',
'MOF-808',
'NU-1000',
'NU-1200',
'NU-1500-Fe',
'SIFSIX-3-Ni'
]

for MOF in MOFs:
	df = pd.read_csv(f'GCMC_N2_77K_isotherms_SESAMI_web_format/{MOF}.csv')

	# Rename columns appropriately
	df = df.rename(columns={'Pressure (Pa)': 'Relative Pressure (P/Po)', 'Loading (mol/kg)': 'Loading (mol/g)'})

	# Apply multipliers to correct units
	df['Relative Pressure (P/Po)'] = df['Relative Pressure (P/Po)'].apply(lambda x: x/1e5) # Since P0 is 1e5
	df['Loading (mol/g)'] = df['Loading (mol/g)'].apply(lambda x: x/1000) # Going from mol/kg to mol/g

	df.to_csv(f'GCMC_N2_77K_isotherms_beatmap_format/{MOF}.csv', index=False, header=False)
		# Since example file had no column names: https://github.com/PMEAL/beatmap/blob/main/examples/vulcan_chex.csv
# The goal of this script is to convert the CSV files in GCMC_N2_77K_isotherms_SESAMI_web_format into a format compatible with BETSI.
# Will drop these new files into GCMC_N2_77K_isotherms_BETSI_format

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
	df = df.rename(columns={'Pressure (Pa)': 'Relative Pressure (P/Po)', 'Loading (mol/kg)': ' Quantity Adsorbed (cm3/g STP)'})

	# Apply multipliers to correct units
	df['Relative Pressure (P/Po)'] = df['Relative Pressure (P/Po)'].apply(lambda x: x/1e5) # Since P0 is 1e5
	df[' Quantity Adsorbed (cm3/g STP)'] = df[' Quantity Adsorbed (cm3/g STP)'].apply(lambda x: x*22.4139)

	df.to_csv(f'GCMC_N2_77K_isotherms_BETSI_format/{MOF}.csv', index=False)
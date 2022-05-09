# INTRODUCTION
This website is developed to standardize the Brauner-Emmett-Teller (BET) and Excess Sorption Work (ESW) methods for surface area
estimation in nanoporous materials. The web interface allows user to upload either [Adsorption Information File (AIF)](https://pubs.acs.org/doi/10.1021/acs.langmuir.1c00122) or Comma Separated-Values (CSV) file. 

This website is based on [MOFSimplify](https://github.com/hjkgrp/MOFSimplify) website developed by [Kulik Group](http://hjkgrp.mit.edu/) at MIT.
# Preparing Input files
AIF file: use http://raw2aif.herokuapp.com/ 
- Details of AIF file can be found in [this](https://github.com/AIF-development-team/adsorptioninformationformat) repository.

CSV file: see [example](/example_input/example_loading_data.csv)
# Using the Software
1. Use the following command in the terminal to run:
`python app.py`
2. Upload `AIF` or `CSV` formatted data.
3. Click `Run Calculation` and wait.
# REFERENCES
- [Surface Area Determination of Porous Materials Using the Brunauer–Emmett–Teller (BET) Method: Limitations and Improvements](https://pubs.acs.org/doi/abs/10.1021/acs.jpcc.9b02116),
J. Phys. Chem. C 2019, 123, 33, 20195 - 20209
- [Beyond the BET Analysis: The Surface Area Prediction of Nanoporous Materials Using a Machine Learning Method](https://pubs.acs.org/doi/abs/10.1021/acs.jpclett.0c01518)
J. Phys. Chem. Lett. 2020, 11, 14, 5412 - 5417

# AUTHORS
- Archit Datar (SESAMI python code development)
- Gianmarco Terrones (SESAMI web interface development)
- Prof. Yongchul G. Chung (project supervision, database integration, website maintaince)

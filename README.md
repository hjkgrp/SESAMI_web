# Introduction
Forget about using old excel spreadsheet from your co-workers! **On-the-fly**, this website performs the Brauner-Emmett-Teller (BET), Excess Sorption Work (ESW), BET-ESW, and Machine Learning (ML) methods for surface area
estimation in nanoporous materials. The web interface allows user to upload either [Adsorption Information File (AIF)](https://pubs.acs.org/doi/10.1021/acs.langmuir.1c00122) or Comma Separated-Values (CSV) file. 

This website is based on [MOFSimplify](https://github.com/hjkgrp/MOFSimplify) website developed by [Kulik Group](http://hjkgrp.mit.edu/) at MIT.

For additional support, feedback, and inquiry, contact support(at)sesami-web.org

# Sample Output
You will be able to change font type, font size, dot-per-inch (dpi) etc on the website for your publication.

![example_input](/example_input/sesami-output.png)

# Website Configuration
Website is powered by `Mongo DB 5.3.1` and `Google Cloud Run`

# Calculation Details
The algorithms employed in this code select the linear region from the isotherms and compute the areas. Detailed algorithm can be found from page S5 from J. Phys. Chem. C 2019, 123, 33, 20195 - 20209. Excerpt from the SI is provided below for completeness.

## BET areas
We consider the “right-most” region, which is the region having a high-pressure limit at the point where the **first maximum of q(1 − p/p0) occurs** (q is the loading), as per consistency **criterion 1**, and a low-pressure limit at the lowest pressure point on the isotherm. Next, we consider a region that has the same upper pressure limit but a lower pressure limit that is shifted to the right by one point on the pressure axis. We continue to move the lower pressure limit to the right **until we locate a region with 4 consecutive data points**. Then, we shift the upper pressure limit to a smaller value by one point, and again move the lower pressure limit to the right as before until we reach another 4-point linear region. The process continues until we reach **a 4-point region at the lowest pressure point on the isotherm**, which we define as the “left-most” region. We select a linear region to compute the BET area that satisfies as many consistency criteria as possible. 

### Best Region for BET area calculation
To select the best region (i.e., the linear region that satisfies the most consistency criteria), we search through all possible “linear” regions.
Here, a **linear region is a set of 4 consecutive points having an R2 value of greater than 0.998**, and **fulfilling the consistency criteria 1 and 2**. We start with the “right-most” region from the isotherm, and check if it is “linear”. If it is, we store it as the “current best region”. If not, we continue to consider subsequent regions till we find one that is “linear”. Then, we move on to further regions as per the above scheme. If a region is not “linear”, it is disregarded. If it is, **we check if it satisfies consistency criteria 3, 4 and has an R2 > 0.9995**. The satisfaction of these three conditions indicates that the region satisfies all the requirements of the BET analysis. We choose this as the “final best region” and the algorithm ends. If not, we check if it satisfies more consistency criteria than the “current best region”. If it does, we replace the “current best region” with the new region. This process is repeated until we reach the “left-most” region. At this point, we end the search by choosing the “current best region” as the “final best region”. The **final best region** is used to compute the **BET area for the structure**. 

## ESW areas
The ESW area was computed from the loading at the first minima on the ESW plot. 

We computed the slope at each point and identified the point where the slope changed sign from negative to positive to obtain the ESW minima. The slope at each point was the slope of a line fitted through 7 points; 3 before and 3 after the selected point. Even though using 7 points to compute the slopes in our study yielded satisfactory results, we still highly recommend that users visually inspect the choice of the first local minimum to ensure that it is reasonable. 

## BET-ESW areas
The BET + ESW areas are computed in the same way as the BET areas except that the algorithm is forced to include the ESW minimum in the selected region. Thus, the chosen region **must satisfy** the consistency criteria 1, 2 and have an R2>0.998, and include the relative pressure corresponding to the ESW minimum point. The correct calculation of the BET + ESW areas depends on the correct identification of the ESW minimum. If the ESW minimum is wrongly identified, the BET + ESW area will also be wrong. Thus, we recommend that users ensure that the first minimum is correctly identified. 

## ML areas
The machine learning areas are computed using a Lasso linear regression model that takes as input the mean loading values of seven logarithmically divided pressure subregions. For more information, see [Beyond the BET Analysis: The Surface Area Prediction of Nanoporous Materials Using a Machine Learning Method](https://pubs.acs.org/doi/abs/10.1021/acs.jpclett.0c01518).

# Preparing Input files
AIF file: use http://raw2aif.herokuapp.com/ 
- Details of AIF file can be found in [this](https://github.com/AIF-development-team/adsorptioninformationformat) repository.

CSV file: see [example](/example_input/example_loading_data.csv)
# Using the Software
1. Use the following command in the terminal to run:
`python app.py`
2. Upload `AIF` or `CSV` formatted data.
3. Click `Run Calculation` and wait.

# References
- [Surface Area Determination of Porous Materials Using the Brunauer–Emmett–Teller (BET) Method: Limitations and Improvements](https://pubs.acs.org/doi/abs/10.1021/acs.jpcc.9b02116),
J. Phys. Chem. C 2019, 123, 33, 20195 - 20209
- [Beyond the BET Analysis: The Surface Area Prediction of Nanoporous Materials Using a Machine Learning Method](https://pubs.acs.org/doi/abs/10.1021/acs.jpclett.0c01518),
J. Phys. Chem. Lett. 2020, 11, 14, 5412 - 5417

# Authors
- Archit Datar (SESAMI python code development)
- Gianmarco Terrones (SESAMI web interface development)
- Prof. Yongchul G. Chung (project supervision, Mongo DB Atlas and Google Cloud integration)

# Funding Acknowledgement
- to do

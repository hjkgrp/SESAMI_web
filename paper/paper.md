---
title: 'SESAMI Web: An Accessible Interface for Surface Area Prediction of Materials from Adsorption Isotherms'
tags:
  - SESAMI
  - surface area
  - isotherm
  - BET
  - BET+ESW
  - machine learning
authors:
  - name: Gianmarco G. Terrones
    orcid: 0000-0001-5360-165X
    affiliation: 1g
  - name: Yu Chen
    orcid: 0000-0002-6530-0974
    affiliation: 2
  - name: Archit Datar
    orcid: 0000-0002-5276-0103
    affiliation: 3
  - name: Li-Chiang Lin
    orcid: 0000-0002-2821-9501
    affiliation: 4
  - name: Heather J. Kulik
    orcid: 0000-0001-9342-0191
    affiliation: "1, 5"
  - name: Yongchul G. Chung
    orcid: 0000-0002-7756-0589
    corresponding: true
    affiliation: 2
affiliations:
 - name: Department of Chemical Engineering, Massachusetts Institute of Technology, Cambridge, MA, USA
   index: 1
 - name: School of Chemical Engineering, Pusan National University, Busan, South Korea
   index: 2
 - name: William G. Lowrie Department of Chemical and Biomolecular Engineering, The Ohio State University, Columbus, OH, USA
   index: 3
 - name: Department of Chemical Engineering, National Taiwan University, Taipei, Taiwan
   index: 4
 - name: Department of Chemistry, Massachusetts Institute of Technology, Cambridge, MA, USA
   index: 5
date: 17 March 2023
bibliography: paper.bib


---

# Statement of need

Surface area determination is important for the evaluation of a porous material’s viability in applications ranging from catalysis to separations to gas storage. The most widely used approach for the evaluation of a material’s specific surface area, i.e. surface area per unit mass, is the Brunauer-Emmett-Teller (BET) method [@brunauer1938adsorption]. That is, given the adsorption isotherm of a gas (i.e., N~2~ or Ar) in an adsorbent, one can use the BET method to determine the specific surface area of the adsorbent upon identification of an appropriate linear region in the isotherm. The BET equation is used to fit the isotherm data to locate the linear region of pressure where a monolayer forms. Afterwards, the uptake value at a data point within the pressure range is chosen based on the Rouquerol consistency criteria [@rouquerol2013adsorption; @rouquerol2007bet]. The value is then multiplied by the molecular cross-sectional area of the adsorbate to obtain the material's surface area, under the assumption that the material's surface is completely covered by the adsorbate molecules. This procedure is sometimes automatically performed by commercial adsorption apparatuses that measure adsorption isotherms, but a suitable linear region is not always identified. Consequently, many researchers perform the analyses manually on a spreadsheet, which is time-consuming, nearly impossible for some types of isotherms, and leads to large variability in BET-calculated areas [@betsi]. These challenges have motivated the development of programs for the automated determination of BET areas [@betsi; @sesami_1; @sesami_2; @pygaps; @beatmap]. Furthermore, shortcomings of BET as a tool for surface area calculation, such as its relatively poor performance in treating high surface area materials with multimodal pore sizes [@gomez2016application; @wang2015ultrahigh], have led to the development of alternate methods for surface area calculation from isotherms [@sesami_1; @sesami_2].

# Theory background

In the BET method, specific surface area is calculation using Equation \ref{eq:surface_area}. $S$ is a material's specific surface area, $q_m$ is the molar amount of adsorbate forming a monolayer per unit mass of adsorbent, $N$ is the Avogadro constant, $A_m$ is the area taken up by a single adsorbate molecule in the monolayer. 

\begin{equation}\label{eq:surface_area}
S = \frac{q_m} N A_m
\end{equation}

In order to attain $q_m$, it is necessary to identify the monolayer loading region. This region is assigned to the section of the isotherm where $\frac{p/p_0}{1-p/p_0} \cdot \frac{1}{q}$ is linear as a function of $\frac{p}{p_0}$, where $p$ is the vapor pressure and $p_0$ is the saturated vapor pressure. $s$ is the slope of the line of $\frac{p/p_0}{1-p/p_0} \cdot \frac{1}{q}$ versus $\frac{p}{p_0}$ within the monolayer loading region, and $i$ is the intercept of the line [@fagerlund1973determination]. $s$ and $i$ can be used to calculate the BET constant, $C$, and $q_m$ (see Equations \ref{eq:C} and \ref{eq:qm}).  

\begin{equation}\label{eq:C}
C = \frac{s}{i} + 1
\end{equation}

\begin{equation}\label{eq:qm}
q_m = \frac{1}{s+i}
\end{equation}

The Rouquerol consistency criteria are as follows:  
<!-- Use two spaces for a line break. -->
1. The linear region should only be a range of $p/p_0$ in which the value of $q(1-p/p_0)$ monotonically increases with $p/p_0$, where $q$ is adsorbate loading.  
2. The value of $C$ should be positive.  
3. The value of the monolayer loading capacity should correspond to a value of $p/p_0$ which falls within the selected linear region.  
4. The value of $p/p_0$ calculated from BET theory, $1/(\sqrt{C}+1)$, and $p/p_0$ calculated from the third consistency rule should be equal (with ±10% tolerance).    
5. The linear region should end at the knee of the isotherm.  
Note to Greg: some of the criteria above are nearly verbatim from the SESAMI 1 paper


# Summary

In contrast to previously developed programs which require use of the command line [@betsi; @pygaps] and familiarity with Python [@sesami_1; @sesami_2; @pygaps], the SESAMI web interface allows a user to make surface area predictions on their web browser simply by uploading isotherm data. The website facilitates access to the previously developed SESAMI models (SESAMI 1 and 2) for porous material surface area prediction [@sesami_1; @sesami_2] and has been tested by experimental groups. The motivation for this interface is to lower the barrier of entry for research groups seeking to use SESAMI code, which was previously packaged in Python and Jupyter Notebook scripts.

SESAMI 1 applies computational routines to identify suitable linear regions of adsorption isotherms for BET surface area predictions [@fagerlund1973determination]. The automated workflow includes consideration of Rouquerol criteria and the use of coefficients of determination as a measure of linearity. Furthermore, SESAMI 1 supports a combined BET+ESW (excess sorption work) approach for linear region selection; this combined approach has been shown to outperform the BET method in some cases [@sesami_1]. A user can specify a cutoff R^2^ and a minimum R^2^, such that a candidate linear region is favored to be selected if it has an R^2^ above the cutoff, and a candidate linear region is only considered if it has an R^2^ above the minimum. On the other hand, SESAMI 2 applies a machine learning (specifically, regularized linear regression with LASSO) model for the accurate surface area prediction of high surface area materials, improving on BET performance for these materials [@sesami_2]. The LASSO model uses as input the average loading in seven isotherm pressure regions as well as pairwise products of these loadings. The SESAMI routines support isotherms with N~2~ and argon adsorbate at 77 K or 87 K, respectively. We note that a recent study shows that surface areas determined from N~2~ or Ar isotherms are similar, despite the latest 2015 IUPAC report's suggested use of Ar [@datar2022brunauer; @thommes2015physisorption].

The SESAMI web interface has extensive error handling and clearly alerts users of issues with their adsorption isotherm data. For example, it alerts the user if no ESW minima is found by SESAMI 1 or if the data is incompatible with SESAMI 2 code due to data sparsity in certain pressure regions. As shown in \autoref{fig:interface}, the interface displays SESAMI 1 calculation results including information on the chosen linear region, namely the satisfied Rouquerol criteria, the pressure range and number of data points in the region, and the coefficient of determination. The interface also displays intermediate SESAMI 1 values for surface area calculation, namely the BET constant, $C$, and the monolayer adsorption loading, $q_m$. Furthermore, the SESAMI web interface allows the user to download figures generated by SESAMI 1 that indicate, among other things, the chosen linear monolayer loading regions by the BET and BET+ESW approaches as well as the excess sorption work plot (\autoref{fig:interface}). The user can convert output from commercial equipment to AIF format and upload the converted data to the interface for analysis. The SESAMI web interface is publicly available at <https://sesami-web.org/>, and source code is available at <https://github.com/hjkgrp/SESAMI_web>.


![Information displayed by the SESAMI web interface after a calculation has been run, here for a GCMC isotherm of MIL-101. Apart from the inclusion of the LASSO prediction, default settings were used (e.g. N~2~ gas). a) Interface printout of information on the SESAMI 1 chosen linear regions, and SESAMI 1 and 2 calculation results. b) Figure download functionality for figures detailing the SESAMI 1 calculation.\label{fig:interface}](figures/web_interface.tif)

# Benchmarking

To assess the performance of the SESAMI code in predicting surface areas from isotherms, we benchmark the SESAMI routines against other similar programs for 13 simulated and 9 experimental N~2~ isotherms obtained at 77 K for 14 metal-organic frameworks (MOFs), some of which are shown in \autoref{fig:isotherms}. Simulated isotherms are obtained from grand canonical Monte Carlo (GCMC) simulations using the open-source RASPA software [@dubbeldam2016raspa], and experimental adsorption isotherms are obtained from the experimental data reported by Islamogu and coworkers [@islamoglu2022you]. The data are then used to calculate the surface areas from the SESAMI website, BETSI [@betsi; @betsi_github], pyGAPS [@pygaps; @pygaps_docs], and BEaTmap [@beatmap].

![The crystal structures and isotherms of 3 of the 14 MOFs used to benchmark different isotherm to surface area codes.\label{fig:isotherms}](figures/crystal_structs_and_isotherms.tif)

We find that over the set of 13 GCMC isotherms, the SESAMI machine learning model (run from the web interface) and BEaTmap have the best correlation with Zeo++ version 0.3 surface areas [@willems2012algorithms] calculated with a 1.67 Å probe N~2~ molecule (Tables \ref{gcmc_area_table} and \ref{corr_table}). Nevertheless, all software are in generally good agreement, underscoring the benefit of a computational approach to surface area calculation. The agreement between software is also not surprising due to the similar approach taken by most of the codes of considering multiple subsets of consecutive data points and applying checks like the Rouquerol criteria to select a linear region for BET analysis. Indeed, this agreement is also observed over the 9 experimental isotherms (Table \ref{exp_area_table}). The benchmark isotherms, XLSX files of surface area predictions across different software tools for both GCMC and experimental isotherms, detailed settings used for each software, and analysis scripts employed are available at <https://github.com/hjkgrp/SESAMI_web>.

Table: Calculated surface areas (m^2^/g) for the 13 MOFs with GCMC isotherms. Cases where a software does not find a surface area are denoted by N/A. Zeo++ calculations are conducted with the same CIF files used to generate GCMC isotherms, and a 1.67 Å probe N~2~ molecule, the high accuracy flag, and 2,000 Monte Carlo samples per atom are used. All other software take as input the GCMC isotherms.\label{gcmc_area_table}

| | SESAMI 1 (BET)  | SESAMI 1 (BET+ESW)  | SESAMI 2 (LASSO)  | BETSI  | pyGAPS  | BEaTmap  | Zeo++  |
| ------ | ------ | ------- | ------ | ---- | ---- | ----- | ---- |
| HKUST-1 | 2001 | 1933 | 2089 | 1962 | 1902 | 1980 | 2397 |
| IRMOF-1 | 3502 | 3543 | 3123 | 3519 | 3504 | N/A | 3722 |
| MIL-100 (Cr) | 2107 | 1853 | 2111 | N/A | 1852 | 2094 | 1957 |
| MIL-100 (Fe) | 2386 | 2438 | 2203 | 2426 | 82 | 2423 | 1933 |
| MIL-101 | 3828 | 2862 | 2944 | N/A | 2939 | 3331 | 3164 |
| MIL-53 (Al) | 1221 | 1168 | 1405 | 1164 | 1183 | 1212 | 1510 |
| MOF-74 (Mg) | 1828 | 1834 | 1902 | N/A | 1839 | 1791 | 1796 |
| MOF-808 | 44 | N/A | 1275 | N/A | N/A | 1147 | 1690 |
| NU-1000 | 2439 | 2181 | 2633 | N/A | 2144 | 2672 | 3050 |
| NU-1200 | 2711 | 934 | 2601 | N/A | 1073 | 2930 | 3192 |
| NU-1500 (Fe) | 3543 | 3594 | 3111 | N/A | 3758 | 3492 | 3944 |
| UiO-66 | 1239 | 1239 | 1443 | N/A | 1242 | 1304 | 1289 |
| ZIF-8 | 1429 | 1386 | 1575 | 1381 | 1390 | 1414 | 1588 |

Table: Comparison between surface area predictions from software for isotherm to surface area calculation and from Zeo++, over the 13 MOFs with GCMC isotherms. The mean absolute percent error and Pearson correlation coefficient are taken with respect to Zeo++ predictions for each software, over all successful surface area calculations for that software.\label{corr_table}

| Software | Mean absolute percent error (MAPE)  | Pearson correlation coefficient  | Successful calculations (out of 13) |
| ------ | ---- | ----- | --- |
| SESAMI 1 (BET) | 19.4 | 0.85 | 13 |
| SESAM1 1 (BET+ESW) | 17.9 | 0.72 | 12 |
| SESAMI 2 (LASSO) | 12.4 | 0.95 | 13 |
| BETSI | 17.0 | 0.92 | 5 |
| pyGAPS | 23.0 | 0.75 | 12 |
| BEaTmap | 12.6 | 0.93 | 12 |

Table: Calculated surface areas (m^2^/g) for the 9 MOFs with experimental isotherms. Cases where a software does not find a surface area are denoted by N/A. All other software take as input the experimental isotherms.\label{exp_area_table}

| | SESAMI 1 (BET)  | SESAMI 1 (BET+ESW)  | SESAMI 2 (LASSO)  | BETSI  | pyGAPS  | BEaTmap  |
| ------ | ------ | ------- | ------ | ---- | ---- | ----- |
| HKUST-1 | 1505 | 1466 | 1668 | N/A | 1495 | 1498 |
| MOF-74 (Mg) | 1580 | 1467 | 1692 | N/A | 1574 | 1565 |
| MOF-808 | 1998 | 900 | 1727 | N/A | 2439 | 1752 |
| NU-1000 | 2154 | 2090 | 2385 | N/A | 2654 | 2459 |
| NU-1200 | 2893 | 2718 | 2781 | 2758 | 3917 | 3069 |
| NU-1500 (Fe) | 3305 | 3409 | 2809 | N/A | 3413 | 3227 |
| SIFSIX-3 (Ni) | 356 | 201 | 716 | N/A | 355 | 353 |
| UiO-66 | 1251 | 1228 | 1413 | 1250 | 1249 | 1246 |
| ZIF-8 | 1092 | 910 | 1214 | N/A | 1082 | 1047 |

Table: Settings used for software for isotherm to surface area calculation. All BET calculations by SESAMI 1 and pyGAPS reported in this work fulfill Rouquerol criteria 1 and 2.\label{settings_table}
<!-- Need to use grid table for new lines in table. https://stackoverflow.com/questions/11700487/how-do-i-add-a-newline-in-a-markdown-table -->

+-----------------------------------+------------------------------------+-----------------------------------------------------+
| Software                          | Mode of access                     | Settings                                            |
+===================================+====================================+=====================================================+
| SESAMI 1 (BET)\                   | Run from SESAMI web interface\     | Type of gas: Nitrogen\                              |
| SESAM1 1 (BET+ESW)\               | Accessed February 2023             | Scope: BET and BET+ESW\                             |
| SESAMI 2 (LASSO)                  |                                    | R^2^ cutoff: 0.9995\                                |
|                                   |                                    | R^2^ min: 0.998\                                    |
|                                   |                                    | Include ML prediction?: Yes\                        |
+-----------------------------------+------------------------------------+-----------------------------------------------------+
| BETSI                             | GUI started from the command line\ | Minimum number of points in the linear region: 10\  |
|                                   | GitHub version 1.0.20              | Minimum R^2^: 0.998\                                |
|                                   |                                    | Rouquerol criteria 1: Yes\                          |
|                                   |                                    | Rouquerol criteria 2: Yes\                          |
|                                   |                                    | Rouquerol criteria 3: No\                           |
|                                   |                                    | Rouquerol criteria 4: No\                           |
|                                   |                                    | Rouquerol criteria 5: No\                           |
+-----------------------------------+------------------------------------+-----------------------------------------------------+
| pyGAPS                            | Python package\                    | Used function `area_BET`\                           |
|                                   | Conda version 4.4.2                | Default values for keyword arguments\               |
+-----------------------------------+------------------------------------+-----------------------------------------------------+
| BEaTmap                           | Run from BEaTmap web interface\    | Adsorbate cross-sectional area: 16.2 Å^2^/molecule\ |
|                                   | Accessed February 2023             | Criteria 1: Yes\                                    |
|                                   |                                    | Criteria 2: Yes\                                    |
|                                   |                                    | Criteria 3: No\                                     |
|                                   |                                    | Criteria 4: No\                                     |
|                                   |                                    | Minimum number of data points: 5\                   |
|                                   |                                    | BET calculation criteria: Maximum data points       |
+-----------------------------------+------------------------------------+-----------------------------------------------------+


# Acknowledgements

This publication was made possible by the generous support of the Government of Portugal through the Portuguese Foundation for International Cooperation in Science, Technology and Higher Education and was undertaken in the MIT Portugal Program. Software and website development was supported by the Office of Naval Research under grant number N00014-20-1-2150, as well as by the National Research Foundation of Korea (NRF) under grant number 2020R1C1C1010373 funded by the government of Korea (MSIT). L. C. L. acknowledges the support from the Yushan Young Scholar Program (NTU-110VV009) and the National Science of Technology Council (110-2222-E-002-011-MY3). We thank Timur Islamoglu, Karam Idrees, and Omar Farha for kindly providing the raw data of the experimental isotherms in the work by @islamoglu2022you.

<!-- # Citations

Citations to entries in paper.bib should be in
[rMarkdown](http://rmarkdown.rstudio.com/authoring_bibliographies_and_citations.html)
format.

If you want to cite a software repository URL (e.g. something on GitHub without a preferred
citation) then you can do it with the example BibTeX entry below for @fidgit.

For a quick reference, the following citation commands can be used:
- `@author:2001`  ->  "Author et al. (2001)"
- `[@author:2001]` -> "(Author et al., 2001)"
- `[@author1:2001; @author2:2001]` -> "(Author1 et al., 2001; Author2 et al., 2002)" -->

# References
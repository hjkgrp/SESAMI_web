---
title: 'SESAMI web: an accessible interface for surface area prediction from adsorption isotherms'
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
    affiliation: 1
  - name: Yu Chen
    affiliation: 2
  - name: Li-Chiang Lin
    orcid: 0000-0002-2821-9501
    affiliation: 3
  - name: Heather J. Kulik
    orcid: 0000-0001-9342-0191
    affiliation: "1, 4"
  - name: Yongchul G. Chung
    orcid: 0000-0002-7756-0589
    corresponding: true
    affiliation: 1
affiliations:
 - name: Department of Chemical Engineering, Massachusetts Institute of Technology, USA
   index: 1
 - name: School of Chemical and Biomolecular Engineering, Pusan National University, South Korea
   index: 2
 - name: William G. Lowrie Department of Chemical and Biomolecular Engineering, The Ohio State University, USA
   index: 3
 - name: Department of Chemistry, Massachusetts Institute of Technology, USA
   index: 4
date: 17 March 2023
bibliography: paper.bib


---

# Statement of need

Surface area determination is important for the evaluation of a porous material’s viability in applications ranging from catalysis to separations to gas storage. The most widely used approach for the evaluation of a material’s specific surface area, i.e. surface area per unit mass, is Brunauer-Emmett-Teller (BET) theory [@brunauer1938adsorption]. Given the adsorption isotherm of a gas in an adsorbent, one can use BET theory to determine the specific surface area of the adsorbent upon identification of an appropriate linear region in the isotherm. This procedure is sometimes automatically performed by the software program that comes with the commercial adsorption apparatus that measures the adsorption isotherm. Unfortunately, the linear region selection is a large source of variability in BET-calculated areas. In addition, for certain types of isotherms, automatic selection of the linear region by the commercial software sometimes fails. As a result, many researchers perform the analyses manually on a spreadsheet, which can become time-consuming and nearly impossible for some types of isotherms [@betsi]. These challenges have motivated the development of programs for the automated determination of BET areas [@betsi; @sesami_1; @sesami_2; @pygaps; @beatmap]. Furthermore, shortcomings of BET as a tool for surface area calculation, such as its relatively poor performance in treating high surface area materials with multimodal pore sizes [@gomez2016application; @wang2015ultrahigh], have led to the development of alternate methods for surface area calculation from isotherms [@sesami_1; @sesami_2].

# Summary

In contrast to previously developed programs which require use of the command line [@betsi; @pygaps] and familiarity with Python [@sesami_1; @sesami_2; @pygaps], the SESAMI web interface allows a user to generate surface area predictions on their web browser by uploading isotherm data. The website facilitates access to the previously developed SESAMI models (SESAMI 1 and 2) for porous material surface area prediction [@sesami_1; @sesami_2] and has been tested by experimental groups. The motivation for this interface is to lower the barrier of entry for research groups seeking to use SESAMI code, which was previously packaged in Python and Jupyter Notebook scripts.

SESAMI 1 applies computational routines to identify suitable linear regions of adsorption isotherms for Brunauer-Emmett-Teller surface area prediction [@fagerlund1973determination]. The automated workflow includes consideration of Rouquerol criteria [@rouquerol2013adsorption; @rouquerol2007bet] and the use of coefficients of determination as a measure of linearity. Furthermore, SESAMI 1 supports a combined BET+ESW (excess sorption work) approach for linear region selection; this combined approach has been shown to outperform the BET approach in some cases [@sesami_1]. A user can specify a cutoff R^2^ and a minimum R^2^, such that a candidate linear region is favored to be selected if it has an R^2^ above the cutoff, and a candidate linear region is only considered if it has an R^2^ above the minimum. On the other hand, SESAMI 2 applies a machine learning (specifically, regularized linear regression with LASSO) model for the accurate surface area prediction of high surface area materials, improving on BET performance for these materials [@sesami_2]. The LASSO model uses as input the average loading in seven isotherm pressure regions as well as pairwise products of these loadings. The SESAMI routines support isotherms with N~2~ and argon adsorbate at 77 K or 87 K, respectively.

The SESAMI web interface has extensive error handling and clearly alerts users of issues with their adsorption isotherm data. For example, it alerts the user if no ESW minima is found by SESAMI 1 or if the data is incompatible with SESAMI 2 code due to data sparsity in certain pressure regions. As shown in \autoref{fig:interface}, the interface displays SESAMI 1 calculation results including information on the chosen linear region, namely the satisfied Rouquerol criteria [@rouquerol2013adsorption; @rouquerol2007bet], the pressure range and number of data points in the region, and the coefficient of determination. The interface also displays intermediate SESAMI 1 values for surface area calculation, namely the BET constant, C, and the monolayer adsorption loading, q~m~. Furthermore, the SESAMI web interface allows the user to download figures generated by SESAMI 1 that indicate, among other things, the chosen linear monolayer loading regions by the BET and BET+ESW approaches as well as the excess sorption work plot (\autoref{fig:interface}). The user can convert output from commercial equipment to AIF format and upload the converted data to the interface for analysis. The SESAMI web interface is publicly available at <https://sesami-web.org/>, and source code is available at <https://github.com/hjkgrp/SESAMI_web>.


![Information displayed by the SESAMI web interface after a calculation has been run. a) Interface printout of information on the SESAMI 1 chosen linear regions, and SESAMI 1 and 2 calculation results. b) Figure download functionality for figures detailing SESAMI 1 calculation.\label{fig:interface}](figures/web_interface.tif)

# Benchmarking

To assess the performance of SESAMI code in predicting surface areas from isotherms, we benchmarked the SESAMI routines against other similar programs for 13 simulated and 9 experimental N~2~ isotherms obtained at 77 K for 14 metal-organic frameworks, some of which are shown in \autoref{fig:isotherms}. Simulated isotherms were obtained from Grand Canonical Monte Carlo (GCMC) simulations using RASPA open-source software [@dubbeldam2016raspa], and experimental adsorption isotherms were obtained from the experimental data reported by Islamogu and coworkers [@islamoglu2022you]. The data were then used to calculate the surface areas from the SESAMI website, BETSI [@betsi; @betsi_github], pyGAPS [@pygaps; @pygaps_docs], and BEaTmap [@beatmap].

![The crystal structures and isotherms of 3 of the 14 metal-organic frameworks used to benchmark different isotherm to surface area codes.\label{fig:isotherms}](figures/crystal_structs_and_isotherms.tif)

We find that over the set of 13 GCMC isotherms, the SESAMI machine learning model and BEaTmap have the best correlation with Zeo++ surface areas [@willems2012algorithms] calculated with a 1.67 Å probe N~2~ molecule (Tables \ref{corr_table} and \ref{area_table}). Nevertheless, all software are in generally good agreement, underscoring the benefit of a computational approach to surface area calculation. The agreement between software is also not surprising due to the similar approach taken by most of the codes of considering multiple subsets of consecutive data points and applying checks like the Rouquerol criteria to select a linear region for BET analysis. The benchmark isotherms, CSV files of surface area predictions across different software tools for both GCMC and experimental isotherms, details about settings used for each software, and employed analysis scripts are available at <https://github.com/hjkgrp/SESAMI_web>.

Table: Comparison between surface area predictions from Zeo++ with a 1.67 Å probe N~2~ molecule, and software for isotherm to surface area calculation. Zeo++ calculations were conducted with the same CIF files used to generate GCMC isotherms, and the high accuracy flag and 2,000 samples were used. The surface area calculation software took as input the GCMC isotherms. The number of successful isotherm to surface area calculations for each software are indicated as well. \label{corr_table}

| Surface area calculation software | Mean Absolute Percent Error (MAPE)  | Pearson correlation coefficient  | Successful calculations  |
| ------- | --- | --- | --- |
| SESAMI 1 (BET) | 19.4 | 0.85 | 13 |
| SESAM1 1 (BET+ESW) | 17.9 | 0.72 | 12 |
| SESAMI 2 (LASSO) | 12.4 | 0.95 | 13 |
| BETSI | 17.0 | 0.92 | 5 |
| pyGAPS | 23.0 | 0.75 | 12 |
| BEaTmap | 12.6 | 0.93 | 12 |

Table: Calculated surface areas (m^2^/g) for the 13 MOFs with GCMC isotherms. Cases where a software does not find a surface area are denoted by N/A. \label{area_table}

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


# Acknowledgements

This publication was made possible by the generous support of the Government of Portugal through the Portuguese Foundation for International Cooperation in Science, Technology and Higher Education and was undertaken in the MIT Portugal Program. Software and website development was supported by the Office of Naval Research under grant number N00014-20-1-2150, as well as by the National Research Foundation of Korea (NRF) under grant number 2020R1C1C1010373 funded by the government of Korea (MSIT). We thank Omar Farha, Timur Islamoglu, and Karam Idrees for kindly providing the raw data of the experimental isotherms in the work by @islamoglu2022you.

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
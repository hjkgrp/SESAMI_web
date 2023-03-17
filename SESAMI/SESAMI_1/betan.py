import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import ticker
import pandas as pd
import os
import numpy as np
import scipy
import statsmodels.formula.api as smf
import scipy.stats as ss

"""
Created on Mon Apr  9 11:29:12 2018

@author: architdatar

Integrated for use with the SESAMI website by Gianmarco Terrones.
"""

mpl.use("agg")
mpl.rcParams["mathtext.default"] = "regular"  # preventing italics in axis labels
pd.set_option("display.max_rows", 500)


class BETAn:
    def __init__(
        self, selected_gas, selected_temperature, minlinelength, plotting_information
    ):
        self.R = 8.314  # J/mol/K
        self.N_A = 6.023e23  # molecules/mol

        self.T = selected_temperature

        if selected_gas == "Argon":
            self.selected_gas_cs = 0.142e-18  # m²/molecule; Ref: 10.1039/D1TA08021K
        elif selected_gas == "Nitrogen":
            self.selected_gas_cs = 0.162e-18  # m²/molecule; Ref: 10.1039/D1TA08021K
        # elif selected_gas == "Carbon dioxide":
        #     self.selected_gas_cs = 0.142e-18  # m²/molecule; Ref: 10.1039/D1TA08021K
        # elif selected_gas == "Krypton":
        #     self.selected_gas_cs = 0.210e-18  # m²/molecule; Ref: 10.1039/D1TA08021K
        elif selected_gas == "Custom":
            # Multiply by 1e-20 to convert to m²/molecule, from Å²/molecule
            self.selected_gas_cs = float(plotting_information['custom cross section']) * 1e-20 

        self.loadunits = "mol/kg"
        # self.weight_of_box = 1e-20 #gm

        self.minlinelength = (
            minlinelength  # min number of points for it to be called a line.
        )

        self.R2cutoff = plotting_information[
            "R2 cutoff"
        ]  # Website default is 0.9995

        # This is the minimum R2 value required for a region to be considered a line.
        self.R2min = plotting_information[
            "R2 min"
        ]  # Website default is 0.998 

        # Setting these variables to none allows users to set them externally later on.
        self.eswminimamanual = "No"
        self.eswminima = None
        self.con1limitmanual = "No"
        self.con1limit = None

    def prepdata(
        self, data, loading_col="Loading", conv_to_molperkg=1, p0=1e5, full=True
    ):
        """
        This function prepares data for BET analysis. We create the columns P_rel, BETy, BET_y2 and phi. Needs arguments data and weight of box to calculate the required columns.

        Parameters 
        ----------
        data : pandas.core.frame.DataFrame
            Represents an isotherm. Columns are "Pressure" and "Loading".
        loading_col : str
            The name of the column in data that contains the loading data.
        conv_to_molperkg : int
            Specify the conversion to convert from the current units to mol/kg. For SESAMI 1.0 integrated with the SESAMI website, this is taken care of before betan.py.
        p0 : float
            Saturation pressure. We assume that we want to plot from 0 to this pressure.
        full : bool
            Indicates whether or not to calculate Consistency 1 maximum and ESW minimum. 

        Returns
        -------
        data: pandas.core.frame.DataFrame
            The augmented data representing an isotherm. Columns are "Pressure", "Loading", "P_rel", "BETy", "BET_y2", and "phi".

        """
        # Next, we will prepare the data for analysis by assigning the appropriate column numbers and names.
        data = data.copy(deep=True)
        # First, we will sort the incoming data.
        data["P_rel"] = data["Pressure"] / p0
        data.sort_values("P_rel", inplace=True)
        data["Loading"] = data[loading_col] * conv_to_molperkg
        # data['VolLoad'] = vol_loading
        data["BETy"] = data["P_rel"] / (data["Loading"] * (1 - data["P_rel"]))
        data["BET_y2"] = data["Loading"] * (1 - data["P_rel"]) # Used for first Rouquerol consistency criterion. See SESAMI 1 paper.
        data["phi"] = (
            data["Loading"] / 1000 * self.R * self.T * scipy.log(data["P_rel"])
        )  # J/g ; equation 1 of https://doi.org/10.1021/acs.jpcc.9b02116. Factor of 1000 to convert from 1/kg to 1/g

        # We will also add a line here that calculates the consistency 1 limit. This will ensure that the we need to compute the upper limit of consistency1 only once.
        if (
            full
        ):  # In some applications, we don't want the ESW limits and stuff, we only want the values.
            # In those cases, we can simply change this parameter to something else.
            if self.con1limitmanual == "No":
                self.con1limit = self.getoptimum(
                    data, column="BET_y2", x="P_rel", how="Maxima", which=0, points=3
                )[0]

            if self.eswminimamanual == "No":
                self.eswminima = self.getoptimum(
                    data, column="phi", x="P_rel", how="Minima", which=0, points=3
                )[0]

        return data

    def getoptimum(self, data, column=None, x=None, how="Minima", which=0, points=3):
        """
        This function will get the optimum value and the corresponding index from a given set of finite number of data points.
        Such a function is not easily available elsewhere. The rationale is that we compute the slope at every point by fitting
        a line through 'points' number of points before and after the chosen point. We then compute the minimum where the slope changes
        sign. In order to ensure that we are not selecting a point due to the noise, we compute the mean value of 'points' number of points
        before and after the chosen point and ensure that it is greater than the value at the chosen point (suggested by Li-Chiang).

        This code may not be very efficient since it involves a lot of regression, but it works for a small quantum of data.

        Parameters 
        ----------
        data : pandas.core.frame.DataFrame
            Represents an isotherm. Columns are "Pressure", "Loading", "P_rel", "BETy", "BET_y2", and "phi".
        column : str
            The name of the feature for which to get the optimum.            
        x : str
            The name of the dependent variable. Always "P_rel" for this script.
        how : str
            "Minima" or "Maxima", depending if it is desired to minimize or maximize the feature in `column`.
        which : int
            Which of the good minimas (good meaning that it is not just a minima due to noise) to choose from.
        points : int
            How many points before and after a point to use in computing slope. Also used in computing the mean of the points before and after a point.

        Returns
        -------
        minima : numpy.int64
            Index of minima of the feature represented by `column`.
        targetvalue : numpy.float64
            Minima of the feature represented by `column`.
        data[["x", "target", "slopes"]] : pandas.core.frame.DataFrame
            Contains information of interest for the independent and dependent variable, as well as the slopes at each data point for target vs x.

        """
        data = data.copy(deep=True)
        start = data.index.values[0]
        end = data.index.values[-1]

        # Target is the name of the column that we will choose
        if column is None:
            target = data.columns[0]
        if type(column) == int:
            target = data.columns[column]
        if type(column) == str:
            target = column

        data["target"] = data[target]
        if how == "Maxima":
            data["target"] = -data["target"]

        if x is None:
            data["x"] = data.index
        elif type(x) == int:
            data["x"] = data[data.columns[x]]
        elif type(x) == str:
            data["x"] = data[x]
        else:
            raise ValueError

        data["slopes"] = 0.0
        points = int(points)  # Number of points before and after a chosen point.
        for i in np.arange(start + points, end - points + 1, 1):
            regdata = data[i - points : i + points + 1][["target", "x"]]
            res = smf.ols("target ~ x", regdata).fit()
            slope = res.params[1]
            data.at[i, "slopes"] = slope
        minimas = data.index[
            (data["slopes"].shift(1).fillna(0) < 0)
            & (data["slopes"].shift(-1).fillna(0) > 0)
        ].values
        # We thus have a list of potential minimas. But now, we need to discard the ones that are there because of the noise.
        goodminimas = []
        if minimas.shape[0] != 0:
            for minimap in minimas:
                if (
                    data[minimap - points : minimap]["target"].mean()
                    > data[data.index == minimap]["target"].values[0]
                    and data[minimap + 1 : minimap + points + 1]["target"].mean()
                    > data[data.index == minimap]["target"].values[0]
                ):
                    # This means that this is really a minima and not just due to the noise.
                    goodminimas.append(minimap)
            if goodminimas != []:
                # Now, we need to get the minima that we are really looking for.
                if type(which) == int:
                    minima = goodminimas[which]
                    targetvalue = data[data.index == minima]["target"].values[0]
                if type(which) == list:
                    minima = [goodminimas[minima] for minima in which]
                    targetvalue = [
                        data[data.index == minima]["target"].values[0]
                        for minima in minima
                    ]
            else:
                minima = None
                targetvalue = None
        else:
            minima = None
            targetvalue = None

        return minima, targetvalue, data[["x", "target", "slopes"]]

    def th_loading(self, x, params):
        """
        Calculates the BET loading given relative pressures and BET parameters.
        See equation 3 of Fagerlund, G. (1973). Determination of specific surface by the BET method.

        Parameters 
        ----------
        x : numpy.ndarray
            Array of p/p0 values. p is vapor pressure, and p0 is saturation vapor pressure.
        params : tuple
            The variables needed for the BET equations. A molar version of Xm (qm) and C, from Fagerlund, G. (1973). Determination of specific surface by the BET method.        

        Returns
        -------
        bet_loading: numpy.ndarray
            The mass adsorbed at each relative vapor pressure in x.

        """
        [qm, C] = params
        bet_y = (C - 1) / (qm * C) * x + 1 / (qm * C)
        bet_loading = x / (bet_y * (1 - x)) # See equation 3 of the original BET paper.
        return bet_loading

    def gen_phi(self, load, p_rel, T=87.0):
        """
        This function will generate phi values given the x points.

        Parameters 
        ----------
        load : numpy.ndarray
            The adsorption loadings of the isotherm data.
        p_rel : numpy.ndarray
            The relative pressures of the isotherm data.
        T : float
            The temperature.

        Returns
        -------
        phi: numpy.ndarray
            Excess sorption work.

        """
        # See equation 1 of 10.1021/acs.jpcc.9b02116. The SESAMI 1 paper.
        phi = load / 1000 * 8.314 * T * scipy.log(p_rel)

        return phi

    def makeisothermplot(
        self,
        plotting_information,
        ax,
        data,
        yerr=None,
        maketitle="Yes",
        tryminorticks="Yes",
        xscale="log",
        with_fit="No",
        fit_data=None,
    ):
        """
        This function takes an axis as an input and makes an isotherm plot on it.

        Parameters 
        ----------
        plotting_information : dict
            Lots of plotting and calculation settings from the front end (i.e. the SESAMI webpage). The keys are 'dpi', 'font size', 'font type', 'legend', 'R2 cutoff', 'R2 min', 'gas', 'scope', 'ML', 'custom adsorbate', 'custom cross section', 'custom temperature', and 'custom saturation pressure'.
        ax : matplotlib.axes._subplots.AxesSubplot
            The axes on which to plot.
        data : pandas.core.frame.DataFrame
            Represents an isotherm. Columns are "Pressure", "Loading", "P_rel", "BETy", "BET_y2", and "phi".
        yerr : float or array-like
            The errorbar sizes.
        maketitle : str
            If set to "Yes", the plot will be titled; otherwise, not.        
        tryminorticks : str
            If xscale='log' and tryminorticks='Yes', the xscale will be from 0 to 1. The user has no control over it.
        xscale : str
            Either 'log' or 'linear'. Affects the x-axis. If xscale='log' and tryminorticks='Yes', the xscale will be from 0 to 1. The user has no control over it.
        with_fit : str
            If set to "Yes", the plot will include the BET fit, the BET+ESW fit, the BET region, and the BET+ESW region; otherwise, not.            
        fit_data : list
            Information for BET and BET+ESW. In particular (for BET and for BET+ESW), the indices of the data points that start and end the chosen linear region (rbet), as well as a molar version of Xm (called qm here) and C. These last two are referred to as params in the code.

        Returns
        -------
        None

        """     
        scope = plotting_information['scope']

        ax.errorbar(
            data["P_rel"],
            data["Loading"],
            yerr=yerr,
            fmt="o",
            capsize=3,
            label="BET data points",
        )

        ax.xaxis.label.set_text("$p/p_0$")
        ax.yaxis.label.set_text("$q$" + " / " + "$%s$" % self.loadunits)

        if xscale == "log":
            ax.set_xscale("log")
            if tryminorticks == "Yes":
                locmaj = mpl.ticker.LogLocator(base=10.0, numticks=10)
                ax.xaxis.set_major_locator(locmaj)
                locmin = mpl.ticker.LogLocator(
                    base=10.0,
                    subs=(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9),
                    numticks=10,
                )
                ax.xaxis.set_minor_locator(locmin)
                ax.xaxis.set_minor_formatter(mpl.ticker.NullFormatter())
                # We will try to set the ticks for y axis.
        if xscale == "linear":
            ax.set_xlim((0, 1))
            ax.set_xticks(np.arange(0, 1.1, 0.1))

        ax.set_ylim((0, ax.get_ylim()[1]))

        if scope == 'BET and BET+ESW': # In this case, run the BET+ESW code and the BET code.
            if with_fit == "Yes":
                [bet_info, betesw_info] = fit_data
                [rbet, bet_params] = bet_info
                [rbetesw, betesw_params] = betesw_info

                if rbet != (None, None):
                    ax.axvspan(
                        data.at[rbet[0], "P_rel"],
                        data.at[rbet[1], "P_rel"],
                        facecolor=plt.cm.PuOr(70),
                        edgecolor="none",
                        alpha=0.6,
                        label="BET region",
                    )
                    ax.plot(
                        data["P_rel"].values,
                        self.th_loading(data["P_rel"].values, bet_params),
                        color=plt.cm.PuOr(20),
                        label="BET fit",
                    )
                if rbetesw != (None, None):
                    ax.axvspan(
                        data.at[rbetesw[0], "P_rel"],
                        data.at[rbetesw[1], "P_rel"],
                        facecolor=plt.cm.Greens(70),
                        edgecolor="none",
                        alpha=0.6,
                        label="BET+ESW region",
                    )
                    ax.plot(
                        data["P_rel"].values,
                        self.th_loading(data["P_rel"].values, betesw_params),
                        color=plt.cm.Greens(200),
                        label="BET+ESW fit",
                    )

                # Setting the y-axis limits to include more of the fit
                # Only consider BET values that correspond to x values within our plotting range
                bet_values = [
                    data["Loading"].values[i]
                    for i, value in enumerate(data["P_rel"].values)
                    if ax.get_xlim()[0] <= value <= ax.get_xlim()[1]
                ]

                y_max = max(bet_values) + 10

                ax.set_ylim(top=y_max)

            if self.eswminima is not None:
                ax.vlines(
                    data.at[self.eswminima, "P_rel"],
                    ax.get_ylim()[0],
                    ax.get_ylim()[1],
                    colors=plt.cm.Greens(200),
                    linestyles="dashed",
                    label="ESW minimum",
                )
            if self.con1limit is not None:
                ax.vlines(
                    data.at[self.con1limit, "P_rel"],
                    ax.get_ylim()[0],
                    ax.get_ylim()[1],
                    linestyles="dashed",
                    color=plt.cm.Purples(230),
                    label="Consistency 1 maximum",
                )

            if maketitle == "Yes":
                titletext = "Isotherm Data"
                ax.set_title(titletext)

            if plotting_information["legend"] == "Yes":  # Add a legend in this case.
                ax.legend(loc="upper left")

        else: # This indicates the scope is 'BET'. Only run the BET related code. No BET+ESW region nor BET+ESW fit nor ESW minimum vertical line.
            if with_fit == "Yes":
                [bet_info, betesw_info] = fit_data
                [rbet, bet_params] = bet_info

                if rbet != (None, None):
                    ax.axvspan(
                        data.at[rbet[0], "P_rel"],
                        data.at[rbet[1], "P_rel"],
                        facecolor=plt.cm.PuOr(70),
                        edgecolor="none",
                        alpha=0.6,
                        label="BET region",
                    )
                    ax.plot(
                        data["P_rel"].values,
                        self.th_loading(data["P_rel"].values, bet_params),
                        color=plt.cm.PuOr(20),
                        label="BET fit",
                    )

                # Setting the y-axis limits to include more of the fit
                # Only consider BET values that correspond to x values within our plotting range
                bet_values = [
                    data["Loading"].values[i]
                    for i, value in enumerate(data["P_rel"].values)
                    if ax.get_xlim()[0] <= value <= ax.get_xlim()[1]
                ]

                y_max = max(bet_values) + 10

                ax.set_ylim(top=y_max)

            if self.con1limit is not None:
                ax.vlines(
                    data.at[self.con1limit, "P_rel"],
                    ax.get_ylim()[0],
                    ax.get_ylim()[1],
                    linestyles="dashed",
                    color=plt.cm.Purples(230),
                    label="Consistency 1 maximum",
                )

            if maketitle == "Yes":
                titletext = "Isotherm Data"
                ax.set_title(titletext)

            if plotting_information["legend"] == "Yes":  # Add a legend in this case.
                ax.legend(loc="upper left")


    def makeconsistencyplot(
        self, plotting_information, ax3, data, maketitle="Yes", tryminorticks="Yes"
    ):
        """
        This function takes an axis as an input and makes the plot to see the limits of the region
        to be chosen to satisfy the first consistency criteria.

        Parameters 
        ----------
        plotting_information : dict
            Lots of plotting and calculation settings from the front end (i.e. the SESAMI webpage). The keys are 'dpi', 'font size', 'font type', 'legend', 'R2 cutoff', 'R2 min', 'gas', 'scope', 'ML', 'custom adsorbate', 'custom cross section', 'custom temperature', and 'custom saturation pressure'.
        ax3 : matplotlib.axes._subplots.AxesSubplot
            The axes on which to plot.
        data : pandas.core.frame.DataFrame
            Represents an isotherm. Columns are "Pressure", "Loading", "P_rel", "BETy", "BET_y2", and "phi".
        maketitle : str
            If set to "Yes", the plot will be titled; otherwise, not.
        tryminorticks : str
            If tryminorticks='Yes', the xscale will be from 0 to 1. The user has no control over it.

        Returns
        -------
        None

        """       
        ax3.xaxis.label.set_text("$p/p_0$")
        ax3.yaxis.label.set_text("$q(1-p/p_{0})$" + " / " + "$%s$" % self.loadunits)
        ax3.set_xscale("log")
        if maketitle == "Yes":
            titletext = "BET Consistency Plot"
            ax3.set_title(titletext)
        ax3.errorbar(data["P_rel"], data["BET_y2"], fmt="o", label="BET data points")
        ax3.set_ylim(ax3.get_ylim())

        if tryminorticks == "Yes":
            locmaj = mpl.ticker.LogLocator(base=10.0, numticks=10)
            ax3.xaxis.set_major_locator(locmaj)
            locmin = mpl.ticker.LogLocator(
                base=10.0,
                subs=(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9),
                numticks=10,
            )
            ax3.xaxis.set_minor_locator(locmin)
            ax3.xaxis.set_minor_formatter(mpl.ticker.NullFormatter())

        # We will use our code to determine x_max
        ind_max = self.con1limit
        if ind_max is not None:
            x_max = data[data.index == ind_max]["P_rel"].values[0]
            ax3.vlines(
                x_max,
                ax3.get_ylim()[0],
                ax3.get_ylim()[1],
                colors=plt.cm.Purples(230),
                linestyles="dashed",
                label="Consistency 1 maximum",
            )
        else:
            x_max = data["P_rel"][data["BET_y2"].idxmax()]

        # bbox_props = dict(boxstyle='square', ec= 'k', fc='w', lw = 1.0)
        # ax3.annotate('$p/p_0$'+'=%.2e'%(x_max), xy=(x_max,0 ),xytext =(-150, 15),
        #            textcoords='offset points',arrowprops=dict(facecolor='black',width=0.5, shrink=0.05, headwidth=5), bbox=bbox_props)
        if self.eswminima is not None:
            ax3.vlines(
                data.at[self.eswminima, "P_rel"],
                ax3.get_ylim()[0],
                ax3.get_ylim()[1],
                colors=plt.cm.Greens(200),
                linestyles="dashed",
                label="ESW minimum",
            )
        ax3.set_xlim(right=1.000)

        if plotting_information["legend"] == "Yes":  # Add a legend in this case.
            ax3.legend(loc="upper left")

    def makelinregplot(
        self, plotting_information, ax2, p, q, data, maketitle="Yes", mode="BET"
    ):
        """
        This function takes an axis as an input to make a plot summarizing information about a
        chosen linear region.

        Parameters 
        ----------
        plotting_information : dict
            Lots of plotting and calculation settings from the front end (i.e. the SESAMI webpage). The keys are 'dpi', 'font size', 'font type', 'legend', 'R2 cutoff', 'R2 min', 'gas', 'scope', 'ML', 'custom adsorbate', 'custom cross section', 'custom temperature', and 'custom saturation pressure'.
        ax2 : matplotlib.axes._subplots.AxesSubplot
            The axes on which to plot.
        p : numpy.int64
            The index of the data point that is chosen as the start of the linear region.
        q : numpy.int64
            The index of the data point that is chosen as the end of the linear region.
        data : pandas.core.frame.DataFrame
            Represents an isotherm. Columns are "Pressure", "Loading", "P_rel", "BETy", "BET_y2", and "phi".
        maketitle : str
            If set to "Yes", the plot will be titled; otherwise, not.
        mode : str
            Either "BET" or "BET+ESW". This affects the title of the plot if one is made.

        Returns
        -------
        my_dict: dict
            Contains SESAMI 1.0 intermediate calculation results, and the predicted area A_BET. The keys are "C", "qm", "A_BET", "con3", "con4", "length_linear_region", "R2_linear_region", "low_P_linear_region", and "high_P_linear_region".

        """
        bbox_props = dict(boxstyle="square", ec="k", fc="w", lw=1.0)

        if (p, q) == (None, None):
            ax2.text(
                0.97,
                0.22,
                "No suitable linear region found.",
                horizontalalignment="right",
                verticalalignment="center",
                bbox=bbox_props,
                transform=ax2.transAxes,
            )
        else:
            [
                linear,
                stats,
                C,
                qm,
                x_max,
                x_BET3,
                x_BET4,
                con1,
                con2,
                con3,
                con4,
                A_BET,
            ] = self.linregauto(p, q, data)
            [ftest, ttest, outlierdata, shaptest, r2, r2adj, results] = stats
            intercept, slope = results.params

            low_p = data.iloc[p]["Pressure"]
            high_p = data.iloc[q]["Pressure"]

            ax2.xaxis.label.set_text("$p/p_0$")
            ax2.yaxis.label.set_text(r"$\frac{p/p_0}{q(1-p/p_0)}$" + " / " + "kg/mol")
            if maketitle == "Yes":
                if mode == "BET":
                    titletext = "BET Linear Region Plot"
                elif mode == "BET+ESW":
                    titletext = "BET+ESW Linear Region Plot"
                ax2.set_title(titletext)
            ax2.errorbar(
                linear["P_rel"], linear["BETy"], fmt="o", label="BET data points"
            )
            ax2.plot(
                linear["P_rel"],
                slope * linear["P_rel"] + intercept,
                "k",
                alpha=0.5,
                label="Fitted Linear Region",
            )
            # ax2.text(linear['P_rel'].values[4], linear['BETy'].values[1], "R2=%.6f, C= %.4g,\nqm=%.2fmlSTP/gm, \nBETSA=%.2f m2/g"%(results.rsquared, C, qm,A_BET))

            # Change: I comment out the properties, since they will be displayed separately on the website.
            # ax2.text(0.97, 0.22,'C= %.4g\n'%C+'$q_m$'+'=%.2f mol/kg \nBETSA=%.3f'%(qm,A_BET)+ '$m^{2}/g$'+'\nConsistency 3: %s\n Consistency 4: %s\n'%(con3, con4)+'Length of region: %d\n'%(q-p)+'$R^{2}$'+'=%.6f'%(results.rsquared),horizontalalignment='right', verticalalignment='center', bbox = bbox_props,transform= ax2.transAxes) # TODO here are the properties
            ax2.xaxis.set_major_formatter(ticker.FormatStrFormatter("%.1e"))
            ax2.yaxis.set_major_formatter(ticker.FormatStrFormatter("%.1e"))
            plt.setp(ax2.xaxis.get_majorticklabels(), rotation=30)
            plt.setp(ax2.yaxis.get_majorticklabels(), rotation=30)
            # fig2.subplots_adjust(left =-0.1)

            if plotting_information["legend"] == "Yes":  # Add a legend in this case.
                ax2.legend()

        # Returning stats to display in the website.
        my_dict = {
            "C": C,
            "qm": qm,
            "A_BET": A_BET,
            "con3": con3,
            "con4": con4,
            "length_linear_region": q - p,
            "R2_linear_region": results.rsquared,
            "low_P_linear_region": low_p,
            "high_P_linear_region": high_p
        }  # This will be BET_dict or BET_ESW_dict
        return my_dict

    def eswdata(self, data, eswpoints=3):
        """
        This function computes the ESW area and ESW minima.
        Inputs:
            data: The DataFrame containing columns 'Pressure' in Pa and 'Loading' in mol/kg framework.
            eswpoints (optional): int. Helps calculate the slope at a point. The number of points around the point at which slope is to be
            computed.
        Outputs:
            data['Loading']: Pandas Series object containing 'Loading' data in mol/kg framework
            data['phi']: Pandas series object containing 'phi' values in J/g
                phi: qxNaxAcs where q: Loading in mol/kg=framework, Na: Avogadro number, Acs: Cross-sectional area of Ar atom.
            minima: numpy.int64. The index of 'Loading' value corresponding to a minima of 'phi' values.
            eswarea: numpy.float64. The surface area in m²/g corresponding to the 'Loading' at which 'phi' is minimum.
        """
        data = data.copy(deep=True)

        data["phi"] = (
            data["Loading"] / 1000 * self.R * self.T * scipy.log(data["P_rel"])
        )  # J/g ; equation 1 of https://doi.org/10.1021/acs.jpcc.9b02116. Factor of 1000 to convert from 1/kg to 1/g

        # Now, we will use our function to get minima.
        if self.eswminima is None:
            minima = self.getoptimum(
                data, column="phi", x="P_rel", how="Minima", which=0, points=eswpoints
            )[0]
        else:
            minima = self.eswminima
        if minima is not None:
            eswarea = (
                data[data.index == minima]["Loading"].values[0]
                / 1000
                * self.N_A
                * self.selected_gas_cs
            )  # m²/g
        else:
            eswarea = None

        return [data["Loading"], data["phi"], minima, eswarea]

    def makeeswplot(
        self,
        plotting_information,
        ax,
        data,
        eswpoints=3,
        maketitle="Yes",
        with_fit="No",
        fit_data=None,
    ):
        """
        This function modifies the axes parsed as input to make an ESW figure.
        Inputs:
            ax: Axes to be modified to make a figure upon
            data: The DataFrame from which the graph is to be constructed.

        Parameters 
        ----------
        plotting_information : dict
            Lots of plotting and calculation settings from the front end (i.e. the SESAMI webpage). The keys are 'dpi', 'font size', 'font type', 'legend', 'R2 cutoff', 'R2 min', 'gas', 'scope', 'ML', 'custom adsorbate', 'custom cross section', 'custom temperature', and 'custom saturation pressure'.
        ax : matplotlib.axes._subplots.AxesSubplot
            The axes on which to plot.
        data : pandas.core.frame.DataFrame
            Represents an isotherm. Columns are "Pressure", "Loading", "P_rel", "BETy", "BET_y2", and "phi".
        eswpoints : int
            Helps calculate the slope at a point. The number of points around the point at which slope is to be computed.
        maketitle : str
            If set to "Yes", the plot will be titled; otherwise, not.
        with_fit : str
            If set to "Yes", the plot will include the BET fit, the BET+ESW fit, the BET region, and the BET+ESW region; otherwise, not.             
        fit_data : list
            Information for BET and BET+ESW. In particular (for BET and for BET+ESW), the indices of the data points that start and end the chosen linear region (rbet), as well as a molar version of Xm (called qm here) and C. These last two are referred to as params in the code.           

        Returns
        -------
        None

        """
        [loading, phi, minima, eswarea] = self.eswdata(data, eswpoints)

        ax.plot(loading, phi, "o")
        ax.set_ylim(ax.get_ylim())

        ax.xaxis.label.set_text("q / mol/kg")
        ax.yaxis.label.set_text("$\Phi$" + " / J/g")
        if maketitle == "Yes":
            ax.set_title("ESW Plot")
        ax.set_xlim((0, ax.get_xlim()[1]))
        bbox_props = dict(boxstyle="square", ec="k", fc="w", lw=1.0)

        if with_fit == "Yes":
            [bet_info, betesw_info] = fit_data
            [rbet, bet_params] = bet_info
            [rbetesw, betesw_params] = betesw_info

            if rbet != (None, None):
                ax.axvspan(
                    data.at[rbet[0], "Loading"],
                    data.at[rbet[1], "Loading"],
                    facecolor=plt.cm.PuOr(70),
                    edgecolor="none",
                    alpha=0.6,
                    label="BET region",
                )
                load_bet = self.th_loading(data["P_rel"].values, bet_params)
                ax.plot(
                    load_bet,
                    self.gen_phi(load_bet, data["P_rel"].values),
                    color=plt.cm.PuOr(20),
                    label="BET fit",
                )
            if rbetesw != (None, None):
                ax.axvspan(
                    data.at[rbetesw[0], "Loading"],
                    data.at[rbetesw[1], "Loading"],
                    facecolor=plt.cm.Greens(70),
                    edgecolor="none",
                    alpha=0.6,
                    label="BET+ESW region",
                )
                load_betesw = self.th_loading(data["P_rel"].values, betesw_params)
                ax.plot(
                    load_betesw,
                    self.gen_phi(load_betesw, data["P_rel"].values),
                    color=plt.cm.Greens(200),
                    label="BET+ESW fit",
                )

            # Setting the y-axis limits to include more of the fit
            # Only consider phi values that correspond to x values within our plotting range
            phi_values = [
                phi[i]
                for i, value in enumerate(loading)
                if ax.get_xlim()[0] <= value <= ax.get_xlim()[1]
            ]

            y_min = min(phi_values) - 10
            y_max = max(phi_values) + 10

            ax.set_ylim(bottom=y_min, top=y_max)

        if minima is not None:
            ax.vlines(
                data.at[minima, "Loading"],
                ax.get_ylim()[0],
                ax.get_ylim()[1],
                colors=plt.cm.Greens(200),
                linestyles="dashed",
                label="ESW minimum",
            )
        else:
            ax.text(
                0.03,
                0.90,
                "Minima not found",
                horizontalalignment="left",
                verticalalignment="center",
                transform=ax.transAxes,
                bbox=bbox_props,
            )

        if self.con1limit is not None:
            ax.vlines(
                data.at[self.con1limit, "Loading"],
                ax.get_ylim()[0],
                ax.get_ylim()[1],
                colors=plt.cm.Purples(230),
                linestyles="dashed",
                label="Consistency 1 maximum",
            )

        if plotting_information["legend"] == "Yes":  # Add a legend in this case.
            ax.legend(loc="upper center")

    # include ANOVA, t-tests, shapiro wilk test, outliers, generate graphs of residuals.
    def linregauto(self, p, q, data):
        """
        This function computes all the statistical parameters associated with the fitting of a line. It also checks which consistency criteria that range satisfies and which ones it doesn't.

        Parameters 
        ----------
        p : numpy.int64
            The index of the data point that is chosen as the start of the linear region.
        q : numpy.int64
            The index of the data point that is chosen as the end of the linear region.
        data : pandas.core.frame.DataFrame
            Represents an isotherm. Columns are "Pressure", "Loading", "P_rel", "BETy", "BET_y2", and "phi".


        Returns
        -------
        linear : pandas.core.frame.DataFrame
            The initial data, but only the rows of the linear region.
        stats : list
            The results of various statistical tests.
        C : float
            See equation 6 of Fagerlund, G. (1973). Determination of specific surface by the BET method. Heat of adsorption in the first layer.
        qm : float
            See equation 5 of Fagerlund, G. (1973). Determination of specific surface by the BET method. Mass of adsorbate forming a monolayer on unit mass of adsorbent.
        x_max : numpy.float64
            The relative pressure at which BET_y2 is maximized. BET_y2 is defined in prepdata.
        x_BET3 : numpy.float64
            Value of relative pressure that corresponds to monolayer loading capacity.
        x_BET4 : numpy.float64
            Value used in the evaluation of the fourth Rouquerol consistency criterion.
        con1 : str
            "Yes" or "No", depending on whether the first consistency criterion is satisfied.
        con2 : str
            "Yes" or "No", depending on whether the second consistency criterion is satisfied.
        con3 : str
            "Yes" or "No", depending on whether the third consistency criterion is satisfied.
        con4 : str
            "Yes" or "No", depending on whether the fourth consistency criterion is satisfied.
        A_BET : float
            The predicted BET surface area.           

        """        
        data = data.copy(deep=True)
        linear = data[p:q] # Grab the rows of the DataFrame that correspond to the data points in the chosen linear region
        results = smf.ols("BETy ~ P_rel", linear).fit()
        intercept, slope = results.params

        # We will perform all the statistical tests here.
        # First, the whole model ANOVA test.
        ftest = (results.fvalue, results.f_pvalue)
        # Then, we will do the parameter tests. We won't really do the effect test, since there is
        # only one variable.
        Ttest = results.t_test(np.array([[1, 0], [0, 1]]))
        ttest = (Ttest.tvalue, Ttest.pvalue)
        influence = results.get_influence()
        # We are using externally studentized residuals.
        resid_stud = influence.get_resid_studentized_external()
        # If any studentized residual is above 3, we will flag this as an outlier. Different softwares have
        # different ways of flagging outliers, but we will use 3.0 (https://tinyurl.com/ycomecvg)
        prel = linear["P_rel"].values
        bety = linear["BETy"].values

        isoutlier = "No"
        preloutlier = False
        betyoutlier = False
        if np.absolute(resid_stud).max() > 3.0:
            isoutlier = "Yes"
            arrindexoutlier = np.where(resid_stud > 3.0)[0]
            preloutlier = prel[arrindexoutlier]
            betyoutlier = bety[arrindexoutlier]
        outlierdata = [isoutlier, preloutlier, betyoutlier]
        # Ultimately, we would like to highlight the outlier points on the graph.
        # Now, we want to perform the Shapiro Wilk test on the residuals. We will perform it on normalized residuals.
        norm_res = (resid_stud - resid_stud.mean()) / resid_stud.std()
        shaptest = ss.shapiro(norm_res)
        # Model adequacy
        r2 = results.rsquared
        r2adj = results.rsquared_adj
        # Now, we want to pack the results of all these tests into a single list.
        stats = [ftest, ttest, outlierdata, shaptest, r2, r2adj, results]
        if intercept == 0.0:
            intercept += 1e23
        C = slope / intercept + 1
        qm = 1 / (slope + intercept)  # 1/(mol/kg framework)
        # To check for 1st consistency criterion

        ind_max = self.con1limit
        if ind_max is not None:
            x_max = data[data.index == ind_max]["P_rel"].values[0]
        else:
            x_max = data["P_rel"][data["BET_y2"].idxmax()]

        if linear["P_rel"].max() <= x_max:
            con1 = "Yes"
        else:
            con1 = "No"
        # to check for second consistency criteria
        if C > 0:
            con2 = "Yes"
        else:
            con2 = "No"
        # checking if third consistency criteria is satisfied
        lower_limit_y = data["Loading"][data["Loading"] <= qm].max()
        upper_limit_y = data["Loading"][data["Loading"] > qm].min()
        lower_limit_x = data["P_rel"][data["Loading"] <= qm].max()
        upper_limit_x = data["P_rel"][data["Loading"] > qm].min()

        # Now i will do a linear interpolation to figure out x
        m = (upper_limit_y - lower_limit_y) / (upper_limit_x - lower_limit_x) # slope
        x_BET3 = upper_limit_x - (upper_limit_y - qm) / m
        if linear["P_rel"].min() <= x_BET3 <= linear["P_rel"].max():
            con3 = "Yes"
        else:
            con3 = "No"

        # Checking for BET 4th BET consistency criteria
        x_BET4 = 1 / (scipy.sqrt(C) + 1)
        if np.abs((x_BET4 - x_BET3) / x_BET3) < 0.2:
            con4 = "Yes"
        else:
            con4 = "No"

        # This is related to equation 1 of Fagerlund, G. (1973). Determination of specific surface by the BET method.
        # qm[=]mmol/g[=]mol/kg
        # self.N_A[=]atoms/mol
        # self.selected_gas_cs[=]m²/atom
        # Factor of 1000 to convert from mmol to mol.
        # A_BET[=]m²/g
        A_BET = qm * self.N_A * self.selected_gas_cs / 1000  # m²/g

        return [
            linear,
            stats,
            C,
            qm,
            x_max,
            x_BET3,
            x_BET4,
            con1,
            con2,
            con3,
            con4,
            A_BET,
        ]

    def picklen(self, data, method="BET+ESW"):
        """
        The objective of this function is to choose a linear region.
        -------------------------------------------------------------------------------------------------------------------------------------
        HOWEVER, WE MUST EMPHASIZE THAT THE PROCESS OF CHOOSING A LINEAR REGION IS HIGHLY DEPENDENT ON THE QUALITY OF THE DATA. DO NOT TAKE
        THE RESULT OF THIS FUNCTION AS FINAL. HUMAN INTERFERENCE IS HIGHLY RECOMMENDED FOR THIS STEP.
        -------------------------------------------------------------------------------------------------------------------------------------
        We are trying to make this process objective. The way we will go about this is that we will start choosing linear regions from the largest
        to the smallest. We will assign priority in the following order:
            1. No. of consistency criteria fulfilled (among the 3rd and 4th)
            2. Length of the region.
            3. R2 value (we will keep that as a lower limit)

        Parameters 
        ----------
        data : pandas.core.frame.DataFrame
            Contains the data of the isotherm being analyzed. Keys are "Pressure", "Loading", "P_rel", "BETy", "BET_y2", "phi".
        method : str
            Either "BET" or "BET+ESW". Indicates whether the Excess Sorption Work method will be used in choosing the linear monolayer loading region or not.

        Returns
        -------
        fp : numpy.int64
            The index of the data point that is chosen as the start of the linear region.
        fq : numpy.int64
            The index of the data point that is chosen as the end of the linear region.

        """  
        data_og = data.copy(deep=True)
        # We want to make sure that we always satisfy first consistency criterion, so we take the upper limit from the maxima function
        # we have defined.
        iddatamax = self.con1limit
        if iddatamax is None:
            iddatamax = data["BET_y2"].idxmax()
        # Considering data points up to iddatamax+2 makes sense because that way, we can consider linear regions right up until the point
        # where BET_y2 is max.
        data = data_og[: (iddatamax + 2)].copy(deep=True)

        minlength = int(
            self.minlinelength - 1
        )  # The minimum number of points this considers a line is 1 greater than minlength.
        # Thus, for the user to be able to specify the actual number, we deduct one here.

        R2cutoff = self.R2cutoff

        start = data.index.values[0]
        end = data.index.values[-1]

        # Current best linear region
        # This is just a variable to initialize the list. It will likely get replaced.
        curbest = [ 
            None, # fp
            None, # fq
            -1, # fconscore
            1, # flength
            0.0, # fR2
        ]  

        satisflag = (
            0  # Will be set to 1 if a region satisfying all our demands is found.
        )
        # We will incorporate the ESW condition here.
        endlowlimit = start + minlength
        starthighlimit = end - minlength
        if method == "BET+ESW":
            # We are ensuring that the ESW consistency criterion is always satisfied.
            eswminima = self.eswminima
            minima = eswminima
            if minima is not None:
                endlowlimit = minima + 1
                starthighlimit = (
                    minima - 1
                )  # So that the ESW minima is contained exactly within the chosen range.

        # Looping through all possibilities of consecutive data points. 
        for i in np.arange(end, endlowlimit, -1):
            for j in np.arange(start, i - minlength, 1):
                p, q = j, i # p is the starting point (data index) of the current region. q is the ending point of the current region.
                if p > starthighlimit:
                    """
                    This means that the starting point is higher than the starting point is allowed to be.
                    In the case of BET+ESW, this means that the ESW condition will be violated.
                    """
                    continue
                if q - p > 10:
                    """
                    This condition is to ensure that we have a maximum limit on the length of the
                    linear region length so that we don't end up selecting a really huge linear region.
                    """
                    continue
                [
                    linear,
                    stats,
                    C,
                    qm,
                    x_max,
                    x_BET3,
                    x_BET4,
                    con1,
                    con2,
                    con3,
                    con4,
                    A_BET,
                ] = self.linregauto(p, q, data)
                [ftest, ttest, outlierdata, shaptest, r2, r2adj, results] = stats
                # first, let's see if we can satisfy the first two consistency criteria, statistical significance and min R2 value of the line.
                # As of 05/25/2018, we are doing away with all these wonderful statistical criteria to ensure consistency with the current practices in the field.
                # So, we will replace 0.05 by 0.90 such that these consistency criteria essentially become absent.
                if (
                    con1 == "Yes"
                    and con2 == "Yes"
                    and ftest[1] < 0.99
                    and ttest[1].max() < 0.99
                    and shaptest[1] > 0.01
                    and r2 > self.R2min
                ):
                    # Now this is a potential linear region. Now the race begins.
                    scon3 = int(1) if con3 == "Yes" else int(0)
                    scon4 = int(1) if con4 == "Yes" else int(0)
                    conscore = (
                        scon3 + scon4
                    )  # Score based on the number of consistency criteria satisfied
                    length = q - p
                    R2 = r2
                    # Will check if the chosen region satisfies our requirements for the "Best" region.
                    if conscore == int(2) and length > minlength and R2 > R2cutoff:
                        curbest = [p, q, conscore, length, R2]
                        satisflag = 1
                        break # Select this region and look no further. See bottom left of Figure S2 of the SI of the SESAMI 1 paper: https://pubs.acs.org/doi/full/10.1021/acs.jpcc.9b02116

                    # These lines are to initiate the process of overwriting the data for the linear region.
                    if curbest[2] == -1: # Initially set to -1 near the beginning of this function.
                        curbest = [p, q, conscore, length, R2]
                    if conscore > curbest[2]: # More consistency criteria are fulfilled than the previous best linear region
                        curbest = [p, q, conscore, length, R2]
                    """
                    #We have commented this section out because in some cases, where no region was
                    #found to satisfy 3rd or 4th consistency criterion, this code would select regions
                    #with a higher length or R2 value. This was found to be a bit problematic because
                    #in the event of multiple linear regions, we should select the one closest to the Consistency 4 limit. So
                    #we have altered that here.
                    if conscore == curbest[2]:
                        if length>curbest[3]:
                            curbest = [p,q,conscore,length,R2]
                            if length==curbest[3]:
                                if R2>curbest[4]:
                                    curbest = [p,1,conscore,length, R2]
                    """
            if satisflag == 1:
                break
        fp, fq, fconscore, flength, fR2 = curbest

        return fp, fq

    def saveimgsummary(
        self,
        plotting_information,
        bet_info,
        betesw_info,
        data,
        plot_number,
        sumpath=os.path.join(os.curdir, "imgsummary"),
        saveindividual="No",
        eswminima=None,
    ):
        """
        This function creates a summary of the BET process and stores it as a collection in the specified outlet directory.
        This function also generates plots.

        Parameters 
        ----------
        plotting_information : dict
            Lots of plotting and calculation settings from the front end (i.e. the SESAMI webpage). The keys are 'dpi', 'font size', 'font type', 'legend', 'R2 cutoff', 'R2 min', 'gas', 'scope', 'ML', 'custom adsorbate', 'custom cross section', 'custom temperature', and 'custom saturation pressure'.
        bet_info : list
            [rbet, bet_params]. The first entry contains the indices of the data points that start and end the chosen linear region (rbet). The second entry contains a molar version of Xm (called qm here) and C.
        betesw_info : list
            [rbet, bet_params]. The first entry contains the indices of the data points that start and end the chosen linear region (rbet). The second entry contains a molar version of Xm (called qm here) and C.
        data : pandas.core.frame.DataFrame
            Represents an isotherm. Columns are "Pressure", "Loading", "P_rel", "BETy", "BET_y2", and "phi".
        plot_number : int
            A number identifier for which round of plots this is, for the current website user. Prevents issues with plot downloads.
        sumpath : str
            Path at which the figures will be saved.
        saveindividual : str
            If "Yes", saves the plots from the multiplot individually as well.
        eswminima : numpy.int64
            The 'Loading' value corresponding to a minima of 'phi' values.

        Returns
        -------
        BET_dict: dict
            Contains SESAMI 1.0 intermediate calculation results, and the predicted area A_BET, when BET is used. The keys are "C", "qm", "A_BET", "con3", "con4", "length_linear_region", "R2_linear_region", "low_P_linear_region", and "high_P_linear_region".
        BET_ESW_dict: dict
            Contains SESAMI 1.0 intermediate calculation results, and the predicted area A_BET, when BET is used and ESW helps pick the linear region. The keys are "C", "qm", "A_BET", "con3", "con4", "length_linear_region", "R2_linear_region", "low_P_linear_region", and "high_P_linear_region".

        """
        scope = plotting_information['scope']

        if scope == 'BET and BET+ESW': # In this case, run the BET+ESW code
            rbet = bet_info[0]
            rbetesw = betesw_info[0]
            if saveindividual == "Yes":
                fig, fig2, fig3, fig4, fig5 = (
                    plt.figure(),
                    plt.figure(),
                    plt.figure(),
                    plt.figure(),
                    plt.figure(),
                )
                ax, ax2, ax3, ax4, ax5 = (
                    fig.add_subplot(111),
                    fig2.add_subplot(111),
                    fig3.add_subplot(111),
                    fig4.add_subplot(111),
                    fig5.add_subplot(111),
                )
                self.makeisothermplot(
                    plotting_information,
                    ax,
                    data,
                    maketitle="No",
                    with_fit="Yes",
                    fit_data=[bet_info, betesw_info],
                )
                self.makelinregplot(
                    plotting_information, ax2, rbet[0], rbet[1], data, maketitle="No"
                )
                self.makeconsistencyplot(plotting_information, ax3, data, maketitle="No")
                self.makeeswplot(
                    plotting_information,
                    ax4,
                    data,
                    maketitle="No",
                    with_fit="Yes",
                    fit_data=[bet_info, betesw_info],
                )
                self.makelinregplot(
                    plotting_information, ax5, rbetesw[0], rbetesw[1], data, maketitle="No"
                )  # TODO can set maketitle to "Yes" if you want the individual plots to have titles
                dpi = plotting_information["dpi"]
                fig.savefig(
                    os.path.join(sumpath, f"isotherm_{plot_number}.png"),
                    format="png",
                    dpi=dpi,
                    bbox_inches="tight",
                )
                fig2.savefig(
                    os.path.join(sumpath, f"BETPlotLinear_{plot_number}.png"),
                    format="png",
                    dpi=dpi,
                    bbox_inches="tight",
                )
                fig3.savefig(
                    os.path.join(sumpath, f"BETPlot_{plot_number}.png"),
                    format="png",
                    dpi=dpi,
                    bbox_inches="tight",
                )
                fig4.savefig(
                    os.path.join(sumpath, f"ESWPlot_{plot_number}.png"),
                    format="png",
                    dpi=dpi,
                    bbox_inches="tight",
                )
                fig5.savefig(
                    os.path.join(sumpath, f"BETESWPlot_{plot_number}.png"),
                    format="png",
                    dpi=dpi,
                    bbox_inches="tight",
                )
                plt.close(fig)
                plt.close(fig2)
                plt.close(fig3)
                plt.close(fig4)
                plt.close(fig5)

            # Next, the multiplot.
            figf = plt.figure(figsize=(3 * 7.0, 2 * 6.0))
            [[axf, ax3f, ax4f], [ax2f, ax5f, blanksubplot]] = figf.subplots(
                nrows=2, ncols=3
            )
            self.makeisothermplot(
                plotting_information,
                axf,
                data,
                with_fit="Yes",
                fit_data=[bet_info, betesw_info],
            )
            self.makeconsistencyplot(plotting_information, ax3f, data)

            BET_dict = self.makelinregplot(
                plotting_information, ax2f, rbet[0], rbet[1], data
            )

            self.makeeswplot(
                plotting_information,
                ax4f,
                data,
                with_fit="Yes",
                fit_data=[bet_info, betesw_info],
            )

            BET_ESW_dict = None  # Set this to nothing to start. Will evaluate whether eswminima was None by whether the value changes from nothing.
            if eswminima is None:
                ax5f.axis("off")
            else:
                BET_ESW_dict = self.makelinregplot(
                    plotting_information, ax5f, rbetesw[0], rbetesw[1], data, mode="BET+ESW"
                )
            blanksubplot.axis("off")
            figf.tight_layout()
            figf.savefig(
                os.path.join(sumpath, f"multiplot_{plot_number}.png"),
                format="png",
                dpi=dpi,
                bbox_inches="tight",
            )
            plt.close(figf)

            return BET_dict, BET_ESW_dict

        else: # Only run the BET related code
            rbet = bet_info[0]
            if saveindividual == "Yes":
                fig, fig2, fig3 = (
                    plt.figure(),
                    plt.figure(),
                    plt.figure()
                )
                ax, ax2, ax3 = (
                    fig.add_subplot(111),
                    fig2.add_subplot(111),
                    fig3.add_subplot(111)
                )
                self.makeisothermplot(
                    plotting_information,
                    ax,
                    data,
                    maketitle="No",
                    with_fit="Yes",
                    fit_data=[bet_info, betesw_info],
                )
                self.makelinregplot(
                    plotting_information, ax2, rbet[0], rbet[1], data, maketitle="No"
                )
                self.makeconsistencyplot(plotting_information, ax3, data, maketitle="No")
                dpi = plotting_information["dpi"]
                fig.savefig(
                    os.path.join(sumpath, f"isotherm_{plot_number}.png"),
                    format="png",
                    dpi=dpi,
                    bbox_inches="tight",
                )
                fig2.savefig(
                    os.path.join(sumpath, f"BETPlotLinear_{plot_number}.png"),
                    format="png",
                    dpi=dpi,
                    bbox_inches="tight",
                )
                fig3.savefig(
                    os.path.join(sumpath, f"BETPlot_{plot_number}.png"),
                    format="png",
                    dpi=dpi,
                    bbox_inches="tight",
                )
                plt.close(fig)
                plt.close(fig2)
                plt.close(fig3)

            # Next, the multiplot.
            figf = plt.figure(figsize=(3 * 7.0, 1 * 6.0))
            [axf, ax2f, ax3f] = figf.subplots( # Only have three plots, since not making the BET+ESW plots
                nrows=1, ncols=3
            )
            self.makeisothermplot(
                plotting_information,
                axf,
                data,
                with_fit="Yes",
                fit_data=[bet_info, betesw_info],
            )
            self.makeconsistencyplot(plotting_information, ax3f, data)

            BET_dict = self.makelinregplot(
                plotting_information, ax2f, rbet[0], rbet[1], data
            )

            figf.tight_layout()
            figf.savefig(
                os.path.join(sumpath, f"multiplot_{plot_number}.png"),
                format="png",
                dpi=dpi,
                bbox_inches="tight",
            )
            plt.close(figf)         

            return BET_dict, None # None is a placeholder, since two outputs are expected

    def generatesummary(
        self,
        data,
        plotting_information,
        MAIN_PATH,
        plot_number,
        eswpoints=3,
        sumpath=os.path.join(os.curdir, "imgsummary"),
        saveindividual="Yes",
    ):
        """
        This function will call the required functions to compute BET, ESW and BET+ESW areas and write the output into the files.
        Format:
        Name BETLowerPressureLimit BETHigherPressureLimit BETArea Nm_BET C_BET Consistency 1 Consistency2 Consistency3 Consistency4 ESWq ESWpressure ESWSA BETESWLowerPressureLimit BETESWHigherPressureLimit BETESWArea Nm_BETESW C_BETESW Consistency 1 Consistency2 Consistency3 Consistency4
        This function calls saveimgsummary for plot generation.

        Parameters 
        ----------
        data : pandas.core.frame.DataFrame
            Represents an isotherm. Columns are "Pressure", "Loading", "P_rel", "BETy", "BET_y2", and "phi".
        plotting_information : dict
            Lots of plotting and calculation settings from the front end (i.e. the SESAMI webpage). The keys are 'dpi', 'font size', 'font type', 'legend', 'R2 cutoff', 'R2 min', 'gas', 'scope', 'ML', 'custom adsorbate', 'custom cross section', 'custom temperature', and 'custom saturation pressure'.
        MAIN_PATH : str
            The main directory of the SESAMI website code.
        plot_number : int
            A number identifier for which round of plots this is, for the current website user. Prevents issues with plot downloads.
        eswpoints : int
            Helps calculate the slope at a point. The number of points around the point at which slope is to be computed.
        sumpath : str
            Path at which the figures will be saved.
        saveindividual : str
            If "Yes", saves the plots from the multiplot individually as well.

        Returns
        -------
        BET_dict: dict
            Contains SESAMI 1.0 intermediate calculation results, and the predicted area A_BET, when BET is used. The keys are "C", "qm", "A_BET", "con3", "con4", "length_linear_region", "R2_linear_region", "low_P_linear_region", and "high_P_linear_region".
            None is returned if the calculation fails.
        BET_ESW_dict: dict
            Contains SESAMI 1.0 intermediate calculation results, and the predicted area A_BET, when BET is used and ESW helps pick the linear region. The keys are "C", "qm", "A_BET", "con3", "con4", "length_linear_region", "R2_linear_region", "low_P_linear_region", and "high_P_linear_region".
            None is returned if the calculation fails, or if the BET+ESW calculation is not asked for in 'scope' in plotting_information.

        """ 
        scope = plotting_information['scope']

        stylepath = os.path.join(MAIN_PATH, "SESAMI", "SESAMI_1", "mplstyle")
        plt.style.use(stylepath)

        # We are calling the eswdata function once from this function to get the variable minima.
        [loading, phi, eswminima, eswarea] = self.eswdata(data, eswpoints)
        # will get the linear region from using the BET criteria only.

        p, q = self.picklen(data, method="BET") # Indices of the data points that start and end the chosen linear region.
        rbet = (p, q)

        if rbet == (None, None):
            # This means that no suitable BET linear region has been found.
            return (
                'BET linear failure',
                'BET linear failure', # The second returned value is a placeholder, since the SESAMI_1.py call expects two values.
            )  # Since SESAMI failed, return values to indicate that. Will report an error message to the website.
        else:
            # A BET region has been found.
            (p, q) = rbet
            [
                linear,
                stats,
                C,
                qm,
                x_max,
                x_BET3,
                x_BET4,
                con1,
                con2,
                con3,
                con4,
                A_BET,
            ] = self.linregauto(p, q, data)
            bet_params = (qm, C)

        betesw_info = None # placeholder, in case scope is 'BET'
        if scope == 'BET and BET+ESW': # In this case, run the BET+ESW code
            # We want to get the bet+esw data ONLY when the eswminima exists.
            if eswminima is None:
                rbetesw = (None, None)
                return 'No eswminima', 'No eswminima' # The second returned value is a placeholder, since the SESAMI_1.py call expects two values.
            else:
                p, q = self.picklen(data, method="BET+ESW") # Indices of the data points that start and end the chosen linear region.
                rbetesw = (p, q)

            # Write BET+ESW
            if rbetesw == (None, None):
                # This means that no suitable BET+ESW linear region has been found.
                return (
                    'BET+ESW linear failure',
                    'BET+ESW linear failure',
                )  # Since SESAMI failed, return values to indicate that. Will report an error message to the website.
            else:
                # A BET region has been found.
                (p, q) = rbetesw
                [
                    linear,
                    stats,
                    C,
                    qm,
                    x_max,
                    x_BET3,
                    x_BET4,
                    con1,
                    con2,
                    con3,
                    con4,
                    A_BET,
                ] = self.linregauto(p, q, data)
                betesw_params = (qm, C)

            betesw_info = [rbetesw, betesw_params]

        bet_info = [rbet, bet_params]
        mpl.rcParams.update(
            {"font.size": plotting_information["font size"]}
        )  # changing the font size to be used in the figures
        mpl.rcParams["font.family"] = plotting_information[
            "font type"
        ]  # setting the font family to be used in the figures
        BET_dict, BET_ESW_dict = self.saveimgsummary(
            plotting_information,
            bet_info,
            betesw_info,
            data,
            plot_number,
            sumpath=sumpath,
            saveindividual=saveindividual,
            eswminima=eswminima,
        )

        return BET_dict, BET_ESW_dict
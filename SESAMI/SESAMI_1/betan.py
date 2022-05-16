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
            self.selected_gas_cs = 0.142e-18  # m2/molecule; Ref: 10.1039/D1TA08021K
        elif selected_gas == "Nitrogen":
            self.selected_gas_cs = 0.162e-18  # m2/molecule; Ref: 10.1039/D1TA08021K
        elif selected_gas == "Carbon dioxide":
            self.selected_gas_cs = 0.142e-18  # m2/molecule; Ref: 10.1039/D1TA08021K
        elif selected_gas == "Krypton":
            self.selected_gas_cs = 0.210e-18  # m2/molecule; Ref: 10.1039/D1TA08021K

        self.loadunits = "mol/kg"
        # self.weight_of_box = 1e-20 #gm

        self.minlinelength = (
            minlinelength  # min number of points for it to be called a line.
        )

        self.R2cutoff = plotting_information[
            "R2 cutoff"
        ]  # 0.9995 #The way this works is if a region satisfies this criterion while satisfying other conditions,
        self.R2min = plotting_information[
            "R2 min"
        ]  # 0.998 #This is the minimum R2 value required for a region to be considered a line.
        # self.method = "BET-ESW" #This is the method. Either BET or BET-ESW
        # Setting these variables to none allows users to set them externally later on.
        self.eswminimamanual = "No"
        self.eswminima = None
        self.con1limitmanual = "No"
        self.con1limit = None

    def prepdata(
        self, data, loading_col="Loading", conv_to_molperkg=1, p0=1e5, full="Yes"
    ):
        """
        This function prepares data for BET analysis. We create the columns P_rel, BETy, BET_y2 and slopes. Needs arguments data and weight of box to calculate the required columns.
        In future, we will also adapt this for different units.
        conv_to_molperkg: Specify the conversion to convert from the current units to mol/kg.
        p0: saturation pressure. We assume that we want to plot from 0 to this pressure.
        """
        # Next, we will prepare the data for analysis by assigning the appropriate column numbers and names.
        data = data.copy(deep=True)
        # First, we will sort the incoming data.
        data["P_rel"] = data["Pressure"] / p0
        data.sort_values("P_rel", inplace=True)
        data["Loading"] = data[loading_col] * conv_to_molperkg
        # data['VolLoad'] = vol_loading
        data["BETy"] = data["P_rel"] / (data["Loading"] * (1 - data["P_rel"]))
        data["BET_y2"] = data["Loading"] * (1 - data["P_rel"])
        data["phi"] = (
            data["Loading"] / 1000 * self.R * self.T * scipy.log(data["P_rel"])
        )  # J/g

        # We will also add a line here that calculates the consistency 1 limit. This will ensure that the we need to compute the upper limit of consistency1 only once.
        if (
            full == "Yes"
        ):  # In some applications, we dont want the ESW limits and stuff, we only want the values.
            # In those cases, we can simply change this paramter to something else.
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
        return [minima, targetvalue, data[["x", "target", "slopes"]]]

    def th_loading(self, x, params):
        """
        Calculates the BET loading given relative pressures and BET parameters.
        """
        [qm, C] = params
        bet_y = (C - 1) / (qm * C) * x + 1 / (qm * C)
        return x / (bet_y * (1 - x))

    def gen_phi(self, load, p_rel, T=87.0):
        """
        This function will generate a phi plot given the x points.
        """
        return load / 1000 * 8.314 * T * scipy.log(p_rel)

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
        If xscale='log' and tryminorticks='Yes', the xscale will be from 0 to 1. The user has no control over it.
        """
        ax.errorbar(
            data["P_rel"],
            data["Loading"],
            yerr=yerr,
            fmt="o",
            capsize=3,
            label="BET Data points",
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
                    label="BET-ESW region",
                )
                ax.plot(
                    data["P_rel"].values,
                    self.th_loading(data["P_rel"].values, betesw_params),
                    color=plt.cm.Greens(200),
                    label="BET-ESW fit",
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
        """
        ax3.xaxis.label.set_text("$p/p_0$")
        ax3.yaxis.label.set_text("$q(1-p/p_{0})$" + " / " + "$%s$" % self.loadunits)
        ax3.set_xscale("log")
        if maketitle == "Yes":
            titletext = "BET Consistency Plot"
            ax3.set_title(titletext)
        ax3.errorbar(data["P_rel"], data["BET_y2"], fmt="o", label="BET Data points")
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
                makefig2,
            ] = self.linregauto(p, q, data)
            [ftest, ttest, outlierdata, shaptest, r2, r2adj, results] = stats
            intercept, slope = results.params

            ax2.xaxis.label.set_text("$p/p_0$")
            ax2.yaxis.label.set_text(r"$\frac{p/p_0}{q(1-p/p_0)}$" + " / " + "kg/mol")
            if maketitle == "Yes":
                if mode == "BET":
                    titletext = "BET Linear Region Plot"
                elif mode == "BET-ESW":
                    titletext = "BET-ESW Linear Region Plot"
                ax2.set_title(titletext)
            ax2.errorbar(
                linear["P_rel"], linear["BETy"], fmt="o", label="BET Data points"
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
            "length": q - p,
            "R2": results.rsquared,
        }  # This will be BET_dict or BET_ESW_dict
        return my_dict

    def eswdata(self, data, eswpoints=3):
        """
        This function computes the ESW area and ESW minima.
        Inputs:
            data: The dataframe containing columns 'Pressure'in Pa and 'Loading' in mol/kg framework.
            eswpoints (optional): Helps calculate the slope at a point. The number of points around the point at which slope is to be
            computed.
        Outputs:
            data['Loading']: Pandas Series object containng 'Loading' data in mol/kg framework
            data['phi']: Pandas series object containing 'phi' values in J/g
                phi: qxNaxAcs where q: Loading in mol/kg=framework, Na: Avogradro number, Acs: Cross-sectional area of Ar atom.
            minima: The 'Loading' value corresponding to a minima of 'phi' values.
            eswarea: The surface area in m2/g corresponding to the 'Loading' at which 'phi' is minimum.
            index: Index of the minima of phi in the dataframe.
            infolist: List of additional information such as slopes of all points on the ESW plot and minimas.
        """
        data = data.copy(deep=True)

        data["phi"] = (
            data["Loading"] / 1000 * self.R * self.T * scipy.log(data["P_rel"])
        )  # J/g

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
            )  # m2/g
        else:
            eswarea = None

        return [data["Loading"], data["phi"], minima, eswarea, []]

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
            data: The dataframe from which the graph is to be constructucted.
        """
        [loading, phi, minima, eswarea, infolist] = self.eswdata(data, eswpoints)

        ax.plot(loading, phi, "o")
        ax.set_ylim(ax.get_ylim())

        ax.xaxis.label.set_text("q / mol/kg")
        ax.yaxis.label.set_text("$\Phi$" + " / J/g")
        if maketitle == "Yes":
            ax.set_title("ESW Plot")
        ax.set_xlim((0, ax.get_xlim()[1]))
        bbox_props = dict(boxstyle="square", ec="k", fc="w", lw=1.0)

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
                    label="BET-ESW region",
                )
                load_betesw = self.th_loading(data["P_rel"].values, betesw_params)
                ax.plot(
                    load_betesw,
                    self.gen_phi(load_betesw, data["P_rel"].values),
                    color=plt.cm.Greens(200),
                    label="BET-ESW fit",
                )

        if plotting_information["legend"] == "Yes":  # Add a legend in this case.
            ax.legend(loc="upper center")

    # include ANOVA, t-tests, shapiro wilk test, outliers, generate graphs of residuals.
    def linregauto(self, p, q, data):
        """
        This function comptes all the statistical parameters associated with the fitting of a line. It also checks which consistency criteria that range satisfies and which ones it doesn't.
        """
        data = data.copy(deep=True)
        linear = data[p:q]
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
        # If any studentized resiudal is above 3, we will flag this as an outlier. Different softwares have
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
        qm = 1 / (slope + intercept)  # 1/(mol/kgframework)
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
        m = (upper_limit_y - lower_limit_y) / (upper_limit_x - lower_limit_x)
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

        # Valid when units of loading is in mlSTP/g
        A_BET = qm * self.N_A * self.selected_gas_cs / 1000  # m2/g

        # vol_loading = volume/weight_of_box #mlSTP/g
        if np.isnan(slope):
            makefig2 = "No"
        else:
            makefig2 = "Yes"
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
            makefig2,
        ]

    def picklen(self, data, method="BET-ESW"):
        """
        The objective of this function is to choose a linear region.
        -------------------------------------------------------------------------------------------------------------------------------------
        HOWEVER, WE MUST EMPHASIZE THAT THE PROCESS OF CHOOSING A LINEAR REGION IS HIGHLY DEPENDENT ON THE QUALITY OF THE DATA. DO NOT TAKE
        THE RESULT OF THIS FUNCTION AS FINAL. HUMAN INTERFERENCE IS HIGHLY RECOMMENDED FOR THIS STEP.
        -------------------------------------------------------------------------------------------------------------------------------------
        We are trying to make this process objective. The way we will go about this is that we will start choosing linear regions from the largest
        to the smallest. We will asign priority in the following order:
            1. No. of consistency criteria fulfilled (among the 3rd and 4th)
            2. Length of the region.
            3. R2 value (we will keep that as a lower limit)
        """
        data_og = data.copy(deep=True)
        # We want to make sure that we always satisfy first consistency criterion, so we take the upper limit from the maxima funciton
        # we have defined.
        iddatamax = self.con1limit
        if iddatamax is None:
            iddatamax = data["BET_y2"].idxmax()
        # Considering data points up to iddatamax+2 makes sense because that way, we can consider linear regions right uptil the point
        # where BET_y2 is max.
        data = data_og[: (iddatamax + 2)].copy(deep=True)

        minlength = int(
            self.minlinelength - 1
        )  # The minimum number of points this considers a line is 1 greater than minlength.
        # Thus, for the user to be able to specify the actual number, we deduct one here.

        R2cutoff = self.R2cutoff

        start = data.index.values[0]
        end = data.index.values[-1]
        curbest = [
            None,
            None,
            -1,
            1,
            0.0,
        ]  # This is just a variable to initialize the list so that it gets replaced.
        satisflag = (
            0  # Will be set to 1 if a region satisfying all our demands is found.
        )
        # We will incorportate the ESW conditon here.
        endlowlimit = start + minlength
        starthighlimit = end - minlength
        if method == "BET-ESW":
            # We are ensuring that the ESW consistency criterion is always satisfied.
            eswminima = self.eswminima
            minima = eswminima
            if minima is not None:
                endlowlimit = minima + 1
                starthighlimit = (
                    minima - 1
                )  # So that the ESW minima is contained exactly within the chosen range.

        (fp, fq) = (None, None)
        for i in np.arange(end, endlowlimit, -1):
            for j in np.arange(start, i - minlength, 1):
                p, q = j, i
                if p > starthighlimit:
                    """
                    This means that the starting point is higher than the starting point is allowed to be.
                    In the case of BET-ESW, this means that the ESW condition will be violated.
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
                    makefig2,
                ] = self.linregauto(p, q, data)
                [ftest, ttest, outlierdata, shaptest, r2, r2adj, results] = stats
                # first, lets see if we can satisfy the first two consistency criteria, statistical significance and min R2 value of the line.
                # As of 05/25/2018, we are doing away with all these wonderful statistical criteria to ensure consistency with the current practices in the field.
                # So, we will replace 0.05 by 0.90 such that these consistency crieria essentially become absent.
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
                        break
                    # These lines are to initiate the process of overwriting the data for the linear region.
                    if curbest[2] == -1:
                        curbest = [p, q, conscore, length, R2]
                    if conscore > curbest[2]:
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
        return (fp, fq)

    def saveimgsummary(
        self,
        plotting_information,
        bet_info,
        betesw_info,
        data,
        plot_number,
        sumpath=os.path.join(os.curdir, "imgsummary"),
        saveindividual="No",
        eswminima=None
    ):
        """
        This function creates a summary of the BET process and stores it as a collection in the specified outlet directory.
        """
        rbet = bet_info[0]
        rbetesw = betesw_info[0]
        if saveindividual == "Yes":
            fig, fig3, fig2, fig4, fig5 = (
                plt.figure(),
                plt.figure(),
                plt.figure(),
                plt.figure(),
                plt.figure(),
            )
            ax, ax2, ax3, ax4, ax5 = (
                fig.add_subplot(111),
                fig3.add_subplot(111),
                fig2.add_subplot(111),
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
            self.makeconsistencyplot(plotting_information, ax3, data, maketitle="No")
            self.makelinregplot(
                plotting_information, ax2, rbet[0], rbet[1], data, maketitle="No"
            )
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
                os.path.join(sumpath, f"BETPlot_{plot_number}.png"),
                format="png",
                dpi=dpi,
                bbox_inches="tight",
            )
            fig3.savefig(
                os.path.join(sumpath, f"BETPlotLinear_{plot_number}.png"),
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
            plt.close(fig3)
            plt.close(fig2)
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
                plotting_information, ax5f, rbetesw[0], rbetesw[1], data, mode="BET-ESW"
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

    def generatesummary(
        self,
        data,
        plotting_information,
        MAIN_PATH,
        plot_number,
        filepath=os.curdir,
        filename="summary.txt",
        eswpoints=3,
        sumpath=os.path.join(os.curdir, "imgsummary"),
        saveindividual="Yes",
    ):
        """
        This function will call the required functions to compute BET, ESW and BET + ESW areas and write the output into the files.
        Format:
        Name BETLowerPressureLimit BETHigherPressureLimit BETArea Nm_BET C_BET Consistency 1 Consistency2 Consistency3 Consistency4 ESWq ESWpressure ESWSA BETESWLowerPressureLimit BETESWHigherPressureLimit BETESWArea Nm_BETESW C_BETESW Consistency 1 Consistency2 Consistency3 Consistency4
        """

        stylepath = os.path.join(MAIN_PATH, "SESAMI", "SESAMI_1", "mplstyle")
        plt.style.use(stylepath)

        # We are calling the eswdata function once from this function to get the variable minima.
        [loading, phi, eswminima, eswarea] = self.eswdata(data, eswpoints)[:4]
        # will get the linear region from using the BET criteria only.

        (p, q) = self.picklen(data, method="BET")
        rbet = (p, q)

        # We want to get the bet+esw data ONLY when the eswminima exists.
        if eswminima is None:
            rbetesw = (None, None)
        else:
            (p, q) = self.picklen(data, method="BET-ESW")
            rbetesw = (p, q)

        if rbet == (None, None):
            # This means that no suitable linear region has been found.
            return (
                None,
                None,
            )  # Since SESAMI failed, return None, None to indicate that. Will report an error message to the website.
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
                makefig2,
            ] = self.linregauto(p, q, data)
            bet_params = (qm, C)

        # Write BET+ESW
        if rbetesw == (None, None):
            # This means that no suitable linear region has been found.
            return (
                None,
                None,
            )  # Since SESAMI failed, return None, None to indicate that. Will report an error message to the website.
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
                makefig2,
            ] = self.linregauto(p, q, data)
            betesw_params = (qm, C)

        bet_info = [rbet, bet_params]
        betesw_info = [rbetesw, betesw_params]
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

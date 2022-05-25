# Most of the code in this file is from SESAMI_2.0.ipynb, which was released with the paper at https://doi.org/10.1021/acs.jpclett.0c01518
# The structure uploaded to the website is called the test_data in this script.

import numpy as np
import pandas as pd
import pickle


class ML:
    def __init__(self):
        self.N_A = 6.022 * 10 ** 23  # molecules/mol
        self.A_cs = (
            0.142 * 10 ** -18
        )  # m2/molecule, for argon. #from refs with DOI: 10.1021/acs.langmuir.6b03531

        # Values by which we will normalize the dataset. Gotten from the training data, in SESAMI_2.0.ipynb
        self.norm_vals = np.array(
            [
                [
                    1.58953000e-04,
                    1.00155915e-02,
                    4.39987176e-02,
                    3.24635588e-01,
                    2.05368726e00,
                    2.71670605e00,
                    2.81671833e00,
                    2.52660562e-08,
                    1.59200831e-06,
                    6.99372815e-06,
                    5.16018006e-05,
                    6.20679622e-04,
                    2.02395972e-03,
                    2.28557690e-03,
                    1.00312072e-04,
                    4.40673180e-04,
                    3.25141742e-03,
                    3.91088782e-02,
                    1.27529230e-01,
                    1.44013667e-01,
                    1.93588715e-03,
                    1.42835495e-02,
                    1.71806178e-01,
                    5.60238764e-01,
                    6.32655265e-01,
                    1.05388265e-01,
                    1.26763694e00,
                    4.13360776e00,
                    4.66791819e00,
                    4.21763134e00,
                    6.85987932e00,
                    7.11241758e00,
                    7.38049176e00,
                    7.65219574e00,
                    7.93390218e00,
                ],
                [
                    4.78708045e00,
                    2.68703345e01,
                    3.80141609e01,
                    4.78106234e01,
                    6.17790024e01,
                    1.06410565e02,
                    1.61478833e02,
                    2.29161393e01,
                    1.28630453e02,
                    1.50296581e02,
                    1.60737108e02,
                    1.66083055e02,
                    1.72479679e02,
                    1.80115011e02,
                    7.22014876e02,
                    8.43628897e02,
                    9.02232560e02,
                    9.32239866e02,
                    9.68144720e02,
                    1.01100256e03,
                    1.44507643e03,
                    1.65793236e03,
                    1.73340193e03,
                    1.82180829e03,
                    1.87702758e03,
                    2.28585571e03,
                    2.95369262e03,
                    3.20344500e03,
                    3.25911476e03,
                    3.81664514e03,
                    4.13936531e03,
                    5.18387215e03,
                    1.13232083e04,
                    1.71830538e04,
                    2.60754134e04,
                ],
            ]
        )

    def initialize_multiple_cols(self, data, col_list, default_val=np.nan):
        """
        In pandas, we cannot initialize multiple columns together with a single value, although we can do that for a single column. So,
        this function helps us do that.
        data : The dataframe for which we need inititalization.
        col_list : The list of columns which we need intialized.
        default_value : The default value we want in those columns.
        """
        for col in col_list:
            data[col] = default_val
        return data

    def pressure_bin_features(self, data, pressure_bins, isotherm_data_path):
        """
        This function computes the mean loading for isotherms for the given set of pressure bins and adds it to the given dataframe as columns
        c_1, c_2, ... c_n.
        data: Dataframe containing 'Name' and 'TrueSA' columns.
        pressure_bins: list of tuples giving the start and end points of the pressure ranges we want to use. The interval is half open with equality on
            the greater than side.
        isotherm_data_path: Path to the location of the isotherm data.
        """
        feature_list = ["c_%d" % i for i in range(len(pressure_bins))]
        data = self.initialize_multiple_cols(
            data, feature_list
        )  # This is the dataframe that will store the feature values.

        column_names = ["Pressure", "Loading"]
        df = pd.read_table(
            isotherm_data_path, skiprows=1, sep="\t", names=column_names
        )  # That text file gets made by the app.py python script.

        for i, p_bin in enumerate(pressure_bins):
            try:
                val = df.loc[
                    (df["Pressure"] >= pressure_bins[i][0])
                    & (df["Pressure"] < pressure_bins[i][1]),
                    "Loading",
                ].mean()
                data[
                    "c_%d" % i
                ] = val  # We are computing the mean values and assigning them to the cell.
                # This dataframe is just one row, corresponding to the material described by the isotherm uploaded to the GUI.
            except Exception:
                print("Feature issue in pressure_bin_features")

        return data

    def normalize_df(self, df, col_list, set_="Training", reset_norm_vals="No"):
        """
        This function seeks to normalize the feature columns in the dataframe by the maximum and minimum values of the data.
        One needs to be careful while applying this function, especially to the test set. It is important to ensure that we are using the same
        normalization values as the corresponding training set.
        df: The dataframe whose columns are to be normlized.
        col_list: The list of columns which need to be normalized.
        set_ : The set (Training or Test) to which the data belongs.
        reset_norm_vals: If this is set to "Yes", the normalization values will be reset even if they have already been set before.
        """
        df[col_list] = (df[col_list] - self.norm_vals[0, :]) / (
            self.norm_vals[1, :] - self.norm_vals[0, :]
        )

        return df

    def generate_combine_feature_list(self, feature_list, degree=2):
        """
        This function generates the list for 2nd order combined features.
        feature_list: The list of features which needs to be combined.
        """
        out_feature_list = []
        for n1 in np.arange(0, len(feature_list)):
            for n2 in np.arange(n1, len((feature_list))):
                el1 = feature_list[n1]
                el2 = feature_list[n2]
                out_feature_list.append(el1 + "-" + el2)
        return out_feature_list

    def combine_features(self, data, feature_list, degree=2, normalize="No"):
        """
        This function combines the given features to the required degree.
        data: The dataframe containing the features.
        feature_list: The features to be combined.
        degree: The degree to which we want to combine them. In this version, we only support 2nd degree combination.
        """
        out_feature_list = self.generate_combine_feature_list(
            feature_list, degree=degree
        )
        for feature in out_feature_list:
            data[feature] = data[feature.split("-")[0]] * data[feature.split("-")[1]]
        return data

    def build_pressure_bins(self, init_val, final_val, n_points):
        """
        This function creates pressure bins.
        init_val: The initial value of the pressure bins.
        final_val: The final value of the pressure bins.
        n_points: The number of points we want to have.
        """
        p_points = np.logspace(
            np.log10(init_val), np.log10(final_val), n_points
        )  # This is wrt log 10.
        p_points = np.insert(p_points, 0, 0)

        p_points = np.round(
            p_points, decimals=0
        )  # Here, we round the numbers to the nearest integer.

        bins = []
        for index, point in enumerate(p_points[:-1]):
            bins.append((p_points[index], p_points[index + 1]))
        return bins

    def add_features(
        self,
        tr_data,
        pressure_bins,
        feature_list,
        col_list,
        method="actual",
        set_="Training",
        reset_norm_vals="No",
        isotherm_data_path="isotherm_data",
    ):
        """
            This function adds the necessary features for the machine learning model.
            tr_data : The data for which we want to add the features.
            pressure_bins: list of tuples giving the start and end points of the pressure ranges we want to use. The interval is half open with equality on
                the greater than side.
        feature_list: The list of features. Will look something like ['c_0', 'c_1', 'c_2', 'c_3', 'c_4', 'c_5', 'c_6']
        col_list: An expanded list of features that includes cross effect terms. Will look something like ['c_0', 'c_1', 'c_2', 'c_3', 'c_4', 'c_5', 'c_6', 'c_0-c_0', 'c_0-c_1', 'c_0-c_2', 'c_0-c_3', 'c_0-c_4', 'c_0-c_5', 'c_0-c_6', 'c_1-c_1', 'c_1-c_2', 'c_1-c_3', 'c_1-c_4', 'c_1-c_5', 'c_1-c_6', 'c_2-c_2', 'c_2-c_3', 'c_2-c_4', 'c_2-c_5', 'c_2-c_6', 'c_3-c_3', 'c_3-c_4', 'c_3-c_5', 'c_3-c_6', 'c_4-c_4', 'c_4-c_5', 'c_4-c_6', 'c_5-c_5', 'c_5-c_6', 'c_6-c_6']
            method : The method we want to use for ML.
            set_: The set (Training or Test) for which we want to add the features.
            reset_norm_vals: If this is set to "Yes", the normalization values will be reset even if they have already been set before.
            The variables set_ and reseet_norm_vals are only required for normalizing the feature set and details are provided in the
            function "normalize_df".
        """
        # if method=="actual": #This means we are using ML model to compute true monolayer areas.
        tr_data = self.pressure_bin_features(
            tr_data, pressure_bins, isotherm_data_path=isotherm_data_path
        )
        tr_data = self.combine_features(tr_data, feature_list)
        tr_data = self.normalize_df(
            tr_data, col_list, set_=set_, reset_norm_vals=reset_norm_vals
        )

        return tr_data


# This function returns the ML prediction of the surface area for the new structure, uploaded to the website by the user.
def calculation_v2_runner(MAIN_PATH, USER_ID):
    # The function takes the main path to the SESAMI web folder and the user's unique ID so that the correct isotherm (input.txt) is read and 
    # figures can be placed in the appropriate folder.

    my_ML = ML()  # This initiates the class.

    # This is the description for this particular type of run. All of the output files will have this in their name which can be used to identify them.

    isotherm_data_path = (
        f"{MAIN_PATH}user_{USER_ID}/input.txt"  # path to isotherm data.
    )

    test_data = pd.DataFrame(
        {"name": ["user_input"]}
    )  # This will hold the features of the new MOF/material that is input at the GUI.

    # Actual pressure bins as features.

    # Here, we are creating the pressure bins which can be used for the ML model.
    n_bins = 7
    pressure_bins = my_ML.build_pressure_bins(5, 1e5, n_bins)

    # Here, we generate a string for the various columns in the regression which we will input to the formula.
    feature_list = ["c_%d" % i for i in range(len(pressure_bins))]

    # This is the list of features that we want to use.
    col_list = feature_list + my_ML.generate_combine_feature_list(
        feature_list, degree=2
    )

    # We now proceed to add the features to the dataframe.
    test_data = my_ML.add_features(
        test_data,
        pressure_bins,
        feature_list,
        col_list,
        method="actual",
        set_="Test",
        isotherm_data_path=isotherm_data_path,
    )

    # Check if any values in the dataframe are Null
    if test_data.isnull().values.any(): # This would prevent lasso.predict from running correctly.
        return f"Missing data in a pressure bin, so the ML prediction could not be generated. The bins are, in Pa, {pressure_bins}" # Quits, does not proceed with the rest of the function.

    test_data = test_data.dropna(subset=col_list)

    # Loading the LASSO model.
    lasso = pickle.load(open(f"{MAIN_PATH}/SESAMI/SESAMI_2/lasso_model.sav", "rb"))
        # The LASSO model was trained following the jupyter notebook code in the SESAMI 2 paper
        # It was saved using pickle.dump(lasso, open('lasso_model.sav', 'wb'))

    test_data["FittedValues"] = lasso.predict(test_data[col_list])

    test_prediction = test_data.iloc[0]["FittedValues"]
    test_prediction = f"{test_prediction:.2f}"  # 2 digits after the decimal place

    return test_prediction

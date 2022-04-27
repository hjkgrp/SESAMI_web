import flask
from flask import session
import json
import csv
import os
import time
import stat
import shutil
import pandas as pd
from SESAMI.SESAMI_1.SESAMI_1 import calculation_runner
from SESAMI.SESAMI_2.SESAMI_2 import calculation_v2_runner

app = flask.Flask(__name__)
app.secret_key = "TODO make this actually secret later"

MAIN_PATH = os.path.abspath(".") + "/"  # the main directory
RUN_SESAMI_RUNNING = False # This variable keeps track of whether the function run_SESAMI is currently running.


@app.route("/")
def index():
    return flask.send_from_directory(".", "index.html")


@app.route("/libraries/<path:path>")
def serve_library_files(path):
    return flask.send_from_directory("libraries", path)


@app.route("/images/<path:path>")
def serve_images(path):
    return flask.send_from_directory("images", path)


@app.route("/generated_plots/<path:path>")
def serve_plots(path):
    return flask.send_from_directory(f'user_{session["ID"]}', path)


# Saves the uploaded CSV as a CSV and TXT file
@app.route("/save_txt", methods=["POST"])
def save_txt():
    my_dict = json.loads(flask.request.get_data())  # This is a dictionary.
    my_content = my_dict["my_content"]

    # Writing the CSV the user provided.
    with open(f'{MAIN_PATH}user_{session["ID"]}/input.csv', "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(my_content)

    # Converting the CSV to a TXT
    with open(f'{MAIN_PATH}user_{session["ID"]}/input.txt', "w") as output_file:
        with open(f'{MAIN_PATH}user_{session["ID"]}/input.csv', "r") as input_file:
            [
                output_file.write("\t".join(row) + "\n")
                for row in csv.reader(input_file)
            ]  # \t is tab

    return "0"


@app.route("/run_SESAMI", methods=["POST"])
def run_SESAMI():
    """
    TODO fix the docstring
    Calculate the distance between two points.

    Parameters
    ----------
    rA, rB : np.ndarray
        The coordinates of each point.

    Returns
    -------
    distance: float
        The distance between the two points.

    """
    global RUN_SESAMI_RUNNING

    # Only one user can run this function at a time.
    while RUN_SESAMI_RUNNING:
        time.sleep(5) # Sleep for 5 seconds.
    RUN_SESAMI_RUNNING = True

    ### SESAMI 1
    plotting_information = json.loads(flask.request.get_data())  # This is a dictionary.

    ### End of the user input check.

    # Running the calculation. Makes plots.
    BET_dict, BET_ESW_dict = calculation_runner(
        MAIN_PATH, plotting_information, session["ID"]
    )

    # Displaying statistics
    if BET_dict is None or BET_ESW_dict is None:
        RUN_SESAMI_RUNNING = False
        return "Linear failure"
    else:
        # reformatting
        BET_dict["C"] = "%.4g" % BET_dict["C"]
        BET_dict["qm"] = "%.2f" % BET_dict["qm"]
        BET_dict["A_BET"] = "%.3f" % BET_dict["A_BET"]
        BET_dict["R2"] = "%.6f" % BET_dict["R2"]

        BET_analysis = f'C = {BET_dict["C"]}\n\
            qmsub = {BET_dict["qm"]} mol/kg\n\
            BET surface area = {BET_dict["A_BET"]} m2sup/g\n\
            Consistency 1: Yes\n\
            Consistency 2: Yes\n\
            Consistency 3: {BET_dict["con3"]}\n\
            Consistency 4: {BET_dict["con4"]}\n\
            Length of region: {BET_dict["length"]}\n\
            R2sup: {BET_dict["R2"]}'  # If a linear region is selected, it satisfies criteria 1 and 2. See SI for https://pubs.acs.org/doi/abs/10.1021/acs.jpcc.9b02116

        # reformatting
        BET_ESW_dict["C"] = "%.4g" % BET_ESW_dict["C"]
        BET_ESW_dict["qm"] = "%.2f" % BET_ESW_dict["qm"]
        BET_ESW_dict["A_BET"] = "%.3f" % BET_ESW_dict["A_BET"]
        BET_ESW_dict["R2"] = "%.6f" % BET_ESW_dict["R2"]

        BETESW_analysis = f'C = {BET_ESW_dict["C"]}\n\
            qmsub = {BET_ESW_dict["qm"]} mol/kg\n\
            BET surface area = {BET_ESW_dict["A_BET"]}m2sup/g\n\
            Consistency 1: Yes\n\
            Consistency 2: Yes\n\
            Consistency 3: {BET_ESW_dict["con3"]}\n\
            Consistency 4: {BET_ESW_dict["con4"]}\n\
            Length of region: {BET_ESW_dict["length"]}\n\
            R2sup: {BET_ESW_dict["R2"]}'  # If a linear region is selected, it satisfies criteria 1 and 2. See SI for https://pubs.acs.org/doi/abs/10.1021/acs.jpcc.9b02116

    ### SESAMI 2
    ML_prediction = calculation_v2_runner(MAIN_PATH, session["ID"])

    calculation_results = {
        "ML_prediction": ML_prediction,
        "BET_analysis": BET_analysis,
        "BETESW_analysis": BETESW_analysis,
    }

    RUN_SESAMI_RUNNING = False
    return calculation_results


def file_age_in_seconds(pathname):
    """
    TODO fix the docstring
    Calculate the distance between two points.

    Parameters
    ----------
    rA, rB : np.ndarray
        The coordinates of each point.

    Returns
    -------
    distance: float
        The distance between the two points.

    """

    """
    file_age_in_seconds returns the age of the file/folder specified in pathname since the last modification.
    It is used as a helper function in the set_ID function.

    :return: The age of the file/folder specified in pathname since the last modification, in seconds.
    """

    return (
        time.time() - os.stat(pathname)[stat.ST_MTIME]
    )  # time since last modification


# The two functions that follow handle user session creation and information passing
@app.route("/new_user", methods=["GET"])
def set_ID():
    """
    TODO fix the docstring
    Calculate the distance between two points.

    Parameters
    ----------
    rA, rB : np.ndarray
        The coordinates of each point.

    Returns
    -------
    distance: float
        The distance between the two points.

    """

    """
    set_ID sets the session user ID.
    This is also used to generate unique folders, so that multiple users can use the website at a time.
        The user's folder is user_[ID]
    This function also deletes user folders and files that have not been used for a while in order to reduce clutter.

    :return: string, The session ID for this user.
    """

    session["ID"] = time.time()  # a unique ID for this session

    os.makedirs(f'user_{session["ID"]}')  # Making a folder for this user.

    target_str = "user_"

    # Delete all user folders that haven't been used for a while, to prevent folder accumulation.
    for root, dirs, files in os.walk(MAIN_PATH):
        for dir in dirs:
            # Note: the way this is set up, don't name folders with the phrase "user_" in them if you want them to be permanent.
            if (
                target_str in dir and file_age_in_seconds(dir) > 7200
            ):  # 7200s is two hours
                # target_str in dir to find all folders with user_ in them
                shutil.rmtree(dir)

    return str(session["ID"])


@app.route("/get_ID", methods=["GET"])
def get_ID():
    """
    TODO fix the docstring
    Calculate the distance between two points.

    Parameters
    ----------
    rA, rB : np.ndarray
        The coordinates of each point.

    Returns
    -------
    distance: float
        The distance between the two points.

    """

    """
    get_ID gets the session user ID.
    This is used for getting building block generated MOFs.

    :return: string, The session ID for this user.
    """
    return str(session["ID"])


# Function to check if a type is a number.
def type_number(my_type):
    return not (
        my_type == "int64" or my_type == "float64"
    )  # true if my_type is not a number


@app.route("/check_csv", methods=["GET"])
def check_csv():
    """
    TODO fix the docstring
    Calculate the distance between two points.

    Parameters
    ----------
    rA, rB : np.ndarray
        The coordinates of each point.

    Returns
    -------
    distance: float
        The distance between the two points.

    """
    
    ### Checks

    input_location = f'{MAIN_PATH}user_{session["ID"]}/input.txt'

    data = pd.read_table(input_location, skiprows=1, sep="\t")

    if data.shape[1] != 2:
        return "Wrong number of columns in the CSV. There should be two. Please refer to the example CSV."

    column_names = ["Pressure", "Loading"]
    data = pd.read_table(input_location, skiprows=1, sep="\t", names=column_names)
    dataTypeSeries = (
        data.dtypes
    )  # Series object containing the data type objects of each column of the DataFrame.

    # For each column, check its type. If it is not of int64 or float64 type, raise an Exception.
    for col in column_names:
        if type_number(dataTypeSeries[col]):
            # non numbers in this column
            return "The CSV must contain numbers only. Please refer to the example CSV."

    # Checking for NaN values
    if data.isnull().values.any():
        return "The CSV cannot have any empty cells (gaps), since they lead to NaN values. Please refer to the example CSV."

    # Checking to ensure the first row of the CSV reads Pressure, Loading
    data_header = pd.read_table(input_location, nrows=1, sep="\t", names=column_names)
    if (data_header["Pressure"][0] != "Pressure (Pa)") or (
        data_header["Loading"][0] != "Loading (mol/kg)"
    ):
        return "The CSV does not have the correct first row. The first entries of the two columns should be Pressure (Pa) and Loading (mol/kg), respectively. Please refer to the example CSV."

    # Check to make sure the lowest loading divided by the highest loading is not less than 0.05
    # If it is, the isotherm does not have enough low pressure data.
    data = pd.read_table(input_location, skiprows=1, sep="\t", names=column_names)
    loading_data = list(data["Loading"])
    if loading_data[0] / loading_data[-1] >= 0.05:
        return "Lacking data at low pressure region."

    # If the code gets to this point, the CSV likely doesn't have any problems with it.
    return "All good!"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)

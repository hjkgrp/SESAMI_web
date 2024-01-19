import flask
from flask import session, request
import json
import csv
import os
import time
import stat
import shutil
import uuid
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from SESAMI.SESAMI_1.SESAMI_1 import calculation_runner
from SESAMI.SESAMI_2.SESAMI_2 import calculation_v2_runner
from datetime import datetime

# Mongo Atlas
from pymongo import MongoClient

app = flask.Flask(__name__)


app.secret_key = "The not-so-secret secret key"  # Necessary for sessions.

MAIN_PATH = os.path.abspath(".") + "/"  # the main directory
RUN_SESAMI_RUNNING = False  # This variable keeps track of whether the function run_SESAMI is currently running.
RUN_SESAMI_RUNNING_SETTIME = time.time() # This variable keeps track of the last time RUN_SESAMI_RUNNING was changed to True; set it to time.time() on startup
MONGODB_URI = "mongodb+srv://iast:Tuxe5F5TL0oQQjcM@cluster1.jadjk.mongodb.net/data_isotherm?retryWrites=true&w=majority"

# Next two lines are for later use, when comparing any user uploaded isotherms to the example isotherm.
with open(f"{MAIN_PATH}example_input/example_input.txt", "r") as f:
    EXAMPLE_FILE_CONTENT = f.readlines()


# Flask redirects (that is what all the app.route stuff is). Deals with anything from the index.html frontend.
@app.route("/")
def index():
    return flask.send_from_directory(".", "index.html")


@app.route("/about_page")
def about_page():
    return flask.send_from_directory(".", "about_page.html")


@app.route("/how_to_cite")
def cite_page():
    return flask.send_from_directory(".", "how_to_cite.html")


@app.route("/libraries/<path:path>")
def serve_library_files(path):
    return flask.send_from_directory("libraries", path)


@app.route("/ris_files/<path:path>")
def serve_ris_files(path):
    return flask.send_from_directory("ris_files", path)


@app.route("/images/<path:path>")
def serve_images(path):
    return flask.send_from_directory("images", path)


@app.route("/generated_plots/<path:path>")
def serve_plots(path):
    return flask.send_from_directory(f'user_{session["ID"]}', path)


@app.route("/example_inputs")
def serve_examples():
    return flask.send_from_directory(".", "example_inputs.html")


@app.route("/example_csv")
def serve_csv():
    return flask.send_from_directory("example_input", "example_loading_data.csv")


@app.route("/example_aif")
def serve_aif():
    return flask.send_from_directory("example_input", "example_loading_data.aif")


# Writes the uploaded CSV as a CSV and TXT file. Writes them in the users designated folder.
@app.route("/save_csv_txt", methods=["POST"])
def save_csv_txt():
    my_dict = json.loads(
        flask.request.get_data()
    )  # This is a dictionary. It is the information passed in from the frontend.
    my_content = my_dict["my_content"]

    # Writing the CSV the user provided.
    with open(f'{MAIN_PATH}user_{session["ID"]}/input.csv', "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(my_content)

    # Converting the CSV to a TXT, and saving the TXT.
    with open(f'{MAIN_PATH}user_{session["ID"]}/input.txt', "w") as output_file:
        with open(f'{MAIN_PATH}user_{session["ID"]}/input.csv', "r") as input_file:
            [
                output_file.write("\t".join(row) + "\n")
                for row in csv.reader(input_file)
            ]  # \t is tab

    return "0"  # The return value does not really matter here.


# Writes the uploaded AIF as an AIF and TXT file. Writes them in the users designated folder.
@app.route("/save_aif_txt", methods=["POST"])
def save_aif_txt():
    my_dict = json.loads(
        flask.request.get_data()
    )  # This is a dictionary. It is the information passed in from the frontend.
    my_content = my_dict["my_content"]

    # Writing the AIF the user provided.
    with open(f'{MAIN_PATH}user_{session["ID"]}/input.aif', "w", newline="") as f:
        f.writelines(my_content)

    # Converting the AIF to a TXT, and saving the TXT.
    status = aif_to_txt(my_content)

    return status


def aif_to_txt(content):
    # This helper function converts the AIF into an isotherm text file.
    # content is the content of the AIF

    # Currently, the code does not check the adsorbate, p0, nor the temperature in the AIF file.

    content = content.splitlines()  # split into an array based on new line characters

    # Find the adsorption data, in order to convert to an isotherm data file.
    start_idx = None  # Will instantiate in the loop below.
    for idx, line in enumerate(content):
        if (
            line[:5] == "loop_"
            and content[idx + 1][:16] == "_adsorp_pressure"
            and content[idx + 2][:10] == "_adsorp_p0"
            and content[idx + 3][:14] == "_adsorp_amount"
        ):  # getting only the first 5/16/10/14 characters of respective lines
            start_idx = idx
            break  # No need to keep checking. We found the start of the adsorption data.
    if start_idx is None:  # This means there is a problem.
        return "Incorrectly formatted AIF file. Please refer to the example AIF in the Source Code."  # Quits, does not proceed with the rest of the function.

    # quote from AIF paper Langmuir 2021, 37, 4222−4226: "The data loops, as used here, are terminated by a new data item, a new data loop, or an end of file"
    # Code block below grabs the adsorption data from the AIF file.
    counter = 0
    full_adsorption_data = []
    while True:
        # Note, we have start_idx + 4 because want to skip the first three lines, which are _adsorp_pressure, _adsorp_p0, and _adsorp_amount
        if (start_idx + 4 + counter) >= len(content):  # termination by end of file
            break

        line = content[start_idx + 4 + counter]

        if len(line.strip()) == 0: # termination by an empty line
            break
        if line[0] == "_":  # termination by a new data item
            break
        if line[:5] == "loop_":  # termination by a new data loop
            break

        full_adsorption_data.append(line)

        counter += 1

    if len(full_adsorption_data) == 0:  # This means there is a problem.
        return "Missing adsorption data in the AIF file. Please refer to the example AIF in the Source Code."  # Quits, does not proceed with the rest of the function.

    # Now, we have all of the adsorption data in the variable full_adsorption_data.

    # Next, find the units of loading
    units_loading = None
    for line in content:
        if "_units_loading" in line:
            line_modified = line.replace("'", "") # Removing all single quotation marks
            units_loading = line_modified.split()  # split on spaces
            units_loading = units_loading[1]
            break

    if units_loading is None:  # This means there is a problem.
        return "Incorrectly formatted AIF file. Did not include units of loading. Please refer to the example AIF in the Source Code."  # Quits, does not proceed with the rest of the function.
    supported_units_loading = [
        "mol/kg",
        "mmol/g",
        "cm³/g"
    ]  # May expand on allowed units in the future.
    if units_loading not in supported_units_loading:  # This means there is a problem.
        return f"Invalid/unsupported loading units in AIF file. Supported units are {supported_units_loading}. Please refer to the example AIF in the Source Code."  # Quits, does not proceed with the rest of the function.

    # Grabbing just the adsorption amount data
    adsorption_data = [
        item.split()[2] for item in full_adsorption_data
    ]  # Get the third element of each row (after splitting on spaces)

    # Convert adsorption_data to mol/kg
    if units_loading == "mmol/g" or units_loading == "mol/kg":
        conversion_multiplier = 1 # No action needed
    elif units_loading == "cm³/g":
        conversion_multiplier = 0.044615 # conversion factor mol/kg -> cm^3 STP/g is 22.4139. So here, use its reciprocal
    adsorption_data = [
        str(float(datum) * conversion_multiplier) for datum in adsorption_data
    ]  # Results in a list with entries of the correct units

    # Next, find the units of pressure
    units_pressure = None
    for line in content:
        if "_units_pressure" in line:
            units_pressure = line.split()  # split on spaces
            units_pressure = units_pressure[1]

    if units_pressure is None:  # This means there is a problem.
        return "Incorrectly formatted AIF file. Did not include units of pressure. Please refer to the example AIF in the Source Code."  # Quits, does not proceed with the rest of the function.
    supported_units_pressure = [
        "Pa",
        "pascal",
        "bar",
        "torr",
        "mbar",
        "mb",
    ]  # May expand on allowed units in the future.
    if units_pressure not in supported_units_pressure:  # This means there is a problem.
        return f"Invalid/unsupported pressure units in AIF file. Supported units are {supported_units_pressure}. Please refer to the example AIF in the Source Code."  # Quits, does not proceed with the rest of the function.

    # Grabbing just the pressure data
    pressure_data = [
        item.split()[0] for item in full_adsorption_data
    ]  # Get the first element of each row (after splitting on spaces)

    # # Grabbing just the p0 data
    # saturation_pressure_data = [item.split()[1] for item in full_adsorption_data] # Get the second element of each row (after splitting on spaces)
    # saturation_pressure = saturation_pressure_data[0] # All elements in saturation_pressure_data should be the same anyway. Since saturation pressure depends on the temperature and adsorbate type, and these aren't changing.
    # p0 = float(saturation_pressure)

    # Convert pressure units
    if units_pressure in ["Pa", "pascal"]:
        conversion_multiplier = 1 # No action needed
    elif units_pressure == "bar":
        conversion_multiplier = 100000 # bar to Pascal
    elif units_pressure == "torr":
        conversion_multiplier = 133.322 # torr to Pascal
    elif units_pressure in ["mbar", "mb"]:
        conversion_multiplier = 100 # mbar to Pascal
    pressure_data = [
        str(float(datum) * conversion_multiplier) for datum in pressure_data
    ]  # Results in a list with entries of the correct units.

    with open(f'{MAIN_PATH}user_{session["ID"]}/input.txt', "w") as f:
        f.write("\t".join(["Pressure", "Loading"]) + "\n")  # The column titles
        [
            f.write("\t".join([pressure_data[i], adsorption_data[i]]) + "\n")
            for i in range(len(pressure_data))
        ]  # \t is tab
        # join on tabs, and add a new line after each join

    # If the code gets to this point, the AIF hopefully doesn't have any problems with it.
    return "All good!"


@app.route("/run_SESAMI", methods=["POST"])
def run_SESAMI():
    # This function runs SESAMI 1 and SESAMI 2 on the user's isotherm.
    # It generates diagnostics (SESAMI 1 and 2) and figures (SESAMI 1).
    # Assumes the user's input.txt has been made by the website already.

    global RUN_SESAMI_RUNNING, RUN_SESAMI_RUNNING_SETTIME  # global variables

    # Only one user can run this function at a time.
    while RUN_SESAMI_RUNNING:
        time.sleep(5)  # Sleep for 5 seconds.
        print("Sleep 5 seconds")
        if (time.time() - RUN_SESAMI_RUNNING_SETTIME) > 15: # more than fifteen seconds have passed since run_SESAMI was triggered by some user
            RUN_SESAMI_RUNNING = False

    RUN_SESAMI_RUNNING = True
    RUN_SESAMI_RUNNING_SETTIME = time.time()

    ### SESAMI 1
    user_options = json.loads(
        flask.request.get_data()
    )  # This is a dictionary. It is the information passed in from the frontend.

    # Running the SESAMI 1 calculation. Makes plots.
    BET_dict, BET_ESW_dict = calculation_runner(
        MAIN_PATH, user_options, session["ID"], session["plot_number"]
    )

    session["plot_number"] += 1  # So that the next set of plots have different names

    # Packaging the diagnostics to be sent back to the frontend (index.html).
    if BET_dict == 'No eswminima': # This is a problem.
        RUN_SESAMI_RUNNING = False  # Important to set this to False when the function is quit, so that other users can use the function.
        return (
            "No eswminima"  # Quits, does not proceed with the rest of the function.
        )        
    if BET_dict == 'BET linear failure':  # This is a problem.
        RUN_SESAMI_RUNNING = False  # Important to set this to False when the function is quit, so that other users can use the function.
        return (
            "BET linear failure"  # Quits, does not proceed with the rest of the function.
        )
    if BET_ESW_dict == 'BET+ESW linear failure': # This is a problem.
        RUN_SESAMI_RUNNING = False  # Important to set this to False when the function is quit, so that other users can use the function.
        return (
            "BET+ESW linear failure"  # Quits, does not proceed with the rest of the function.
        )        
    
    # reformatting
    BET_dict["C"] = "%.4g" % BET_dict["C"]
    BET_dict["qm"] = "%.2f" % BET_dict["qm"]
    BET_dict["A_BET"] = "%.1f" % BET_dict["A_BET"]
    BET_dict["R2_linear_region"] = "%.4f" % BET_dict["R2_linear_region"]

    BET_analysis = f'BET area = {BET_dict["A_BET"]} m2sup/g\n\
        C = {BET_dict["C"]}\n\
        qmsub = {BET_dict["qm"]} mol/kg\n\
        Rouquerol consistency criteria 1 and 2: Yes\n\
        Rouquerol consistency criterion 3: {BET_dict["con3"]}\n\
        Rouquerol consistency criterion 4: {BET_dict["con4"]}\n\
        Number of points in linear region: {BET_dict["length_linear_region"]}\n\
        Lowest pressure of linear region: {int(np.rint(BET_dict["low_P_linear_region"]))} Pa\n\
        Highest pressure of linear region: {int(np.rint(BET_dict["high_P_linear_region"]))} Pa\n\
        R2sup of linear region: {BET_dict["R2_linear_region"]}'  # If a linear region is selected, it satisfies criteria 1 and 2. See SI for https://pubs.acs.org/doi/abs/10.1021/acs.jpcc.9b02116
    # np.rint rounds to the nearest integer

    if user_options['scope'] == 'BET': # Exclude ESW analysis
        BETESW_analysis = None
    else: # Include ESW analysis
        # reformatting
        BET_ESW_dict["C"] = "%.4g" % BET_ESW_dict["C"]
        BET_ESW_dict["qm"] = "%.2f" % BET_ESW_dict["qm"]
        BET_ESW_dict["A_BET"] = "%.1f" % BET_ESW_dict["A_BET"]
        BET_ESW_dict["R2_linear_region"] = "%.4f" % BET_ESW_dict["R2_linear_region"]

        BETESW_analysis = f'BET area = {BET_ESW_dict["A_BET"]} m2sup/g\n\
            C = {BET_ESW_dict["C"]}\n\
            qmsub = {BET_ESW_dict["qm"]} mol/kg\n\
            Rouquerol consistency criteria 1 and 2: Yes\n\
            Rouquerol consistency criterion 3: {BET_ESW_dict["con3"]}\n\
            Rouquerol consistency criterion 4: {BET_ESW_dict["con4"]}\n\
            Number of points in linear region: {BET_ESW_dict["length_linear_region"]}\n\
            Lowest pressure of linear region: {int(np.rint(BET_ESW_dict["low_P_linear_region"]))} Pa\n\
            Highest pressure of linear region: {int(np.rint(BET_ESW_dict["high_P_linear_region"]))} Pa\n\
            R2sup of linear region: {BET_ESW_dict["R2_linear_region"]}'  # If a linear region is selected, it satisfies criteria 1 and 2. See SI for https://pubs.acs.org/doi/abs/10.1021/acs.jpcc.9b02116

    if user_options['ML'] == 'No': # Exclude ML prediction
        ML_prediction = None # Placeholder        
    else:
        ### SESAMI 2
        ML_prediction = calculation_v2_runner(
            MAIN_PATH, session["ID"]
        )  # ML stands for machine learning.

        if is_number(ML_prediction): # If ML_prediction is not a number, it is the error message about a bin being empty. If it is a number, the ML calculation ran, and we want to run some code on the number.
            ML_prediction = float(ML_prediction
                ) # Casting to float.

            # Multiply by 1.148 if Nitrogen gas used instead of Argon, to account for difference in cross-sectional areas.
            if user_options['gas'] == 'Nitrogen':
                ML_prediction *= 1.148

            ML_prediction = "%.1f" % ML_prediction # One decimal precision. Casting back to string.

    calculation_results = {
        "ML_prediction": ML_prediction, 
        "BET_analysis": BET_analysis,
        "BETESW_analysis": BETESW_analysis,
        "plot_number": session["plot_number"] - 1,
    }

    RUN_SESAMI_RUNNING = False  # Important to set this to False when the function is quit, so that other users can use the function.
    return calculation_results  # Sends back SESAMI 1 and 2 diagnostics to be displayed, as well as the plot number so the appropriate plots are displayed.


def is_number(s):
    """
    is_number assesses whether the inputted string is a number; that it an be cast to a float.
    It is used as a helper function in the run_SESAMI function.

    :return: Boolean indicating whether the input string can be cast to a float.
    """
    try:
        float(s)
        return True
    except ValueError:
        return False


def file_age_in_seconds(pathname):
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
    set_ID sets the session user ID.
    This is also used to generate unique folders, so that multiple users can use the website at a time.
        The user's folder is user_[ID]
    This function also deletes user folders and files that have not been used for a while in order to reduce clutter.

    :return: string, The session ID for this user.
    """

    session["ID"] = uuid.uuid4()  # a unique ID for this session
    session[
        "permission"
    ] = True  # keeps track of if user gave us permission to store the isotherms they predict on; defaults to True
    session["plot_number"] = 0  # the number identifier for the SESAMI 1 figures
    # Having unique names for all figures generated (as opposed to overwriting figures) prevents issues in the front end when displaying figures.
    session["raw_plot_number"] = 0  # the number identifier for the raw data figures

    os.makedirs(f'user_{session["ID"]}')  # Making a folder for this user.

    target_str = "user_"

    # Delete all old user folders that haven't been used for a while, to prevent folder accumulation.
    for root, dirs, files in os.walk(MAIN_PATH):
        for dir in dirs:
            # Note: the way this is set up, don't name folders with the phrase "user_" in them if you want them to be permanent.
            if (
                target_str in dir and file_age_in_seconds(dir) > 7200
            ):  # 7200s is two hours
                # target_str in dir to find all folders with user_ in them
                shutil.rmtree(dir)

    return str(session["ID"])


# Function to check if a type is a number.
def type_number(my_type):
    return not (
        my_type == "int64" or my_type == "float64"
    )  # true if my_type is not a number


@app.route("/check_csv", methods=["GET"])
def check_csv():
    # This function checks the user uploaded CSV to make sure it is correctly formatted.

    ### Checks

    input_location = f'{MAIN_PATH}user_{session["ID"]}/input.txt'  # Looks in the user's folder. The input file is made by the function save_csv_txt.

    data = pd.read_table(input_location, skiprows=1, sep="\t")

    if data.shape[1] != 2:  # This is a problem.
        return "Wrong number of columns in the CSV. There should be two. Please refer to the example CSV in the Source Code."

    column_names = ["Pressure", "Loading"]
    data = pd.read_table(input_location, skiprows=1, sep="\t", names=column_names)
    dataTypeSeries = (
        data.dtypes
    )  # Series object containing the data type objects of each column of the DataFrame.

    # For each column, check its type. If it is not of int64 or float64 type, raise an Exception.
    for col in column_names:
        if type_number(dataTypeSeries[col]):  # This is a problem.
            # non numbers in this column
            return "The CSV must contain numbers only. Please refer to the example CSV in the Source Code."

    # Checking for NaN values
    if data.isnull().values.any():  # This is a problem.
        return "The CSV cannot have any empty cells (gaps), since they lead to NaN values. Please refer to the example CSV in the Source Code."

    # Checking to ensure the first row of the CSV reads Pressure, Loading
    data_header = pd.read_table(input_location, nrows=1, sep="\t", names=column_names)
    if (data_header["Pressure"][0] != "Pressure (Pa)") or (
        data_header["Loading"][0] != "Loading (mol/kg)"
    ):  # This is a problem.
        return "The CSV does not have the correct first row. The first entries of the two columns should be Pressure (Pa) and Loading (mol/kg), respectively. Please refer to the example CSV in the Source Code."

    # Check to make sure the lowest loading divided by the highest loading is not less than 0.05
    # If it is, the isotherm does not have enough low pressure data.
    data = pd.read_table(input_location, skiprows=1, sep="\t", names=column_names)
    loading_data = list(data["Loading"])
    if loading_data[0] / loading_data[-1] >= 0.05:  # This is a problem.
        return "Warning: Lacking data at low pressure region. The ratio of the lowest loading to the highest loading is not less than 0.05. You can still run calculations, though."

    # If the code gets to this point, the CSV likely doesn't have any problems with it.
    return "All good!"


## Handle information storage
connection_string = ""


@app.route("/process_info", methods=["POST"])
def process_info():
    """
    process_info inserts the website info into the MongoDB isotherm database.
    """

    global EXAMPLE_FILE_CONTENT  # global variable

    if not session[
        "permission"
    ]:  # The user has not given us permission to store information on their isotherms
        return (
            "",
            204,
        )  # 204 no content response. Don't proceed with the rest of the function.

    # If the user is predicting on the example isotherm data, we don't store that.
    with open(f'{MAIN_PATH}user_{session["ID"]}/input.txt', "r") as f:
        isotherm_data = f.readlines()
    if isotherm_data == EXAMPLE_FILE_CONTENT:
        return (
            "",
            204,
        )  # 204 no content response. Don't proceed with the rest of the function.

    client = MongoClient(MONGODB_URI)  # connect to public ip google gcloud mongodb

    db = client.data_isotherm
    collection = db.BET  # The BET collection in isotherm_db database

    # The keys of this dictionary will be name, email, institution, adsorbent, isotherm_data, adsorbate, ip, and timestamp.
    final_dict = {}

    info_dict = json.loads(
        flask.request.get_data()
    )  # This is a dictionary. It is the information passed in from the frontend.

    final_dict["name"] = info_dict["name"]
    final_dict["email"] = info_dict["email"]
    final_dict["institution"] = info_dict["institution"]
    final_dict["adsorbent"] = info_dict["adsorbent"]
    final_dict["isotherm_data"] = isotherm_data
    final_dict["custom_adsorbate"] = info_dict["custom_adsorbate"]

    if info_dict["custom_adsorbate"] == 'No':  
        final_dict["adsorbate"] = info_dict["adsorbate"]

        if info_dict["adsorbate"] == "Nitrogen":
            final_dict["temperature"] = 77
            final_dict["cross_section"] = 16.2
        elif info_dict["adsorbate"] == "Argon":
            final_dict["temperature"] = 87 
            final_dict["cross_section"] = 14.2

        # For both of the above gases, saturation pressure is 1e5 Pa
        final_dict["saturation_pressure"] = 100000
    elif info_dict["custom_adsorbate"] == 'Yes':
        final_dict["adsorbate"] = "Custom" # We specify the special case, since a custom gas is used.
        final_dict["temperature"] = info_dict["custom_temperature"]
        final_dict["cross_section"] = info_dict["custom_cross_section"]
        final_dict["saturation_pressure"] = info_dict["custom_saturation_pressure"]


    final_dict["ip"] = request.remote_addr
    final_dict["timestamp"] = datetime.now().isoformat()

    # insert the dictionary into the mongodb collection
    collection.insert_one(final_dict)
    return ("", 204)  # 204 no content response


@app.route("/permission", methods=["POST"])
def change_permission():
    """
    change_permission adjusts whether or not the website stores information on the isotherms the user predicts on, as well as user name, email, etc.

    :return: string, The boolean sent from the frontend. We return this because we have to return something, but nothing is done with the returned value on the frontend.
    """

    # Grab data
    permission = json.loads(flask.request.get_data())
    session["permission"] = permission

    return str(permission)


@app.route("/copy_example", methods=["GET"])
def copy_example():
    # This function copies over the example isotherm into the user's folder. This lets the user run the SESAMI calculations on the example isotherm.

    shutil.copyfile(
        f"{MAIN_PATH}example_input/example_input.txt",
        f'{MAIN_PATH}user_{session["ID"]}/input.txt',
    )

    return "0"  # The return value does not really matter here.


@app.route("/show_data", methods=["GET"])
def show_data():
    # This function generates a scatter plot of the user's isotherm data.

    column_names = ["Pressure", "Loading"]
    data = pd.read_table(
        f'{MAIN_PATH}user_{session["ID"]}/input.txt',
        skiprows=1,
        sep="\t",
        names=column_names,
    )

    plt.figure()
    ax = plt.gca()
    ax.plot(
        data["Pressure"],
        data["Loading"],
        "o",
        c="blue",
        markeredgecolor="none",
        label="Your data",
    )
    ax.set_xscale("log")
    ax.set_xlabel("Pressure (Pa), log scale")
    ax.set_ylabel("Loading (mol/kg)")
    ax.set_title("Your isotherm")
    ax.legend()
    plt.savefig(
        f'{MAIN_PATH}user_{session["ID"]}/raw_data_{session["raw_plot_number"]}.png',
        format="png",
        dpi=300,
        bbox_inches="tight",
    )

    session["raw_plot_number"] += 1

    return str(session["raw_plot_number"] - 1)


if __name__ == "__main__":
    print(MONGODB_URI)
    app.run(host="0.0.0.0", port=8000, debug=True)

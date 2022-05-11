import flask
from flask import session, request
import json
import csv
import os
import time
import stat
import shutil
import pandas as pd
from SESAMI.SESAMI_1.SESAMI_1 import calculation_runner
from SESAMI.SESAMI_2.SESAMI_2 import calculation_v2_runner
from datetime import datetime
# Mongo Atlas
from pymongo import MongoClient

app = flask.Flask(__name__)

app.secret_key = "TODO make this actually secret later" # Necessary for sessions
MAIN_PATH = os.path.abspath(".") + "/"  # the main directory
RUN_SESAMI_RUNNING = False # This variable keeps track of whether the function run_SESAMI is currently running.
MONGODB_URI = "mongodb+srv://iast:Tuxe5F5TL0oQQjcM@cluster1.jadjk.mongodb.net/data_isotherm?retryWrites=true&w=majority"


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

# Saves the uploaded CSV as a CSV and TXT file
@app.route("/save_csv_txt", methods=["POST"])
def save_csv_txt():
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
    my_dict = json.loads(flask.request.get_data())  # This is a dictionary.
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

    return "0"

# Saves the uploaded AIF as an AIF and TXT file
@app.route("/save_aif_txt", methods=["POST"])
def save_aif_txt():
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
    my_dict = json.loads(flask.request.get_data())  # This is a dictionary.
    my_content = my_dict["my_content"]

    # Writing the AIF the user provided.
    with open(f'{MAIN_PATH}user_{session["ID"]}/input.aif', "w", newline="") as f:
        f.writelines(my_content)

    # Converting the AIF to a TXT, and saving the TXT.
    status = aif_to_txt(my_content)

    return status

def aif_to_txt(content):
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
    # This function converts the AIF into a isotherm text file.
    # content is the content of the AIF

    # Currently, the code does not check the adsorbate, p0, nor the temperature in the AIF file.

    content = content.splitlines() # split into an array based on new line characters

    # Find the adsorption data, in order to convert to an isotherm data file.
    start_idx = None # Will instatiate in the loop below.
    end_idx = None # Will instatiate in the loop below.
    for idx, line in enumerate(content):
        if line[:5] == 'loop_' and content[idx+1][:16] == '_adsorp_pressure' and \
        content[idx+2][:10] == '_adsorp_p0' and content[idx+3][:14] == '_adsorp_amount': # getting only the first 5/16/10/14 characters of respective lines
            start_idx = idx
            break # No need to keep checking. We found the start of the adsorption data.
    if start_idx == None:
        return("Incorrectly formatted AIF file. Please see example file.")

    # quote from AIF paper Langmuir 2021, 37, 4222−4226: "The data loops, as used here, are terminated by a new data item, a new data loop, or an end of file"
    # Code block below grabs the adsorption data from the AIF file.
    counter = 0
    full_adsorption_data = []
    while True:
        # Note, we have start_idx + 4 because want to skip the first three lines, which are _adsorp_pressure, _adsorp_p0, and _adsorp_amount
        if (start_idx + 4 + counter) >= len(content): # termination by end of file
            break 

        line = content[start_idx + 4 + counter]

        if line[0] == '_': # termination by a new data item
            break
        if line[:5] == 'loop_': # termination by a new data loop
            break

        full_adsorption_data.append(line)

        counter += 1

    if len(full_adsorption_data) == 0:
        return("Missing adsorption data in the AIF file.")

    # Now, we have all of the adsorption data in the variable full_adsorption_data.

    # Next, find the units of loading
    units_loading = None
    for line in content:
        if '_units_loading' in line:
            units_loading = line.split() # split on spaces
            units_loading = units_loading[1]
            break

    if units_loading == None:
        return("Incorrectly formatted AIF file. Did not include units of loading.")
    supported_units_loading = ['mol/kg', 'mmol/g'] # TODO expand on allowed units in the future
    if units_loading not in supported_units_loading: 
        return(f'Invalid/unsupported loading units in AIF file. Supported units are {supported_units_loading}')

    # Grabbing just the adsorption amount data
    adsorption_data = [item.split()[2] for item in full_adsorption_data] # Get the third element of each row (after splitting on spaces)

    # Convert adsorption_data to mol/kg
    if units_loading == 'mmol/g':
        conversion_multiplier =  1
        adsorption_data = [datum * conversion_multiplier for datum in adsorption_data] # Results in a list with entries of the correct units
    elif units_loading == 'mol/kg':
        pass # No action needed.

    # Next, find the units of pressure
    units_pressure = None
    for line in content:
        if '_units_pressure' in line:
            units_pressure = line.split() # split on spaces
            units_pressure = units_pressure[1]

    if units_pressure == None:
        return("Incorrectly formatted AIF file. Did not include units of pressure.")
    supported_units_pressure = ['Pa', 'pascal', 'bar'] # TODO expand on allowed units in the future
    if units_pressure not in supported_units_pressure: 
        return(f'Invalid/unsupported pressure units in AIF file. Supported units are {supported_units_pressure}')

    # Grabbing just the pressure data
    pressure_data = [item.split()[0] for item in full_adsorption_data] # Get the first element of each row (after splitting on spaces)

    # # Grabbing just the p0 data
    # saturation_pressure_data = [item.split()[1] for item in full_adsorption_data] # Get the second element of each row (after splitting on spaces)
    # saturation_pressure = saturation_pressure_data[0] # All elements in saturation_pressure_data should be the same anyway. Since saturation pressure depends on the temperature and adsorbate type, and these aren't changing.
    # p0 = float(saturation_pressure)

    # Convert pressure units
    if units_pressure in ['Pa', 'pascal']:
        pass # No action needed
    else: # bar
        conversion_multiplier =  100000
        pressure_data = [datum * conversion_multiplier for datum in pressure_data] # Results in a list with entries of the correct units

    with open(f'{MAIN_PATH}user_{session["ID"]}/input.txt', 'w') as f:
        f.write("\t".join(['Pressure', 'Loading'])+'\n') # The column titles
        [f.write("\t".join([pressure_data[i], adsorption_data[i]])+'\n') for i in range(len(pressure_data))] # \t is tab          
        # join on tabs, and add a new line after each join

    # If the code gets to this point, the AIF hopefully doesn't have any problems with it.
    return "All good!"


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

    # Assumes the user's input.txt has been made by the website already.

    global RUN_SESAMI_RUNNING

    # Only one user can run this function at a time.
    while RUN_SESAMI_RUNNING:
        time.sleep(5) # Sleep for 5 seconds.
        print('Sleep 5 seconds')
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
        BET_dict["A_BET"] = "%.1f" % BET_dict["A_BET"]
        BET_dict["R2"] = "%.4f" % BET_dict["R2"]

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
        BET_ESW_dict["A_BET"] = "%.1f" % BET_ESW_dict["A_BET"]
        BET_ESW_dict["R2"] = "%.4f" % BET_ESW_dict["R2"]

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
    session['permission'] = True # keeps track of if user gave us permission to store the isotherms they predict on; defaults to Yes

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

## Handle information storage
connection_string = ""
@app.route('/process_info', methods=['POST'])
def process_info():
    """
    process_info inserts the website info into the MongoDB isotherm database. 
    """

    client = MongoClient(MONGODB_URI)  # connect to public ip google gcloud mongodb

    db = client.data_isotherm
    # The SESAMI collection in the isotherm database.
    collection = db.BET # data collection in isotherm_db database
    fields = ['name', 'email', 'institution', 'isotherm_data', 'adsorbate', 'temperature']
    final_dict = {}

    with open(f'{MAIN_PATH}user_{session["ID"]}/input.txt', "r") as f:
        isotherm_data = f.readlines()

    info_dict = json.loads(flask.request.get_data())  # This is a dictionary.

    final_dict['name'] = info_dict['name']
    final_dict['email'] = info_dict['email']
    final_dict['institution'] = info_dict['institution']
    
    if session['permission']: # The user has given us permission to store information on their isotherms
        final_dict['isotherm_data'] = isotherm_data
    else:
        final_dict['isotherm_data'] = ''
    
    final_dict['adsorbate'] = info_dict['adsorbate']

    if info_dict['adsorbate'] == 'Nitrogen':
        final_dict['temperature'] = 77
    elif info_dict['adsorbate'] == 'Argon':
        final_dict['temperature'] = 87
    ###

    # for field in fields: # TODO uncomment this for loop later
    #     final_dict[field] = request.form.get(field)

    # Populate special fields
    # uploaded_file = request.files['file']
    # if uploaded_file.filename == '' and request.form.get('feedback_form_name') != 'upload_form':
    #     # User did not upload the optional TGA trace
    #     print('No TGA trace')

    # final_dict['filetype'] = uploaded_file.content_type
    # filename = secure_filename(uploaded_file.filename)
    # final_dict['filename'] = filename
    # final_dict['file'] = uploaded_file.read()
    # file_ext = os.path.splitext(filename)[1].lower()
    # if file_ext not in app.config['UPLOAD_EXTENSIONS']:
    #     return ('', 204)  # 204 no content response

    # # Special tasks if the form is upload_form
    # if request.form.get('feedback_form_name') == 'upload_form':
    #     uploaded_cif = request.files['cif_file']
    #     cif_filename = secure_filename(uploaded_cif.filename)
    #     file_ext = os.path.splitext(cif_filename)[1].lower()
    #     if file_ext != '.cif':
    #         return ('', 204)  # 204 no content response
    #     final_dict['cif_file_name'] = cif_filename
    #     final_dict['structure'] = uploaded_cif.read()

    final_dict['ip'] = request.remote_addr
    final_dict['timestamp'] = datetime.now().isoformat()

    print(final_dict)
    # insert the dictionary into the mongodb collection
    db.BET.insert_one(final_dict)
    return ('', 204)  # 204 no content response

@app.route('/permission', methods=['POST'])
def change_permission():
    """
    change_permission adjusts whether or not the website stores information on the isotherms the user predicts on.

    :return: string, The boolean sent from the front end. We return this because we have to return something, but nothing is done with the returned value on the front end.
    """

    # Grab data
    permission = json.loads(flask.request.get_data())
    session['permission'] = permission
    print('Permission check')
    print(permission)
    return str(permission)

@app.route("/copy_example", methods=["GET"])
def copy_example():
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

    shutil.copyfile(f'{MAIN_PATH}example_input/example_input.txt', f'{MAIN_PATH}user_{session["ID"]}/input.txt')

    return "0"


if __name__ == "__main__":
    print(MONGODB_URI)
    app.run(host="0.0.0.0", port=8000, debug=True)

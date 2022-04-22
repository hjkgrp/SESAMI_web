import flask
from flask import session
import json
import csv
import os
import time
import stat
import shutil
from SESAMI.SESAMI_1.SESAMI_1 import calculation_runner
from SESAMI.SESAMI_2.SESAMI_2 import calculation_v2_runner

app = flask.Flask(__name__)
app.secret_key = 'TODO make this actually secret later'

MAIN_PATH = os.path.abspath('.') + '/' # the main directory

@app.route("/")
def index():
    return flask.send_from_directory('.', 'index.html')

@app.route('/libraries/<path:path>')
def serve_library_files(path):
    return flask.send_from_directory('libraries', path)

@app.route('/images/<path:path>') 
def serve_images(path):
    return flask.send_from_directory('images', path)

@app.route('/generated_plots/<path:path>') 
def serve_plots(path):
    return flask.send_from_directory('generated_plots', path)

# Saves the uploaded CSV as a TXT file
@app.route('/save_txt', methods=['POST'])
def save_txt():
    my_dict = json.loads(flask.request.get_data()) # This is a dictionary.
    my_content = my_dict['my_content']

    # Writing the CSV the user provided.
    with open(f'{MAIN_PATH}user_{session["ID"]}/input.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(my_content)

    # Converting the CSV to a TXT
    with open(f'{MAIN_PATH}user_{session["ID"]}/input.txt', 'w') as output_file:
        with open(f'{MAIN_PATH}user_{session["ID"]}/input.csv', 'r') as input_file:
            [output_file.write("\t".join(row)+'\n') for row in csv.reader(input_file)] # \t is tab    

    return '0'

@app.route('/run_SESAMI', methods=['POST']) 
def run_SESAMI():
    ### SESAMI 1
    plotting_information = json.loads(flask.request.get_data()) # This is a dictionary.

    ### End of the user input check.

    # Running the calculation. Makes plots.
    BET_dict, BET_ESW_dict = calculation_runner(MAIN_PATH, plotting_information, session["ID"])
    print(f'BET_dict: {BET_dict}')
    print(BET_dict is None)

    # Displaying statistics
    if BET_dict is None or BET_ESW_dict is None:
        return 'Linear failure'
    else:
        # reformatting
        BET_dict["C"] = '%.4g'%BET_dict["C"]
        BET_dict["qm"] = '%.2f'%BET_dict["qm"]
        BET_dict["A_BET"] = '%.3f'%BET_dict["A_BET"]
        BET_dict["R2"] = '%.6f'%BET_dict["R2"]

        BET_analysis = f'C = {BET_dict["C"]}<br>\
            q<sub>m</sub> = {BET_dict["qm"]} mol/kg<br>\
            BET surface area = {BET_dict["A_BET"]} m<sup>2</sup>/g<br>\
            Consistency 1: Yes<br>\
            Consistency 2: Yes<br>\
            Consistency 3: {BET_dict["con3"]}<br>\
            Consistency 4: {BET_dict["con4"]}<br>\
            Length of region: {BET_dict["length"]}<br>\
            R<sup>2</sup>: {BET_dict["R2"]}' # If a linear region is selected, it satisfies criteria 1 and 2. See SI for https://pubs.acs.org/doi/abs/10.1021/acs.jpcc.9b02116

        # reformatting
        BET_ESW_dict["C"] = '%.4g'%BET_ESW_dict["C"]
        BET_ESW_dict["qm"] = '%.2f'%BET_ESW_dict["qm"]
        BET_ESW_dict["A_BET"] = '%.3f'%BET_ESW_dict["A_BET"]
        BET_ESW_dict["R2"] = '%.6f'%BET_ESW_dict["R2"]

        BETESW_analysis = f'C = {BET_ESW_dict["C"]}<br>\
            q<sub>m</sub> = {BET_ESW_dict["qm"]} mol/kg<br>\
            BET surface area = {BET_ESW_dict["A_BET"]}m<sup>2</sup>/g<br>\
            Consistency 1: Yes<br>\
            Consistency 2: Yes<br>\
            Consistency 3: {BET_ESW_dict["con3"]}<br>\
            Consistency 4: {BET_ESW_dict["con4"]}<br>\
            Length of region: {BET_ESW_dict["length"]}<br>\
            R<sup>2</sup>: {BET_ESW_dict["R2"]}' # If a linear region is selected, it satisfies criteria 1 and 2. See SI for https://pubs.acs.org/doi/abs/10.1021/acs.jpcc.9b02116


    ### SESAMI 2
    ML_prediction = calculation_v2_runner(MAIN_PATH, session["ID"])
    print(f'ML_prediction is {ML_prediction}')

    calculation_results = {'ML_prediction': ML_prediction, 'BET_analysis': BET_analysis, 'BETESW_analysis': BETESW_analysis}

    return calculation_results

def file_age_in_seconds(pathname): 
    """
    file_age_in_seconds returns the age of the file/folder specified in pathname since the last modification.
    It is used as a helper function in the set_ID function.

    :return: The age of the file/folder specified in pathname since the last modification, in seconds.
    """ 

    return time.time() - os.stat(pathname)[stat.ST_MTIME] # time since last modification

# The two functions that follow handle user session creation and information passing
@app.route('/new_user', methods=['GET'])
def set_ID():
    """
    set_ID sets the session user ID. 
    This is also used to generate unique folders, so that multiple users can use the website at a time. 
        The user's folder is user_[ID]
    This function also deletes user folders and files that have not been used for a while in order to reduce clutter.

    :return: string, The session ID for this user.
    """ 

    session['ID'] = time.time() # a unique ID for this session

    os.makedirs(f'user_{session["ID"]}') # Making a folder for this user.

    target_str = 'user_'
    target_str_2 = str(session["ID"])

    # Delete all user folders that haven't been used for a while, to prevent folder accumulation.
    for root, dirs, files in os.walk(MAIN_PATH):
        for dir in dirs:
            # Note: the way this is set up, don't name folders with the phrase "user_" in them if you want them to be permanent.
            if target_str in dir and file_age_in_seconds(dir) > 7200: # 7200s is two hours
                # target_str in dir to find all folders with user_ in them
                shutil.rmtree(dir)

        for file in files:
            if target_str_2 in file and file_age_in_seconds(file) > 7200:
                os.remove(file)

    return str(session['ID'])

@app.route('/get_ID', methods=['GET'])
def get_ID():
    """
    get_ID gets the session user ID. 
    This is used for getting building block generated MOFs.

    :return: string, The session ID for this user.
    """ 
    return str(session['ID'])


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
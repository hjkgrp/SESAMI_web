import flask
import json
import csv
import os
from SESAMI.SESAMI_1.SESAMI_1 import calculation_runner
from SESAMI.SESAMI_2.SESAMI_2 import calculation_v2_runner

app = flask.Flask(__name__)

MAIN_PATH = os.path.abspath('.') + '/' # the main directory

@app.route("/")
def index():
    return flask.send_from_directory('.', 'index.html')

@app.route('/libraries/<path:path>')
def serve_library_files(path):
    return flask.send_from_directory('libraries', path)

@app.route('/generated_plots/<path:path>') # TODO change from user_0 to specific user ID down the line
def serve_plots(path):
    return flask.send_from_directory('generated_plots', path)

# Saves the uploaded CSV as a TXT file
@app.route('/save_txt', methods=['POST'])
def save_txt():
    my_dict = json.loads(flask.request.get_data()) # This is a dictionary.
    my_content = my_dict['my_content']

    # Writing the CSV the user provided.
    with open(f'{MAIN_PATH}user_0/input.csv', 'w', newline='') as f: # TODO change from user_0 to specific user ID down the line
        writer = csv.writer(f)
        writer.writerows(my_content)

    # Converting the CSV to a TXT
    with open(f'{MAIN_PATH}user_0/input.txt', 'w') as output_file: # TODO change from user_0 to specific user ID down the line
        with open(f'{MAIN_PATH}user_0/input.csv', 'r') as input_file:
            [output_file.write("\t".join(row)+'\n') for row in csv.reader(input_file)] # \t is tab    

    return '0'

@app.route('/run_SESAMI', methods=['POST']) 
def run_SESAMI():
    user_id = 0 # TODO fix this later

    ### SESAMI 1 # TODO fix this up
    plotting_information = json.loads(flask.request.get_data()) # This is a dictionary.

    ### End of the user input check.

    # Running the calculation. Makes plots.
    BET_dict, BET_ESW_dict = calculation_runner(MAIN_PATH, plotting_information)
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
    ML_prediction = calculation_v2_runner(MAIN_PATH, user_id)
    print(f'ML_prediction is {ML_prediction}')

    calculation_results = {'ML_prediction': ML_prediction, 'BET_analysis': BET_analysis, 'BETESW_analysis': BETESW_analysis}

    return calculation_results

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
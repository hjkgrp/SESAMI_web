import pandas as pd
from SESAMI.SESAMI_1.betan import BETAn


def calculation_runner(MAIN_PATH, user_options, USER_ID, plot_number):
    # This function runs SESAMI 1 code.
    # It generates 6 different types of plots (BET, BET Linear, BET-ESW, ESW, Isotherm, and a Multiplot which shows the previous five types of plots all combined in different panes).
    # It also generates SESAMI 1 BET and BET-ESW information to display on the website.

    # The function takes the main path to the SESAMI web folder, the user-selected plotting information, the user's unique ID so that the correct isotherm (input.txt) is read and 
    # figures can be placed in the appropriate folder, and the plot number so that plots can all be named uniquely.

    minlinelength = 4 # Minimum number of points required for a group of points to be considered a line

    p0 = 1e5  # Note that this is fixed. For both argon at 87 K and nitrogen at 77 K, the saturation pressure is 1e5 Pa.
    gas = user_options["gas"]
    if gas == 'Argon':
        temperature = 87 # K
    elif gas == 'Nitrogen':
        temperature = 77 # K

    # changing some variable types
    user_options["font size"] = int(user_options["font size"])
    user_options["R2 cutoff"] = float(user_options["R2 cutoff"])
    user_options["R2 min"] = float(user_options["R2 min"])
    user_options["dpi"] = float(user_options["dpi"])

    b = BETAn(gas, temperature, minlinelength, user_options)

    column_names = ["Pressure", "Loading"]
    data = pd.read_table(
        f"{MAIN_PATH}user_{USER_ID}/input.txt", skiprows=1, sep="\t", names=column_names
    )
    # Preventing issues with zero pressure in the first row
    if data["Pressure"].iloc[0] == 0: # Zero pressure in the first row
        data.loc[0, 'Pressure'] = data["Pressure"].iloc[1] / 2 # Set the first row's entry to something non-zero (half of the second row's Pressure)

    data = b.prepdata(data, p0=p0)

    # This command generates BET and BET-ESW information and figures.
    BET_dict, BET_ESW_dict = b.generatesummary(
        data, user_options, MAIN_PATH, plot_number, sumpath=f"{MAIN_PATH}user_{USER_ID}/"
    )

    return BET_dict, BET_ESW_dict

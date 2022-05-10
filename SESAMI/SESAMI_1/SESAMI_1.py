import pandas as pd
from SESAMI.SESAMI_1.betan import BETAn


def calculation_runner(MAIN_PATH, plotting_information, USER_ID):
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

    minlinelength = 4

    p0 = 1e5  # Note that this is fixed 
    gas = plotting_information["gas"]
    if gas == 'Argon':
        temperature = 87 # K
    elif gas == 'Nitrogen':
        temperature = 77 # K

    # changing some variable types
    plotting_information["font size"] = int(plotting_information["font size"])
    plotting_information["R2 cutoff"] = float(plotting_information["R2 cutoff"])
    plotting_information["R2 min"] = float(plotting_information["R2 min"])
    plotting_information["dpi"] = float(plotting_information["dpi"])

    b = BETAn(gas, temperature, minlinelength, plotting_information)

    column_names = ["Pressure", "Loading"]
    data = pd.read_table(
        f"{MAIN_PATH}user_{USER_ID}/input.txt", skiprows=1, sep="\t", names=column_names
    )
    data = b.prepdata(data, p0=p0)

    # This command generates BET and BET-ESW information and figures.
    BET_dict, BET_ESW_dict = b.generatesummary(
        data, plotting_information, MAIN_PATH, sumpath=f"{MAIN_PATH}user_{USER_ID}/"
    )

    return BET_dict, BET_ESW_dict

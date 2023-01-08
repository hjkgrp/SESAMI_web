import os
import pytest
import shutil
from SESAMI.SESAMI_2.SESAMI_2 import calculation_v2_runner

MAIN_PATH = os.path.abspath(".") + "/"
USER_ID = 'test' # user ID of 'test' for the purposes of this test

# Getting the example file ready
if not os.path.exists(f'{MAIN_PATH}user_test'):
	os.mkdir(f'{MAIN_PATH}user_test')
shutil.copyfile(
    f"{MAIN_PATH}example_input/example_input.txt",
    f'{MAIN_PATH}user_test/input.txt', # Use an ID of 'test' for the purposes of the test
)

@pytest.mark.parametrize("MAIN_PATH, USER_ID", [(MAIN_PATH, USER_ID)])
def test_SESAMI_2(MAIN_PATH, USER_ID): 
	prediction = calculation_v2_runner(MAIN_PATH, USER_ID)	

	assert prediction == "2099.06" # Benchmark value on the right

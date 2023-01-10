import pandas as pd 

# List of tasks which are automated in current version - note that each of these needs a corresponding evaluation function in Dashboard_automation_setup.py
automated_task_list = ['Multiple object types', 'Single object','Negation','Numbers (multiple objects)','Simple arithmetic']

# Import the list of prompts used in current version
prompt_dir = pd.read_csv('data/Prompt_dir_230104.csv')

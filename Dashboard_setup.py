import streamlit as st
import pandas as pd 

# Dashboard version variables
code_version = 'v0.0.5'
prompt_dir_version = '230228'
compatible_versions = ['0.0.5_pd230228', 'None']
dashboard_version_code = code_version+'_pd'+prompt_dir_version

# List of tasks which are automated in current version - note that each of these needs a corresponding evaluation function in Dashboard_automation_setup.py
automated_task_list = ['Multiple object types', 'Single object','Negation','Numbers (multiple objects)','Simple arithmetic','Conditional generation']

# Import the list of prompts used in current version
prompt_dir = pd.read_csv('data/Prompt_dir_{0}.csv'.format(prompt_dir_version))

# Create sidebar information
def sidebar_information():
    st.sidebar.image('assets/IL_Logo.png')
    st.sidebar.text(dashboard_version_code)

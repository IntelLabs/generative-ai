import streamlit as st
import numpy as np
from itertools import compress
from PIL import Image
from Dashboard_automation_setup import fun_dict

st.title('Automated Assessment')
st.write('On this page you can use automated assessment algorithms to assess how good uploaded images match their respective prompts.')
st.write(' ')
st.sidebar.image('assets/IL_Logo.png')

try:
    # Create necessary variables
    prompt_dir = st.session_state['prompt_dir']
    curr_eval_df = st.session_state['eval_df']
    curr_eval_df['Picture_index']=curr_eval_df.index.values

    # Assess how many images are available for automatic assessment
    automated_eval_available = sum(curr_eval_df['automated_eval'])

    # Add task name to eval_df
    temp_prompt_dir=prompt_dir[['ID','Representations','Task_specific_label']]
    temp_prompt_dir['Prompt_no']=temp_prompt_dir['ID'].astype('str')
    curr_eval_df = curr_eval_df.merge(temp_prompt_dir,on='Prompt_no')

    # Check that user correctly filled out the automation setup file
    assert list(fun_dict.keys())==st.session_state['automated_tasks'], 'Unsure that the list of automated tasks in Dashboard_setup.py is the same as the keys of the function dict in Dashboard_automation_setup.py'
except KeyError:
    automated_eval_available = 0


# If images for assessment available: create form to start assessment
# Else: Note to upload images for assessment
if automated_eval_available > 0:
    
    # Create objects to hold selections of tasks for automated assessment
    task_list = list(fun_dict.keys())
    task_list_len = len(task_list)
    task_list_selected = task_list.copy()

    with st.form("auto_assessment_form",clear_on_submit=True):
        # Form info statment
        st.write('Select tasks to assess with the automated assessment below. Once you started an assessment you will not be able to leave this page before the assessment is completed.')

        # Create list of bool selection buttons, one for every task
        for i_task in range(task_list_len):
            curr_task = task_list[i_task] 
            curr_task_count = len(curr_eval_df.loc[
                        (curr_eval_df['automated_eval']==True)&
                        (curr_eval_df['Task']==curr_task)])
            task_list_selected[i_task] = st.checkbox(      
                '{0} ({1} images available)'.format(curr_task, str(curr_task_count)))

        submitted = st.form_submit_button("Start automated assessment")
        if submitted:        
            # Create list for tasks which were selected for assessment
            selected_tasks = list(compress(task_list,task_list_selected))


            # Create dataset to loop over with assessment
            assessed_df = curr_eval_df.loc[
                    (curr_eval_df['automated_eval']==True)&
                    (curr_eval_df['Task'].isin(selected_tasks))]
            results_column = []
            
            for row in assessed_df.itertuples():
                # Apply task based classifier and safe in list
                temp_image = Image.open(st.session_state['uploaded_img'][row.Picture_index])
                temp_result = fun_dict[row.Task](
                    temp_image,row.Representations,row.Task_specific_label)
                results_column.append(temp_result)

            assessed_df['Score']=results_column
            st.session_state['auto_eval_df']=assessed_df[['File_name','Prompt_no','Picture_index','Task','Score']]
            st.write('Completed assessment. Access results on the summary page.')
else:
    st.write('Upload files on dashboard starting page to start automated assessment.')

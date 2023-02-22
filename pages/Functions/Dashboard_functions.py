# General functions and routines used in the dashboard
'''
- Functions below are ordered by page on which they are used
- If possible, functions should not manipulate the session_state within them
'''

import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from PIL import Image

##### Page-unspecific functions

def if_true_rerun(bool_input):
    '''
    This function triggers a rerun of the page if the input == True
    '''
    if bool_input == True:
        st.experimental_rerun()

def assert_uploaded_frame(uploaded_df):
    # Set up variables checked for
    asserted_columns = {
      'Prompt_no':pd.api.types.is_integer_dtype,
      'Score':pd.api.types.is_bool_dtype,
      'Task':pd.api.types.is_object_dtype,
      'File_name':pd.api.types.is_object_dtype}
    asserted_column_names = ['Prompt_no','Score','Task','File_name']

    # Check whether all needed column names are present
    df_columns_list = uploaded_df.columns.tolist()
    existing_column_names = [(x in df_columns_list) for x in asserted_column_names]
    assert all(existing_column_names), "The uploaded dataframe is missing a column needed for import. Your table needs to contain the columns: 'Prompt_no', 'Score', 'Task', 'File_name' "

    # Check whether all needed columns have correct dtypes
    correct_column_dtypes = []
    for i_item in asserted_columns.items():
        dtype_test = i_item[1](uploaded_df[i_item[0]].dtype)
        correct_column_dtypes.append(dtype_test)
    assert all(correct_column_dtypes), "Incorrect dtypes in uploaded dataframe."

def assert_multi_frame_upload(list_of_uploaded_dfs):
    # Apply uploaded frame assert to list of frames
    for i_df in list_of_uploaded_dfs:
        assert_uploaded_frame(i_df)

##### Dashboard main page
def prompt_to_csv(df, added_version_code='vNone'):
    df_download = df
    df_download['Filename']='p'+df_download['ID'].astype('str')+'_1_'+added_version_code+'.png'
    df_download = df[['Prompt','Filename']].drop_duplicates(subset='Filename')
    return df_download.to_csv().encode('utf-8')

def prompt_df_for_download(prompt_dir):
    '''
    Function to create a subset of the prompt_dir via count based selection
    '''
    # Create local copy of variables
    temp_prompt_dir = prompt_dir

    # Create dict to hold counts of downloaded prompts
    prompt_download_dict = {}
    ## Count how many prompts are in database to allow for max value in selection
    prompt_task_count = temp_prompt_dir.Task.value_counts(sort=False)
    prompt_task_select = prompt_task_count.copy()

    # Create numerical selector for every task in prompt directory, add count per task to dict
    for i_task in prompt_task_select.index:
        prompt_task_select[i_task] = st.number_input(
            i_task,
            value = prompt_task_count[i_task], 
            max_value=prompt_task_count[i_task],
            min_value=0,
            step = 1)

    # Create df with selected number of prompts per task
    for i_task in prompt_task_select.index:
        temp_df = temp_prompt_dir.loc[temp_prompt_dir['Task']==i_task][0:prompt_task_select[i_task]]
        if len(temp_df)>0:
            prompt_download_dict[i_task]=temp_df

    # Concat all tasks to dataframe
    prompt_download = pd.concat(prompt_download_dict.values())

    # Add linked prompts, if the user chooses to
    download_linked_prompts = st.checkbox('Download linked prompts', value=True)
    if download_linked_prompts:

        # Delete rows which do not have linked prompts to avoid type error
        linked_prompts_info = prompt_download.dropna(subset='Linked_prompts')

        # Add relevant linked prompts
        linked_prompts_ids = linked_prompts_info.Linked_prompts.str.split(',').explode().unique().astype('int')
        prompt_download = pd.concat(
            [prompt_download,
            temp_prompt_dir.loc[temp_prompt_dir['ID'].isin(linked_prompts_ids)]])

        # Drop rows prompts which appear twice
        prompt_download = prompt_download.drop_duplicates(subset='ID')

    return prompt_download

##### Manual assessment

def set_eval_df_rating_vals(eval_df, picture_index, manual_eval, manual_eval_completed, manual_eval_task_score):
    '''
    Function to set a block of key manual rating related variables of eval_df
    '''
    temp_eval_df = eval_df
    temp_eval_df.loc[picture_index,'manual_eval']=manual_eval
    temp_eval_df.loc[picture_index,'manual_eval_completed']=manual_eval_completed
    temp_eval_df.loc[picture_index,'manual_eval_task_score']=manual_eval_task_score
    return temp_eval_df 

def radio_rating_index_translation(manual_rating_value):
    if manual_rating_value == "No":
        return 1
    else:
        return 0 


def collect_linked_prompt_ratings(curr_linked_prompts, curr_eval_df, curr_prompt_dir):
    '''
    Create elements to collect ratings on linked prompts:
    If there are linked prompts, create df with info
    Else create emtpy df which will automatically skip the rating creation for these prompts
    Here we do not test for (curr_eval_df['manual_eval']==True) as the curr_linked_prompts 
    is already testing for valid prompt number and we want to ignore the exclusion for subprompts
    '''
    if type(curr_linked_prompts)==list:
        curr_linked_rows = curr_eval_df.loc[
            (curr_eval_df['manual_eval_completed']==False)&
            (curr_eval_df['Prompt_no'].isin(curr_linked_prompts))]
        curr_linked_rows = curr_linked_rows.groupby('Prompt_no').first()
    else:
        curr_linked_rows = pd.DataFrame()

    # Create rating for subprompts if a df for subprompt info was created
    for row in curr_linked_rows.itertuples():
        # Preselected radio option
        radio_preselect = radio_rating_index_translation(row.manual_eval_task_score)
        # Prompt
        st.write('Prompt: {0}'.format(
            curr_prompt_dir.loc[curr_prompt_dir['ID']==int(row.Index)]['Prompt'].item()
        ))
        # Image
        st.image(st.session_state['uploaded_img'][row.Picture_index],width=350)
        # Rating
        curr_linked_rows.loc[curr_linked_rows['Picture_index']==row.Picture_index,'manual_eval_task_score'] = st.radio(
            "Does the image match the prompt?",('Yes', 'No'), horizontal=True, key=row.Picture_index, index=radio_preselect)
        st.write(' ')
        st.write(' ')

    return curr_linked_rows


def delete_last_manual_rating(session_history, eval_df):
    '''
    Routine to delete last manual rating and hence to return to it
    '''
    # Create local copies of objects
    temp_session_history = session_history
    temp_eval_df = eval_df.copy()
    temp_submit = False

    if len(temp_session_history)>0:
        if st.button('Return to last rated image'):
            # The list contains sublists of images rated together, here we loop over these images to reset all of them
            deleted_picture_index_list = temp_session_history.pop()
            for i_picind in deleted_picture_index_list:
                temp_eval_df.loc[
                    i_picind,'manual_eval_completed']=False
                #temp_eval_df.loc[
                #    i_picind,'manual_eval_task_score']=np.nan  
            
            # Set submit boolean to true, to rerun the page
            temp_submit = True
    
    return temp_session_history, temp_eval_df, temp_submit
     

def add_previous_manual_assessments_upload_back(eval_df):
    '''
    Routine to upload a dataframe of previous (manual) assessment to add it to existing database.
    The uploaded df is assessed, matching counts are printed and it returns the imported df for furthe processing.
    '''
    # Create necessary local variables
    temp_eval_df = eval_df

    # Upload single dataframe, setting default to None for code type checking
    temp_uploaded_ratings = None
    temp_uploaded_ratings = st.file_uploader('Select .csv for upload', accept_multiple_files=False)
    if temp_uploaded_ratings != None:
        try:
            # Import the uploaded csv as dataframe
            uploaded_ratings_df = pd.read_csv(temp_uploaded_ratings)
            
            # Run standard assert pipeline
            assert_uploaded_frame(uploaded_ratings_df)

            # Show matching image count and instructions
            overlapping_files_df = pd.merge(temp_eval_df,uploaded_ratings_df,on='File_name',how='inner')
            st.write('Number of matching file names found: '+ str(len(overlapping_files_df)))
            st.write('Click "Add results" button to add / override current ratings with uploaded ratings.')

            return uploaded_ratings_df
        except UnicodeDecodeError:
            st.write('WARNING: The uploaded file has to be a .csv downloaded from the "Assessment summary" page.')
    return temp_uploaded_ratings


def add_previous_manual_assessments_upload(eval_df, dashboard_version_code='vNone'):
    '''
    Routine to upload a dataframe of previous (manual) assessment to add it to existing database.
    The uploaded df is assessed, matching counts are printed and it returns the imported df for furthe processing.
    '''
    # Create necessary local variables
    temp_eval_df = eval_df

    # Upload single dataframe, setting default to None for code type checking
    temp_uploaded_ratings = None
    temp_uploaded_ratings = st.file_uploader('Select .csv for upload', accept_multiple_files=False)
    if temp_uploaded_ratings != None:
        try:
            # Import the uploaded csv as dataframe
            uploaded_ratings_df = pd.read_csv(temp_uploaded_ratings)
            
            # Run standard assert pipeline
            assert_uploaded_frame(uploaded_ratings_df)

            # Check the uploaded df has a registered dashboard version
            assert 'Dashboard_version' in uploaded_ratings_df.columns,"The uploaded dataframe needs to have a Dashboard_version column."
            # Check for correct dashboard version in uploaded file
            matching_dashboard_version = uploaded_ratings_df['Dashboard_version'] == dashboard_version_code
            assert all(matching_dashboard_version),"The dashboard version of your uploaded results does not match the version of this dashboard."

            # Show matching image count and instructions
            overlapping_files_df = pd.merge(temp_eval_df,uploaded_ratings_df,on='File_name',how='inner')
            st.write('Number of matching file names found: '+ str(len(overlapping_files_df)))
            ## Show warning if some of the matching images already have a rating
            if len(overlapping_files_df.manual_eval_task_score.dropna())>0:
                st.write('WARNING: {0} of {1} matching files already have a saved rating. These will be overriden when you click "Add results".'.format(
                    str(len(overlapping_files_df.manual_eval_task_score.dropna())),str(len(overlapping_files_df))))
            st.write('Click "Add results" button to add uploaded ratings to current ratings.')
            return uploaded_ratings_df
        except UnicodeDecodeError:
            st.write('WARNING: The uploaded file has to be a .csv downloaded from the "Assessment summary" page.')
    return temp_uploaded_ratings

def add_previous_manual_assessments_submit(eval_df, uploaded_ratings):
    '''
    If uploaded_ratings != None, this will create a button which when pressed will trigger
    for the provided ratings to be added to eval_df
    '''
    # Create necessary local variables
    temp_eval_df = eval_df
    temp_submitted = False

    # Create dict to translate uploaded score into str format used during manual assessment
    bool_str_dict = {True:'Yes',False:'No'}

    # If a dataframe of uploaded ratings was provided: create a button which allows to add ratings to existing eval_df
    if type(uploaded_ratings) == pd.DataFrame:
        temp_submitted = st.button("Add results")
        if temp_submitted:
            for row in uploaded_ratings.itertuples():
                temp_eval_df.loc[temp_eval_df['File_name']==row.File_name,'manual_eval']=True
                temp_eval_df.loc[temp_eval_df['File_name']==row.File_name,'manual_eval_completed']=True
                temp_eval_df.loc[temp_eval_df['File_name']==row.File_name,'manual_eval_task_score']=bool_str_dict[row.Score]
    return temp_eval_df, temp_submitted


def add_previous_manual_assessments(eval_df, dashboard_version_code):
    '''
    Full routine to allow the user to upload past ratings and add these to eval_df
    '''
    st.subheader('Add previous assessments')
    st.write('Upload results of previous assessment (as downloaded from summary page) to add these results and skip these images in your current manual assessment. Note that you can only add results for images which you have uploaded using the same file name.')

    # Create necessary local variables
    temp_eval_df = eval_df

    # Allow user to upload .csv with prior ratings
    uploaded_ratings = add_previous_manual_assessments_upload(temp_eval_df, dashboard_version_code)

    # Add rating to eval_df, if some were uploaded
    temp_eval_df, temp_submitted = add_previous_manual_assessments_submit(temp_eval_df, uploaded_ratings)

    return temp_eval_df, temp_submitted

##### Assessment summary

def print_results_tabs(file_upload, results_df):
    '''
    #Routine used to give user the choice between showing results as bar chart or table
    '''
    # Create a tab for bar chart and one for table data
    fig, table = multi_comparison_plotI(results_df=results_df, uploaded_df_list=file_upload)
    tab1, tab2 = st.tabs(["Bar chart", "Data table"])
    with tab1:
      st.pyplot(fig)

    with tab2:
        st.write(table)


def pre_assessment_visualisation(type_str):
    '''
    Routine used to allow user to visualise uploaded results before completing any assessments
    '''
    st.write('Complete {0} assessment or upload .csv with saved {0} assessment to generate summary.'.format(type_str))

    # Display file uploader
    file_upload = st.file_uploader("Upload .csv with saved {0} assessment to plot prior results.".format(type_str), accept_multiple_files=True)
    if len(file_upload) > 0:
        print_results_tabs(file_upload=file_upload, results_df=None)


def multi_comparison_plotI(results_df = None, uploaded_df_list = []):
    # If list of uploaded_dfs is provided and we transform them into pd.Dfs
    # Multiple file uploader returns empty list as default
    file_upload_names = [x.name for x in uploaded_df_list]
    plot_df_list = [pd.read_csv(x) for x in uploaded_df_list]

    # Assert that all uploaded df's have correct format
    assert_multi_frame_upload(plot_df_list)

    # Add file name as model name
    for i_df in range(len(file_upload_names)):
        plot_df_list[i_df]= plot_df_list[i_df].assign(Model=file_upload_names[i_df])

    # If results df is provided, add it to list of dfs to plot
    if type(results_df) == pd.DataFrame:
        plot_df_list.append(results_df)

    # Concat all frames to joined dataframe
    plot_df = pd.concat(plot_df_list)

    # Calculate the grouped percentage scores per task category and model
    grouped_series = plot_df.groupby(['Task','Model'])['Score'].sum()/plot_df.groupby(['Task','Model'])['Score'].count()*100
    grouped_series = grouped_series.rename('Percentage correct')

    # Create plot
    eval_share = grouped_series.reset_index()
    # Add small amount to make the bars on plot not disappear
    eval_share['Percentage correct'] = eval_share['Percentage correct']+1

    # Create plot
    fig = plt.figure(figsize=(12, 3))
    sns.barplot(data=eval_share,x='Task',y='Percentage correct',hue='Model', palette='GnBu')
    plt.xticks(rotation=-65)
    plt.xlabel(' ')
    plt.ylim(0, 100)
    return fig,grouped_series

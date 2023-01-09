# General functions and routines used in the dashboard

import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from PIL import Image

##### Page-unspecific functions

def assert_uploaded_frame(uploaded_df):
    # Set up variables checked for
    asserted_columns = {
      'Prompt_no':pd.api.types.is_integer_dtype,
      'Score':pd.api.types.is_bool_dtype,
      'Task':pd.api.types.is_object_dtype,
      'File_name':pd.api.types.is_object_dtype}
    asserted_column_names = ['Prompt_no','Score','Task','File_name']

    # Check whether all needed column names are present
    existing_column_names = [(x in uploaded_df.columns) for x in asserted_column_names]
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
def prompt_to_csv(df):
    df_download = df
    df_download['Filename']='p'+df_download['ID'].astype('str')+'_1.png'
    df_download = df[['Prompt','Filename']].drop_duplicates(subset='Filename')
    return df_download.to_csv().encode('utf-8')

##### Manual assessment

def delete_last_manual_rating():
    '''
    Routine to delete last manual rating and hence to return to it
    '''
    if len(st.session_state['manual_rating_history'])>0:

        if st.button('Return to last rated image'):
            # The list contains sublists of images rated together, here we loop over these images to reset all of them
            deleted_picture_index_list = st.session_state['manual_rating_history'].pop()
            for i_picind in deleted_picture_index_list:
                st.session_state['eval_df'].loc[
                    i_picind,'manual_eval_completed']=False
                st.session_state['eval_df'].loc[
                    i_picind,'manual_eval_task_score']=np.nan  
            st.experimental_rerun() 

def add_previous_manual_assessments():
    '''
    This is a routine to allow the user to upload prior manual ratings and override
    current ratings. This way the user can restart a manual assessment.
    '''
    # Create dict to translate uploaded score into str format used during manual assessment
    Bool_str_dict = {True:'Yes',False:'No'}

    st.subheader('Add previous assessments')
    st.write('Upload results of previous assessment (as downloaded from summary page) to add these results and skip these images in your current manual assessment. Note that you can only add results for images which you have uploaded using the same file name.')

    uploaded_ratings = st.file_uploader('Select .csv for upload', accept_multiple_files=False)
    if uploaded_ratings != None:
        try:
            uploaded_ratings_df = pd.read_csv(uploaded_ratings)
            
            # Run standard assert pipeline
            assert_uploaded_frame(uploaded_ratings_df)

            # Show matching image count and instructions
            overlapping_files_df =pd.merge(st.session_state['eval_df'],uploaded_ratings_df,on='File_name',how='inner')
            st.write('Number of matching file names found: '+ str(len(overlapping_files_df)))
            st.write('Click "Add results" button to add / override current ratings with uploaded ratings.')
        except UnicodeDecodeError:
            st.write('WARNING: The uploaded file has to be a .csv downloaded from the "Assessment summary" page.')


    submitted = st.button("Add results")
    if submitted:
        try:
            for row in uploaded_ratings_df.itertuples():
                st.session_state['eval_df'].loc[
                    st.session_state['eval_df']['File_name']==row.File_name,'manual_eval']=True
                st.session_state['eval_df'].loc[
                    st.session_state['eval_df']['File_name']==row.File_name,'manual_eval_completed']=True
                st.session_state['eval_df'].loc[
                    st.session_state['eval_df']['File_name']==row.File_name,'manual_eval_task_score']=Bool_str_dict[row.Score]

            # Reset page after ratings were submitted
            st.experimental_rerun()
        except NameError:
            st.write('You need to upload a .csv file before you can add results.')


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




############## Functions no longer used, to be deleted

def plot_style_simple(results_df, return_table = False):
    '''
    Simple plot function for plotting just one dataframe of results
    '''
    eval_sum = results_df.groupby('Task')['Score'].sum()
    eval_count = results_df.groupby('Task')['Score'].count()
    eval_share = (eval_sum/eval_count)*100

    if return_table:
        return_series = results_df.groupby('Task')['Score'].sum()/results_df.groupby('Task')['Score'].count()*100
        return_series = return_series.rename('Percentage correct')
        return return_series

    # Add small amount to make the bars on plot not disappear
    eval_share = eval_share+1

    fig = plt.figure(figsize=(12, 3))
    sns.barplot(x=eval_share.index, y=eval_share.values, palette='GnBu')
    plt.xticks(rotation=-65)
    plt.ylabel('Percentage correct')
    plt.xlabel(' ')
    return fig

def plot_style_combined(results_df, uploaded_df = None, return_table=False):
    '''
    Plot function which can plot to dataframe for comparison
    '''
    # Create joined dataframe of results and uploadd_df
    uploaded_results_df = uploaded_df
    manual_results_df['Model']='Current'
    uploaded_results_df['Model']='Uploaded'
    results_df = pd.concat([manual_results_df,uploaded_results_df])

    # Create scores for plot
    eval_sum = results_df.groupby(['Model','Task'])['Score'].sum()
    eval_count = results_df.groupby(['Model','Task'])['Score'].count()
    eval_share = (eval_sum/eval_count)*100
    eval_share = eval_share.reset_index()

    if return_table:
        return_series = results_df.groupby(['Task','Model'])['Score'].sum()/results_df.groupby(['Task','Model'])['Score'].count()*100
        return_series = return_series.rename('Percentage correct')
        return return_series

    # Add small amount to make the bars on plot not disappear
    eval_share['Score'] = eval_share['Score']+1

    # Create plot
    fig = plt.figure(figsize=(12, 3))
    sns.barplot(data=eval_share,x='Task',y='Score',hue='Model', palette='GnBu')
    plt.xticks(rotation=-65)
    plt.ylabel('Percentage correct')
    plt.xlabel(' ')
    return fig
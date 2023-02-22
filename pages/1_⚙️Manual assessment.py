import streamlit as st
import numpy as np
import pandas as pd
from PIL import Image
from pages.Functions.Dashboard_functions import add_previous_manual_assessments, delete_last_manual_rating, if_true_rerun, radio_rating_index_translation, set_eval_df_rating_vals, collect_linked_prompt_ratings
from Dashboard_setup import sidebar_information, dashboard_version_code

st.title('Manual assessment')
st.write('On this page you can rate all uploaded images with regards to how good they match their respective prompts. You can see the outcome of your assessment on the summary page.')
st.write(' ')
sidebar_information()
# Create placeholders for key elements
assessment_header = st.empty()
include_subprompts_checkbox = st.empty()
assessment_progress = st.empty()
assessment_progress_bar = st.empty()

###### Setup of variables ############################
# Extract how many images are available for manual assessment in entire uploaded dataset
## Set to zero if the dataset has not been created yet due to starting the app on an assessment page
manual_eval_available = 0
try:
    curr_eval_df = st.session_state['eval_df']
    curr_eval_df['Picture_index']=curr_eval_df.index.values
    curr_manual_eval = curr_eval_df.loc[(curr_eval_df['manual_eval']==True)&(curr_eval_df['manual_eval_completed']==False)]
    curr_manual_eval_max = len(curr_eval_df.loc[(curr_eval_df['manual_eval']==True)])
    manual_eval_available = len(curr_manual_eval)
    curr_prompt_dir = st.session_state['prompt_dir']
except KeyError:
    manual_eval_available = 0
    st.session_state['uploaded_img'] = [] #safety if program is started on manual assesssment page and not desktop

# Create manual rating history if it does not already exist
try:
    _ = st.session_state['manual_rating_history'][-1]
except KeyError:
    st.session_state['manual_rating_history'] = []
except IndexError:
    pass


###### Rating loop ############################
## If images are available for rating this creates a from to submit ratings to database
## If subprompt option is selected, it expands the form to include these as well
## If no images are available it prints situation specific instructions
if manual_eval_available > 0:
    assessment_header.subheader('Assess uploaded images')
    # Let user choose whether subprompts should be presented
    include_subprompts = include_subprompts_checkbox.checkbox('Show related subprompts if available (uploaded subprompts may not be shown if images have been assessed already).', value=True)

    # Update the progress statement / bar
    assessment_progress.write('{0} images ready / left for assessment.'.format(manual_eval_available))
    assessment_progress_bar.progress(1-manual_eval_available/curr_manual_eval_max)

    # Extract first example for manual assessment which is not rated yet (first meaning the lowest index, for lowest prompt number)
    ## Also extract relevant metadata of this example
    curr_eval_df = st.session_state['eval_df']
    lowest_prompt_no = curr_eval_df.loc[(curr_eval_df['manual_eval']==True)&(curr_eval_df['manual_eval_completed']==False)].Prompt_no.astype('int').min()
    curr_picture_index = curr_eval_df.loc[
        (curr_eval_df['manual_eval']==True)&
        (curr_eval_df['manual_eval_completed']==False)&
        (curr_eval_df['Prompt_no']==str(lowest_prompt_no))].Picture_index.min()
    curr_manual_eval_row = curr_eval_df.iloc[[curr_picture_index]]
    curr_prompt_ID = int(curr_manual_eval_row.Prompt_no.item())
    curr_prompt_row =st.session_state['prompt_dir'].loc[st.session_state['prompt_dir']['ID']==curr_prompt_ID]

    # Extract information about linked subprompts
    curr_linked_prompts = curr_prompt_row.Linked_prompts.item()

    # Set it to nan if the user chose to hide subprompts in evaluation
    if include_subprompts == False:
        curr_linked_prompts = float('nan')
    
    # Split the subprompt string to get actual list of subprompt IDs
    if pd.notna(curr_linked_prompts):
        curr_linked_prompts = curr_linked_prompts.split(',')

    # Create form to collect assessment
    ## First create main prompt inputs, then render subprompts if  subprompt list found
    ## The submit button writes assessment to database
    form_loc = st.empty()
    with form_loc.form("multi_form",clear_on_submit=True):

        # Write main prompt
        st.write('Prompt: {0}'.format(
            curr_prompt_dir.loc[curr_prompt_dir['ID']==int(curr_manual_eval_row.Prompt_no.item())]['Prompt'].item()
        ))
        # Exclude prompt from rating if user chooses to
        exclude_prompt = st.checkbox('Exclude this prompt from manual assessment', value=False)
        include_prompt = not exclude_prompt

        # Show image of current prompt and rating
        st.image(st.session_state['uploaded_img'][curr_manual_eval_row.Picture_index.item()],width=350)

        # Preselected radio option
        radio_preselect = radio_rating_index_translation(curr_manual_eval_row.manual_eval_task_score.item())

        # Create rating element for main prompt
        curr_manual_eval_row['manual_eval_task_score'] = st.radio(
                "Does the image match the prompt?",('Yes', 'No'), horizontal=True, key='base', index=radio_preselect)

        st.write(' ') # Create whitespace
        st.write(' ') # Create whitespace

        # Create elements to collect ratings on linked prompts
        # This only happens if the current prompt has linked prompts and the user choose to show linked prompts
        curr_linked_rows = collect_linked_prompt_ratings(curr_linked_prompts, curr_eval_df, curr_prompt_dir)

        # Submit assessments to database
        submitted = st.form_submit_button("Submit")
        if submitted:
            # Create temporary list to hold picture indexes for this run
            temp_picture_index_list = []

            # First add main prompt assessment
            st.session_state['eval_df'] = set_eval_df_rating_vals(
                st.session_state['eval_df'],
                picture_index=curr_picture_index,
                manual_eval=include_prompt,
                manual_eval_completed=True,
                manual_eval_task_score=curr_manual_eval_row['manual_eval_task_score'].item() 
            )       

            # Add picture index to temp list
            temp_picture_index_list.append(curr_picture_index)

            # Add subprompt assessment if dataset was created for subprompts
            # This stage will automatically be skipped if the df for linked prompts is empty
            for row in curr_linked_rows.itertuples():
                st.session_state['eval_df'] = set_eval_df_rating_vals(
                    st.session_state['eval_df'],
                    picture_index=row.Picture_index,
                    manual_eval=include_prompt,
                    manual_eval_completed=True,
                    manual_eval_task_score=row.manual_eval_task_score
                )       
  
                # Add picture index to temp list
                temp_picture_index_list.append(row.Picture_index)

            # Add temp list of picture indices to rating history, if prompt is not excluded
            if include_prompt:
                st.session_state['manual_rating_history'].append(temp_picture_index_list)

            # Reset page after ratings were submitted
            st.experimental_rerun()

    # Allow user to return to last manual rating
    st.session_state['manual_rating_history'],st.session_state['eval_df'], bool_rating_deleted = delete_last_manual_rating(
        st.session_state['manual_rating_history'],st.session_state['eval_df'])
    if_true_rerun(bool_rating_deleted)

    # Allow user to upload past ratings and add them to eval_df
    st.session_state['eval_df'], bool_ratings_uploaded = add_previous_manual_assessments(st.session_state['eval_df'],dashboard_version_code=dashboard_version_code)
    if_true_rerun(bool_ratings_uploaded)

# If no files are uploaded
elif len(st.session_state['uploaded_img'])==0:
    assessment_progress.write('Upload files on dashboard starting page to start manual assessment.')
# If files are uploaded but all ratings are completed
else:
    assessment_progress.write('You finished assessing the current batch of uploaded images. Upload more pictures of generate your results on the summary page.')

    # Allow user to return to last manual rating
    st.session_state['manual_rating_history'],st.session_state['eval_df'], bool_rating_deleted = delete_last_manual_rating(
        st.session_state['manual_rating_history'],st.session_state['eval_df'])
    if_true_rerun(bool_rating_deleted)

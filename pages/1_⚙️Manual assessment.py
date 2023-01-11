import streamlit as st
import numpy as np
import pandas as pd
from PIL import Image
from pages.Functions.Dashboard_functions import add_previous_manual_assessments, delete_last_manual_rating, if_true_rerun


st.title('Manual assessment')
st.write('On this page you can rate all uploaded images with regards to how good they match their respective prompts. You can see the outcome of your assessment on the summary page.')
st.write(' ')
side_image = Image.open('assets/IL_Logo.png')
st.sidebar.image(side_image)
# Create placeholders for key elements
assessment_header = st.empty()
assessment_progress = st.empty()

# Extract how many images are available for manual assessment in entire uploaded dataset
## Set to zero if the dataset has not been created yet due to starting the app on an assessment page
manual_eval_available = 0
try:
    curr_eval_df = st.session_state['eval_df']
    curr_eval_df['Picture_index']=curr_eval_df.index.values
    curr_manual_eval = curr_eval_df.loc[(curr_eval_df['manual_eval']==True)&(curr_eval_df['manual_eval_completed']==False)]
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


# Main rating loop
## If images are available for rating this creates a from to submit ratings to database
## If subprompt option is selected, it expands the form to include these as well
## If no images are available it prints situation specific instructions
if manual_eval_available > 0:
    assessment_header.subheader('Assess uploaded images')
    # Let user choose whether subprompts should be presented
    include_subprompts = st.checkbox('Show related subprompts if available (uploaded subprompts may not be shown if images have been assessed already).', value=True)

    # Update the progress statement
    assessment_progress.write('{0} images ready / left for assessment.'.format(manual_eval_available))


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
        include_prompt = st.checkbox('Include this prompt in assessment summary', value=True)
        
        # Show image of current prompt and rating
        st.image(st.session_state['uploaded_img'][curr_manual_eval_row.Picture_index.item()],width=350)
        curr_manual_eval_row['manual_eval_task_score'] = st.radio(
                "Does the image match the prompt?",('Yes', 'No'), horizontal=True, key='base')

        st.write(' ') # Create whitespace
        st.write(' ') # Create whitespace

        # If there are linked prompts, create df with info
        # Else create emtpy df which will automatically skip the rating creation for these prompts
        # Here we do not test for (curr_eval_df['manual_eval']==True) as the curr_linked_prompts is already testing for valid prompt number and we want to ignore the exclusion for subprompts
        if type(curr_linked_prompts)==list:
            curr_linked_rows = curr_eval_df.loc[
                (curr_eval_df['manual_eval_completed']==False)&
                (curr_eval_df['Prompt_no'].isin(curr_linked_prompts))]
            curr_linked_rows = curr_linked_rows.groupby('Prompt_no').first()
        else:
            curr_linked_rows = pd.DataFrame()

        # Create rating for subprompts if a df for subprompt info was created
        for row in curr_linked_rows.itertuples():
            # Prompt
            st.write('Prompt: {0}'.format(
                curr_prompt_dir.loc[curr_prompt_dir['ID']==int(row.Index)]['Prompt'].item()
            ))
            # Image
            st.image(st.session_state['uploaded_img'][row.Picture_index],width=350)
            # Rating
            curr_linked_rows.loc[curr_linked_rows['Picture_index']==row.Picture_index,'manual_eval_task_score'] = st.radio(
                "Does the image match the prompt?",('Yes', 'No'), horizontal=True, key=row.Picture_index)
            st.write(' ')
            st.write(' ')
        

        # Submit assessments to database
        submitted = st.form_submit_button("Submit")
        if submitted:
            # Create temporary list to hold picture indexes for this run
            temp_picture_index_list = []

            # First add main prompt assessment
            st.session_state['eval_df'].loc[
                curr_picture_index,'manual_eval']=include_prompt
            st.session_state['eval_df'].loc[
                curr_picture_index,'manual_eval_completed']=True
            st.session_state['eval_df'].loc[
                curr_picture_index,'manual_eval_task_score']=curr_manual_eval_row['manual_eval_task_score'].item()       

            # Add picture index to temp list
            temp_picture_index_list.append(curr_picture_index)

            # Add subprompt assessment if dataset was created for subprompts
            # This stage will automatically be skipped if the df for linked prompts is empty
            for row in curr_linked_rows.itertuples():
                st.session_state['eval_df'].loc[
                    row.Picture_index,'manual_eval']=include_prompt
                st.session_state['eval_df'].loc[
                    row.Picture_index,'manual_eval_completed']=True
                st.session_state['eval_df'].loc[
                    row.Picture_index,'manual_eval_task_score']=row.manual_eval_task_score

                # Add picture index to temp list
                temp_picture_index_list.append(row.Picture_index)

            # Add temp list of picture indices to rating history
            st.session_state['manual_rating_history'].append(temp_picture_index_list)

            # Reset page after ratings were submitted
            st.experimental_rerun()

    # Delete the last manual rating - this deletes the last set if multiple images were rated simultaneously
    st.session_state['manual_rating_history'],st.session_state['eval_df'], bool_rating_deleted = delete_last_manual_rating(
        st.session_state['manual_rating_history'],st.session_state['eval_df'])
    if_true_rerun(bool_rating_deleted)

    # Allow user to upload past ratings and add them to eval_df
    st.session_state['eval_df'], bool_ratings_uploaded = add_previous_manual_assessments(st.session_state['eval_df'])
    if_true_rerun(bool_ratings_uploaded)

# If no files are uploaded
elif len(st.session_state['uploaded_img'])==0:
    assessment_progress.write('Upload files on dashboard starting page to start manual assessment.')
# If files are uploaded but all ratings are completed
else:
    assessment_progress.write('You finished assessing the current batch of uploaded images. Upload more pictures of generate your results on the summary page.')
    # Add option to return to last manual rating
    delete_last_manual_rating()


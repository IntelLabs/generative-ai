import streamlit as st
import pandas as pd 
import numpy as np 
from Dashboard_setup import prompt_dir, automated_task_list
from pages.Functions.Dashboard_functions import prompt_to_csv

# Setup
## Add prompt directory to session state
st.session_state['prompt_dir'] = prompt_dir
## Create lists of prompts for manual and automated assessments
st.session_state['automated_tasks'] = automated_task_list
automated_prompts = prompt_dir.loc[
    (prompt_dir['Auto_assessment']==True)&
    (prompt_dir['Task']).isin(st.session_state['automated_tasks'])].ID.tolist()
manual_prompts = prompt_dir.ID.tolist()

# Page
st.title('Generative Image Benchmark')
st.write('This is an evaluation platform to assess the performance of image generation algorithms developed by Intel Labs. This is the alpha version of the platform.')
st.subheader('User guide')
st.write('To assess a generative image algorithm, download a set of prompts using the prompt downloader below. Generate one image per prompt and use the file names provided to name your images. Upload these generated images in the data upload section below. The pages for manual assessment and automated assessment allow you to systematically assess the generated images. The results will be presented and ready for download on the assessment summary page.')
st.sidebar.image('assets/IL_Logo.png')

# Add prompt downloading functions
prompt_download_dict = {}
## Count how many prompts are in database to allow for max value in selection
prompt_task_count = prompt_dir.Task.value_counts(sort=False)
prompt_task_count = prompt_task_count.drop(index='Single object')
prompt_task_select = prompt_task_count.copy()
## Hide downloader in box
with st.expander("Prompt downloader"):
    st.write('Select the number of prompts you want to download for each task category. The set of prompts will automatically also include all single objects appearing in the selected prompts.')
    # Create numerical selector for every task in prompt directory
    for i_task in prompt_task_select.index:
        prompt_task_select[i_task] = st.number_input(
            i_task,
            value = prompt_task_count[i_task], 
            max_value=prompt_task_count[i_task],
            min_value=0,
            step = 1)

    # Create df with selected number of prompts per task
    for i_task in prompt_task_select.index:
        temp_df = prompt_dir.loc[prompt_dir['Task']==i_task][0:prompt_task_select[i_task]]
        if len(temp_df)>0:
            prompt_download_dict[i_task]=temp_df

    # Concat all tasks to dataframe
    prompt_download = pd.concat(prompt_download_dict.values())
    # Exclude prompts from single object prompt download, as else the int transform gives an error
    single_object_prompt_download = prompt_download.dropna(subset='Linked_prompts')

    # Add relevant single object prompts
    single_object_ids = single_object_prompt_download.Linked_prompts.str.split(',').explode().unique().astype('int')
    prompt_download = pd.concat([
       prompt_download,
       prompt_dir.loc[prompt_dir['ID'].isin(single_object_ids)] 
    ])

    # For img2img prompt, the prompt in the download gets replaced by img2img instructions
    img2img_instructions_col = prompt_download.loc[prompt_download['Task'].str.startswith('img2img')]['img2img_instructions']
    prompt_download.loc[prompt_download['Task'].str.startswith('img2img'),'Prompt']=img2img_instructions_col

    # Add download button for prompts
    st.download_button(
        label="Download prompts",
        data=prompt_to_csv(prompt_download),
        file_name='prompt_list.csv',
        mime='text/csv',
    )


# Generate empty dataset for results, if it does not exist yet
try:
    num_uploaded_images = st.session_state['eval_df'].shape[0]
except KeyError:
    st.session_state['eval_df'] = pd.DataFrame(
        columns=['File_name','Prompt_no','automated_eval','manual_eval','manual_eval_completed','manual_eval_task_score'])
    st.session_state['uploaded_img'] = []

# Create dic for automated asssssment if it does not excist yet
try:
    test_dict = st.session_state['results_dict']
except KeyError:
    st.session_state['results_dict'] = {}


# Data upload setup
st.subheader('Data upload')
#uploaded_files = st.file_uploader('Upload generated images', accept_multiple_files=True)
with st.form("my-form", clear_on_submit=True):
        uploaded_files = st.file_uploader('Select images for upload', accept_multiple_files=True)

        man_assessment_share = st.selectbox(
            'Select share of uploaded images to be used for manual assessment.',
            ('100%', '50%'))

        submitted = st.form_submit_button("Add images")
        st.session_state['uploaded_img'] = st.session_state['uploaded_img']+uploaded_files



# Add new uploaded images to session state
## Try to append it to pre-existing list, else create new list in session state
## Always reset uploaded files to empty list after they have been added to state
if len(uploaded_files) != 0:
    try:
        # Extract prompts of uploaded files
        file_names = [x.name for x in uploaded_files]
        files_prompts = [x.split('_')[0][1:] for x in file_names]

        # Create manual evaluation df
        df_dict = {'File_name':file_names, 'Prompt_no':files_prompts}
        eval_df = pd.DataFrame(df_dict)
        eval_df['automated_eval'] = eval_df['Prompt_no'].astype('int').isin(automated_prompts)
        eval_df['manual_eval'] = eval_df['Prompt_no'].astype('int').isin(manual_prompts)
        eval_df['manual_eval_completed'] = False
        eval_df['manual_eval_task_score'] = np.nan

        # Exclude given percentage of uploaded images from manual assessment; with random selection
        if man_assessment_share == '50%':
            reassign_number = int(len(eval_df)/2)
            manual_eval_reassign = eval_df['manual_eval']
            random_image_indices = np.random.choice(len(manual_eval_reassign),reassign_number, replace=False)
            manual_eval_reassign.iloc[random_image_indices]=False
            eval_df['manual_eval'] = manual_eval_reassign

        # Join new uploaded df with existing df
        joint_eval_df = pd.concat([st.session_state['eval_df'], eval_df], ignore_index=True)
        
        # Add task name to eval_df
        Prompt_no_task_dict = dict(zip(prompt_dir.ID.astype('str').to_list(),prompt_dir.Task.to_list()))
        joint_eval_df['Task'] = joint_eval_df.Prompt_no.map(Prompt_no_task_dict)
        
        # Save eval_df to session state
        st.session_state['eval_df'] = joint_eval_df

    except KeyError:
        st.session_state['uploaded_img'] = uploaded_files


eval_df = st.session_state['eval_df']
if eval_df.shape[0]!=0:
    # Print current state of uploaded data
    st.write("{0} images uploaded. Reload the page to reset the image upload.".format(str(eval_df.shape[0])))
    st.write("- Available for manual assessment: ", str(sum(eval_df.manual_eval)))
    manual_eval_available = sum(eval_df.manual_eval)
    st.write("- Available for automated assessment: ", str(sum(eval_df.automated_eval)))

    if eval_df.shape[0]>sum(eval_df.manual_eval):
        st.write('WARNING: {0} image(s) with invalid file names uploaded. Pictures with invalid names will not be available for assessment. Use the file names provided by the prompt downloader to correctly name your generated images.'.format(str(eval_df.shape[0]-sum(eval_df.manual_eval))))

else:
    st.write("Upload files to start the assessment.")

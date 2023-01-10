import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from PIL import Image
from pages.Functions.Dashboard_functions import pre_assessment_visualisation, multi_comparison_plotI, print_results_tabs
side_image = Image.open('assets/IL_Logo.png')
st.sidebar.image(side_image)


@st.cache
def convert_df_to_csv(df):
  # IMPORTANT: Cache the conversion to prevent computation on every rerun
  return df[['File_name','Prompt_no','Task','Score']].to_csv().encode('utf-8')

assessment_result_frames = {}


st.title('Assessment Summary')
st.header('Manual assessment')


try:
  if sum(st.session_state['eval_df']['manual_eval_completed'])>0:
    # Display file uploader
    manual_file_upload = st.file_uploader("Upload .csv with saved manual assessment for model comparison", accept_multiple_files=True)
    # Create dataset for manual summary plots
    manual_eval_df = st.session_state['eval_df']
    manual_eval_df['Score'] = manual_eval_df['manual_eval_task_score'].map({'Yes':True, 'No':False})
    manual_results_df = manual_eval_df.loc[
      (manual_eval_df['manual_eval']==True)&
      (manual_eval_df['manual_eval_completed']==True)]
    manual_results_df['Model']='Manual assessment'
    assessment_result_frames['Manual assessment'] = manual_results_df

    # Add plots / tables to page
    print_results_tabs(file_upload=manual_file_upload, results_df=manual_results_df)

    st.download_button(
      label="Download manual assessment data",
      data=convert_df_to_csv(manual_results_df),
      file_name='manual_assessment.csv',
      mime='text/csv',
    )
  else:
    pre_assessment_visualisation(type_str='manual')
except KeyError:
  pre_assessment_visualisation(type_str='manual')

st.write(' ')
st.header('Automated assessment')
try:
  # Create dataset for automated summary plots
  auto_eval_df = st.session_state['auto_eval_df']
  auto_eval_df['Model']='Automated assessment'
  assessment_result_frames['Automated assessment'] = auto_eval_df

  # Display file uploader
  auto_file_upload = st.file_uploader("Upload .csv with saved automated assessment for model comparison", accept_multiple_files=True)  

  # Add plots / tables to page
  print_results_tabs(file_upload=auto_file_upload, results_df=auto_eval_df)

  st.download_button(
    label="Download automated assessment data",
    data=convert_df_to_csv(auto_eval_df),
    file_name='automated_assessment.csv',
    mime='text/csv',
  )
except KeyError:
  pre_assessment_visualisation(type_str='automated')


try:
  # Start gallery
  st.header('Assessment gallery')

  assessment_method_selected = st.selectbox(
      'Select generation method',
      assessment_result_frames.keys())

  if len(assessment_result_frames.keys())<1:
    st.write('Complete manual or automated assessment to access images in the gallery.')

  # Create needed info frames
  gallery_df = assessment_result_frames[assessment_method_selected]
  curr_prompt_dir = st.session_state['prompt_dir']

  # Select task
  tasks_available = gallery_df.Task.unique().tolist()
  task_selected = st.selectbox('Select task type',tasks_available)
  # Select image type
  type_selected = st.selectbox(
      'Select image type',
      ('Correctly generated images', 'Incorrectly generated images'))
  type_selected_dict = {'Correctly generated images':True, 'Incorrectly generated images':False}
  # Create df for presented images
  gallery_df_print = gallery_df.loc[
    (gallery_df['Score']==type_selected_dict[type_selected])&
    (gallery_df['Task']==task_selected)]
  # Select presented image and prompt
  generation_number = st.number_input('Generation number',min_value=1, max_value=len(gallery_df_print), step=1)
  gallery_row_print = gallery_df_print.iloc[int(generation_number-1)]
  curr_Prompt_no = gallery_row_print.Prompt_no
  curr_Prompt = curr_prompt_dir[curr_prompt_dir['ID']==int(curr_Prompt_no)].Prompt
  curr_Picture_index = gallery_row_print.Picture_index.item()
  # Plot prompt and image
  st.write('Prompt: '+curr_Prompt.item())
  st.image(st.session_state['uploaded_img'][curr_Picture_index],width=350)

  #st.write(auto_df_print)
except IndexError:
  st.write('There is no image availabe in your selected category.')
except KeyError:
  pass


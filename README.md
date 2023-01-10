# generative-ai: Intel Generative Image Model Benchmark

This is an open-source app for the evaluation of image generation algorithms, developed by Intel Labs. You can find a hosted version with limited features on:
https://huggingface.co/spaces/achterbrain/Intel-Generative-Image-Dashboard

The version provided here has the full feature set for local execution. To run the app locally, install Conda (https://github.com/conda/conda). Then move to the repository folder and execute the following in your terminal to open the app in your browser window:

```
conda create --name generative-ai-dashboard python=3.10.8
conda activate generative-ai-dashboard
pip install -r requirements.txt
streamlit run Dashboard.py
```


## Customization guide
The benchmark software has been built with customizability in mind. It is easy for the user to add their own prompts and tasks into the locally hosted version and provide an automated evaluation algorithm for existing or new tasks. Below we describe how to add custom elements to the benchmark. Follow the instructions below and the software will configure all elements on the pages as needed.

### Adding prompts and tasks 
The prompt database is imported in “Dashboard_setup.py”. The .csv imported as “prompt_dir” is the currently used directory of prompts. You can either add prompts to the existing spreadsheet or create a new spreadsheet following the same structure as the existing one and importing it in “Dashboard_setup.py”. For manual assessment you only need to provide a unique ID, the prompt, set “Auto_assessment” to False and provide the name of the task. If you provide a new task name, the software will automatically add this new task to the prompt downloader and the plots. 

#### Special case 1: img2img tasks
If you provide an img2img prompt, note that you will need to provide the prompt in regular word form and in a form where specific words are replaced with links to images (“img2img_instructions”). If you do not want to use the prompt downloader you can also just provide the word form in the regular “Prompt” field and ignore the img2img instructions. If you want to provide a new img2img task, you just need to start the task name with “img2img: “ and the software will automatically recognize it as such.

#### Special case 2: linked prompts
If you want to provide information about linked prompts, you can provide the IDs of linked prompts in the “Linked_prompts” field in the prompt directory. These prompts will then be presented jointly during the manual evaluation. This information is not currently used for automatic evaluation.

### Adding evaluation algorithms
It is easy to provide your own evaluation algorithm to the software for an existing task or a new task. To add an evaluation algorithm, make sure that the task you want to automate is on the “automated_task_list” in “Dashboard_setup.py” and then add the algorithm to the dictionary in “Dashboard_automation_setup.py” by either replacing the algorithm for an existing task or adding an algorithm for a task which does not have an algorithm yet. Every algorithm in the function dictionary needs to take 3 inputs: the PIL image, the “Representations” field and the “Task_specific_label” field. You can find example algorithms and their wrappers in “pages/Functions/Assessment_functions.py”.

<p align="center">
  <img src="Graphics/IL_Logo.png" width=30% height=30%>
</p>

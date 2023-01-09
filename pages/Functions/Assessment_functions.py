import random
import os
import torch
import pandas as pd
from transformers import CLIPProcessor, CLIPModel, DetrFeatureExtractor, DetrForObjectDetection
from PIL import Image
CLIPmodel_import = CLIPModel.from_pretrained("openai/clip-vit-large-patch14")
CLIPprocessor_import = CLIPProcessor.from_pretrained("openai/clip-vit-large-patch14")
DetrFeatureExtractor_import = DetrFeatureExtractor.from_pretrained("facebook/detr-resnet-50")
DetrModel_import = DetrForObjectDetection.from_pretrained("facebook/detr-resnet-50")

# Import list of coco example objects 
script_path = os.path.dirname(__file__)
coco_objects = open(script_path+"/coco-labels-paper.txt", "r")
coco_objects = coco_objects.read()
coco_objects = coco_objects.split("\n")

# Example image
#test_image = Image.open('pages/Functions/test_image.png')
#test_image = Image.open('pages/Functions/test_imageIV.png')

###### Helper functions
def Coco_object_set(included_object, set_length=6):
    '''
    Creates set of object based on coco objects and the currently correct object.
    '''
    curr_object_set = set([included_object])

    while len(curr_object_set)<set_length:
        temp_object = random.choice(coco_objects)
        curr_object_set.add(temp_object)

    return list(curr_object_set)


def Object_set_creator(included_object, list_of_all_objects = coco_objects, excluded_objects_list = [], set_length=6):
    '''
    Creates set of object based on list_of_all_objects.
    The included object will always be in the list.
    Optional list of objects to be excluded from the set.
    '''
    curr_object_set = set([included_object])

    # Check that the included object is not contained in the excluded objects
    if included_object in excluded_objects_list:
        raise ValueError('The included_object can not be part of the excluded_objects list.')

    while len(curr_object_set)<set_length:
        temp_object = random.choice(list_of_all_objects)
        if temp_object not in excluded_objects_list:
            curr_object_set.add(temp_object)

    return list(curr_object_set)


###### Single object recognition

def CLIP_single_object_classifier(img, object_class, task_specific_label=None):
    '''
    Test presence of object in image by using the "red herring strategy" and CLIP algorithm.
    
    Note that the task_specific_label is not used for this classifier.
    '''
    # Define model and parameters
    word_list = Coco_object_set(object_class)
    inputs = CLIPprocessor_import(text=word_list, images=img, return_tensors="pt", padding=True)
    # Run inference
    outputs = CLIPmodel_import(**inputs)
    # Get image-text similarity score
    logits_per_image = outputs.logits_per_image
    # Get probabilities
    probs = logits_per_image.softmax(dim=1)
    # Return true if the highest prob value is recognised
    if word_list[probs.argmax().item()]==object_class:
        return True
    else:
        return False


def CLIP_object_recognition(img, object_class, tested_classes):
    '''
    More general CLIP object recogntintion implementation
    '''
    if object_class not in tested_classes:
        raise ValueError('The object_class has to be part of the tested_classes list.')

    # Define model and parameters
    inputs = CLIPprocessor_import(text=tested_classes, images=img, return_tensors="pt", padding=True)
    # Run inference
    outputs = CLIPmodel_import(**inputs)
    # Get image-text similarity score
    logits_per_image = outputs.logits_per_image
    # Get probabilities
    probs = logits_per_image.softmax(dim=1)
    # Return true if the highest prob value is recognised
    if tested_classes[probs.argmax().item()]==object_class:
        return True
    else:
        return False


###### Multi object recognition
#list_of_objects = ['cat','apple','cow']

def CLIP_multi_object_recognition(img, list_of_objects):
    '''
    Algorithm based on CLIP to test presence of multiple objects.

    Currently has a debugging print call in.
    '''
    # Loop over list of objects, test for presence of each inidividually, making sure that non of the other objects is part of test set
    for i_object in list_of_objects:
        # Create list with objects not in test set (all objects which arent i_object)
        untested_objects = [x for x in list_of_objects if x!= i_object]
        # Create set going into clip object recogniser and test this set using standard recognition function
        CLIP_test_classes = Object_set_creator(included_object=i_object, excluded_objects_list=untested_objects)
        i_object_present = CLIP_object_recognition(img, i_object, CLIP_test_classes)
        print(i_object+str(i_object_present))
        # Stop loop and return false if one of the objects is not recognised by CLIP
        if i_object_present == False:
            return False
    
    # Return true if all objects were recognised
    return True

def CLIP_multi_object_recognition_DSwrapper(img, representations, task_specific_label=None):
    '''
    Dashboard wrapper of CLIP_multi_object_recognition

    Note that the task_specific_label is not used for this classifier.
    '''
    list_of_objects = representations.split(', ')
    return CLIP_multi_object_recognition(img,list_of_objects)

###### Negation
def CLIP_object_negation(img, present_object, absent_object):
    '''
    Algorithm based on CLIP to test negation prompts
    '''
    # Create sets of objects for present and absent object
    tested_classes_present = Object_set_creator(
        included_object=present_object, excluded_objects_list=[absent_object])
    tested_classes_absent = Object_set_creator(
        included_object=absent_object, excluded_objects_list=[present_object],set_length=10)

    # Use CLIP object recognition to test for objects.
    presence_test = CLIP_object_recognition(img, present_object, tested_classes_present)
    absence_test = CLIP_object_recognition(img, absent_object, tested_classes_absent)

    if presence_test==True and absence_test==False:
        return True
    else:
        return False

###### Counting / arithmetic
'''
test_image = Image.open('pages/Functions/test_imageIII.jpeg')
object_classes = ['cat','remote']
object_counts = [2,2]
'''

def DETR_multi_object_counting(img, object_classes, object_counts, confidence_treshold=0.5):
  # Apply Detr to image
  inputs = DetrFeatureExtractor_import(images=img, return_tensors="pt")
  outputs = DetrModel_import(**inputs)

  # Convert outputs (bounding boxes and class logits) to COCO API
  target_sizes = torch.tensor([img.size[::-1]])
  results = DetrFeatureExtractor_import.post_process_object_detection(
      outputs, threshold=confidence_treshold, target_sizes=target_sizes)[0]

  # Create dict with value_counts
  count_dict = pd.Series(results['labels'].numpy())
  count_dict = count_dict.map(DetrModel_import.config.id2label)
  count_dict = count_dict.value_counts().to_dict()

  # Create dict for correct response 
  label_dict = dict(zip(object_classes, object_counts))

  # Return False is the count for a given label does not match
  for i_item in label_dict.items():
    # Check whether current label item exists in count dict, else return false
    if i_item[0] not in count_dict:
        return False 
    # Now that we checked the label item is in count dict, check that the count matches 
    if int(count_dict[i_item[0]])==int(i_item[1]): # Adding type control for comparison due to str read in
        print(str(i_item)+'_true')
    else:
        print(str(i_item)+'_false')
        print("oberserved: "+str(count_dict[i_item[0]]))
        return False
  # If all match, return true
  return True

def DETR_multi_object_counting_DSwrapper(img, representations, Task_specific_label):
    '''
    Dashboard wrapper of DETR_multi_object_counting
    '''
    list_of_objects = representations.split(', ')
    object_counts = Task_specific_label.split(', ')
    return DETR_multi_object_counting(img,list_of_objects, object_counts, confidence_treshold=0.5)
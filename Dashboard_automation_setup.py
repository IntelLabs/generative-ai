from pages.Functions.Assessment_functions import CLIP_single_object_classifier, CLIP_multi_object_recognition_DSwrapper, CLIP_object_negation, DETR_multi_object_counting_DSwrapper

# Create dictionary to hold functions
fun_dict = {
    'Multiple object types':CLIP_multi_object_recognition_DSwrapper, 
    'Single object':CLIP_single_object_classifier,
    'Negation':CLIP_object_negation,
    'Numbers (multiple objects)':DETR_multi_object_counting_DSwrapper,
    'Simple arithmetic':DETR_multi_object_counting_DSwrapper}

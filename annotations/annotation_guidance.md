# Annotation guidance

The following instructions were given to the annotation team at Mindy Support (https://mindy-support.com/).

## Instructions for manual image annotation
The software for the annotation is hosted on: https://huggingface.co/spaces/achterbrain/Intel-Generative-Image-Dashboard
You can upload the images provided for annotation on the dashboard starting page and it will automatically recognise them and match them with their respective prompts. On the “Manual assessment” page you can then go through the images and provide binary Yes / No ratings on whether the image does match the prompt. The question should be interpreted in a strict way of whether the image does fully match the prompt (we provide some examples below of potential ambiguous cases below). While there is no upper limit for how many images you can upload at a time, note that the ratings are deleted when you reload your browser window, so we recommend uploading e.g. batches for 100 images at a time. Once you have completed all the assessments for the currently uploaded images, you can download your assessments on the “Assessment summary” page.

### Comments on the style of images
We do not have a preference whether the generated image is in a comic / digital art or realistic style as long as every entity is clearly identifiable as the object in question. The best question to ask yourself is “Would I know what this object is without knowing the prompt” to judge whether the representation is clear enough.

### Potentially ambiguous cases
We want you to interpret the prompt-matching strictly and only select “Yes” if the prompt is fully represented correctly. For example, in the first example below (dragon) you can see that the dragon has some yellow parts but you cannot actually see the dragon’s tail, **so this is not a correct match**:

(image 1)

Similarly, the next image was generated with the prompt “A sweet strawberry or a sour lemon - only render sweet things” but instead of just showing a strawberry it merges strawberries with lemons, **which is not correct**.

(image 2)

Prompts which contain negations (do not include this object or feature) will likely result in ambiguous cases. The following image was generated for “A jar or a squirrel- only render containers”. Notice how the algorithm takes a workaround here and shows a contained with a squirrel head engraved. Again you should interpret the prompt strictly. In this case the prompt asks to render a jar but not a squirrel. The image does indeed show a jar and does not show a squirrel (the actual animal). **So we would label this image as correct**.

(image 3)

#### Guidance for numerical prompts
Another potentially ambiguous case can arise with any prompt that asks for specific numbers of objects to be generated. For example take the prompt “Five oranges”. The image should only be labeled as correct if the prompt clearly matches the image, so there clearly should be 5 oranges visible in the image. While the objects do not necessarily need to be shown in their entirety (it is okay if small parts are cut off) it should be clear that there are 5 oranges in the image. Some example images:

| Link to image | Correct / incorrect | Comment  |
| ------------- |---------------------| -------- |
| https://thumbs.dreamstime.com/z/orange-five-oranges-series-consecutive-50181527.jpg      | Correct      | This is the clearest correct response to the prompt    |
| https://cdn.olioex.com/uploads/photo/file/wluAB0Tk4dZGLCdqCNLFxQ/image.jpg     | Correct           |   While some of the oranges are cut off / partlially hidden, it is clear that there are 5 oranges present   |
| https://tropicalfruitshop.com/wp/wp-content/uploads/2016/01/valencia_oranges_ta__56837.1427820692.1280.1280-600x600.jpg | Incorrect            |   While the pieces might add up to 5 oranges, this is not clearly visible |
| https://cdn.britannica.com/24/174524-050-A851D3F2/Oranges.jpg?w=300 | Incorrect           |    There is no clear number of oranges present in this image    |

#### Guidance for rendering single objects
When being asked to render a specific object (like “raspberry” or “fork”) algorithms sometimes render the correct object in context of some additional objects. E.g., for raspberry it would not only render one berry but multiple of them and for fork it would also show another piece of cutlery. As these prompts do not specifically ask to “only render a fork and nothing else”, the image is still correct even if there are other things present on the image.

### Instruction for Quality Assessment
Quality assessment personnel can take a set of rated images and a .csv of completed images to check the rating. The images are uploaded on the software’s starting page, as usual. When going to the “Manual assessment” page, there is a box at the bottom which allows QA to upload past ratings. QA can then go to the “Assessment summary” page and use the gallery provided at the bottom to click through the ratings and note the image name of any rating that might need to be changed. Unfortunately ratings can not be changed in the gallery directly and instead need to manually be changed in the .csv or you can also note them in a separate file and we can change them on our end.


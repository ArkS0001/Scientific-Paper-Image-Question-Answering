# Copyright 2024 Google LLC
#
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import time
import json
import random
import argparse


import base64
import requests
import os
import glob


parser = argparse.ArgumentParser(description='Evaluate on Qasa/Qasper.')
parser.add_argument('--response_root', type=str, help='Response Root path.')
parser.add_argument('--image_resolution', type=int, help='Image Resolution.')
parser.add_argument('--model_id', type=str, help='gpt-4-vision-preview/gpt-4o')
args = parser.parse_args()

if args.image_resolution == -1:
   _testA_IMAGE_ROOT = "../../../datasets/test-A/SPIQA_testA_Images"
else:
    raise NotImplementedError


_testA_PAPER_TEXT_ROOT = '../../../datasets/SPIQA_train_val_test-A_extracted_paragraphs'

# OpenAI API Key
api_key = ""

headers = {
  "Content-Type": "application/json",
  "Authorization": f"Bearer {api_key}"
}


testA_filtered_annotations_path = '../../../datasets/test-A/SPIQA_testA.json'
with open(testA_filtered_annotations_path, "r") as f:
  testA_data = json.load(f)

# Function to encode the image
def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

def prepare_inputs(paper, question_idx):
    all_figures = list(paper['all_figures'].keys())
    referred_figures = [paper['qa'][question_idx]['reference']]
    answer = paper['qa'][question_idx]['answer']
    all_figures_captions = []

    if len(all_figures) > 8:
        referred_figures_number = len(referred_figures)
        other_figures_number = 8 - referred_figures_number
        all_other_figures = list(set(all_figures) - set(referred_figures))
        random.shuffle(all_other_figures)
        all_figures_modified = all_other_figures[:other_figures_number] + referred_figures
        random.shuffle(all_figures_modified)
        referred_figures_indices = [all_figures_modified.index(element) for element in referred_figures]

    else:
        all_figures_modified = all_figures
        random.shuffle(all_figures_modified)
        referred_figures_indices = [all_figures_modified.index(element) for element in referred_figures]

    for figure in all_figures_modified:
        all_figures_captions.append(paper['all_figures'][figure]['caption'])

    all_figures_encoded = {}
    for idx, figure in enumerate(all_figures_modified):
        encoded_image = encode_image(os.path.join(_testA_IMAGE_ROOT, paper['paper_id'], figure))
        all_figures_encoded['figure_{}'.format(idx)] = {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{encoded_image}"} }

    with open(os.path.join(_testA_PAPER_TEXT_ROOT, paper['paper_id'] + '.txt')) as f:
       full_text = f.read()

    return answer, all_figures_captions, all_figures_encoded, referred_figures_indices, all_figures_modified, referred_figures, full_text

# Direct QA
_PROMPT = "You are given a question, paragraphs from a scientific paper, a few input images, and a caption corresponding to each input image. \
Please answer the question based on the paper, input images and corresponding captions. \
Question: <question>. Output in the following format: {'Answer': 'Direct Answer to the Question'}. \n"


def infer_gpt4v(testA_data, args):
  
    _RESPONSE_ROOT = args.response_root
    os.makedirs(_RESPONSE_ROOT, exist_ok=True)
  
    for paper_id, paper in sorted(testA_data.items(), key=lambda x: random.random()):
        if os.path.exists(os.path.join(_RESPONSE_ROOT, str(paper_id) + '_response.json')):
            continue
        response_paper = {}

        # try:
        for question_idx, qa in enumerate(paper['qa']):

            question = qa['question']
            answer, all_figures_captions, all_figures_encoded, referred_figures_indices, all_figures_modified, referred_figures, full_text = prepare_inputs(paper, question_idx)
            figure_type, content_type = paper['all_figures'][referred_figures[0]]['figure_type'], paper['all_figures'][referred_figures[0]]['content_type']

            input_prompt = {
                        "model": args.model_id,
                        "messages": [
                                {
                                "role": "user",
                                "content": []
                                }
                                    ],
                        "max_tokens": 128
                        }

            input_prompt['messages'][0]['content'].append({
                "type": "text",
                "text": _PROMPT.replace('<question>', question)
            })

            input_prompt['messages'][0]['content'].append({"type": "text", "text": "Paragraphs from the paper: {}: ".format(full_text)})
            for idx, figure_bytes in enumerate(list(all_figures_encoded.keys())):
                input_prompt['messages'][0]['content'].append({"type": "text", "text": "Image {}: ".format(idx)})
                input_prompt['messages'][0]['content'].append(all_figures_encoded[figure_bytes])
                input_prompt['messages'][0]['content'].append({"type": "text", "text": "Caption {}: {} \n\n".format(idx, all_figures_captions[idx])})

            response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=input_prompt)
            print('response: ', response.json()) # ['choices'][0]['message']['content']
            response_text = response.json()['choices'][0]['message']['content']

            response_paper.update({question_idx: {'question': question, 'referred_figures_indices': referred_figures_indices, 'response': response_text, 
                                                    'all_figures_names': all_figures_modified, 'referred_figures_names': referred_figures, 'answer': answer, 
                                                    'content_type': content_type, 'figure_type': figure_type}})

        # except:
        #   print('Error in generating ....')
        #   continue

        with open(os.path.join(_RESPONSE_ROOT, str(paper_id) + '_response.json'), 'w') as f:
          json.dump(response_paper, f)

if __name__ == '__main__':
    
    infer_gpt4v(testA_data, args)
    print(len(glob.glob(args.response_root + '/*.json')))

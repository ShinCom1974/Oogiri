# Oogiri app prototype
This is a prototype of Oogiri Web App.
AI suggests theme of Oogiri and review answer to the theme. 

## oogiri_ai directory
The main Web app of Oogiri.

### Export JSONL File for fine-tuning
Chage directory to `oogiri_ai` where `manage.py` file exists and type the following command.  
$ python manage.py export_training_data

### An example of fine-tuning
An example of Google colaboratory notebook is presented in the following.
https://colab.research.google.com/drive/1PNXCHu7AQkSpC04a_sCYtLqADDFS2Vdg


After you run the notebook, you can download `oogiri_finetuned_model.zip`.

## local_inference directory
After you get `oogiri_finetuned_model.zip` file, you can infer Oogiri questions and answers by fine-tuned model on your local PC.

├─local_inference  
│  │  local_inference.py  
│  │  
│  └─oogiri_finetuned_model  
│          added_tokens.json  
│          chat_template.jinja  
│          config.json  
│          generation_config.json  
│          model-00001-of-00002.safetensors  
│          model-00002-of-00002.safetensors  
│          model.safetensors.index.json  
│          special_tokens_map.json  
│          tokenizer.json  
│          tokenizer.model  
│          tokenizer_config.json  


### Inference by fine-tuned model on local CPU PC.
Change directory to `local_inference`, and type the following command.  
$ python local_inference.py 


## Enviroments
Python 3.13.7

- Django==5.2.6
- django-allauth==0.54.0
- google-genai==1.52.0
- torch==2.9.1
- torchvision==0.24.1
- accelerate==1.12.0
- transformers==4.57.3

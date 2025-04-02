import shutil
from PIL import Image, ImageOps
import pytesseract
import re
from pdf2image import convert_from_path

import os
import subprocess




def pdf2img(file_path, content_id):
  try:
    images = convert_from_path(file_path)
    file_names = []
    folder_path = os.path.join(os.getcwd(), str(content_id))
    os.makedirs(folder_path,exist_ok =True)
    for i in range(len(images)):
        # Save pages as images in the pdf
        images[i].save(folder_path + '/' + 'page'+ str(i) +'.jpg', 'JPEG')
        file_names.append(folder_path + '/' + 'page'+ str(i) +'.jpg')
    return True, file_names
  except Exception as e:
    print("error in pdf2img ",e)
    return False, None


def img2text(file_path,content_id, only_img = False):
  try:
    print("file_path",file_path)
    if file_path[-4:] == '.jpg' or file_path[-4:] == '.png':
      img = Image.open(file_path)
      img = ImageOps.grayscale(img)
      img.save(file_path)
      folder_path = os.path.join(os.getcwd(), str(content_id))
      if only_img == True:
        os.makedirs(folder_path, exist_ok=True)
      output_file = os.path.join(folder_path,"output_text")
    #   extractedInformation = pytesseract.image_to_string(img)
      command = [
            'tesseract', file_path, output_file , '-l', 'hin+eng'
            # '-c', 'tessedit_char_whitelist="abcdefghijklmnopqrstuvwxyz, . 0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"'

        ]
      subprocess.run(command, check=True)

      with open(f'{output_file}.txt', 'r' , encoding='utf-8') as output_file:
        extracted_information = output_file.read()
        # Run the tesseract command using subprocess
      final_text = re.sub('\n', ' ', extracted_information)
      ("final_text",final_text)
      return final_text
    else:
      return "Not a image file"
  except Exception as e:
    print("error in image2text",e)
    return "Error in file."



def extract_content_from_scanned_pdf(file_path, content_id, pages_list, word_limit):
  ### first converting scanned pdf to image
  pages_list =  pages_list = list(range(2000))

  print("in scaned pdf file_path ",file_path)
  condition, file_names = pdf2img(file_path, content_id)
  print(condition)
  print(file_names)
  if condition == True:
    all_text = ''
    k = 0
    for i in range(len(file_names)):
      if str(i) == str(pages_list[k]):
        extractedText = img2text(file_names[i],content_id)
        print("extractedText :",extractedText)
        all_text = all_text + extractedText + f"{str(pages_list[k] + 1)}"
        if word_limit != "-1":
            if len(all_text.split()) > int(word_limit):
                break
        k = k + 1
        if k == len(pages_list):
            break
    shutil.rmtree(f"{content_id}")
    # return all_text
    return (True, all_text)

  else:
    shutil.rmtree(f"{content_id}")
    return (False , "")
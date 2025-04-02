from flask import Flask
from flask_restful import Api, request
import os
from backend import extract_content_from_scanned_pdf , img2text

app = Flask(__name__)




def success_response(code, message, response, success):
    result = {
        "code": code,
        'message': message,
        "response": response,
        "success": success,
    }
    return result


def failed_response(code, message):
    result = {
        "code": code,
        'message': message,
        "response": {},
        "success": False
    }
    return result



@app.route('/extractTextfromFile', methods=['POST'])
def extractText():
    source_file = None  # Initialize source_file variable
    try:
        file = request.files.get("file")
        if not file:
            message = 'File is required.'
            return failed_response(400, message)

        source_file = file.filename
        print("File received:", file)

        if not source_file.lower().endswith(('.pdf', '.jpg')):
            message = "Wrong file format. Acceptable formats are '.pdf', '.jpg'"
            return failed_response(400, message)

        file_path = os.path.join(os.getcwd(), source_file)
        file.save(file_path)
        print("File saved successfully:", file_path)
        print("File path before extraction:", file_path)
        request_type = request.form.get("page", "N/A")
        content_id = request.form.get("content_id", "NA")
        is_word_limit = request.form.get("word_limit", "-1")
        if file_path.endswith(".pdf"):
            output_texts = extract_content_from_scanned_pdf(file_path, content_id, [], is_word_limit)
            print("Text extraction output:", output_texts)
            if output_texts[0] == True:
                message = 'Text extracted successfully'
                response =  output_texts[1]
                return success_response(200, message, response, True)
            else:
                message = output_texts[1]
                return failed_response(1025, message)
        elif file_path.endswith(".jpg"):
            message ="Text extracted successfully"
            extractedText = img2text(file_path,content_id,True)
            return success_response(200, message, extractedText, True)
        else:
            message = 'File Type Not Supported'
            return failed_response(1025, message)
    except Exception as e:
        print("Unexpected error:", e)
        message = 'File is corrupted or damaged. Try another one.'
        return failed_response(1025, message)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port='80')
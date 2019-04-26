__author__ = 'Nick Sarris (ngs5st)'

import urllib.parse
import io, os, requests
from google.cloud import vision
from google.cloud.vision import types
import pyscreenshot as ImageGrab
from bs4 import BeautifulSoup

def run_ocr(img_name):

    client = vision.ImageAnnotatorClient()
    file_name = os.path.join(os.path.dirname(__file__), img_name)

    with io.open(file_name, 'rb') as image_file:
        content = image_file.read()

    image = types.Image(content=content)

    response = client.text_detection(image=image)
    texts = response.text_annotations

    all_text = texts[0].description.strip()
    lines = all_text.split("\n")

    ans_1 = lines[-3].lower().encode('utf-8')
    ans_2 = lines[-2].lower().encode('utf-8')
    ans_3 = lines[-1].lower().encode('utf-8')

    del lines[-1]
    del lines[-1]
    del lines[-1]

    question = u" ".join([line.strip() for line in lines]).encode('utf-8')
    return {"question": question, "ans_1": ans_1, "ans_2": ans_2, "ans_3": ans_3}

def google(q_list, num):

    params = {"q": " ".join(q_list), "num": num}
    url_params = urllib.parse.urlencode(params)
    google_url = "https://www.google.com/search?" + url_params

    r = requests.get(google_url)
    soup = BeautifulSoup(r.text, "lxml")
    spans = soup.find_all('span', {'class': 'st'})

    text = u" ".join([span.get_text() for span in spans]).lower().encode('utf-8').strip()
    return text

def rank_answers(question_block):

    question = question_block["question"]
    ans_1 = question_block["ans_1"]
    ans_2 = question_block["ans_2"]
    ans_3 = question_block["ans_3"]

    results = []
    query = str(question).lstrip("b'").rstrip("'")

    text = google([query], 100)
    results.append({"ans": ans_1, "count": text.count(ans_1)})
    results.append({"ans": ans_2, "count": text.count(ans_2)})
    results.append({"ans": ans_3, "count": text.count(ans_3)})

    sorted_results = []

    sorted_results.append({"ans": ans_1, "count": text.count(ans_1)})
    sorted_results.append({"ans": ans_2, "count": text.count(ans_2)})
    sorted_results.append({"ans": ans_3, "count": text.count(ans_3)})

    if (sorted_results[0]["count"] == sorted_results[1]["count"]):

        text = google([query,
                       str(ans_1).lstrip("b'").rstrip("'"),
                       str(ans_2).lstrip("b'").rstrip("'"),
                       str(ans_3).lstrip("b'").rstrip("'")], 50)

        results = []

        results.append({"ans": ans_1, "count": text.count(ans_1)})
        results.append({"ans": ans_2, "count": text.count(ans_2)})
        results.append({"ans": ans_3, "count": text.count(ans_3)})

    return results

def gen_output(results, question_block):

    reverse = False
    results = sorted(results, key=lambda k: k['count'])
    question = question_block["question"]
    if " not " in str(question).lower():
        reverse = True

    if reverse == False:
        output = [str(results[-1]['ans']).lstrip("b'").rstrip("'").title(),
                  str(results[-1]['count'])]
    else:
        output = [str(results[0]['ans']).lstrip("b'").rstrip("'").title(),
                  str(results[0]['count'])]

    print('Question: ', str(question).lstrip("b'").rstrip("'"))
    print('')
    print('Answer 1: ', str(results[0]['ans']).lstrip("b'").rstrip("'").title() + " | " + str(results[0]['count']))
    print('Answer 2: ', str(results[1]['ans']).lstrip("b'").rstrip("'").title() + " | " + str(results[1]['count']))
    print('Answer 3: ', str(results[2]['ans']).lstrip("b'").rstrip("'").title() + " | " + str(results[2]['count']))
    print('')
    print('Calculated Response: ', output)

if __name__ == '__main__':

    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = ""

    im = ImageGrab.grab(bbox=(40, 280, 400, 640))
    im.save("q.png")

    question_block = run_ocr("q.png")
    results = rank_answers(question_block)
    gen_output(results, question_block)

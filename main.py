from __future__ import print_function
import pafy
import pydub
import json
from os.path import join, dirname
import re
import json
import sys
import os
from watson_developer_cloud import SpeechToTextV1
from watson_developer_cloud import NaturalLanguageUnderstandingV1
from watson_developer_cloud.natural_language_understanding_v1 import Features, EntitiesOptions, KeywordsOptions
from watson_developer_cloud import DiscoveryV1
from goose import Goose
from requests import get
from requests.exceptions import ConnectionError
from flask import Flask, request, render_template, jsonify
import jinja2
import signal
import sys

is_fake_news = False
sentiment_differential_global = 0
return_text = ""
app = Flask(__name__)
@app.route('/interactive')
def interactive():
    return render_template('index.html')
'''
@app.route('/userInput', methods=['POST'])
def userInput():
    sys.stdout.write("test1")
    sys.stdout.flush()
    link = request.form['txtInput']
    sys.stdout.write("test2")
    sys.stdout.flush()
    print(json.dumps({'status':'ok','link':link}))
    sys.stdout.write("test3")
    sys.stdout.flush()
    operations(link)
    sys.stdout.write("test4")
    sys.stdout.flush()
'''
@app.route('/background_process')
def background_process():
    try:
        try:
            link = request.args.get('text', 0, type=str)
            print("LINK: " + link)
            if len(link) > 0:
                answer = operations(link)
                return jsonify(result=answer)
            else:
                return jsonify(result='Try again.')
        except ConnectionError as e:
            print("Network Connection is Insufficient to Connect to Watson API")
    except Exception as e:
        return str(e)

def speechToText(filePath):
    modified_file_path = filePath[0:len(filePath) - 3] + 'txt'
    txt_file = open(modified_file_path, 'w')
    speech_to_text = SpeechToTextV1(
        username='8c7dee22-09f2-4948-a3a8-db5ff45f02e2',
        password='OaM80s4VzBLy',
        x_watson_learning_opt_out=False
    )
    with open(join(dirname(__file__), filePath),'rb') as audio_file:
        txt_file.write(json.dumps(speech_to_text.recognize(
            audio_file, content_type='audio/wav', timestamps=True,
            word_confidence=True),
                         indent=2))
    txt_file.close()
    return modified_file_path
 
def audioFromVideo(url):
    video = pafy.new(url)
    bestaudio = video.getbestaudio()
    videoTitle = re.sub(r'\W+', '', video.title)
    filePath = 'YHack/audio/' + videoTitle + "."
    bestaudio.download(filepath=filePath + bestaudio.extension)
    sound = pydub.AudioSegment.from_file(filePath + bestaudio.extension, bestaudio.extension)
    sound.export(filePath + "wav", format="wav")
    return filePath + "wav"

def getTranscriptFromTxt(file_path):
    modified_file_path = file_path[0:len(file_path) - 4] + '_transcript.txt'
    txt_file = open(file_path, 'r')
    transcript_file = open(modified_file_path, 'w')
    for line in txt_file:
        if 'transcript' in line:
            modified_line = line.replace('"transcript": "', '')
            modified_line = modified_line.replace('",', '')
            transcript_file.write(modified_line + '\n')
    txt_file.close()
    transcript_file.close()
    return modified_file_path

def extractArticleFromLink(url):
    if 'http://' in url:
        pass
    else:
        url = 'http://' + url
    file_path = 'YHack\\url\\' + re.sub(r'\W+', '', url).replace('html','') + '.txt'
    text_file = open(file_path, 'w')
    response = get(url)
    extractor = Goose()
    article = extractor.extract(raw_html=response.content)
    text_file.write(article.cleaned_text.encode('utf-8'))
    return file_path

def applyNaturalLangaugeUnderstandingAudio(file_path):

    transcript_file = open(file_path, 'r')
    modified_file_path = file_path[0:len(file_path) - 4] + '_nlp_json.txt'
    nlp_json_file = open(modified_file_path, 'w')
    transcript = ""
    for line in transcript_file:
        transcript += line.strip() + " "
    
    natural_language_understanding = NaturalLanguageUnderstandingV1(
        username="f4b95692-641f-479c-81c6-922f9c89e42d",
        password="5cURV1IktQbb",
        version="2017-02-27")
    
    response = natural_language_understanding.analyze(
    text=transcript,
    features=Features(entities=EntitiesOptions(emotion=True, sentiment=True), keywords=KeywordsOptions(emotion=True, sentiment=True))
    )
    nlp_json_file.write(json.dumps(response, indent=2))
    transcript_file.close()
    nlp_json_file.close()
    return modified_file_path

def applyNaturalLanguageUnderstandingURL(url, file_path):
    modified_file_path = file_path[0:len(file_path) - 4] + '_nlp_json.txt'
    nlp_json_file = open(modified_file_path, 'w')

    natural_language_understanding = NaturalLanguageUnderstandingV1(
        username="f4b95692-641f-479c-81c6-922f9c89e42d",
        password="5cURV1IktQbb",
        version="2017-02-27")
    
    response = natural_language_understanding.analyze(
    url=url,
    features=Features(entities=EntitiesOptions(emotion=True, sentiment=True), keywords=KeywordsOptions(emotion=True, sentiment=True))
    )
    nlp_json_file.write(json.dumps(response, indent=2))
    nlp_json_file.close()
    return modified_file_path

def analyzeJSON(json_file_path, transcript_file_path):
    linking_verbs = ['is','are','am','was','were','can be','could be','will be','would be','shall be','should be','may be','might be','must be','might be','must be','has been','have been','had been','feel','look','smell','sound','taste','act','appear','become','get','grow','prove','remain','seem','stay','turn','have been''is','are','am','was','were','can be','could be','will be','would be','shall be','should be','may be','might be','must be','might be','must be','has been','have been','had been','feel','look','smell','sound','taste','act','appear','become','get','grow','prove','remain','seem','stay','turn','have been']
    fake_news_check_counter = 0
    fake_news_verified_counter = 0
    sentiment_differential_total = 0
    json_file = open(json_file_path, 'r')
    transcript_file = open(transcript_file_path, 'r')
    transcript = ""
    for line in transcript_file:
        transcript += line.strip() + " "
    transcript_list = transcript.split()
    is_keyword_bool = True
    for line in json_file:
        relevance, text, anger, joy, sadness, fear, disgust, sentiment_score, sentiment_label, entity_type = None, None, None, None, None, None, None, None, None, None
        line = line.strip()
        if '"entities":' in line:
            is_keyword_bool = False
        if is_keyword_bool:
            if 'relevance' in line:
                relevance = float(line[13:len(line) - 1])
                if relevance >= 0.5:
                    line = next(json_file).strip().rstrip().replace(" ","0").replace('-','6')
                    text = re.sub(r'\W+', '', line[9:]).replace("0"," ").replace('6','-')
                    if 'donald j trump' == text.lower():
                        text = 'Trump'
                    line = next(json_file).strip()                    
        if 'emotion' in line:
            line= next(json_file).strip()
            line = next(json_file).strip()
            line = next(json_file).strip()
            line = next(json_file).strip()
            line = next(json_file).strip()
            line = next(json_file).strip()
            line = next(json_file).strip()
        count_line_present = False
        if '"count"' in line:
            line = next(json_file).strip()
            count_line_present = True
        if '"sentiment"' in line:
            line = next(json_file).strip()
            sentiment_score = float(line[9:len(line) - 2])
            line = next(json_file).strip()
            line = next(json_file).strip()
        if '},' in line and count_line_present:
            line = next(json_file)
            line = line.strip().rstrip().replace(" ", "0")
            text = re.sub(r'\W+', '', line[9:]).replace("0"," ")
            if 'trump' in text.lower():
                text = 'Trump'
            line = next(json_file).strip()
            if 'relevance' in line:
                relevance = float(line[13:len(line) - 1])
            line = next(json_file).strip()
        if relevance != None and relevance >= 0.60:
            extended_text = ""
            text_list = text.split()
            text_index = None
            try:
                text_index = transcript_list.index(text_list[0])
            except(ValueError, IndexError):
                try:
                    text_index = transcript_list.index(text_list[1])
                except(ValueError, IndexError):
                    pass
            if text_index is None:
                pass
            else:
                linking_verb_count = 0
                qualifier_count = 0
                begin_index = text_index - 15
                end_index = text_index + 15
                if begin_index < 0:
                    while begin_index < 0:
                        begin_index += 1
                if end_index > len(transcript_list) - 1:
                    while end_index > len(transcript_list) - 1:
                        end_index -= 1
                        if begin_index > 0:
                            begin_index -= 1
                for x in range(begin_index, end_index):
                    extended_text += transcript_list[x] + " "
                    if transcript_list[x] in linking_verbs:
                        linking_verb_count += 1
                if linking_verb_count > 0:
                    fake_news_check_counter += 1
                    fakeNewsCheck(text, extended_text, sentiment_score)
                    sentiment_differential_total += sentiment_differential_global
                    if is_fake_news: #check if fake news if there's a large amount of average emotion and if there's at least a moderate emotional differential (compared to other emotions) present and there's at least one qualifier and linking verb present
                        fake_news_verified_counter += 1
                        '''
                    emotion_list = [anger, joy, sadness, fear, disgust]
                    largest_emotional_differential = 0
                    if None in emotion_list:
                        pass
                    else:
                        for x in range(0, len(emotion_list)):
                            for y in range(x, len(emotion_list)):
                                if abs(emotion_list[x] - emotion_list[y]) > largest_emotional_differential:
                                    largest_emotional_differential = abs(emotion_list[x] - emotion_list[y])
                        
                        average_emotion = (anger + joy + sadness + fear + disgust) / 5
                        if average_emotion > 0.1:
                        '''
    if fake_news_check_counter > 0:
        sentiment_differential_avg = sentiment_differential_total / fake_news_check_counter
        fake_news_confidence_level = float(fake_news_verified_counter) / float(fake_news_check_counter)
        if sentiment_differential_avg > 0.75 and fake_news_confidence_level >= 0.5:
            return_text = "This link is " + str(fake_news_confidence_level * 100) + "% fake news with an average sentiment differential of " + str(sentiment_differential_avg) + ". There's strong reason to believe this link is fake news."
        elif sentiment_differential_avg > 0.5 and fake_news_confidence_level >= 0.4:
            return_text = "This link is " + str(fake_news_confidence_level * 100) + "% fake news with an average sentiment differential of " + str(sentiment_differential_avg) + ". There's moderate reason to believe this link is fake news."
        else:
            return_text ="This link is " + str(fake_news_confidence_level * 100) + "% fake news with an average sentiment differential of " + str(sentiment_differential_avg) + ". There's weak reason to believe that this link is fake news."
    else:
        return_text = "This link is 0% fake news. There's strong reason to believe it is real news."
                            
def fakeNewsCheck(text, extended_text, emotion_list, sentiment_score, sentiment_label):
    '''
    Here's the plan:
        - get the sentiment analysis of the text and the extended_text using the watson discovery news dataset and if there's a large difference, then
          it's more likely to be fake news. the more of the checks for fake news that are fake news, the more likely that the link as a whole is fake news
    '''
    #print("Potential Fake News Found")
    
    discovery = DiscoveryV1(
      username="e2ea27ec-ec9c-4f3a-b5b2-f112de36ab07",
      password="yiTTwQNrvhQQ",
      version="2017-11-07"
    )
    '''
    qopts = {'query': '{' + extended_text + '}', 'filter': '{enriched_title.entities.type::Company}','term': '{enriched_title.entities.text}','timeslice':'{crawl_date,1day}','term':'{enriched_text.sentiment.document.label}'}
    my_query = discovery.query('system', 'news-en', qopts)
    json_temp_file = open('C:\\Users\\alexa\\Desktop\\YHack\\temp\\temp.txt', 'w')
    json_temp_file.write(json.dumps(my_query, indent = 2))
    sentiment_count = 0
    sentiment_total_extended_text = 0
    json_temp_file.close()
    json_temp_file = open('C:\\Users\\alexa\\Desktop\\YHack\\temp\\temp.txt','r')
    for line in json_temp_file:
        line = line.strip()
        if '"sentiment"' in line:
            line = next(json_temp_file).strip()
            if 'score' in line:
                pass
            else:
                line = next(json_temp_file).strip()
            sentiment_line = float(line[9:len(line) - 1])
            if sentiment_line > 0:
                sentiment_total_extended_text += sentiment_line
                sentiment_count += 1
    sentiment_total_extended_text = sentiment_total_extended_text / sentiment_count #avg_sentiment
    json_temp_file.close()
    '''
    #qopts = {'query': '{' + text + '}', 'filter': '{enriched_text.sentiment.document.score::!"0"}','term': '{enriched_title.entities.text}','count':'{100}','timeslice':'{crawl_date,1day}','term':'{enriched_text.sentiment.document.label}'}
    qopts= {'query':'{' + text + '}','nested':'{enriched_text.sentiment.document','filter':'{enriched_text.sentiment.document.score::!"0"}','average':'{enriched_text.sentiment.document.score}','term':'{text,count:100}'}

    my_query = discovery.query('system', 'news-en', qopts)
    json_temp_file = open('C:\\Users\\alexa\\Desktop\\YHack\\temp\\temp.txt', 'w')
    json_temp_file.write(json.dumps(my_query, indent = 2))
    sentiment_count = 0
    sentiment_total_text = 0
    json_temp_file.close()
    json_temp_file = open('YHack\\temp\\temp.txt','r')
    for line in json_temp_file:
        line = line.strip()
        if '"sentiment"' in line:
            line = next(json_temp_file).strip()
            if 'score' in line:
                pass
            else:
                line = next(json_temp_file).strip()
            sentiment_line = float(line[9:len(line) - 1])
            if sentiment_line > 0:
                sentiment_total_text += sentiment_line
                sentiment_count += 1
    sentiment_total_text = sentiment_total_text / sentiment_count #avg_sentiment
    #print("Sentiment Extended Text: " + str(sentiment_total_extended_text))
    #print("Sentiment Score: " + str(sentiment_score))
    #print("Sentiment Text: " + str(sentiment_total_text))
    sentiment_differential = sentiment_score - sentiment_total_text if sentiment_score >= sentiment_total_text else sentiment_total_text - sentiment_score
    #print("Sentiment Differential: " + str(sentiment_differential))
    if abs(sentiment_differential) > 0.53:
        #print('FAKE NEWS')
        is_fake_news, sentiment_differential_global = True, sentiment_differential
    else:
        #print('NOT FAKE NEWS')
        is_fake_news, sentiment_differential_global = False, sentiment_differential
    
def operations(url):
    try:
        '''
        if 'youtube' in url:
            audio_file_path = audioFromVideo(url)
            text_file_path = speechToText(audio_file_path)
            transcript_file_path = getTranscriptFromTxt(text_file_path)
            nlp_json_file_path = applyNaturalLangaugeUnderstandingAudio(transcript_file_path)
        elif 'facebook' in url:
            pass
        elif 'twitter' in url:
            pass
        else:
            transcript_file_path = extractArticleFromLink(url)
            nlp_json_file_path = applyNaturalLanguageUnderstandingURL(url, transcript_file_path)
        analyzeJSON(nlp_json_file_path, transcript_file_path)
        '''
        analyzeJSON("C:\\Users\\alexa\\Desktop\\YHack\\url\\httpwwwbreitbartcombiggovernment20171201professorfacesstiffcriticismafterhepensproroymoorearticle_nlp_json.txt","C:\\Users\\alexa\\Desktop\\YHack\\url\\httpwwwbreitbartcombiggovernment20171201professorfacesstiffcriticismafterhepensproroymoorearticle.txt")
    except ConnectionError as e:
        return("Internet Connection Isn't Strong Enough to Reach the Link")

if __name__ == "__main__":
    app.run()


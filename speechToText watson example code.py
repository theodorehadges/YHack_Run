from __future__ import print_function
import json
from os.path import join, dirname
from watson_developer_cloud import SpeechToTextV1

def speechToText(filePath):
    speech_to_text = SpeechToTextV1(
        username='8c7dee22-09f2-4948-a3a8-db5ff45f02e2',
        password='OaM80s4VzBLy',
        x_watson_learning_opt_out=False
    )

    print(json.dumps(speech_to_text.models(), indent=2))

    print(json.dumps(speech_to_text.get_model('en-US_BroadbandModel'), indent=2))

    with open(join(dirname(__file__), 'C:/Users/alexa/Desktop/YHack/man2_orig.wav'),
              'rb') as audio_file:
        print(json.dumps(speech_to_text.recognize(
            audio_file, content_type='audio/wav', timestamps=True,
            word_confidence=True),
                         indent=2))

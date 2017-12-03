from flask import Flask, request, render_template, jsonify
import jinja2
import signal
import sys
from decimal import Decimal

fake_news_txt = open("C:\\Users\\alexa\\Desktop\\YHack\\fake_news.txt","r")
return_text = ""

fake_news_dict = dict()
for line in fake_news_txt:
    index = line.find(',')
    key = line[:index]
    val = line[index + 1:]
    num = '0.'
    end_index = 0
    if 'that this is fake news. From this data, ' in line:
        pass
    else:
        for c in range(7, len(val)):
            if unicode(val[c],'utf-8').isnumeric():
                num += val[c]
            else:
                end_index = c
                break
        num = Decimal(('% 6.1f' % float(num)))
        val = val.replace(val[5:end_index],str(num))
        start_index = val.find('public opinion is ') + len('public opinion is ') + 2
        num = '0.' if val[start_index - 1] == '0' else '1.'
        for c in range(start_index, len(val)):
            if unicode(val[c],'utf-8').isnumeric():
                num += val[c]
            else:
                end_index = c
                break
        num = Decimal(('% 6.3f' % float(num)))
        val = val.replace(val[start_index-2:end_index],str(num))
    fake_news_dict[key] = val

app = Flask(__name__)

@app.route('/interactive')
def interactive():
    return render_template('index.html')

@app.route('/background_process')
def background_process():
    try:
        try:
            link = request.args.get('text', 0, type=str)
            if link in fake_news_dict.keys():
                return jsonify(result=fake_news_dict[link])
            else:
                return jsonify(result='Unable to pull-up link. Input a new link.')
        except ConnectionError as e:
            print("Network Connection is Insufficient to Connect to Watson API")
    except Exception as e:
        return str(e)
if __name__ == "__main__":
    app.run()

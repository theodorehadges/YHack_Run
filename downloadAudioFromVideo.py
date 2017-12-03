import pafy
import pydub


def audioFromVideo(url):
    video = pafy.new(url)
    bestaudio = video.getbestaudio()
    filePath = 'C:/Users/alexa/Desktop/YHack/audio/' + video.title
    bestaudio.download(filepath=filePath + video.extension)
    sound = pydub.AudioSegment.from_file("C:/Users/alexa/Desktop/YHack/Ford_Carter_debate_excerpt.webm", "webm")
    sound.export(filePath + ".wav", format="wav")
    return filePath + ".wav"

from pydub import AudioSegment
from speech_recognition import Recognizer, AudioFile
import wavio as wv
import sounddevice as sd
import time, random, sys
import wavio as wv
import sounddevice as sd
from scipy.io.wavfile import write
import nltk
# Python discovers verbs with the same derivative and associates them by reverting to the root or lemma
# of those words (i.e. be for was and is). It requires the below class to do this.
from nltk.stem import WordNetLemmatizer
# The class immediately below carries out statistical analysis to ascertain significance of words in the body of text.
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import  cosine_similarity
#nltk.download('wordnet')
# nltk.download('punkt')
#nltk.download('averaged_perceptron_tagger')
import pandas
# BELOW: for ascertaining mood from text.
#nltk.download('vader_lexicon')
#nltk.download('omw-1.4')
from nltk.sentiment import SentimentIntensityAnalyzer
import schedule
import smtplib
from email.mime.text import MIMEText

def main():

    while True:
        print('''The following program initiates an audio recording, which will subsequently be saved to the system
        and then analysed to ascertain the extent to which the person is in a positive or negative mind frame
        based on the language they use. The recording will last for five minutes. Please begin by telling me how
        you are feeling today and how you have been feeling generally during the course of the last week. Please
        speak clearly and loudly into the microphone.''')
        time.sleep(2)

        while True:
            user_input = str(input('Are you ready to start the recording? (YES or NO)'))
            if user_input.upper() == 'NO':
                print('Thank you. See you again next time.')
                sys.exit()
            elif user_input.upper() == 'YES':
                print('Okay, the recording will start momentarily. So please commence speaking.')
                break
            else:
                print('Please enter a valid option.')

        freq = 44100
        duration = 300

        recording = sd.rec(int(duration * freq),
                           samplerate=freq, channels=1)
        # Record audio for the given number of seconds
        sd.wait()

        # This will convert the NumPy array to an audio file with the given sampling frequency
        # write("recording0.wav", freq, recording)

        # Convert the NumPy array to audio file
        wv.write("recording1.wav", recording, freq, sampwidth=2)
        break

    written_text = text_analysis()

    mood = mood_evaluator(written_text)
    print(mood)

    func_lemma = lemma_me(written_text)
    print(func_lemma)

    # I want to use a set comprehension to obtain just one token of each word that appears more than once in the speech.
    # I can then feed those into a function to cross-reference them with the relevant .txt file. I want to exclude
    # words like 'to', 'and' etc., hence additional condition.
    wordlist = {words for words in func_lemma if func_lemma.count(words) > 1 and len(words) > 2}


    if len(wordlist) > 0:
        key_words = key_word_search(mood, wordlist)
        if len(key_words) > 0:
            print(f'Often the language we use gives a unique insight into our mind-frame.'
                  f'It might interest you to see the words you used repeatedly that most fit your overall mood, '
                  f'These words were: {key_words}. I will give you a moment in case you want to make note.')
        if len(key_words) == 0:
            print(f'Often the language we use gives a unique insight into our mind-frame.'
                  f'It might interest you to see the words you used repeatedly: {wordlist}. I will give you a moment to digest.')
    else:
        print('There were no specific words that stood out here.')

    time.sleep(20)

    email_name = user_email(mood)
    print('Thanks for that! Be in touch soon... Bye!')
# Below I want to run my final function on a preconfigured schedule.
    schedule.every().monday.do(email_send_complete, email_name, mood)
    while True:
        schedule.run_pending()
        time.sleep(1)



def text_analysis():
    recognizer = Recognizer()

    with AudioFile('recording1.wav') as audio_file:
        audio = recognizer.record(audio_file)

    # The below is tied to the Google speech recognition API.
    text = recognizer.recognize_google(audio)
    return text


def lemma_me(written_text):
    lemmatizer = WordNetLemmatizer()
    sentence_tokens = nltk.word_tokenize(written_text.lower())
    pos_tags = nltk.pos_tag(sentence_tokens)

    sentence_lemmas = []
    for token, pos_tag in zip(sentence_tokens, pos_tags):
# We want to take the first letter of the second string of our pos-tag values to ascertain word-type: noun etc.
# Prepositions don't have a lemma, hence conditional below. We don't need prepositions and full-stop as meaningless.
        if pos_tag[1][0].lower() in ['n', 'v', 'a', 'r']:
            lemma = lemmatizer.lemmatize(token, pos_tag[1][0].lower())
            sentence_lemmas.append(lemma)

    return sentence_lemmas


def mood_evaluator(written_text):
    analyzer = SentimentIntensityAnalyzer()


    dictionary = analyzer.polarity_scores(written_text)
# Sum of the above coefficients equal to 1. The compound is an average of values.

    if analyzer.polarity_scores(written_text)['compound'] >= 0.7:
        response_pos = 'Ok, it seems as if you are in a very positive mood at the moment.'
        return response_pos
    elif 0.5 <= analyzer.polarity_scores(written_text)['compound'] < 0.6:
        response_neut = 'Alright, so I can see from what you have said that you are feeling mediocre right now.'
        return response_neut
    else:
        response_neg = 'I am so sorry: you have clearly had a difficult time recently based on the language you are using'
        return response_neg


def key_word_search(mood, wordlist):


    if mood.startswith('Ok') and len(wordlist) > 0:
        positive = open('positive.txt')
        final_positive = positive.read()
        positive_words = list(words for words in wordlist if words in final_positive)
        return positive_words
    elif mood.startswith('Alright') and len(wordlist)>0:
        neutral = open('neutral.txt')
        final_neutral = neutral.read()
        neutral_words = list(words for words in wordlist if words in neutral.read())
    elif mood.startswith('I'):
        negative = open('negative.txt')
        final_negative = negative.read()
        negative_words = list(words for words in wordlist if words in negative.read())
        return negative_words


def user_email(mood):

    while True:
        if mood.startswith('I') or mood.startswith('Alright'):
            final_input = input('''Based on your responses, I wonder whether you would like me to send you
            inspirational quotes at the start of each week to help boost your mood? (YES or NO)''')
            if final_input.upper() == 'NO':
                print('Ok, well feel free to visit again if you change your mind. Take care!')
                sys.exit()
            elif final_input.upper() == 'YES':
                email_input = input('Please enter your email here and I will set that up for you.')
                break
            else:
                print('Please enter a valid input.')
        elif mood.startswith('Ok'):
            final_input = input('''Maintaining a good mood is a habit and requires constant presence of mind
            and active attention to self-care. Would you like me to send you a weekly reminder of easy self-care
            mechanisms you can engage with to sustain your good mood in the future? (YES or NO)''')
            if final_input.upper() == 'NO':
                print('Ok, well feel free to visit again if you change your mind. Take care!')
                sys.exit()
            elif final_input.upper() == 'YES':
                email_input = input('Please enter your email here and I will set that up for you. Make sure it is a valid address.')
                break
            else:
                print('Please enter a valid input.')
    return email_input


def message_complete(mood):

    if mood.startswith('Ok'):
# Python String splitlines() method is used to split the lines at line boundaries.
#The function returns a list of lines in the string, including the line break(optional).
        lines = open('inspiration.txt').read().splitlines()
        my_line = random.choice(lines)
        message = my_line.lower()
    else:
        lines = open('self_care.txt').read().splitlines()
        my_line = random.choice(lines)
        message = f'Always remember to {my_line.lower()}'

    return message


def email_send_complete(email_name, mood):


    complete_message = message_complete(mood)

    subject = 'Mood-lifting material'

    to_email = email_name
    print(to_email)
    from_email = <EMAIL>
    from_password = <PASSWORD>
    server = smtplib.SMTP('smtp.mail.yahoo.com', 587)
    server.starttls()
    server.login(from_email, from_password)


    msg = MIMEText(complete_message, 'html')
    #msg = complete_message
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    print(msg)
    server.send_message(msg)

    return True


if __name__ == '__main__':
    main()


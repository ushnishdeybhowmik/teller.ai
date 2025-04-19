import speech_recognition as sr
class Transcriber:
    def __init__(self):
        self.__recognizer = sr.Recognizer()
        self.__mic = sr.Microphone()
    
    def listen(self) -> dict:
        
        try:
            with self.__mic as source:
                self.__recognizer.adjust_for_ambient_noise(source, duration=2)
                print("Listening...")
                audio: sr.AudioData = self.__recognizer.listen(source, timeout=10, phrase_time_limit=20)
                print("Recognizing...")
                text: str = self.__recognizer.recognize_google(audio)
                return {"text": text, "code": 200}
        except sr.UnknownValueError:
            text: str = "Could not understand audio"
            return {"text": text, "code": 100}
        except sr.RequestError as e:
            text: str = "Could not request results; {0}".format(e)
            return {"text": text, "code": 400}
        except Exception as e:
            text: str = "An error occurred: {0}".format(e)
            return {"text": text, "code": 500}
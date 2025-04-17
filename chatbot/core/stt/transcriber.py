import speech_recognition as sr
class Transcriber:
    def __init__(self):
        pass
    
    def listen(self) -> dict:
        recognizer: sr.Recognizer = sr.Recognizer()
        mic: sr.Microphone = sr.Microphone()
        
        try:
            with mic as source:
                recognizer.adjust_for_ambient_noise(source, duration=2)
                print("Listening...")
                audio: sr.AudioData = recognizer.listen(source, timeout=10, phrase_time_limit=20)
                print("Recognizing...")
                text: str = recognizer.recognize_google(audio)
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
from core.stt.transcriber import Transcriber
from core.processing.context import Context
from core.tts.agent import Agent

transcriber = Transcriber()
context = Context()
agent = Agent()


print(f"Choose an option:\n1. Log in\n2. Sign up")
option = int(input("Option: "))
if option == 1:
    email = input("Email: ")
    password = input("Password: ")
    text, agent.user = agent.customer.login(email, password)
    agent.speak(text)
elif option == 2:
    name = input("Name: ")
    email = input("Email: ")
    password = input("Password: ")
    secret_question = input("Secret question: ")
    secret_answer = input("Secret answer: ")
    text, agent.user = agent.customer.add(name, email, password, secret_question, secret_answer)
    agent.speak(text)


while agent.active:
    corpus = transcriber.listen()
    if corpus['code'] == 200:
        data = context.getContext(corpus['text'])
        agent.action(data)
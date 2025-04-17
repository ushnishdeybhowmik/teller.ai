from core.stt.transcriber import Transcriber
from core.processing.context import Context
from core.tts.agent import Agent

transcriber = Transcriber()
context = Context()
agent = Agent()



while agent.active:
    corpus = transcriber.listen()
    if corpus['code'] == 200:
        data = context.getContext(corpus['text'])
        agent.action(data)
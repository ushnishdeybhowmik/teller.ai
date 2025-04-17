import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk import pos_tag, ne_chunk
from nltk.chunk import RegexpParser
from nltk.wsd import lesk
from nltk.tree import Tree
from nltk.stem import WordNetLemmatizer
import spacy

class Context:
    
    grammar = "NP: {<DT>?<JJ>*<NN.*>+}"
    def __init__(self):
        nltk.download('punkt')
        nltk.download('averaged_perceptron_tagger')
        nltk.download('averaged_perceptron_tagger_eng')
        nltk.download('maxent_ne_chunker')
        nltk.download('maxent_ne_chunker_tab')
        nltk.download('words')
        nltk.download('wordnet')
        nltk.download('omw-1.4')
        nltk.download('punkt_tab')
        self.lemmatizer = WordNetLemmatizer()
        self.chunk_parser = RegexpParser(self.grammar)
        self.nlp = spacy.load("en_core_web_sm")
    
    
    def getContext(self, text):
        sentences = sent_tokenize(text)
        tokens_full = []
        for sentence in sentences:
            tokens = word_tokenize(sentence)
            tokens_full.extend(tokens)
        
        return tokens_full
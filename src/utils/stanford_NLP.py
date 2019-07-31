from stanfordcorenlp import StanfordCoreNLP
import subprocess, shlex
import json
import nltk
import re
nltk.download('punkt')

"""
Download StanfordCoreNLP from https://stanfordnlp.github.io/CoreNLP/download.html
"""

"""Path to StanfordCoreNLP Library"""
stanfordLibrary = "../../stanford-corenlp-full-2018-10-05"

class StanfordNLP(object):
    def __init__(self):
        self.nlp = StanfordCoreNLP(stanfordLibrary, memory='6g', quiet=True)  # , quiet=False, logging_level=logging.DEBUG)
        self.props = {
            'annotators': 'tokenize,ssplit,pos,lemma,ner,depparse,parse,coref,quote',
            'ner.applyFineGrained': 'False',
            'ner.applyNumericClassifiers': 'False',
            'ssplit.newlineIsSentenceBreak': 'always',
            'pipelineLanguage': 'en',
            'outputFormat': 'json',
            'timeout': 150000
        }

    def annotate(self, sentence):
        output = json.loads(self.nlp.annotate(sentence, self.props))
        quotes = output["quotes"]
        quoteResult = [self._extractQuoteInfo(n) for n in quotes if self._bigEnough(n)]
        return [sentence_bundle for quote_bundle in quoteResult for sentence_bundle in self._splitIntoSentences(quote_bundle)] 

    def _extractQuoteInfo(self, thisquote):
        toReturn = [thisquote["text"],thisquote["canonicalSpeaker"],thisquote["endToken"] - thisquote["beginToken"], False]
        if (toReturn[1][0].islower()) or (str.lower(toReturn[1]) in ["his", "her", "unknown", "they", "it", "he", "she", "you"]):
            toReturn[1] = ""
        if thisquote["endSentence"] - thisquote["beginSentence"] > 0:
            toReturn[3] = True
        return toReturn

    def _bigEnough(self, thisquote):
        return thisquote["endToken"] - thisquote["beginToken"] >= 5

    def _splitIntoSentences(self, entry):
        # Turns quote bundle into individual quote sentences of the format:
        # [sentence text, speaker, isFullSentence?]
        tokenizer = nltk.tokenize.RegexpTokenizer(r'\w+')
        sentences = nltk.tokenize.sent_tokenize(entry[0])
        toReturn = []
        for sentence in sentences:
            sentence = re.sub(r"^\W+|[^\w.!,?]+$", "", sentence)            
            isFullSentence = False
            if sentence.endswith(('?','!','.',',')) and sentence[0].isupper():
                isFullSentence = True
            wordCount = len(tokenizer.tokenize(sentence))
            if wordCount > 5: 
                toReturn.append([sentence, entry[1], isFullSentence])
        
        return toReturn
    
    @staticmethod
    def tokens_to_dict(_tokens):
        tokens = defaultdict(dict)
        for token in _tokens:
            tokens[int(token['index'])] = {
                'word': token['word'],
                'lemma': token['lemma'],
                'pos': token['pos'],
                'ner': token['ner']
            }
        return tokens
    
    def close(self):
        self.nlp.close()
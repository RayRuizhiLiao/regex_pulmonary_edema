import os
import sys

current_path = os.path.dirname(os.path.abspath(__file__))
negex_path = os.path.join(current_path, 'negex/')
sys.path.insert(0, negex_path)
import negex

class WordMatch(object):
	"""Word matching in a sentence with negation detection
	"""

	def __init__(self, sentence, words=[], case_insensitive=True):
		self.sentence = sentence
		self.words = words
		self.case_insensitive = case_insensitive
		self.words_mentioned = {}
		self.words_mentioned_positive = {}
		self.words_mentioned_negative = {}

	def mention(self):
		"""Determine which words in the given list are mentioned 
		in the given sentence.

		Returns:
			A dictionary with words and whether or not they're mentioned.  
		"""
		if self.case_insensitive:
			lower_sentence = self.sentence.lower()
			for word in self.words:
				if word.lower() in lower_sentence:
					self.words_mentioned[word] = True
				else:
					self.words_mentioned[word] = False
		else:
			for word in self.words:
				if word in self.sentence:
					self.words_mentioned[word] = True
				else:
					self.words_mentioned[word] = False

		return self.words_mentioned

	def mention_positive(self):
		"""Determine if the mention words are affirmed (positive)

		Returns:
			A dictionary with words and whether or not they're mentioned
			and affirmed
		"""
		self.mention()
		rfile = open(negex_path+'negex_triggers.txt', 'r')
		irules = negex.sortRules(rfile.readlines())
		for key in self.words_mentioned:
			if not self.words_mentioned[key]:
				self.words_mentioned_positive[key] = False
			else:
				tagger = negex.negTagger(sentence = self.sentence, 
										 phrases = [key], rules = irules,
										 negP = False)
				if tagger.getNegationFlag() == 'affirmed':
					self.words_mentioned_positive[key] = True
				else:
					self.words_mentioned_positive[key] = False

		return self.words_mentioned_positive

	def mention_negative(self):
		"""Determine if the mention words are negated (negative)

		Returns:
			A dictionary with words and whether or not they're mentioned
			and negated
		"""
		self.mention()
		rfile = open(negex_path+'negex_triggers.txt', 'r')
		irules = negex.sortRules(rfile.readlines())
		for key in self.words_mentioned:
			if not self.words_mentioned[key]:
				self.words_mentioned_negative[key] = False
			else:
				tagger = negex.negTagger(sentence = self.sentence, 
										 phrases = [key], rules = irules,
										 negP = False)
				if tagger.getNegationFlag() == 'negated':
					self.words_mentioned_negative[key] = True
				else:
					self.words_mentioned_negative[key] = False

		return self.words_mentioned_negative

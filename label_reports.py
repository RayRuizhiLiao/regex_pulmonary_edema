# import csv
# from shutil import copyfile
import sys
import os
import argparse
import pandas as pd
import re

current_path = os.path.dirname(os.path.abspath(__file__))
negex_path = os.path.join(current_path, 'negex/negex.python/')
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


def label_report(report, severities, keywords, tag='mentioned'):
	"""
	Label a given report the pulmonary edema severity the report indicates.
	The keywords associated with each severity level are also given.
	The tag can be "mentioned"/"affirmed"/"negated" and will be used in the keyword matching.
	Note multiple levels (i.e. their keywords) might be detected,
	and the most severe level will be returned. 

	Returns:
		label: the pulmonary edema severity of the given report as an integer between 0 and 3.
		-1 means the report cannot be labeled. 
		severity_keywords: the keywords that are detected in the report associated with each severity level.
	"""
	label = -1
	severity_keywords = {0:[], 1:[], 2:[], 3:[]}

	sentences = re.split('\.|\:', report)
	for sentence in sentences:
		word_match = WordMatch(sentence, keywords)
		if tag == 'mentioned':
			keywords_detected = word_match.mention()
		if tag == 'affirmed':
			keywords_detected = word_match.mention_positive()
		if tag == 'negated':
			keywords_detected = word_match.mention_negative()
		for i in range(len(severities)):
			severity = severities[i]
			keyword = keywords[i]
			if keywords_detected[keyword] == True:
				if keyword not in severity_keywords[severity]:
					severity_keywords[severity].append(keyword)
					label = max(severity, label)

	return label, severity_keywords

def get_chf_cohort(metadata_path):
	"""
	Given a metadata file path, return the radiology study IDs of 
	congestive heart failure cohort.
	"""
	df = pd.read_csv(metadata_path, sep="\t")
	chf_metadata = df.to_dict()

	study_ids = chf_metadata['study_id']
	chf_flags = chf_metadata['heart_failure']
	chf_study_ids = []

	for i in range(len(study_ids)):
		if chf_flags[i] == 1 and study_ids[i] not in chf_study_ids:
			chf_study_ids.append(str(study_ids[i]))

	return chf_study_ids

def main(args):

	df = pd.read_csv(args.negated_keywords_path, 
					 sep="\t")
	negated_keywords = df.to_dict()
	df = pd.read_csv(args.affirmed_keywords_path, 
					 sep="\t")
	affirmed_keywords = df.to_dict()
	df = pd.read_csv(args.mentioned_keywords_path, 
					 sep="\t")
	mentioned_keywords = df.to_dict()

	if args.limit_in_chf:
		chf_study_ids = get_chf_cohort(args.chf_metadata_path)


	labeled_files = {}
	regex_labels = {}
	c = 0
	c_labels = [0,0,0,0]

	for filename in os.listdir(args.report_dir):
		report_path = os.path.join(args.report_dir, filename)
		if args.limit_in_chf and filename[1:9] not in chf_study_ids:
			continue
		with open(report_path, 'r') as file:
			report = file.read()

			severities = [affirmed_keywords['pulmonary_edema_severity'][i] \
				for i in range(len(affirmed_keywords['pulmonary_edema_severity']))]
			keywords = [affirmed_keywords['keyword_terms'][i] \
				for i in range(len(affirmed_keywords['keyword_terms']))]
			label_a, severity_keywords_a = label_report(report, severities,
														keywords, tag='affirmed')

			severities = [negated_keywords['pulmonary_edema_severity'][i] \
				for i in range(len(negated_keywords['pulmonary_edema_severity']))]
			keywords = [negated_keywords['keyword_terms'][i] \
				for i in range(len(negated_keywords['keyword_terms']))]
			label_n, severity_keywords_n = label_report(report, severities,
														keywords, tag='negated')

			severities = [mentioned_keywords['pulmonary_edema_severity'][i] \
				for i in range(len(mentioned_keywords['pulmonary_edema_severity']))]
			keywords = [mentioned_keywords['keyword_terms'][i] \
				for i in range(len(mentioned_keywords['keyword_terms']))]
			label_m, severity_keywords_m = label_report(report, severities,
														keywords, tag='mentioned')

			label = max([label_a, label_n, label_m])
			if label != -1:
				c += 1
				relevant_keywords = severity_keywords_a[label]
				relevant_keywords += severity_keywords_n[label]
				relevant_keywords += severity_keywords_m[label]
				labeled_files[c] = filename
				regex_labels[c] = label
				c_labels[label] += 1

	regex_df = pd.DataFrame({'filename': labeled_files, 'regex_label': regex_labels})
	regex_df.to_csv('tmp.tsv', sep="\t")
	print(c_labels)
	

def past():

	original_report_dir = \
		'/data/vision/polina/projects/chestxray/data_v2/reports'
	report_dir = \
		'/data/vision/polina/projects/chestxray/data_v2/reports_extracted'
	result_dir = \
		'/data/vision/polina/projects/chestxray/work_space_v2/'\
		'report_processing/edema_labels-10-09-2019/all_reports/'

	if not os.path.exists(result_dir):
		os.makedirs(result_dir)

	HF_reports = []
	csv_dir = '/data/vision/polina/projects/chestxray/data_v2'
	HF_label_path = os.path.join(csv_dir, 
								 'mimic-cxr-metadata-HF-7-11-2019.csv')
	with open(HF_label_path, 'r') as HF_label_file:
		HF_label_reader = csv.reader(HF_label_file, delimiter = ',')
		for row in HF_label_reader:
			if row[4] == '1' and 's'+row[1]+'.txt' not in HF_reports:
				HF_reports.append('s'+row[1]+'.txt')

	HFReportFile = open(os.path.join(result_dir, 'HF.txt'), 'a')
	for filename in HF_reports:
		HFReportFile.write(filename+'\n')
	HFReportFile.close()
	print(len(HF_reports))

	level0_words = ['no pulmonary edema', 'no vascular congestion',\
					'no fluid overload', 'no acute cardiopulmonary process']
	level0_words_n = ['pulmonary edema', 'vascular congestion',\
					  'fluid overload', 'acute cardiopulmonary process']
	level1_words = ['cephalization', 'mild pulmonary vascular congestion',\
					'mild hilar engorgement', 'mild vascular plethora']
	level2_words = ['interstitial opacities', 'kerley',\
					'interstitial edema', 'interstitial thickening'\
					'interstitial pulmonary edema', 'interstitial marking'\
					'interstitial abnormality', 'interstitial abnormalities'\
					'interstitial process']
	level3_words = ['alveolar infiltrates', 'severe pulmonary edema',\
					'perihilar infiltrates', 'hilar infiltrates',\
					'parenchymal opaciities', 'alveolar opacities',\
					'ill defined opacities', 'ill-defined opacities'\
					'patchy opacities']

	count = 0
	for filename in os.listdir(report_dir):
		#if filename in HF_reports:
		count += 1
		if count % 1000 == 0:
			print(count)
		report_path = os.path.join(report_dir, filename)
		file = open(report_path, 'r')
		report = file.read()
		sentences = re.split('\.|\:', report)
		label = -1
		for sentence in sentences:
			word_match = WordMatch(sentence, level0_words)
			level0_mentioned = word_match.mention()
			for k in level0_mentioned:
				if level0_mentioned[k]:
					label = 0
					keyword = k
			word_match = WordMatch(sentence, level0_words_n)
			level0_mentioned = word_match.mention_negative()
			for k in level0_mentioned:
				if level0_mentioned[k]:
					label = 0
					keyword = k				
			word_match = WordMatch(sentence, level1_words)
			level1_mentioned = word_match.mention_positive()
			for k in level1_mentioned:
				if level1_mentioned[k]:
					label = 1
					keyword = k
			word_match = WordMatch(sentence, level2_words)
			level2_mentioned = word_match.mention_positive()
			for k in level2_mentioned:
				if level2_mentioned[k]:
					label = 2
					keyword = k
			word_match = WordMatch(sentence, level3_words)
			level3_mentioned = word_match.mention_positive()
			for k in level3_mentioned:
				if level3_mentioned[k]:
					label = 3
					keyword = k	

		if label==0:
			with open(os.path.join(result_dir, 'class0.txt'), 'a') as class_file:
				class_file.write(filename+': ')
				class_file.write(keyword)
				class_file.write('\n')
		if label==1:
			with open(os.path.join(result_dir, 'class1.txt'), 'a') as class_file:
				class_file.write(filename+': ')
				class_file.write(keyword)
				class_file.write('\n')			
		if label==2:
			with open(os.path.join(result_dir, 'class2.txt'), 'a') as class_file:
				class_file.write(filename+': ')
				class_file.write(keyword)
				class_file.write('\n')
		if label==3:
			with open(os.path.join(result_dir, 'class3.txt'), 'a') as class_file:
				class_file.write(filename+': ')
				class_file.write(keyword)
				class_file.write('\n')
	# 		if label != -1:
	# 			HF_reports.remove(filename)
	# 			with open(os.path.join(result_dir, 'HF_labelled.txt'), 'a') as labelled_HF_file:
	# 				labelled_HF_file.write(filename+'\n')

	# with open(os.path.join(result_dir, 'HF_unlabelled.txt'), 'w') as unlabelled_HF_file:
	# 	for filename in HF_reports:
	# 		unlabelled_HF_file.write(filename+'\n')


if __name__ == '__main__':

	current_path = os.path.dirname(os.path.abspath(__file__))
	default_negated_keywords_path = os.path.join(current_path, 'keywords',
												 'miccai2020', 'keywords_negated.tsv')
	default_affirmed_keywords_path = os.path.join(current_path, 'keywords',
												  'miccai2020', 'keywords_affirmed.tsv')
	default_mentioned_keywords_path = os.path.join(current_path, 'keywords',
												  'miccai2020', 'keywords_mentioned.tsv')
	default_report_dir = os.path.join(current_path, 'example_data')
	default_chf_metadata_path = os.path.join(current_path, 'mimic_cxr_heart_failure',
									'mimic_cxr_metadata_hf.tsv')

	parser = argparse.ArgumentParser()

	parser.add_argument(
		'--negated_keywords_path',
		default=default_negated_keywords_path,
		help='the .tsv file that has keyword terms for labeling pulmonary edema severity '\
			 'in a negated fashion')
	parser.add_argument(
		'--affirmed_keywords_path',
		default=default_affirmed_keywords_path,
		help='the .tsv file that has keyword terms for labeling pulmonary edema severity '\
			 'in an affirmed fashion')
	parser.add_argument(
		'--mentioned_keywords_path',
		default=default_mentioned_keywords_path,
		help='the .tsv file that has keyword terms for labeling pulmonary edema severity '\
			 'in a mentioned fashion')
	parser.add_argument(
		'--report_dir',
		default=default_report_dir,
		help='the directory that contains reports for regex labeling')
	parser.add_argument(
		'--limit_in_chf',
		default=True,
		help='whether to limit the cohort to congestive heart failure')
	parser.add_argument(
		'--chf_metadata_path',
		default=default_chf_metadata_path,
		help='the .tsv file that has congestive heart failure diagnosis information '\
			 'for MIMIC-CXR data')

	main(args=parser.parse_args())



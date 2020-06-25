import os
import argparse
import pandas as pd
import re
from regex_utils import WordMatch

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
		print("There are {} CHF radiology studies!".format(len(chf_study_ids)))

	labeled_files = {}
	regex_labels = {}
	c = 0
	c_regex = 0
	c_labels = [0,0,0,0]

	for filename in os.listdir(args.report_dir):
		if args.limit_in_chf and filename[1:9] not in chf_study_ids:
			continue

		c_regex += 1
		if c_regex%100 == 0:
			print("{} reports have been processed!".format(c_regex))

		report_path = os.path.join(args.report_dir, filename)
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
		default=False, action='store_true',
		help='whether to limit the cohort to congestive heart failure')
	parser.add_argument(
		'--chf_metadata_path',
		default=default_chf_metadata_path,
		help='the .tsv file that has congestive heart failure diagnosis information '\
			 'for MIMIC-CXR data')

	main(args=parser.parse_args())


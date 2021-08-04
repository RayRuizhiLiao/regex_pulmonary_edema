#!/usr/bin/env python
# coding: utf-8

# 
# 
# - get most frequent/interesting phrases from chf cohort reports

# In[1]:



import sys
sys.path.append("../../notebooks")

import utils
utils.jpt_autoreload()
utils.jpt_full_width()
utils.jpt_suppress_warnings()


# In[27]:


import os, re, time
import pandas as pd
import numpy as np

from label_reports import get_chf_cohort, label_report
import negex
from regex_utils import WordMatch
from section_parser import section_text
from extract_findings import extract_findings

from tabulate import tabulate
from pprint import pprint

from datasets import MimicCxrLabels, MimicCxrReader, MimicCxrBase


# In[34]:


cxr_reader = MimicCxrReader()
cxr_labels = MimicCxrLabels()


# In[21]:



keywords = [ 
    'acute cardiopulmonary process',
    'focal consolidation',
    'pleural effusion',
    'pneumothorax',
    'nodular opacities',
    'pneumonia'
]


# In[26]:


cohort = 'all'
current_path = '.'
chf_metadata_path = os.path.join(
    current_path, 'mimic_cxr_heart_failure', 'mimic_cxr_metadata_hf.tsv')

if cohort == 'all':
    meta_df = MimicCxrBase().get_meta_df()
    study_ids = meta_df['study_id'].unique()
else:
    meta_df = pd.read_csv(chf_metadata_path, sep='\t')
    meta_df = meta_df[meta_df['heart_failure'] == 1]
    study_ids = meta_df['study_id'].unique()
    


# In[58]:


# study_id = 54577367
# report = cxr_reader.get_report(study_id)

# def section_finding(report):
#     sections, section_names, section_idx = section_text(report)
#     if 'findings' in section_names:
#         ind = section_names.index('findings')
#         return sections[ind]
#     else:
#         ""
# section = section_finding(report)


# data = {}
# data[study_id] = section

# df = pd.DataFrame.from_dict(data, columns=['findings'],orient='index')
# df


# In[63]:


data = {}

start = time.time()
for i, study_id in enumerate(study_ids):

    try:
        report = cxr_reader.get_report(study_id)
        section = section_finding(report)
        data[study_id] = section
    except:
        continue

    if i%1000 == 0:
        end = time.time()
        print(f'Iter={i}\tTime Elapsed={end-start:.3f}')
        start = time.time()

        
df = pd.DataFrame.from_dict(data, columns=['findings'],orient='index')
df.to_csv(f'note_findings_wordfreq_findings_{cohort}_df', index=True)
print(len(df))


# In[80]:





# In[83]:


import nltk

from nltk.collocations import *
bigram_measures = nltk.collocations.BigramAssocMeasures()
trigram_measures = nltk.collocations.TrigramAssocMeasures()

text = '\n'.join([x for x in df['findings'].to_list() if x is not None])
print(len(text))

tokens = nltk.wordpunct_tokenize(text)
print(len(tokens))


# In[89]:



finder = BigramCollocationFinder.from_words(tokens)

# finder
# # # only bigrams that appear 3+ times
finder.apply_freq_filter(500)

# return the 10 n-grams with the highest PMI
ngrams = finder.nbest(bigram_measures.pmi, 100)
ngrams


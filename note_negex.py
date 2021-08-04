#!/usr/bin/env python
# coding: utf-8

# In[51]:


# %matplotlib inline
import sys
sys.path.append("../../notebooks")

import utils
utils.jpt_autoreload()
utils.jpt_full_width()
utils.jpt_suppress_warnings()


# In[53]:


import os
import pandas as pd
import numpy as np

from label_reports import get_chf_cohort, label_report
from regex_utils import WordMatch

from datasets import MimicCxrLabels, MimicCxrReader, MimicCxrBase


# In[50]:


cxr_labels = MimicCxrLabels()
cxr_reader = MimicCxrReader()
meta_df = MimicCxrBase().get_meta_df()


# In[46]:


current_path = '.'
# keyword terms for labeling pulmonary edema severity in a negated fashion
#

keywords_version = 'miccai2020_nopacities' # 'miccai2020'
opacitiesdeconfound = False
negprec = False

# pulmonary_edema_severity	keyword_terms
# 0	pulmonary edema
# 0	vascular congestion 
# 0	fluid overload
# 0	acute cardiopulmonary process
negated_keywords_path = os.path.join(current_path, 'keywords', keywords_version, 'keywords_negated.tsv')
#
# keyword terms for labeling pulmonary edema severity in a affirmed fashion
# pulmonary_edema_severity	keyword_terms
# 1	cephalization
# 1	pulmonary vascular congestion
# 1	hilar engorgement
# etc.
affirmed_keywords_path = os.path.join(current_path, 'keywords', keywords_version, 'keywords_affirmed.tsv')
#
# keyword terms for labeling pulmonary edema severity in a mentioned fashion
# pulmonary_edema_severity	keyword_terms
# 0	no pulmonary edema
# 0	no vascular congestion
# 0	no fluid overload
# 0	no acute cardiopulmonary process
mentioned_keywords_path = os.path.join(current_path, 'keywords', keywords_version, 'keywords_mentioned.tsv')

opacity_keywords = [
    'interstitial opacities',
    'parenchymal opacities',
    'alveolar opacities',
    'ill defined opacities',
    'ill-defined opacities',
    'patchy opacities',
]


# the directory that contains reports for regex labeling
report_dir = os.path.join(current_path, 'example_data')
# CHF diagnosis information for mimic-cxr data
chf_metadata_path = os.path.join(current_path, 'mimic_cxr_heart_failure', 'mimic_cxr_metadata_hf.tsv')
# whether to limit the cohort to congestive heart failure
limit_to_chf = True


df_n = pd.read_csv(negated_keywords_path,  sep="\t")
df_a = pd.read_csv(affirmed_keywords_path, sep="\t")
df_m = pd.read_csv(mentioned_keywords_path, sep="\t")

def keywords_label_to_list(df):
    return df['pulmonary_edema_severity'].to_list(), df['keyword_terms'].to_list()

df_chf = pd.read_csv(chf_metadata_path, sep='\t')
if limit_to_chf:
    df_chf = df_chf[df_chf['heart_failure'] == 1]
chf_study_ids = df_chf['study_id'].unique()
print(len(chf_study_ids))


# In[47]:


df = cxr_labels.df
dft = df[(df['split']=='test_consensus_image')&(df['EdemaSeverity'].notnull())]
SId, studlabels_prev = dft[['study_id', 'EdemaSeverity']]
labels_prev = dft[['study_id', 'EdemaSeverity']].set_index('study_id')['EdemaSeverity'].to_dict()
# labels_prev = {53842858: 0}
# labels_prev = [  # previous labeling is
#	(54462999, 0), # determines interstitial opacities=2, but in fact is mild pulmonry edema ... just removes 
#	(51581379, 0), # hits vascular prominence=1
#	(57851930, 0), # interval resolution of mild interstitial edema
#	(55695728, 2), 
#	(55918606, 0),
#	(59195601, 0),
#	(57542211, 0), # current is fine 
#	(59351052, 0), # current is fine
# ]


# In[ ]:





# In[48]:


labeled_study_ids = {}
regex_labels = {}
relevant_keywords = {}
c = 0
c_regex = 0
c_labels = [0,0,0,0]

import time

start = time.time()

# for i, (study_id, l) in enumerate(labels_prev.items()):
# for i, (study_id, l) in enumerate(labels_prev):
for i, study_id in enumerate(df_chf['study_id'].unique()):
    study_id = int(study_id)

    c_regex += 1
    if c_regex%1000 == 0:
        print("{} reports have been processed!".format(c_regex))

    try:
        report = cxr_reader.get_report(study_id, remove_nextline=True)
    except:
        continue

    
    # if has atlectasis/pneumonia, then do not use opacities for keyword search
    
    if opacitiesdeconfound:
        
        dicom_id = cxr_labels.df[cxr_labels.df['study_id']==study_id]['dicom_id'].to_list()
        if len(dicom_id) != 0:
            chex_labels = cxr_labels.get_chexpert_labels([dicom_id[0]])
            has_confonding_variables = np.any(chex_labels[0,[0,11]]==1)
            edema_binary = chex_labels[0,3]
            if has_confonding_variables:
                df_a_ = df_a[~df_a['keyword_terms'].isin(opacity_keywords)]
            else:
                df_a_ = df_a
    else:
        df_a_ = df_a

    severities, keywords = keywords_label_to_list(df_a_)
    label_a, severity_keywords_a = label_report(
        report, severities, keywords, tag='affirmed')

    severities, keywords = keywords_label_to_list(df_n)
    label_n, severity_keywords_n = label_report(
        report, severities, keywords, tag='negated')
    
    severities, keywords = keywords_label_to_list(df_m)
    label_m, severity_keywords_m = label_report(
        report, severities, keywords, tag='mentioned')
    

    # Negated condition takes precedence.
    # Otherwise, takes the most severe condition
    
    if negprec:
        if label_n == 0:
            label = 0
        else:
            label = max([label_a, label_n, label_m])
    else:
        label = max([label_a, label_n, label_m])

    if label != -1:
        c += 1
        relevant_keywords[c] = severity_keywords_a[label] + severity_keywords_n[label] + severity_keywords_m[label]
        labeled_study_ids[c] = study_id
        regex_labels[c] = label
        c_labels[label] += 1
        

        
end = time.time()
print(f'took {end-start:.2}s')
        
        

regex_df = pd.DataFrame(
    {'study_id': labeled_study_ids,
     'regex_label': regex_labels,
     'relevant_keywords': relevant_keywords})
output_csv_path = f'regex_results_{keywords_version}_negprec={negprec}_opacitiesdeconfound={opacitiesdeconfound}.tsv'
regex_df.to_csv(output_csv_path, sep="\t")

regex_df

# 
# 1	mild pulmonary edema ?
# 2 moderate pulmonary edema ?


# In[49]:


# edema_df = cxr_labels.get_edema_df()
# edema_df = edema_df[['dicom_id', 'EdemaSeverity']]
# dfm = pd.merge(edema_df, regex_df, how='right', on=['dicom_id'], suffixes=('_regex', '_ci'))
consensus_df = pd.read_csv(
    '/data/vision/polina/scratch/wpq/github/interpretability/notebooks/data/MimicCxrDataset/consensus_image_edema_severity.csv')
dfm = pd.merge(consensus_df, regex_df, how='right', on=['study_id'])
print(f"{len(dfm[dfm['edema_severity']!=dfm['regex_label']])}/{len(dfm)} changed labels from regex to consensus image")

# Table
a = np.zeros((4,4))
for x in range(4):
    for y in range(4):
        dfs = dfm[(dfm['regex_label']==x)&(dfm['edema_severity']==y)]
        a[x,y]=len(dfs)
        
        if x == 0 and y == 2 and len(dfs)>0:
            print(dfs['study_id'].to_list()[0])
        
from tabulate import tabulate
print(output_csv_path)
print(tabulate(np.hstack((np.arange(4).reshape(-1,1), a)), headers=['regex->ci', 0,1,2,3]))


# regex_results_miccai2020
# 76/132 changed labels from regex to consensus image
#   regex->ci    0    1    2    3
# -----------  ---  ---  ---  ---
#           0   25    8    0    1
#           1   11   15    5    4
#           2    8   10    7    2
#           3   11    9    7    9
#
# 74/132 changed labels from regex to consensus image
# regex_results_miccai2020_negprec=True_opacitiesdeconfound=False.tsv
#   regex->ci    0    1    2    3
# -----------  ---  ---  ---  ---
#           0   28   10    3    2
#           1   10   14    4    3
#           2    7   10    7    2
#           3   10    8    5    9
#
# 65/121 changed labels from regex to consensus image
# regex_results_miccai2020_negprec=True_opacitiesdeconfound=True.tsv
#   regex->ci    0    1    2    3
# -----------  ---  ---  ---  ---
#           0   28   10    3    2
#           1   10   14    4    3
#           2    7   10    8    2
#           3    7    5    2    6
#
# 67/121 changed labels from regex to consensus image
# regex_results_miccai2020_negprec=False_opacitiesdeconfound=True.tsv
#   regex->ci    0    1    2    3
# -----------  ---  ---  ---  ---
#           0   25    9    0    1
#           1   11   15    5    4
#           2    8   10    8    2
#           3    8    5    4    6

# # remove opacities keyword
# 92/141 changed labels from regex to consensus image
#   regex->ci    0    1    2    3
# -----------  ---  ---  ---  ---
#           0   26    9    2    1
#           1   11   15    5    4
#           2    9   10    8    2
#           3    0    0    0    0   


# In[11]:


# df = cxr_labels.df
# dft = df[(df['split']=='train')&(df['EdemaSeverity'].notnull())]
# # dft = df[df['EdemaSeverity'].notnull()]
# SId, studlabels_prev = dft[['study_id', 'EdemaSeverity']]
# counts = 0
# for i, (study_id, l) in enumerate(dft[['study_id', 'EdemaSeverity']].set_index('study_id')['EdemaSeverity'].to_dict().items()):

#     if i%1000 == 0:
#         print("{} reports have been processed!".format(i))

#     report = cxr_reader.get_report(study_id, remove_nextline=True)
# #     if 'severe pulmonary edema' in report:
#     if 'patchy opacities' in report:
#         counts += 1
        
# print(counts)
        
        
# # 35 reports in training has alveolar opacities

# # parenchymal opacities
# # train: 223, all: 278
# # patchy opacities
# # train: 74, all: 100


# In[45]:


# # negprec ... some makes sense, some not ... will only hurt pulmonary vascular congestion but otherwise helps reduce opacities FP
# # 58988106   Right upper lobe parenchymal opacities are grossly unchanged from ___.  No superimposed acute cardiopulmonary process.
# # 51397090
# # 50145470   Unchanged pulmonary vascular congestion without overt pulmonary edema. ... 
# # 53919055   Pulmonary vascular congestion without overt pulmonary edema.
# # 50762469   pulmonary vascular congestion
# # 52853233   
# # 54393504   Chronic changes in the lungs without definite superimposed acute  cardiopulmonary process.
# # 54594082   Patchy opacities in the lung bases may reflect atelectasis though infection, no overt pulmonary edema. 
# # 52549668   No definitive evidence of acute cardiopulmonary process. 
# study_id = 54594082
# print(cxr_reader.get_report(study_id))

# if opacitiesdeconfound:
#     chex_labels = cxr_labels.get_chexpert_labels(
#         [cxr_labels.df[cxr_labels.df['study_id']==study_id]['dicom_id'].to_list()[0]])
#     has_confonding_variables = np.any(chex_labels[0,[0,11]]==1)
#     edema_binary = chex_labels[0,3]
#     if has_confonding_variables:
#         df_a_ = df_a[~df_a['keyword_terms'].isin(opacity_keywords)]
#     else:
#         df_a_ = df_a
# else:
#     df_a_ = df_a

# severities, keywords = keywords_label_to_list(df_a_)
# label_a, severity_keywords_a = label_report(
#     report, severities, keywords, tag='affirmed')

# severities, keywords = keywords_label_to_list(df_n)
# label_n, severity_keywords_n = label_report(
#     report, severities, keywords, tag='negated')

# severities, keywords = keywords_label_to_list(df_m)
# label_m, severity_keywords_m = label_report(
#     report, severities, keywords, tag='mentioned')

# print(label_a, label_n, label_m)


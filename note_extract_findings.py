#!/usr/bin/env python
# coding: utf-8

# In[2]:


# %matplotlib inline
import sys
sys.path.append("../../notebooks")

import utils
utils.jpt_autoreload()
utils.jpt_full_width()
utils.jpt_suppress_warnings()


# In[10]:


import os, re, time
import pandas as pd
import numpy as np

from label_reports import get_chf_cohort, label_report
import negex
from regex_utils import WordMatch
from section_parser import section_text
from extract_findings import extract_findings

from tabulate import tabulate
from datasets import MimicCxrLabels, MimicCxrReader, MimicCxrBase


# In[4]:



def assign_label(row):
    # Assign label for a keyword's word match result
    #
    #  neg aff
    #  [0. 0.]  ->  nan
    #  [0. 1.]  ->  1
    #  [1. 0.]  ->  0
    #  [1. 1.]  ->  nan
    #
    if sum(row) == 1:
        return row[1]
    else:
        return np.nan


def filter_sections(report):
    # Remove text in INDICATION section ... 
    #     as it might contain keywords which contains keywords 
    #     but does not mean existence of keywords
    # 
    sections, section_names, section_idx = section_text(report)
    filtered = [i for i,x in enumerate(section_names) 
                if x not in ['indication', 'history', 'comparison', 'technique']]
    report = "".join(sections[i] for i in filtered)
    report = report.replace('\n','').replace('\r','')
    return report
    

def cols_value_counts(df):
    C = df.apply(lambda col: pd.Series.value_counts(col, dropna=False))
    C = C.transpose()
    C = C.replace({np.nan: 0})
#     C = C.sort_values(by=[np.nan])
    return C


    


# In[5]:


cxr_labels = MimicCxrLabels()
cxr_reader = MimicCxrReader()
meta_df = MimicCxrBase().get_meta_df()


# In[20]:



# cohort \in [ 'all',  'chf' ]
#               224k    28k 
cohort = 'all'

# current path
current_path = '.'

# chf diagnosis information for mimic-cxr data
chf_metadata_path = os.path.join(current_path, 'mimic_cxr_heart_failure', 'mimic_cxr_metadata_hf.tsv')

# negex
negex_trigger_path = os.path.join(current_path, 'negex', 'negex_triggers.txt')

# keywords
keywords_version = 'miccai2020'
neg_kwd_path = os.path.join(
    current_path, 'keywords', keywords_version, 'keywords_negated.tsv')
aff_kwd_path = os.path.join(
    current_path, 'keywords', keywords_version, 'keywords_affirmed.tsv')

# save resulting labels
df_save_path = os.path.join(current_path, f'negex_findings_version={keywords_version}_cohort={cohort}_v2.csv')


# In[12]:


df_neg = pd.read_csv(neg_kwd_path, sep="\t")
df_aff = pd.read_csv(aff_kwd_path, sep="\t")

aff_kwd = df_aff['keyword_terms'].to_list()
neg_kwd = df_neg['keyword_terms'].to_list()


kwd_to_severities = df_aff.set_index('keyword_terms').to_dict()['pulmonary_edema_severity']
kwd_to_severities.update(df_neg.set_index('keyword_terms').to_dict()['pulmonary_edema_severity'])
kwd_to_severities

keywords = neg_kwd + aff_kwd
keywords = [ 'pulmonary edema',
             'mild pulmonary edema',
             'moderate pulmonary edema',
             'vascular congestion',
             'fluid overload',
             'acute cardiopulmonary process',
             'cephalization',
             'pulmonary vascular congestion',
             'hilar engorgement',
             'vascular plethora',
             'pulmonary vascular prominence',
             'pulmonary vascular engorgement',
             'kerley',
             'interstitial edema',
             'interstitial thickening',
             'interstitial pulmonary edema',
             'interstitial marking',
             'interstitial abnormality',
             'interstitial abnormalities',
             'interstitial process',
             'alveolar infiltrates',
             'severe pulmonary edema',
             'perihilar infiltrates',
             'hilar infiltrates',
             'interstitial opacities',
             'parenchymal opacities',
             'alveolar opacities',
             'ill defined opacities',
             'patchy opacities'
           ]

keywords = keywords + ['no '+x for x in keywords]
keywords


# In[14]:


# `meta_df` restrict to chf cohort
cohort = 'all'
if cohort == 'all':
    meta_df = MimicCxrBase().get_meta_df()
    study_ids = meta_df['study_id'].unique()
elif cohort == 'chf':
    meta_df = pd.read_csv(chf_metadata_path, sep='\t')
    meta_df = meta_df[meta_df['heart_failure'] == 1]
    study_ids = meta_df['study_id'].unique()

print(f"#study_id = {len(study_ids)}")

print(cxr_reader.get_report(study_ids[10]))


# In[23]:


labels = {}
start = time.time()

for i, study_id in enumerate(study_ids):
    
    try:
        report = cxr_reader.get_report(study_id)
    except:
        continue

    label = extract_findings(report, keywords)
    labels[study_id] = label

    if i%1000 == 0:
        end = time.time()
        print(f'Iter={i}\tTime Elapsed={end-start:.3f}')
        start = time.time()
        
        
df = pd.DataFrame.from_dict(labels, orient='index', columns=keywords)
df = df.rename_axis('study_id').reset_index()
print(len(df))


# In[24]:


df.to_csv(df_save_path, index=False)
print(f'saved to {df_save_path}')


# In[9]:


# take a look at summary statistics
#
def cols_value_counts(df):
    C = df.apply(lambda col: pd.Series.value_counts(col, dropna=False))
    C = C.transpose()
    C = C.replace({np.nan: 0})
    C_index = C.index
    C['severity'] = [kwd_to_severities[idx] if idx in kwd_to_severities else np.nan for idx in C_index]
    C = C.sort_values(by=['severity'])
    return C

df_save_path = './negex_findings_version=miccai2020_nopacities_cohort=all.csv'
# df_save_path = './negex_findings_version=miccai2020_nopacities_cohort=chf.csv'
df = pd.read_csv(df_save_path)
C = cols_value_counts(df.iloc[:,1:])

# C = C[(C[0]+C[1])>500]
label_names = C.index.to_list()
label_remove = [
    'cephalization',
    'hilar engorgement',
    'vascular plethora',
    'pulmonary vascular prominence',
    'interstitial process',
    'interstitial abnormalities',
    'interstitial pulmonary edema',
    'interstitial thickening',
    'kerley',
    'ill defined opacities',
    'alveolar infiltrates',
    'perihilar infiltrates',
    'hilar infiltrates',
]
df = df[list(set(label_names)-set(label_remove))]


C = cols_value_counts(df.iloc[:,1:])


print(tabulate(C, headers=['findings'] + [str(x) for x in list(C.columns)]))


# In[64]:




def cols_value_counts(df):
    C = df.apply(lambda col: pd.Series.value_counts(col, dropna=False))
    C = C.transpose()
    C = C.replace({np.nan: 0})
    C = C.sort_values(by=[np.nan])
    return C


def proc_findings_labels(df, thresh=500, unwanted_cols = ['pulmonary edema']):

    # thresholding entries with >thresh number of samples
    C = cols_value_counts(df.iloc[:,1:])
    C = C[(C[0]+C[1])>thresh]
    label_names = C.index.to_list()

    # remove unwanted labels
    label_names = list(set(label_names)-set(unwanted_cols))

    # filter columns
    df_f = df[['study_id']+label_names]

    # randomly sample minor class to match major class
    #    so that #samples with 0/1 are the same
    #
    for l in label_names:
        addv = 0 if (C.loc[l,0] < C.loc[l,1]) else 1
        addn =  int(np.abs(C.loc[l,0] - C.loc[l,1]))
        addIdx = np.random.choice(df_f[df_f[l].isnull()].index, size=addn, replace=False)
        df_f.iloc[addIdx, df_f.columns.get_loc(l)] = addv
        
    return df_f


df_f = proc_findings_labels(df)

C = cols_value_counts(df_f.iloc[:,1:])
print(tabulate(C, headers=['findings'] + [str(x) for x in list(C.columns)]))


# In[10]:


df_ = df[df['kerley']==0]


for i, study_id in enumerate(df_['study_id']):
    
    print('----------------------------------------')
    print(cxr_reader.get_report(study_id))
    print(df_.iloc[i,:][df_.iloc[i,:].notnull()])
    
    if i > 10:
        break


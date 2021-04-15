import os, re
import numpy as np

from regex_utils import WordMatch
from section_parser import section_text


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
    

def extract_findings(report, keywords):

    report = filter_sections(report)
    sentences = re.split('\.|\:', report)

    # (#keywords, #tags, #sentences)
    #     where tags = [negated, affirmed]
    T = np.zeros((len(keywords), 2, len(sentences)))

    for si, sentence in enumerate(sentences):
        word_match = WordMatch(sentence, keywords)
        kwd_aff = word_match.mention_positive()
        kwd_neg = word_match.mention_negative()
        for ki, k in enumerate(keywords):
            T[ki,0,si] = kwd_neg[k]
            T[ki,1,si] = kwd_aff[k]

    # aggregate results wrt sentences in reports
    T = np.amax(T, axis=2)
    label = np.apply_along_axis(assign_label, axis=1, arr=T)
    assert(label.size == len(keywords))

    return label



keywords = [ 
    'acute cardiopulmonary process',
    'focal consolidation',
    'pleural effusion',
    'pneumothorax',
    'nodular opacities',
    'pneumonia'
]

report = \
"""
                              FINAL REPORT
EXAMINATION:  CHEST (PA AND LAT)

INDICATION:  ___F with new onset ascites  // eval for infection

TECHNIQUE:  Chest PA and lateral

COMPARISON:  None.

FINDINGS: 

There is no focal consolidation, pleural effusion or pneumothorax.  Bilateral
nodular opacities that most likely represent nipple shadows. The
cardiomediastinal silhouette is normal.  Clips project over the left lung,
potentially within the breast. The imaged upper abdomen is unremarkable.
Chronic deformity of the posterior left sixth and seventh ribs are noted.

IMPRESSION: 

No acute cardiopulmonary process.
"""


label = extract_findings(report, keywords)
for i in range(len(keywords)):
    print(f'{keywords[i]:40}\t {label[i]}')
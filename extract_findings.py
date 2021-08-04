import os, re
import numpy as np
import pandas as pd

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


def combine_label_synonyms(x, y):
    """ Combine label, 
        x    y    output
        0    0    0
        1    0    nan
        0    1    nan
        1    1    1
        nan  0/1  0/1
        0/1  nan  0/1
        
        ```
            df = pd.DataFrame({'x': [0,1,0,1,np.nan,1],'y': [0,0,1,1,0,np.nan]})
            df.agg(lambda row: combine_label_synonyms(row['x'], row['y']), axis=1)
            # 0    0.0
            # 1    NaN
            # 2    NaN
            # 3    1.0
            # 4    0.0
            # 5    1.0
        ```
    """
    x_notnull = not np.isnan(x)
    y_notnull = not np.isnan(y)
    if x_notnull and y_notnull:
        if x == y:
            return x
        else:
            return np.nan
    else:
        if x_notnull:
            return x
        else:
            return y
        
def merge_2cols(df, col1, col2):
    # merge col1 to col2
    df[col2] = df.agg(lambda row: combine_label_synonyms(row[col1], row[col2]), axis=1)
    return df

def cols_value_counts(df):
    C = df.apply(lambda col: pd.Series.value_counts(col, dropna=False))
    C = C.transpose()
    C = C.replace({np.nan: 0})
    C_index = C.index
    return C


if __name__ == '__main__':

    keywords = [ 
        'acute cardiopulmonary process',
        'no focal consolidation',
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

    keywords = ['perihilar vessels']
    report = \
    """
                                    FINAL REPORT
EXAMINATION:  CHEST (PORTABLE AP)

INDICATION:  History: ___F with sob, prior effusion, hypoxia  // eval effusion

COMPARISON:  ___

IMPRESSION: 

As compared to the previous radiograph, there is substantial increase in
extent of a pre-existing right pleural effusion.  The effusion now occupies
approximately ___% of the right hemithorax, causing extensive atelectasis at
the right lung bases.  On the left, the elevation of the hemidiaphragm, that
pre existed, has also increased.  The precise size the cardiac silhouette can
no longer be determined.  Increases in diameter of the perihilar vessels
suggest the presence of mild pulmonary edema.
    """


    label = extract_findings(report, keywords)
    for i in range(len(keywords)):
        print(f'{keywords[i]:40}\t {label[i]}')

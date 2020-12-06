# regex_pulmonary_edema

Regular expression (Regex) for extracting pulmonary edema severity from radiology reports.

This repository incorporates the regex algorithms presented in the following publications:

R. Liao et al. Semi-supervised learning for quantification of pulmonary edema in chest x-ray images. *arXiv preprint arXiv:1902.10785*, 2019.

S. Horng<sup>\*</sup>, R. Liao<sup>\*</sup> et al. Deep Learning to Quantify Pulmonary Edema in Chest Radiographs. *Radiology AI* (under review). *arXiv preprint arXiv:2008.05975*, 2020. <br />
(<sup>\*</sup> indicates equal contribution)

G. Chauhan<sup>\*</sup>, R. Liao<sup>\*</sup> et al. Joint Modeling of Chest Radiographs and Radiology Reports for Pulmonary Edema Assessment. *International Conference on Medical Image Computing and Computer-Assisted Intervention*, 2020. <br />
(<sup>\*</sup> indicates equal contribution)

# MIMIC-CXR

The [MIMIC Chest X-ray (MIMIC-CXR) Database](https://physionet.org/content/mimic-cxr/2.0.0/) is a large publicly available dataset of chest radiographs in DICOM format with free-text radiology reports. The dataset contains 377,110 images corresponding to 227,835 radiographic studies performed at the Beth Israel Deaconess Medical Center in Boston, MA.

We recommend that you use regex on selected sections in the radiology reports, such as "FINDINGS", "IMPRESSION".

# CHF and pulmonary edema severity

The regex keyword terms are used for pulmonary edema assessment in the context of congestive heart failure (CHF). We aim to extract pulmonary edema severity assessment from radiology reports as 4 ordinal levels: no edema (0), vascular congestion (1), interstitial edema (2), and alveolar edema (3). 

We recommend that you use regex on radiology reports written during CHF visits, in order to limit confounding from other disease processes.

CHF diagnosis information for [MIMIC-CXR](https://physionet.org/content/mimic-cxr/2.0.0/) can be found in the submodule of [mimic_cxr_heart_failure](https://github.com/RayRuizhiLiao/mimic_cxr_heart_failure). To add this submodule, run the following line in your git repository:

<code> git submodule update --init --recursive </code>

# Example Usage

<code> python label_reports.py --limit_in_chf --report_dir=./example_data/ </code>

# Contact

Ruizhi Liao: ruizhi [at] mit.edu

# Acknowledgement

We built this regex algorithm based on the negation detection algorithm desigend by Wendy Chapman et al. and implemented by Peter Kang.

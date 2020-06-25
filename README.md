# regex_pulmonary_edema

Regex for extracting pulmonary edema severity from radiology reports.

This repository incorporates the regex algorithms presented in the following publications:

R. Liao, et al. Semi-supervised learning for quantification of pulmonary edema in chest x-ray images. *arXiv preprint arXiv:1902.10785*, 2019.

S. Horng<sup>\*</sup>, R. Liao<sup>\*</sup> et al. Deep Learning to Quantify Pulmonary Edema in Chest Radiographs. *Radiology AI* (under review). <br />
(<sup>\*</sup> indicates equal contribution)

G. Chauhan<sup>\*</sup>, R. Liao<sup>\*</sup> et al. Joint Modeling of Chest Radiographs and Radiology Reports for Pulmonary Edema Assessment. *International Conference on Medical Image Computing and Computer-Assisted Intervention*, 2020. <br />
(<sup>\*</sup> indicates equal contribution)

# Congestive Heart Failure

The regex keyword terms are used for pulmonary edema assessment in the context of congestive heart failure (CHF).

We recommend that you use regex on radiology reports written during CHF visits, in order to limit confounding from other disease processes.

CHF diagnosis information for [MIMIC-CXR](https://physionet.org/content/mimic-cxr/2.0.0/) can be found in the submodule of [mimic_cxr_heart_failure](https://github.com/RayRuizhiLiao/mimic_cxr_heart_failure). To add this submodule, run the following line in your git repository:

<code> git submodule update --init --recursive </code>

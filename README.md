# c-arm cardiac imaging: reconstruction 

**1. config_parser.py: DICOM/uCT config file parser**

`python config_parser.py XA_00001`

**User input:**  path to uCT config file || path to DICOM file   
**Output:** .json file with data required for the reconstruction (./configs folder)



**2. run_recon.py: reconstruction module using FDK method (CIL framework)**

`python run_recon.py XA_00001_ ./configs/XA_00001.json`

**User input:**  (1) path to DICOM file || path to folder with .raw uCT projections; (2) path to .json config file  
**Output:** 3D reconstruction image saved as .nii (./results folder)


**cil.yaml:** anaconda env with all required packages 


import pydicom
import argparse
import xml.etree.ElementTree as ET
import numpy as np
import os
import json

if __name__ == "__main__":
    """ Params: set by user """
    #path = './data_XA_00010'

    # Instantiate the parser
    parser = argparse.ArgumentParser()
    parser.add_argument('filename',
                    help='Path to DICOM/config file')
    args = parser.parse_args()

    if pydicom.misc.is_dicom(args.filename):
        dcm_img = pydicom.dcmread(args.filename)

        cfg_json = [
            {
                'distance_source_to_patient':dcm_img.DistanceSourceToPatient,
                'distance_source_to_detector': dcm_img.DistanceSourceToDetector,
                'positioner_primary_angle_increment': np.array(dcm_img.PositionerPrimaryAngleIncrement).tolist(),
                'image_pixel_spacing': np.array(dcm_img.ImagerPixelSpacing).tolist(),
                'detector_pixel_spacing': np.array(dcm_img.ImagerPixelSpacing).tolist(),
                'number_of_frames': dcm_img.NumberOfFrames,
                'voxel_size': dcm_img.ImagerPixelSpacing[0]*dcm_img.DistanceSourceToDetector/dcm_img.DistanceSourceToPatient,
                'num_pixel_x': dcm_img.Rows,
                'num_pixel_y': dcm_img.Colums,
                'num_pixel_z': dcm_img.NumberOfFrames,
                'patient_ID': dcm_img.PatientID,
                'raw_header_size': []
            }
        ]
    else:
        tree = ET.parse(args.filename)
        root_tree = tree.getroot()
        projection_description = root_tree.find('ProjectionDescritpion')  # Projection descritpion
        axial_CT_recipe_parameter = root_tree.find('AxialCTRecipeParameter')
        project_description = root_tree.find('ProjectDescritpion')  # Project descritpion

        cfg_json = [
            {
                'distance_source_to_patient': float(axial_CT_recipe_parameter.get('FOD')),
                'distance_source_to_detector': float(axial_CT_recipe_parameter.get('FDD')),
                'positioner_primary_angle_increment': np.array(np.linspace(float(axial_CT_recipe_parameter.get('StartAngle')), float(axial_CT_recipe_parameter.get('EndAngle')) , int(int(axial_CT_recipe_parameter.get('NoLoops'))))).tolist(),
                'image_pixel_spacing':np.array([int(projection_description.get('PixelSizeX')),
                        int(projection_description.get('PixelSizeY'))]).tolist(),
                'detector_pixel_spacing': np.array([int(projection_description.get('PixelSizeX')),
                        int(projection_description.get('PixelSizeY'))]).tolist(),
                'number_of_frames': int(int(axial_CT_recipe_parameter.get('NoLoops'))),
                'voxel_size': int(projection_description.get('PixelSizeX'))*float(axial_CT_recipe_parameter.get('FDD'))/float(axial_CT_recipe_parameter.get('FOD')),
                'num_pixel_x': int(int(projection_description.get('NumPixelX'))),
                'num_pixel_y': int(int(projection_description.get('NumPixelY'))),
                'num_pixel_z': int(int(axial_CT_recipe_parameter.get('NoLoops'))),
                'patient_ID': project_description.get('SampleName'),
                'raw_header_size': int(int(projection_description.get('RawHeaderSize')))
            }
        ]

    if not os.path.isdir('./configs/'):
        os.makedirs('./configs/')

    with open('./configs/' + args.filename.split('.')[0] + '.json', 'w') as f:
        json.dump(cfg_json, f)

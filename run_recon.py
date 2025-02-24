from cil import io, framework, recon
import pydicom
import matplotlib.pyplot as plt
from cil.utilities.display import show_geometry
from cil.utilities.jupyter import islicer
from cil.processors import Padder, RingRemover, AbsorptionTransmissionConverter, TransmissionAbsorptionConverter
import scipy
import numpy as np
from cil.optimisation.operators import BlurringOperator
from cil.utilities import noise
import os
import numpy as np
import matplotlib.pyplot as plt
import xml.etree.ElementTree as ET
import pydicom
from pydicom.dataset import Dataset, FileDataset
import datetime
import sys
import argparse
import json

""" Config data incl. reconstruction geometry for FDK CIL """
class Config:
    def __init__(self, distance_source_origin, distance_origin_detector, detector_pixel_size, image_pixel_spacing,
                 num_projections, angles, voxel_size, num_pixel_x, num_pixel_y, num_pixel_z, raw_header_size, patientID):
        self.distance_source_origin = distance_source_origin
        self.distance_origin_detector = distance_origin_detector
        self.detector_pixel_size = detector_pixel_size
        self.image_pixel_spacing = image_pixel_spacing
        self.num_projections = num_projections
        self.angles = angles
        self.voxel_size = voxel_size
        self.num_pixel_x = num_pixel_x
        self.num_pixel_y = num_pixel_y
        self.num_pixel_z = num_pixel_z
        self.raw_header_size = raw_header_size
        self.patientID = patientID


def save_array_to_nifti(arr_out, filename):
    affine = np.eye(4)
    nifti_img = nib.Nifti1Image(arr_out, affine)
    nib.save(nifti_img, filename)
    print("NIfTI file saved as: " + filename)

if __name__ == "__main__":
    """ Params: set by user """
    #path = './data_XA_00010'

    # Instantiate the parser
    parser = argparse.ArgumentParser()
    parser.add_argument('path_projection',
                    help='Path to projections')
    parser.add_argument('config_filename',
                        help='Config filename (json)')
    args = parser.parse_args()

    """ Get config data from file """

    with open(args.config_filename) as f:
        cfg_json = json.load(f)

    # (1) distance source to patient, (2) distance source to detector,
    # (3) image pixel spacing, (4) no. of frames, (5) positioner primary angle increment,
    # (6) voxel size, (7) rows, (8) cols, (9) modality
    cfg = Config(cfg_json[0]['distance_source_to_patient'],
                 cfg_json[0]['distance_source_to_detector'],
                 cfg_json[0]['image_pixel_spacing'],
                 cfg_json[0]['detector_pixel_spacing'],
                 cfg_json[0]['number_of_frames'],
                 cfg_json[0]['positioner_primary_angle_increment'],
                 cfg_json[0]['voxel_size'],
                 cfg_json[0]['num_pixel_x'],
                 cfg_json[0]['num_pixel_y'],
                 cfg_json[0]['num_pixel_z'],
                 cfg_json[0]['raw_header_size'],
                 cfg_json[0]['patient_ID']
    )

    """ read projections """
    if pydicom.misc.is_dicom(args.path_projection):
        dcm_img = pydicom.dcmread(args.path_projection)  #
        data = dcm_img.pixel_array[:,:,:].astype(np.float32)
    else:
        files = [f for f in os.listdir(path)]  # list of projection files
        no_projections = len(files)
        projections_stack = []

        """ create 3d volume """
        for raw_file in files:
            if not raw_file.lower().endswith('.tiff'):
                file_path = path + raw_file
                with open(file_path, 'rb') as file:
                    raw_data = np.fromfile(file, dtype=dtype)

                # Reshape if needed
                if channels == 1:
                    image = raw_data[int(raw_header_size/2):].reshape(
                        (int(cfg.num_pixel_y), int(cfg.num_pixel_x)))
                    # image = image[::8,::8]
                else:
                    image = raw_data.reshape((cfg.num_pixel_y, cfg.num_pixel_x, 1))

                projections_stack.append(image.astype('np.float32'))

    """ create 3d volume """
    ag = framework.AcquisitionGeometry.create_Cone3D(source_position=[0, cfg.distance_source_origin, 0],
                                                     detector_position=[0,
                                                                        cfg.distance_origin_detector-cfg.distance_source_origin,
                                                                        0], ) \
        .set_angles(cfg.angles, angle_unit='degree', ) \
        .set_panel([cfg.num_pixel_y, cfg.num_pixel_x], pixel_size=(cfg.detector_pixel_size[0], cfg.detector_pixel_size[1]))

    #ad.RingRemover(decNum=4, wname='db10', sigma=1.5, info=True)

    ig = framework.ImageGeometry(voxel_num_x=cfg.num_pixel_y,
                                 voxel_num_y=cfg.num_pixel_x,
                                 voxel_num_z=cfg.num_pixel_x,
                                 voxel_size_x=cfg.voxel_size,
                                 voxel_size_y=cfg.voxel_size,
                                 voxel_size_z=cfg.voxel_size)

    ad = framework.AcquisitionData(data, geometry=ag)
    #data_padded = Padder.constant(pad_width=86, constant_values=0)(ad)

    fdk = recon.FDK(ad, ig)

    """fdk.set_filter(filter='ram-lak', cutoff=0.4)
    fdk.set_fft_order(13)
    fdk.get_filter_array()"""

    out = fdk.run()
    #scipy.io.savemat('recon_' + output_filename + '.mat', {'recon': out.array}) #save as .mat file
    if not os.path.isdir('./results/'):
        os.makedirs('./results/')

    save_array_to_nifti(out.array, filename=cfg.patientID + ".nii")


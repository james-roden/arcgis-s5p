# -----------------------------------------------
# Project: arcgis-s5p
# Name: s5pgis
# Purpose: Converts Sentinel 5-P netCDF data to point Feature Class
# Version: 0.1
# Author: James M Roden
# Created: Apr 2020
# ArcGIS Version: 10.5
# Python Version 2.7
# PEP8
# -----------------------------------------------

import arcpy
from netCDF4 import Dataset
import numpy as np
import sys
import traceback


class Toolbox(object):
    def __init__(self):
        """ESRI Stub

        """
        self.label = "sp5gis"
        self.alias = "sp5gis"
        self.tools = [Tool]


class Tool(object):
    def __init__(self):
        """ESRI Stub

        """

        self.label = 'sp5gis'
        self.description = ''
        self.canRunInBackground = False

    def getParameterInfo(self):
        """ESRI Stub

        """

        parameter_0 = arcpy.Parameter(
            displayName='Sentinel 5-P Data',
            name='sentinel_5p_data',
            datatype='DEFile',
            parameterType='Required',
            direction='Input'
        )

        parameter_1 = arcpy.Parameter(
            displayName='Variable',
            name='variable',
            datatype='GPString',
            parameterType='Required',
            direction='Input'
        )

        parameter_1.filter.type = 'ValueList'

        parameter_2 = arcpy.Parameter(
            displayName='Output Feature Class',
            name='output_feature_class',
            datatype='DEFeatureClass',
            parameterType='Required',
            direction='Output'
        )

        parameters = [parameter_0, parameter_1, parameter_2]
        return parameters

    def isLicensed(self):
        """ESRI Stub

        """
        return True

    def updateParameters(self, parameters):
        """ESRI Stub

        """

        if parameters[0].value:
            netcdf = parameters[0].valueAsText
            with Dataset(netcdf, 'r') as fh:
                variables = list(fh.groups['PRODUCT'].variables.keys())
                variables = [v for v in variables if v not in ['longitude', 'latitude']]
                variables = [v for v in variables if fh.groups['PRODUCT'].variables[v].datatype == 'float32']
            parameters[1].filter.list = variables

        return

    def updateMessages(self, parameters):
        """"ESRI Stub

        """

        return

    def execute(self, parameters, messages):
        """Converts Sentinel 5-P netCDF data into Feature Class.

        ESRI Stub. Opens and parses the netCDF file and pulls out latitude, longitude, & the specified variable.
        Saves a feature class to user specified location. NoData value: 9.969210e+036

        Args:
            ESRI defined

        """

        try:
            # arcpy environment settings
            arcpy.env.workspace = r'in_memory'
            arcpy.env.scratchWorkspace = r'in_memory'

            # ArcGIS tool parameters
            netcdf = parameters[0].valueAsText
            variable = parameters[1].valueAsText
            out_points = parameters[2].valueAsText

            # Load netCDF file with netCDF4
            with Dataset(netcdf, 'r') as fh:
                # Create longitude & latitude arrays
                longitude = fh.groups['PRODUCT'].variables['longitude'][:][0, :, :]
                latitude = fh.groups['PRODUCT'].variables['latitude'][:][0, :, :]
                data_value = fh.groups['PRODUCT'].variables[variable][:][0, :, :]

            struct = np.rec.fromarrays([longitude, latitude, data_value], formats=['f8', 'f8', 'f8'],
                                       names=['longitude', 'latitude', variable])

            wkt = "GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],\
                           PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]];\
                           -400 -400 1000000000;-100000 10000;-100000 10000;8.98315284119522E-09;\
                           0.001;0.001;IsHighPrecision"

            sr = arcpy.SpatialReference()
            sr.loadFromString(wkt)

            arcpy.da.NumPyArrayToFeatureClass(struct, out_points, ['longitude', 'latitude'], sr)

        except RuntimeError:
            arcpy.AddError('Please ensure you are using Sentinel 5-P L2 ch4 data in original netCDF format')

        except Exception as ex:
            _, error, tb = sys.exc_info()
            traceback_info = traceback.format_tb(tb)[0]
            arcpy.AddError("Error Type: {} \nTraceback: {} \n".format(error, traceback_info))

        finally:
            arcpy.Delete_management('in_memory')
            arcpy.AddMessage("in_memory intermediate files deleted.")
            return

import xml.etree.ElementTree as ET
from glob import glob
import os
import copy
os.umask(0)
#Dict for referencing values of each filter where (WavelengthFWHM, VignettingPolynomial)
#All VignettingPolynomial values are set to a default of 0.35
FILTER_LOOKUP = {
    "RGB": ("243", "0.35"),
    "405": ("15", "0.35"),
    "450": ("30", "0.35"),
    "490": ("38", "0.35"),
    "518": ("20", "0.35"),
    "550": ("30", "0.35"),
    "590": ("32", "0.35"),
    "615": ("21", "0.35"),
    "632": ("30", "0.35"),
    "650": ("31", "0.35"),
    "685": ("24", "0.35"),
    "725": ("23", "0.35"),
    "780": ("34", "0.35"),
    "808": ("14", "0.35"),
    "850": ("30", "0.35"),
    "880": ("26", "0.35"),
    "940": ("60", "0.35"),
    "945": ("8", "0.35"),
}

SENSOR_LOOKUP = {
    '2': ("1280, 960", "5.0, 3.0"),
    '4': ("2048,1536", "7.0656,5.2992"),
    '6': ("4384,3288", "6.14,4.60")
}

LENS_LOOKUP = {
    "0": ("9.6", "3.0"),
    "1": ("8.25", "2.8")
}

ROTATION_LOOKUP = {
    "0": ("0", "180", "0", "180", "0", "180"),
}

modpath = os.path.dirname(os.path.realpath(__file__))

class KernelConfig():
    _infolder = None
    _outfolder = None
    # _roots = []
    _trees = []
    _infiles = None


    def __init__(self, infolder = None):
        self._infolder = infolder
        self._infiles = glob(infolder + os.sep + r'/**/*.kernelconfig', recursive=True)
        for file in self._infiles:
            self._trees.append(ET.parse(file))
        # for tree in self._trees:
        #     self._roots.append(tree.getroot())


    def setInputFolder(self, infolder):
        self._infolder = infolder
    def getItems(self):
        return self._infiles
    def setOutputFolder(self, outfolder):
        self._outfolder = outfolder
    def orderRigs(self, order=[0,1,2,3,4,5]):
        temptrees = copy.deepcopy(self._trees)
        self._trees = []
        for i in range(6):
            if order[i] < 0:
                pass
            else:
                self._trees.append(temptrees[order[i]])
    #TODO def createKernelConfig(self, KernelConfig):

    def createCameraRig(self, rawscale = "16"):
        rigtree = ET.parse(modpath + os.sep + "mapir_kernel.camerarig")

        for root in self._trees:
            filter_ = root.find("Filter").text
            sensor = root.find("Sensor").text
            lens = root.find("Lens").text
            arrayID = root.find("ArrayID").text
            arayType = root.find("ArrayType").text
            prop = ET.SubElement(rigtree.getroot(), "CameraProp")
            ET.SubElement(prop, "CentralWavelength").text = filter_
            ET.SubElement(prop, "WavelengthFWHM").text = FILTER_LOOKUP[filter_][0]
            ET.SubElement(prop, "RawFileSubFolder").text = filter_
            ET.SubElement(prop, "VignettingPolynomial").text = FILTER_LOOKUP[filter_][1]
            ET.SubElement(prop, "SensorBitDepth").text = "12"
            ET.SubElement(prop, "RawValueScaleUsed").text = rawscale
            ET.SubElement(prop, "ImageDimensions").text = SENSOR_LOOKUP[sensor][0]
            ET.SubElement(prop, "SensorSize").text = SENSOR_LOOKUP[sensor][1]
            ET.SubElement(prop, "BandSensitivity").text = "1.0"
            ET.SubElement(prop, "FocalLength").text = LENS_LOOKUP[lens][0]
            ET.SubElement(prop, "Aperture").text = LENS_LOOKUP[lens][1]
            ET.SubElement(prop, "Rotation").text = ROTATION_LOOKUP[arayType][int(arrayID)]
        rigtree.write(self._infolder + os.sep + "mapir_kernel.camerarig")
        #TODO finish this loop by creating a new sub element and deriving the results from the above data.

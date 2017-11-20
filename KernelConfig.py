import xml.etree.cElementTree as ET
from glob import glob
import os


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
    4: ("2048,1536", "7.0656,5.2992"),
    6: ("4384,3288", "6.14,4.60")
}

class KernelConfig():
    _infolder = None
    _outfolder = None
    _roots = None
    _trees = []
    _path = None
    _infiles = None


    def __init__(self, parent = None, infolder = None, rawscale = "16"):
        self.parent = parent
        if parent:
            self._path = self.parent.modpath
        else:
            self._path = infolder
        self._infolder = infolder
        self._infiles = glob(infolder + os.sep + "*.kernelconfig", True)
        for file in self._infiles:
            self._trees.append(ET.parse(file))
        for tree in self._trees:
            self._roots.append(tree.getroot())


    def setInputFolder(self, infolder):
        self._infolder = infolder

    def setOutputFolder(self, outfolder):
        self._outfolder = outfolder

    #TODO def createKernelConfig(self, KernelConfig):

    def createCameraRig(self, rawscale = "16"):
        rigfile = glob(self._path + os.sep + "*.camerarig")
        rigtree = ET.parse(rigfile)
        rigroot = rigtree.getroot()
        for root in self._trees:
            filter_ = root.find("Filter").text
            sensor = root.find("Sensor").text
            lens = root.find("Lens").text
            arrayID = root.find("Array ID").text
            arayType = root.find("Array Type").text
            prop = ET.Element(root, "CameraProp")
            ET.SubElement(prop, "CentralWavelength").text = filter_
            ET.SubElement(prop, "WavelengthFWHM").text = FILTER_LOOKUP[filter_][0]
            ET.SubElement(prop, "RawFileSubFolder").text = filter_
            ET.SubElement(prop, "VignettingPolynomial").text = FILTER_LOOKUP[filter_][1]
            ET.SubElement(prop, "SensorBitDepth").text = "12"
            ET.SubElement(prop, "RawValueScaleUsed").text = rawscale
            ET.SubElement(prop, "ImageDimensions").text = SENSOR_LOOKUP[sensor][0]
            ET.SubElement(prop, "SensorSize").text = SENSOR_LOOKUP[sensor][1]
            ET.SubElement(prop, "BandSensitivity").text = "12"
        #TODO finish this loop by creating a new sub element and deriving the results from the above data.

def classFactory(iface):
	#from script, import class
	from qcTools.qcTools import QC_Tools
	#from StylesAutoLoader import StylesAutoLoader
	return QC_Tools(iface)

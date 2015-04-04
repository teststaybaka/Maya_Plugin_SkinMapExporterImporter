import sys, os
import maya.OpenMaya as OpenMaya
import maya.OpenMayaMPx as OpenMayaMPx
import maya.cmds as cmds
import maya.mel as mel
import math

exportCmdName = "exportSkinWeights_space"
importCmdName = "importSkinWeights_space"

# Command
class exportCommand(OpenMayaMPx.MPxCommand):
    def __init__(self):
        OpenMayaMPx.MPxCommand.__init__(self)

    # Invoked when the command is run.
    def doIt(self,argList):
        polygons = cmds.filterExpand(sm=12)
        if not polygons:
            print 'Please select a polygon.'
            return

        paths = cmds.fileDialog2(dialogStyle=2, fileMode = 3, okCaption = "Save", cancelCaption = "Cancel")
        if not paths:
            return

        for p in range(0, len(polygons)):
            polygon = polygons[p]
            related_cluster = mel.eval('findRelatedSkinCluster '+polygon)
            if related_cluster == '':
                print 'Please bind skin for this polygon.' + polygon
                continue

            path = paths[0]
            joints = cmds.skinPercent(related_cluster, polygon+'.vtx[0]', q = True, t = None);
            f = open(path+'/'+polygon+'.weights', 'w')

            vertices = cmds.getAttr(polygon+'.vrts', multiIndices = True);
            for i in range(0, len(vertices)):
                infs = cmds.skinPercent(related_cluster, polygon+'.vtx['+str(vertices[i])+']', q = True, v = True)
                pos = cmds.xform(polygon+'.vtx['+str(vertices[i])+']', q=1, ws=1, t=1)
                f.write('vp ' + str(pos[0])+' '+str(pos[1])+' '+str(pos[2]) + '\n')
                f.write('vinf');
                for j in range(0, len(infs)):
                    f.write(' ' + joints[j] + ' ' + str(infs[j]))
                f.write('\n')
            f.close()

        print 'Export Complete.'

# Command
class importCommand(OpenMayaMPx.MPxCommand):
    def __init__(self):
        OpenMayaMPx.MPxCommand.__init__(self)

    # Invoked when the command is run.
    def doIt(self,argList):
        polygon = cmds.filterExpand(sm=12)
        if polygon:
            if len(polygon) > 1:
                print 'Please select only one polygon to import.'
                return
            else:
                polygon = polygon[0];
        else:
            print 'Please select a polygon.'
            return

        related_cluster = mel.eval('findRelatedSkinCluster '+polygon)
        if related_cluster == '':
            print 'Please bind skin for this polygon.'
            return;

        paths = cmds.fileDialog2(dialogStyle=2, fileMode = 4, okCaption = "Load", cancelCaption = "Cancel")
        if not paths:
            return;

        for p in range(0, len(paths)):
            path = paths[p]
            joints = cmds.skinPercent(related_cluster, polygon+'.vtx[0]', q = True, t = None);
            f = open(path, 'r')

            vertices = cmds.getAttr(polygon+'.vrts', multiIndices = True)
            while 1:
                line = f.readline()
                if not line:
                    break

                line = line[:-1]
                parts = line.split(' ')
                if parts[0] != 'vp':
                    break
                weights = f.readline()[:-1].split(' ')
                if weights[0] != 'vinf':
                    break

                pos = [float(parts[1]), float(parts[2]), float(parts[3])]
                index = -1
                for i in range(0, len(vertices)):
                    ver = cmds.xform(polygon+'.vtx['+str(vertices[i])+']', q=1, ws=1, t=1)
                    dist = math.sqrt((pos[0]-ver[0])*(pos[0]-ver[0]) + (pos[1]-ver[1])*(pos[1]-ver[1]) + (pos[2]-ver[2])*(pos[2]-ver[2]))
                    if dist < 0.0001:
                        index = i

                        transformValue = []
                        for j in range(1, len(weights), 2):
                            transformValue.append((weights[j], float(weights[j+1]) ))
                        cmds.skinPercent(related_cluster, polygon+'.vtx['+str(vertices[index])+']', transformValue=transformValue)
                        cmds.skinPercent(related_cluster, polygon+'.vtx['+str(vertices[index])+']', normalize=True)

            f.close()
        print 'Import Complete.'


# Creator
def exportCmdCreator():
    return OpenMayaMPx.asMPxPtr( exportCommand() )

def importCmdCreator():
    return OpenMayaMPx.asMPxPtr( importCommand() )

# Initialize the script plug-in
def initializePlugin(mobject):
    mplugin = OpenMayaMPx.MFnPlugin(mobject)
    try:
        mplugin.registerCommand( exportCmdName, exportCmdCreator )
        mplugin.registerCommand( importCmdName, importCmdCreator )
    except:
        sys.stderr.write( "Failed to register command: %s, %s\n" % exportCmdName, importCmdName)
        raise

# Uninitialize the script plug-in
def uninitializePlugin(mobject):
    mplugin = OpenMayaMPx.MFnPlugin(mobject)
    try:
        mplugin.deregisterCommand( exportCmdName )
        mplugin.deregisterCommand( importCmdName )
    except:
        sys.stderr.write( "Failed to unregister command: %s, %s\n" % exportCmdName, importCmdName)

import sys, os
import maya.OpenMaya as OpenMaya
import maya.OpenMayaMPx as OpenMayaMPx
import maya.cmds as cmds
import maya.mel as mel
import math
from PIL import Image, ImageDraw

exportCmdName = "exportSkinWeights"
importCmdName = "importSkinWeights"


def find_next_num(s, start):
    res = ''
    find = False
    index = -1
    for i in range(start, len(s)):
        if s[i] >= 48 and s[i] <= 57:
            find = True
            res += s[i]
        else:
            if find:
                index = i
                break

    if find:
        return [int(res), index]
    else:
        return [-1, -1]

# Command
class exportCommand(OpenMayaMPx.MPxCommand):
    def __init__(self):
        OpenMayaMPx.MPxCommand.__init__(self)

    # Invoked when the command is run.
    def doIt(self,argList):
        imlen = 1024
        polygon = cmds.filterExpand(sm=12)
        if polygon:
            if len(polygon) > 1:
                print 'Please select only one polygon to export.'
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

        paths = cmds.fileDialog2(dialogStyle=2, fileMode = 3, okCaption = "Save", cancelCaption = "Cancel")
        if not paths:
            return;

        path = paths[0]
        joints = cmds.skinPercent(related_cluster, polygon+'.vtx[0]', q = True, t = None);
        imgs = []
        for i in range(0, len(joints)):
            im = Image.new('RGBA', (imlen, imlen), (0, 0, 0, 0)) 
            imgs.append(im)

        vertices = cmds.getAttr(polygon+'.vrts', multiIndices = True);
        warning = False
        for i in range(0, len(vertices)):
            infs = cmds.skinPercent(related_cluster, polygon+'.vtx['+str(vertices[i])+']', q = True, v = True)
            uvs = cmds.polyListComponentConversion(polygon+'.vtx['+str(vertices[i])+']', fromVertex = True, toUV = True)
            uv = cmds.polyEditUV(uvs[0], query = True)
            for j in range(0, len(uv), 2):
                x = int(math.floor(uv[j]*imlen))
                y = int(math.floor((1 - uv[j+1])*imlen))
                for z in range(0, len(infs)):
                    data = imgs[z].getdata()
                    height = imgs[z].size[1]
                    width = imgs[z].size[0]
                    overlapped = False
                    if data[y*width + x][3] != 0:
                        warning = True
                        overlapped = True
                        # return
                    draw = ImageDraw.Draw(imgs[z])
                    if overlapped:
                        draw.point((x, y), fill=(255, 0, int(infs[z]*255), 255))
                    else:
                        draw.point((x, y), fill=(0, 0, int(infs[z]*255), 255))
                    # draw.point((200, 100), 'red')
                    # draw.point((200+1, 100), 'red')
                    # draw.point((200, 100+1), 'red')
                    # draw.point((200-1, 100), 'red')
                    # draw.point((200, 100-1), 'red')
                    # print data[100*width + 200]
                    # print data[101*width + 200]

        for i in range(0, len(joints)):
            imgs[i].save(path+'/'+joints[i]+'.png')
        
        if warning:
            print 'Warning: Some of uv points are too close. Please adjust UV Map or change output size.'
        print 'Export Complete.'

# Command
class importCommand(OpenMayaMPx.MPxCommand):
    def __init__(self):
        OpenMayaMPx.MPxCommand.__init__(self)

    # Invoked when the command is run.
    def doIt(self,argList):
        imlen = 1024
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

        paths = cmds.fileDialog2(dialogStyle=2, fileMode = 3, okCaption = "Load", cancelCaption = "Cancel")
        if not paths:
            return;

        path = paths[0]
        joints = cmds.skinPercent(related_cluster, polygon+'.vtx[0]', q = True, t = None);
        imgs = []
        for i in range(0, len(joints)):
            if not os.path.isfile(path+'/'+joints[i]+'.png'):
                imgs.append(0)
                continue

            print joints[i]+'.png'
            im = Image.open(path+'/'+joints[i]+'.png')
            imgs.append(im)

        vertices = cmds.getAttr(polygon+'.vrts', multiIndices = True);
        for i in range(0, len(vertices)):
            infs = cmds.skinPercent(related_cluster, polygon+'.vtx['+str(vertices[i])+']', q = True, v = True)
            uvs = cmds.polyListComponentConversion(polygon+'.vtx['+str(vertices[i])+']', fromVertex = True, toUV = True)
            uv = cmds.polyEditUV(uvs[0], query = True)
            for j in range(0, len(uv), 2):
                x = int(math.floor(uv[j]*imlen))
                y = int(math.floor((1 - uv[j+1])*imlen))
                transformValue = []
                sum_value = 0
                for z in range(0, len(infs)):
                    if imgs[z] == 0:
                        transformValue.append((joints[z], 0))
                        continue

                    data = imgs[z].getdata()
                    height = imgs[z].size[1]
                    width = imgs[z].size[0]
                    if data[y*width+x][3] == 0:
                        transformValue.append((joints[z], 0))
                    else:
                        transformValue.append((joints[z], data[y*width+x][2]/255.0))
                        sum_value += data[y*width+x][2]/255.0
                        # print data[y*width+x][2]/255.0

                if abs(sum_value) < 0.001:
                    break

                for z in range(0, len(transformValue)):
                    transformValue[z] = (transformValue[z][0], transformValue[z][1]/sum_value)
                cmds.skinPercent(related_cluster, polygon+'.vtx['+str(vertices[i])+']', transformValue=transformValue)
                cmds.skinPercent(related_cluster, polygon+'.vtx['+str(vertices[i])+']', normalize=True )
                break
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

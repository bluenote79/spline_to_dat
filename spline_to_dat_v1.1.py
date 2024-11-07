
import adsk.core, adsk.fusion, adsk.cam, traceback
import os
import os.path
import math
from math import pi

COMMAND_ID = "Airfoil"
SE01_SELECTION1_COMMAND_ID = "select splines"
IN01_VALUE_INPUT_ID = "Airfoilname"
IN02_VALUE_INPUT_ID = "Punkte"


_handlers = []

ui = None
app = adsk.core.Application.get()
if app:
    ui = app.userInterface


    # get orientation of coordinate system y or z axis up
    view = app.activeViewport
    view.goHome()
    camera = view.camera
    vector1 = camera.upVector
    vectorz = adsk.core.Vector3D.create(0,0,1)
    vectory = adsk.core.Vector3D.create(0,1,0)

    if vector1.isParallelTo(vectorz):
        vectorup = "z"
        # ui.messageBox("zup")
    elif vector1.isParallelTo(vectory):
        vectorup = "y"
        # ui.messageBox("yup")
    else:
        vectorup = "x"
        # ui.messageBox("none")

product = app.activeProduct
design = adsk.fusion.Design.cast(product)
root = design.rootComponent
sketches = root.sketches
planes = root.constructionPlanes




class FoilCommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            command = args.firingEvent.sender
            inputs = command.commandInputs

            if inputs.itemById(SE01_SELECTION1_COMMAND_ID).selectionCount == 1:
                spline = inputs.itemById(SE01_SELECTION1_COMMAND_ID).selection(0).entity
                splineO = None
                splineU = None

                parent_Sketch = spline.parentSketch
                reference_plane = parent_Sketch.referencePlane

                if reference_plane == root.xYConstructionPlane:
                    plane = "xy"
                elif reference_plane == root.xZConstructionPlane:
                    plane = "xz"
                    # y-werte (z) sind invertiert
                elif reference_plane == root.yZConstructionPlane:
                    plane = "yz"
                    # x-werte (z) sind invertiert



                fitpoints = spline.fitPoints
                if fitpoints[2].geometry.y > fitpoints[-2].geometry.y:
                    direction = "forward"
                else:
                    direction = "reversed"




                ui.messageBox(direction + ", plane: " + plane)
                
            elif inputs.itemById(SE01_SELECTION1_COMMAND_ID).selectionCount == 2:
                spline1 = inputs.itemById(SE01_SELECTION1_COMMAND_ID).selection(0).entity
                spline2 = inputs.itemById(SE01_SELECTION1_COMMAND_ID).selection(1).entity
                spline = None

                parent_Sketch = spline1.parentSketch
                reference_plane = parent_Sketch.referencePlane

                if reference_plane == root.xYConstructionPlane:
                    plane = "xy"
                elif reference_plane == root.xZConstructionPlane:
                    plane = "xz"
                    # y-werte (z) sind invertiert
                elif reference_plane == root.yZConstructionPlane:
                    plane = "yz"
                    # x-werte (z) sind invertiert


                # direction hier ggf. unnötig, aber oben und unten identifizieren zunächst für die xy-Ebene
                if spline1.startSketchPoint.geometry.x == 0:
                    direction1 = "forward"
                else:
                    direction1 = "reversed"
                
                if spline2.startSketchPoint.geometry.x == 0:
                    direction2 = "forward"
                else:
                    direction2 = "reversed"

                evaluator1 = spline1.evaluator
                evaluator2 = spline2.evaluator
                eval1a = evaluator1.getPointAtParameter(0.1)
                eval1b = evaluator1.getPointAtParameter(0.9)
                eval2a = evaluator2.getPointAtParameter(0.1)
                eval2b = evaluator2.getPointAtParameter(0.9)
                point1a = eval1a[1]
                point1b = eval1b[1]
                point2a = eval2a[1]
                point2b = eval2b[1]
                
                if (point1a.y + point1b.y) > (point2a.y + point2b.y):
                    mirror = False
                    splineO = spline1
                    splineU = spline2
                else:
                    mirror = True
                    splineO = spline2
                    splineU = spline1

                direction = ""
                
                # debugging mirror doch nicht nötig?
                # ui.messageBox("direction1: " + direction1 + ", direction2: " + direction2 + ", mirror: " + str(mirror))
                



            name = inputs.itemById(IN01_VALUE_INPUT_ID)
            count = inputs.itemById(IN02_VALUE_INPUT_ID)
            
           
            foil = Foil()
            foil.Execute(spline, name.value, count.value, splineO, splineU, plane, direction)

        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


class FoilCommandDestroyHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            adsk.terminate()
        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


class Foil:
    def Execute(self, spline, name, punkte, splineO, splineU, plane, direction):

        def cos_verteilung(punkte: int, rootlength: float):
            x_values = []
            step = math.pi / (punkte - 1)

            for i in range(punkte):
                theta = i * step / 2
                x = (1 - math.cos(theta)) 
                x_values.append(x * rootlength)
        
            return x_values

        if splineO == None:
            sketchP = spline.parentSketch
            planeP = sketchP.referencePlane

            for i in range(1, int(punkte)):
                spline.addFitPoint(i/punkte)

            pointlist = spline.fitPoints

            arrayp = []
            for i in range(pointlist.count):
                arrayp.append(pointlist.item(i).geometry.asArray())
            
            if direction == "reversed":
                array2 = list(reversed(arrayp))
            else:
                array2 = arrayp

            # falls Punkte mit x < 0 in unmittelbarer Nähe zum Ursprung generiert werden
            delarray = []
            for i in range(len(array2)):
                if array2[i][0] < 0:
                    delarray.append(i)

            if len(delarray) > 0:
                for i in delarray:
                    del array2[i]


            rootlength = array2[0][0]

            # mirror y-values if z-axis up
            if vectorup == "z" and planeP == root.xZConstructionPlane:
                pre_scaled = [(array2[i][0] / rootlength, -1 * array2[i][1] / rootlength) for i in range(len(array2))]
                scaled = list(reversed(pre_scaled))
            else:
                scaled = [(array2[i][0] / rootlength, array2[i][1] / rootlength) for i in range(len(array2))]


        else:
            sketchP = splineO.parentSketch
            planeP = sketchP.referencePlane

            ar1 = splineO.startSketchPoint.geometry.asArray()
            ar2 = splineO.endSketchPoint.geometry.asArray()
            if ar1[0] > ar2[0]:
                rootlength = ar1[0]
            else:
                rootlength = ar2[0]

            x_verteilung = cos_verteilung(int(punkte), rootlength)

            O = []
            U = []
            
            for i in range(1,len(x_verteilung)):
                collLines = adsk.core.ObjectCollection.create()
                pu = adsk.core.Point3D.create(float(x_verteilung[i]), -10, 0)
                po = adsk.core.Point3D.create(float(x_verteilung[i]), 10, 0)
                line = sketchP.sketchCurves.sketchLines.addByTwoPoints(pu, po)
                collLines.add(line)
                O.append(splineO.intersections(collLines)[2][0].asArray())
                U.append(splineU.intersections(collLines)[2][0].asArray())
                line.deleteMe()
            
            # mirror y-values
            if vectorup == "z" and planeP == root.xZConstructionPlane:
                factory = -1
            else:
                factory = 1

            scaledO = [(O[i][0] / rootlength, factory * O[i][1] / rootlength) for i in range(len(O)-1)]
            scaledO.append((1, O[-1][1]))
            scaledU = [(U[i][0] / rootlength, factory * U[i][1] / rootlength) for i in range(len(U)-1)]
            scaledU.append((1, O[-1][1]))

            origin = [(0,0)]

            if vectorup == "z" and planeP == root.xZConstructionPlane:
                scaled = list(reversed(scaledU)) + list(origin) + list(scaledO)
            else:
                scaled = list(reversed(scaledO)) + list(origin) + list(scaledU)

        msg = ''
        # Set styles of file dialog.
        fileDlg = ui.createFileDialog()
        fileDlg.isMultiSelectEnabled = True
        fileDlg.title = 'Fusion Open File Dialog'
        fileDlg.filter = '*.dat'
        
       
        # Show file save dialog
        fileDlg.title = 'Fusion Save File Dialog'
        dlgResult = fileDlg.showSave()
        if dlgResult == adsk.core.DialogResults.DialogOK:
            msg += '\nFile to Save: {}'.format(fileDlg.filename)
        else:
            return
            
        filename = fileDlg.filename
        
        
        ui.messageBox(msg)



        def write_airfoil_dat(filename, airfoilname, points):
            with open(filename, 'w') as file:
                file.write(f"{airfoilname}\n")
                for x, y in points:
                    if y < 0:
                        file.write(f"  {x:.6f} {y:.6f}\n")
                    else:
                        file.write(f"  {x:.6f}  {y:.6f}\n")
            
        
        write_airfoil_dat(filename, name, scaled)
       
class FoilCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args: adsk.core.CommandEventArgs):
        try:

            onExecute = FoilCommandExecuteHandler()
            args.command.execute.add(onExecute)
            _handlers.append(onExecute)

            onDestroy = FoilCommandDestroyHandler()
            args.command.destroy.add(onDestroy)
            _handlers.append(onDestroy)

            inputs = args.command.commandInputs

            inst_text1 = """ <p><strong>Instructions:</strong></p> \
                <br><p>Option 1:<br>Sketch Airfoil as FittedSpline on xy-Plane beginning at the tail of the top. Go to the nose at the sketch origin and from there sketch the bottom to the tail.<\p>\
                <br><p>Option 2: <br>Sketch two control point splines. The first of two selections must be the top of the airfoil.
                
            """

            i1 = inputs.addSelectionInput(SE01_SELECTION1_COMMAND_ID, SE01_SELECTION1_COMMAND_ID, "select splines")
            i1.addSelectionFilter(adsk.core.SelectionCommandInput.SketchCurves)
            i1.setSelectionLimits(0, 2)
            i2 = inputs.addStringValueInput(IN01_VALUE_INPUT_ID, "Airfoilname", "Airfoilname") 
            i3 = inputs.addValueInput(IN02_VALUE_INPUT_ID, "Punkte hinzufügen", "", adsk.core.ValueInput.createByString("50"))
            i4 = inputs.addTextBoxCommandInput('fullWidth_textBox', '', inst_text1, 12, True)
           
        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


def run(context):
    try:

        cmdDef = ui.commandDefinitions.itemById(COMMAND_ID)
        if not cmdDef:
            cmdDef = ui.commandDefinitions.addButtonDefinition(COMMAND_ID, 'Save to DAT', 'Save to DAT')
        onCommandCreated = FoilCommandCreatedHandler()

        cmdDef.commandCreated.add(onCommandCreated)
        _handlers.append(onCommandCreated)

        
        cmdDef.execute()
        adsk.autoTerminate(False)

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))



    


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
            elif inputs.itemById(SE01_SELECTION1_COMMAND_ID).selectionCount == 2:
                splineO = inputs.itemById(SE01_SELECTION1_COMMAND_ID).selection(0).entity
                splineU = inputs.itemById(SE01_SELECTION1_COMMAND_ID).selection(1).entity
                spline = None


            name = inputs.itemById(IN01_VALUE_INPUT_ID)
            count = inputs.itemById(IN02_VALUE_INPUT_ID)
            
           
            foil = Foil()
            foil.Execute(spline, name.value, count.value, splineO, splineU)

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
    def Execute(self, spline, name, punkte, splineO, splineU):

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
            
            rootlength = arrayp[0][0]
            scaled = [(arrayp[i][0] / rootlength, arrayp[i][1] / rootlength) for i in range(len(arrayp))]

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
            
            for i in range(1,len(x_verteilung)):    #1
                collLines = adsk.core.ObjectCollection.create()
                pu = adsk.core.Point3D.create(float(x_verteilung[i]), -10, 0)
                po = adsk.core.Point3D.create(float(x_verteilung[i]), 10, 0)
                line = sketchP.sketchCurves.sketchLines.addByTwoPoints(pu, po)
                collLines.add(line)
                O.append(splineO.intersections(collLines)[2][0].asArray())
                U.append(splineU.intersections(collLines)[2][0].asArray())
                line.deleteMe()
            
            scaledO = [(O[i][0] / rootlength, O[i][1] / rootlength) for i in range(len(O)-1)]
            scaledO.append((1, O[-1][1]))
            scaledU = [(U[i][0] / rootlength, U[i][1] / rootlength) for i in range(len(U)-1)]
            scaledU.append((1, O[-1][1]))

            origin = [(0,0)]

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
                <br><p>Option 2: <br>Sketch two control point splines. The first of two selections must be the top of the airfoil. Both splines must meet in the sketch origin.
                
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



    

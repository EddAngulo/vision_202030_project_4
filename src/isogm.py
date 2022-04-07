# -*- coding: utf-8 -*-
"""
Created on Sun Oct 11 18:02:24 2020

@author: Eduardo Angulo
@author: Camila Lozano
"""

import vtk

# Get Program Parameters
def get_program_parameters():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('data_file', nargs='?', 
                        default=None, help='isosurface data vti file')
    parser.add_argument('grad_file', nargs='?', 
                        default=None, help='gradient magnitude vti file')
    parser.add_argument('isovals_file', nargs='?', 
                        default=None, help='isovalues file')
    parser.add_argument('--cmap', dest='colours', type=str, 
                        default=None, help='colours file')
    parser.add_argument('--clip', dest='clip', nargs=3, 
                        type=int, default=None)
    args = parser.parse_args()
    return args.data_file, args.grad_file, args.isovals_file, args.colours, args.clip


"""
- File Read Methods
"""

# Read Isovalues File
def readIsovalFile(isoFile):
    isovals = list()
    with open(isoFile) as fp:
        line = fp.readline()
        while line:
            if not line.startswith("#"):
                isovals.append(int(line))
            line = fp.readline()
    return isovals

# Read Colours File
def readColoursFile(colFile):
    colours = list()
    with open(colFile) as fp:
        line = fp.readline()
        while line:
            if not line.startswith("#"):
                data = line.split(" ")
                value = float(data[0])
                rgb = list(map(lambda x: x / 255.0, 
                               [int(data[1]), int(data[2]), int(data[3])]))
                colours.append({'value': value, 'rgb': rgb})
            line = fp.readline()
    return colours


"""
- UI Methods
"""

# Generate Default Color Transfer Function
def defaultCTF(minVal, maxVal):
    step = (maxVal - minVal) / 5
    colorFunction = vtk.vtkColorTransferFunction()
    colorFunction.AddRGBPoint(minVal, 0, 0, 0)
    colorFunction.AddRGBPoint(minVal + step, 1, 0, 0)
    colorFunction.AddRGBPoint(minVal + 2*step, 1, 1, 0)
    colorFunction.AddRGBPoint(minVal + 3*step, 0, 1, 0)
    colorFunction.AddRGBPoint(minVal + 4*step, 0, 1, 1)
    colorFunction.AddRGBPoint(maxVal, 0, 0, 1)
    return colorFunction

# Generate Color Transfer Function
def generateCTF(pairs):
    colorFunction = vtk.vtkColorTransferFunction()
    for pair in pairs:
        rgb = pair['rgb']
        colorFunction.AddRGBPoint(pair['value'], rgb[0], rgb[1], rgb[2])
    return colorFunction

# Create Slide Bar Method
def createSlideBar(min_, max_, val, x1, x2, y, name):
    slideBar = vtk.vtkSliderRepresentation2D()
    slideBar.SetMinimumValue(min_)
    slideBar.SetMaximumValue(max_)
    slideBar.SetValue(val)
    slideBar.SetTitleText(name)
    slideBar.GetPoint1Coordinate().SetCoordinateSystemToNormalizedDisplay()
    slideBar.GetPoint1Coordinate().SetValue(x1, y)
    slideBar.GetPoint2Coordinate().SetCoordinateSystemToNormalizedDisplay()
    slideBar.GetPoint2Coordinate().SetValue(x2, y)
    slideBar.SetLabelFormat(f"%3.0lf / {max_}")
    slideBar.SetTitleHeight(0.025)
    slideBar.SetLabelHeight(0.02)
    return slideBar

# Create Slider Widget Method
def createSliderWidget(slideBar, interactor):
    sliderWidget = vtk.vtkSliderWidget()
    sliderWidget.SetInteractor(interactor)
    sliderWidget.SetRepresentation(slideBar)
    sliderWidget.SetAnimationModeToAnimate()
    sliderWidget.SetEnabled(True)
    return sliderWidget

# Create Scalar Bar Method
def createScalarBar(mapper, title, labels):
    scalarBar = vtk.vtkScalarBarActor()
    scalarBar.SetOrientationToHorizontal()
    scalarBar.SetLookupTable(mapper.GetLookupTable())
    scalarBar.SetTitle(title)
    scalarBar.SetNumberOfLabels(labels)
    scalarBar.SetLabelFormat("%4.0f")
    #scalarBar.SetPosition(0.9, 0.1)
    #scalarBar.SetWidth(0.1)
    #scalarBar.SetHeight(0.7)
    return scalarBar

# Create Scalar Bar Widget
def createScalarBarWidget(scalarBar, interactor):
    scalarBarWidget = vtk.vtkScalarBarWidget()
    scalarBarWidget.SetInteractor(interactor)
    scalarBarWidget.SetScalarBarActor(scalarBar)
    return scalarBarWidget


"""
- Callback Methods
"""

# X Plane Value Slider Bar Callback Method
def vtkXSlideBarCallback(obj, event):
    global xPlane
    slideBar = obj.GetRepresentation()
    value = slideBar.GetValue()
    xPlane.SetOrigin(value, 0, 0)
    
# Y Plane Value Slider Bar Callback Method
def vtkYSlideBarCallback(obj, event):
    global yPlane
    slideBar = obj.GetRepresentation()
    value = slideBar.GetValue()
    yPlane.SetOrigin(0, value, 0)

# Z Plane Value Slider Bar Callback Method
def vtkZSlideBarCallback(obj, event):
    global zPlane
    slideBar = obj.GetRepresentation()
    value = slideBar.GetValue()
    zPlane.SetOrigin(0, 0, value)


"""
- Main Method
"""

def main():
    global xPlane, yPlane, zPlane
    
    data_file, grad_file, isov_file, cmap_file, clip = get_program_parameters()
    
    # Load Data
    dataReader = vtk.vtkXMLImageDataReader()
    dataReader.SetFileName(data_file)
    dataReader.Update()
    
    #Load Gradient Magnitude
    gradReader = vtk.vtkXMLImageDataReader()
    gradReader.SetFileName(grad_file)
    gradReader.Update()
    
    # Get Min and Max Gradient Values
    range_ = gradReader.GetOutput().GetScalarRange()
    min_grad = range_[0]
    max_grad = range_[1]
    
    # Get Isovalues
    isovals = readIsovalFile(isov_file)
    
    # Set Color Transfer Function
    if cmap_file is None:
        colorFunction = defaultCTF(min_grad, max_grad)
    else:
        cmap = readColoursFile(cmap_file)
        if not cmap:
            colorFunction = defaultCTF(min_grad, max_grad)
        else:
            colorFunction = generateCTF(cmap)
    
    # Set Clipping Values
    if clip is None:
        xVal, yVal, zVal = 0, 0, 0
    else:
        xVal, yVal, zVal = clip[0], clip[1], clip[2]
    
    # Get Bounds of Input Data Actor
    m = vtk.vtkDataSetMapper()
    m.SetInputConnection(dataReader.GetOutputPort())
    
    a = vtk.vtkActor()
    a.SetMapper(m)
    aBo = a.GetBounds()
    xMax, yMax, zMax = int(aBo[1] + 1), int(aBo[3] + 1), int(aBo[5] + 1)    
    
    # Generate Contours
    contours = vtk.vtkContourFilter()
    contours.SetInputConnection(dataReader.GetOutputPort())
    contours.ComputeNormalsOn()
    
    i = 0
    for isoval in isovals:
        contours.SetValue(i, isoval)
        i = i + 1
    
    # Apply Probe Filter
    probe = vtk.vtkProbeFilter()
    probe.SetInputConnection(contours.GetOutputPort())
    probe.SetSourceConnection(gradReader.GetOutputPort())
    
    # Define Planes Origins
    origins = vtk.vtkPoints()
    origins.SetNumberOfPoints(3)
    origins.InsertPoint(0, [xVal, 0, 0])
    origins.InsertPoint(1, [0, yVal, 0])
    origins.InsertPoint(2, [0, 0, zVal])
    
    # Define Plane Normals
    normals = vtk.vtkDoubleArray()
    normals.SetNumberOfComponents(3)
    normals.SetNumberOfTuples(3)
    normals.SetTuple(0, [1, 0, 0])
    normals.SetTuple(1, [0, 1, 0])
    normals.SetTuple(2, [0, 0, 1])

    # Generate Planes from Origins and Normals
    planes = vtk.vtkPlanes()
    planes.SetPoints(origins)
    planes.SetNormals(normals)
    
    # Get x, y and z Planes
    xPlane = vtk.vtkPlane()
    yPlane = vtk.vtkPlane()
    zPlane = vtk.vtkPlane()
    
    planes.GetPlane(0, xPlane)
    planes.GetPlane(1, yPlane)
    planes.GetPlane(2, zPlane)
    
    # Set Clippers
    xClipper = vtk.vtkClipPolyData()
    xClipper.SetClipFunction(xPlane)
    xClipper.SetInputConnection(probe.GetOutputPort())
    
    yClipper = vtk.vtkClipPolyData()
    yClipper.SetClipFunction(yPlane)
    yClipper.SetInputConnection(xClipper.GetOutputPort())
    
    zClipper = vtk.vtkClipPolyData()
    zClipper.SetClipFunction(zPlane)
    zClipper.SetInputConnection(yClipper.GetOutputPort())
    
    # Create Mapper and Actor
    mapper = vtk.vtkDataSetMapper()
    mapper.SetInputConnection(zClipper.GetOutputPort())
    mapper.SetLookupTable(colorFunction)
    
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    
    # Create Renderer, Render Window and Render Window Interactor
    ren = vtk.vtkRenderer()
    renWin = vtk.vtkRenderWindow()
    renWin.AddRenderer(ren)
    iren = vtk.vtkRenderWindowInteractor()
    iren.SetRenderWindow(renWin)
    
    ren.AddActor(actor)
    ren.ResetCamera()
    ren.GetActiveCamera().Elevation(270)
    ren.GetActiveCamera().SetRoll(360)
    ren.GetActiveCamera().Zoom(1.0)
    ren.SetBackground(0.25, 0.25, 0.25)
    ren.ResetCameraClippingRange()
    
    renWin.SetSize(800, 600)
    
    # X Plane Value Slider Bar
    xSlideBar = createSlideBar(0, xMax, xVal, 0.05, 0.25, 0.40, "X")
    xSliderWidget = createSliderWidget(xSlideBar, iren)
    xSliderWidget.AddObserver("InteractionEvent", vtkXSlideBarCallback)
    
    # Y Plane Value Slider Bar
    ySlideBar = createSlideBar(0, yMax, yVal, 0.05, 0.25, 0.25, "Y")
    ySliderWidget = createSliderWidget(ySlideBar, iren)
    ySliderWidget.AddObserver("InteractionEvent", vtkYSlideBarCallback)
    
    # Z Plane Value Slider Bar
    zSlideBar = createSlideBar(0, zMax, zVal, 0.05, 0.25, 0.1, "Z")
    zSliderWidget = createSliderWidget(zSlideBar, iren)
    zSliderWidget.AddObserver("InteractionEvent", vtkZSlideBarCallback)
    
    # Gradient Magnitude Scalar Bar
    scalarBar = createScalarBar(mapper, "Gradient Magnitude", 6)
    scalarBarWidget = createScalarBarWidget(scalarBar, iren)
    scalarBarWidget.On()
    
    # Initialize Render
    iren.Initialize()
    renWin.Render()
    iren.Start()

if __name__ == "__main__":
    main()
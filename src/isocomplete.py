# -*- coding: utf-8 -*-
"""
Created on Mon Oct 12 14:25:15 2020

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
    parser.add_argument('params_file', nargs='?', 
                        default=None, help='parameters file')
    parser.add_argument('--clip', dest='clip', nargs=3, 
                        type=int, default=None)
    args = parser.parse_args()
    return args.data_file, args.grad_file, args.params_file, args.clip


"""
- File Read Methods
"""

# Read Parameters File
def readParamsFile(paramsFile):
    params = list()
    with open(paramsFile) as fp:
        line = fp.readline()
        while line:
            if not line.startswith("#"):
                data = line.split(" ")
                isoval = int(data[0])
                gradMin = float(data[1])
                gradMax = float(data[2])
                rgb = list(map(lambda x: x / 255.0, 
                               [int(data[3]), int(data[4]), int(data[5])]))
                a = float(data[6])
                params.append({'isoval': isoval, 
                               'gradMin': gradMin, 
                               'gradMax': gradMax, 
                               'rgb': rgb, 
                               'a': a})
            line = fp.readline()
    return params


"""
- UI Methods
"""

# Generate Color Transfer Function
def generateCTF(param):
    colorFunction = vtk.vtkColorTransferFunction()
    rgb = param['rgb']
    colorFunction.AddRGBPoint(param['gradMin'], rgb[0], rgb[1], rgb[2])
    colorFunction.AddRGBPoint(param['gradMax'], rgb[0], rgb[1], rgb[2])
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
    
    data_file, grad_file, params_file, clip = get_program_parameters()
    
    # Load Data
    reader = vtk.vtkXMLImageDataReader()
    reader.SetFileName(data_file)
    reader.Update()
    
    #Load Gradient Magnitude
    gradReader = vtk.vtkXMLImageDataReader()
    gradReader.SetFileName(grad_file)
    gradReader.Update()
    
    # Load Parameters File
    params = readParamsFile(params_file)
    
    # Set Clipping Values
    if clip is None:
        xVal, yVal, zVal = 0, 0, 0
    else:
        xVal, yVal, zVal = clip[0], clip[1], clip[2]
    
    # Get Bounds of Input Data Actor
    m = vtk.vtkDataSetMapper()
    m.SetInputConnection(reader.GetOutputPort())
    
    a = vtk.vtkActor()
    a.SetMapper(m)
    aBo = a.GetBounds()
    xMax, yMax, zMax = int(aBo[1] + 1), int(aBo[3] + 1), int(aBo[5] + 1)
    
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
    
    # Create Renderer, Render Window and Render Window Interactor
    ren = vtk.vtkRenderer()
    renWin = vtk.vtkRenderWindow()
    renWin.AddRenderer(ren)
    iren = vtk.vtkRenderWindowInteractor()
    iren.SetRenderWindow(renWin)
    
    for param in params:
        # Generate Contours
        contours = vtk.vtkContourFilter()
        contours.SetInputConnection(reader.GetOutputPort());
        contours.ComputeNormalsOn()
        contours.SetValue(0, param['isoval'])
        
        # Apply Probe Filter
        probe = vtk.vtkProbeFilter()
        probe.SetInputConnection(contours.GetOutputPort())
        probe.SetSourceConnection(gradReader.GetOutputPort())
        
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
        
        # Clip by Gradient Magnitude Range
        gradClipper1 = vtk.vtkClipPolyData()
        gradClipper1.SetInputConnection(zClipper.GetOutputPort())
        gradClipper1.InsideOutOff()
        gradClipper1.SetValue(param['gradMin'])
        gradClipper1.Update()
    
        gradClipper2 = vtk.vtkClipPolyData()
        gradClipper2.SetInputConnection(gradClipper1.GetOutputPort())
        gradClipper2.InsideOutOn()
        gradClipper2.SetValue(param['gradMax'])
        gradClipper2.Update()
        
        # Create Color Function
        colorFunction = generateCTF(param)
        
        # Create Mapper, Actor and add Actor to Renderer
        mapper = vtk.vtkDataSetMapper()
        mapper.SetInputConnection(gradClipper2.GetOutputPort())
        mapper.SetLookupTable(colorFunction)
        
        actor = vtk.vtkActor()
        #actor.GetProperty().SetRepresentationToWireframe()  # Uncomment for Triangles Representation
        actor.SetMapper(mapper)
        
        actor.GetProperty().SetOpacity(param['a'])
        
        ren.AddActor(actor)
    
    # Depth Peeling
    ren.SetUseDepthPeeling(1)
    ren.SetMaximumNumberOfPeels(100)
    ren.SetOcclusionRatio(0.1)
    renWin.SetAlphaBitPlanes(1)
    renWin.SetMultiSamples(0)
    
    # Set Renderer Properties
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
    zSlideBar = createSlideBar(0, zMax, zVal, 0.05, 0.25, 0.10, "Z")
    zSliderWidget = createSliderWidget(zSlideBar, iren)
    zSliderWidget.AddObserver("InteractionEvent", vtkZSlideBarCallback)
    
    # Initialize Render
    iren.Initialize()
    renWin.Render()
    iren.Start()


if __name__ == "__main__":
    main()
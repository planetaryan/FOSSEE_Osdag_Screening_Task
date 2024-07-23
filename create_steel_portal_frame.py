from OCC.Core.gp import gp_Vec, gp_Trsf, gp_Ax1, gp_Pnt, gp_Dir
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Fuse
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCC.Core.STEPControl import STEPControl_Writer, STEPControl_AsIs
from OCC.Display.SimpleGui import init_display
import math

def create_i_section(length, width, depth, flange_thickness, web_thickness):
    web_height = depth - 2 * flange_thickness
    bottom_flange = BRepPrimAPI_MakeBox(length, width, flange_thickness).Shape()
    top_flange = BRepPrimAPI_MakeBox(length, width, flange_thickness).Shape()
    trsf = gp_Trsf()
    trsf.SetTranslation(gp_Vec(0, 0, depth - flange_thickness))
    top_flange_transform = BRepBuilderAPI_Transform(top_flange, trsf, True).Shape()
    web = BRepPrimAPI_MakeBox(length, web_thickness, web_height).Shape()
    trsf.SetTranslation(gp_Vec(0, (width - web_thickness) / 2, flange_thickness))
    web_transform = BRepBuilderAPI_Transform(web, trsf, True).Shape()
    i_section_solid = BRepAlgoAPI_Fuse(bottom_flange, top_flange_transform).Shape()
    i_section_solid = BRepAlgoAPI_Fuse(i_section_solid, web_transform).Shape()
    return i_section_solid

def create_purlin_layout(num_purlins, purlin_width, purlin_height, purlin_depth, rafter_angle):

    purlin = BRepPrimAPI_MakeBox(purlin_width, purlin_depth, purlin_height).Shape()
    roof_rise = (8400 / 2) * math.tan(math.radians(rafter_angle))
    purlins = None
    for i in range(num_purlins):
        x = i * (8000 - purlin_width) / (num_purlins - 1)
        if i < num_purlins / 2:
            z = column_height + roof_rise - (num_purlins / 2 - i) * (roof_rise / (num_purlins / 2))
        else:
            z = column_height + roof_rise - (i - num_purlins / 2 + 1) * (roof_rise / (num_purlins / 2))
        trsf = gp_Trsf()
        trsf.SetTranslation(gp_Vec(x, 0, z))
        purlin_instance = BRepBuilderAPI_Transform(purlin, trsf, True).Shape()
        if purlins is None:
            purlins = purlin_instance
        else:
            purlins = BRepAlgoAPI_Fuse(purlins, purlin_instance).Shape()
    return purlins

def create_rafter(length, width, purlin_depth, rafter_flange_thickness, rafter_web_thickness, angle):
    rafter = create_i_section(length, width, purlin_depth, rafter_flange_thickness, rafter_web_thickness)
    rotation = gp_Trsf()
    rotation.SetRotation(gp_Ax1(gp_Pnt(0, 0, 0), gp_Dir(0, 1, 0)), math.radians(angle))
    rotated_rafter = BRepBuilderAPI_Transform(rafter, rotation, True).Shape()
    return rotated_rafter

def create_portal_frame(column_length, column_width, column_height, column_flange_thickness, column_web_thickness,
                        rafter_width, rafter_depth, rafter_flange_thickness, rafter_web_thickness, rafter_angle, num_rafters,
                        purlin_width, purlin_height, purlin_depth):
    # Create columns 
    column = create_i_section(column_length, column_width, column_height, column_flange_thickness, column_web_thickness)
    columns = None
    column_spacing = purlin_depth / (num_columns_per_side - 1)
    for i in range(num_columns_per_side):
        y = i * column_spacing
        x_left = -8000 / 2 + 4000
        trsf_left = gp_Trsf()
        trsf_left.SetTranslation(gp_Vec(x_left, y, 0))
        column_instance_left = BRepBuilderAPI_Transform(column, trsf_left, True).Shape()
        x_right = 8000 / 2 + 4000
        trsf_right = gp_Trsf()
        trsf_right.SetTranslation(gp_Vec(x_right, y, 0))
        column_instance_right = BRepBuilderAPI_Transform(column, trsf_right, True).Shape()
        if columns is None:
            columns = BRepAlgoAPI_Fuse(column_instance_left, column_instance_right).Shape()
        else:
            columns = BRepAlgoAPI_Fuse(columns, column_instance_left).Shape()
            columns = BRepAlgoAPI_Fuse(columns, column_instance_right).Shape()

    # Create purlins 
    purlins = create_purlin_layout(num_purlins, purlin_width, purlin_height, purlin_depth, rafter_angle)

    # Create rafters
    rafter_length = 8000 / 2 / math.cos(math.radians(rafter_angle))

    rafter = create_i_section(rafter_length, rafter_width, rafter_depth, rafter_flange_thickness, rafter_web_thickness)

    rafters = None
    
    rafter_spacing = purlin_depth / (num_rafters - 1)

    for i in range(num_rafters):
        y = i * rafter_spacing
        
        # Left rafter
        trsf_left = gp_Trsf()
        trsf_left.SetTranslation(gp_Vec(-8000 / 2 + 4000, y, column_height))
        rafter_instance_left = BRepBuilderAPI_Transform(rafter, trsf_left, True).Shape()
        
        # Rotate left rafter upward
        rotation_left = gp_Trsf()
        rotation_left.SetRotation(gp_Ax1(gp_Pnt(-8000 / 2 + 4000, y, column_height), gp_Dir(0, -1, 0)), math.radians(rafter_angle))
        rafter_instance_left = BRepBuilderAPI_Transform(rafter_instance_left, rotation_left, True).Shape()

        # Right rafter
        trsf_right = gp_Trsf()
        trsf_right.SetTranslation(gp_Vec(8000 / 2 + 4000 - 4000, y, column_height))
        rafter_instance_right = BRepBuilderAPI_Transform(rafter, trsf_right, True).Shape()

        # Rotate right rafter downward
        rotation_right = gp_Trsf()
        rotation_right.SetRotation(gp_Ax1(gp_Pnt(8000 / 2 + 4000 - 4000, y, column_height), gp_Dir(0, -1, 0)), math.radians(-rafter_angle))
        rafter_instance_right = BRepBuilderAPI_Transform(rafter_instance_right, rotation_right, True).Shape()

        # Shift right rafter to align with purlins
        alignment_shift = gp_Trsf()
        alignment_shift.SetTranslation(gp_Vec(0, 0, (8000 / 2) * math.tan(math.radians(rafter_angle))))
        rafter_instance_right = BRepBuilderAPI_Transform(rafter_instance_right, alignment_shift, True).Shape()

        if rafters is None:
            rafters = BRepAlgoAPI_Fuse(rafter_instance_left, rafter_instance_right).Shape()
        else:
            rafters = BRepAlgoAPI_Fuse(rafters, rafter_instance_left).Shape()
            rafters = BRepAlgoAPI_Fuse(rafters, rafter_instance_right).Shape()

    # Combine all components
    portal_frame_solid = BRepAlgoAPI_Fuse(columns, purlins).Shape()
    portal_frame_solid = BRepAlgoAPI_Fuse(portal_frame_solid, rafters).Shape()

    return portal_frame_solid

def save_to_step(shape, filename):
    step_writer = STEPControl_Writer()
    step_writer.Transfer(shape, STEPControl_AsIs)
    status = step_writer.Write(filename)
    return status == 1

if __name__ == "__main__":
    column_height = 4000.0 
    column_length = 100
    column_width = 200
    column_flange_thickness = 200
    column_web_thickness = 10.0
    num_columns_per_side = 7

    num_rafters = 8
    rafter_width = 200
    rafter_depth = 100
    rafter_flange_thickness = 15.00
    rafter_web_thickness = 4.67
    rafter_angle = 30


    num_purlins = 13
    purlin_width = 125
    purlin_height = 175
    purlin_depth = 6000.0

    portal_frame = create_portal_frame(column_length, column_width, column_height, column_flange_thickness, column_web_thickness,
                                        rafter_width, rafter_depth, rafter_flange_thickness, rafter_web_thickness, rafter_angle, num_rafters,
                                        purlin_width, purlin_height, purlin_depth)

    display, start_display, add_menu, add_function_to_menu = init_display()
    display.DisplayShape(portal_frame, update=True)
    display.FitAll()
    
    filename = "portal_frame.stp"
    if save_to_step(portal_frame, filename):
        print(f"Successfully saved the portal frame to {filename}")
    else:
        print(f"Failed to save the portal frame to {filename}")

    start_display()



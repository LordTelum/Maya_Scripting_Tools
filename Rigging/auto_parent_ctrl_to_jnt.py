import maya.cmds as cmds

def auto_parent_ctrl_to_jnt():
    # Get the selected controls
    selected_controls = cmds.ls(selection=True)
    if not selected_controls:
        cmds.warning("Please select at least one control.")
        return

    # Initialize a dictionary to pair controls with their corresponding joints
    ctrl_joint_pairs = {}

    # Loop through each selected control to find the matching joint
    for control in selected_controls:
        if control.endswith('_Ctrl'):
            base_name = control[:-5]  # Remove '_Ctrl' from the end of the control name
            joint_name = base_name + '_Jnt'  # Append '_Jnt' to find the joint name

            # Search if such a joint exists in the scene
            if cmds.objExists(joint_name):
                ctrl_joint_pairs[control] = joint_name
            else:
                cmds.warning(f"Joint named {joint_name} does not exist for control {control}")

    # Apply parent and scale constraints to matched control-joint pairs
    for control, joint in ctrl_joint_pairs.items():
        cmds.parentConstraint(control, joint, mo=True)
        cmds.scaleConstraint(control, joint, mo=True)
        print(f"Constrained joint {joint} to follow control {control}.")

auto_parent_ctrl_to_jnt()

# This script will automatically parent and scale constrain joint controls to their corresponding joints based on naming conventions.
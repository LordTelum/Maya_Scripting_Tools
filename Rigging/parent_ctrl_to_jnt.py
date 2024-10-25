import maya.cmds as cmds

def parent_ctrl_to_jnt():
    # Get all currently selected objects
    selection = cmds.ls(selection=True)
    if not selection or len(selection) < 2:
        cmds.warning("Please select at least one control and one joint.")
        return

    # Assume the first half of the selection are controls and the second half are joints
    midpoint = len(selection) // 2
    selected_controls = selection[:midpoint]
    selected_joints = selection[midpoint:]

    # Check if selected joints are indeed joints
    selected_joints = [j for j in selected_joints if cmds.objectType(j) == 'joint']
    if not selected_joints:
        cmds.warning("The second half of your selection does not contain any joints.")
        return

    # Check if there are equal numbers of controls and joints
    if len(selected_controls) != len(selected_joints):
        cmds.warning("The number of controls and joints selected does not match.")
        return

    # Perform a parent and scale constraint; constrain the joint to the control
    for control, joint in zip(selected_controls, selected_joints):
        cmds.parentConstraint(control, joint, mo=True)
        cmds.scaleConstraint(control, joint, mo=True)

parent_ctrl_to_jnt()

#This script will parent and scale constrain the selected joints to the selected controls.
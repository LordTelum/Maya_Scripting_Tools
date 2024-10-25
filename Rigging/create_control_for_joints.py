import maya.cmds as cmds

def create_controls_for_joints():
    # Get the currently selected joints
    selected_joints = cmds.ls(selection=True, type='joint')
    if not selected_joints:
        cmds.warning("Please select at least one joint.")
        return

    for joint in selected_joints:
        print("Processing joint: {}".format(joint))  # Debug: print the joint being processed
        # Split the full path and use only the last part for base_name
        joint_name_parts = joint.split('|')
        last_part = joint_name_parts[-1]  # Get the last part of the hierarchy
        base_name = last_part.rsplit('_', 1)[0] if '_' in last_part else last_part
        print("Base name: {}".format(base_name))  # Debug: print the base name derived

        # Create a NURBS circle
        control_name = base_name + '_Ctrl'
        group_name = base_name + '_Ctrl_Grp'
        control = cmds.circle(name=control_name, normal=[0, 1, 0], radius=1.0)[0]

        # Group the control
        group = cmds.group(control, name=group_name)

        # Match the group's transformation to the joint
        cmds.delete(cmds.parentConstraint(joint, group))
        cmds.delete(cmds.scaleConstraint(joint, group))

        # Rename the group and control to match the new naming convention
        cmds.rename(group, group_name)
        cmds.rename(control, control_name)

        # Print control and group names for confirmation
        print("Created Control: {}, Group: {}".format(control, group))

# Run the function
create_controls_for_joints()

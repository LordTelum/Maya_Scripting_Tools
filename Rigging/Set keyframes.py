import maya.cmds as cmds

# This script will set keyframes on the selected control at the specified frames for the specified transforms.
# This is to help speed up weightpainting setup.


# List of frames to set keyframes on
keyframes = [0, 30, 60, 90, 120, 150]

# Get the selected control
selected_controls = cmds.ls(selection=True)

# Check if there is a selection
if not selected_controls:
    cmds.error("Please select a control to keyframe.")

selected_control = selected_controls[0]

# Transforms that will be keyframed
transforms = ['translateX', 'translateY', 'translateZ', 'rotateX', 'rotateY', 'rotateZ']

# Set keyframes for each transform at each frame
for transform in transforms:
    for frame in keyframes:
        # Get the current value of the transform once and use it for keyframing
        value = cmds.getAttr(f"{selected_control}.{transform}")
        cmds.setKeyframe(selected_control, attribute=transform, value=value, time=frame)

print(f"Keyframes set for {selected_control} at frames {keyframes} on attributes {transforms}.")

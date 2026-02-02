'''
This is a tool for mirroring controls from the left to the right.
It is expected that the following naming conventions are kept:

Joints = L_Arm_01_FK_Jnt
Control Groups = L_Arm_01_FK_Ctrl_Grp
Controls = L_Arm_01_FK_Ctrl

If your rig does not follow this naming convention then this version of the script will not work.

This script will take your selected controls and do the following:
duplicate them, re-name them,unparent the controls from their group
match all translations of the control groups to the proper joints
add the controls to an empty group that is created at world 0,
scale that group along the x-axis by a value of -1 re-parent them to the correct group
set translate x,y,z on the control to 0 and finally freezes the transformation.
'''

import maya.cmds as cmds

def reparent_controls_to_groups(controls):

    # controls = list of control transforms (strings)
    for ctrl in controls:
        ctrl_leaf = ctrl.split("|")[-1]  # R_Arm_Ctrl
        if not ctrl_leaf.endswith("_Ctrl"):
            continue

        grp_name = ctrl_leaf.replace("_Ctrl", "_Ctrl_Grp")

        if cmds.objExists(grp_name):
            cmds.parent(ctrl, grp_name)
        else:
            cmds.warning("Missing control group: {}".format(grp_name))

def MirrorControls():
    ctrls = cmds.ls(sl=True, type="transform")
    if not ctrls:
        cmds.warning("please select at least one control")
        return

    #Create a mirror group
    mirror_grp = "mirror_group"
    if not cmds.objExists(mirror_grp):
        # create an empty Group at world origin
        mirror_grp = cmds.group(em=True, name="mirror_group", w=True)

    unparented_ctrls = []

    #For loop to duplicate the controls, rename ctrls and grps
    #unparent them from the newly renamed groups
    #add ctrls to a mirror group
    for ctrl in ctrls:
        parent = cmds.listRelatives(ctrl, parent=True, type="transform")
        if not parent:
            continue
        parent = parent[0]

        # duplicate the ctrl group (returns a list)
        dupe_grp = cmds.duplicate(parent)[0]

        # rename the duplicated group
        new_grp_name = dupe_grp.replace("L_", "R_", 1)
        dupe_grp = cmds.rename(dupe_grp, new_grp_name)
        grp_name_end = dupe_grp.replace("Grp1", "Grp", 1)
        dupe_grp = cmds.rename(dupe_grp, grp_name_end)

        # find the control under the duplicated group (direct child transform)
        kids = cmds.listRelatives(dupe_grp, children=True, type="transform", fullPath=True) or []

        dupe_ctrl = None
        for k in kids:
            if k.split("|")[-1].endswith("_Ctrl"):
                dupe_ctrl = k
                break
        # ONLY operate on it if the ctrl exists
        if dupe_ctrl:
            leaf = dupe_ctrl.split("|")[-1]  # e.g. L_Arm_Ctrl
            if leaf.startswith("L_"):
                new_leaf = leaf.replace("L_", "R_", 1)
                dupe_ctrl = cmds.rename(dupe_ctrl, new_leaf)  # rename using FULL PATH, new name is leaf

                #unparent Ctrl from Grp
                dupe_ctrl = cmds.parent(dupe_ctrl, world=True) [0]

                #store values to reparent them later
                unparented_ctrls.append(dupe_ctrl)

                # after renaming dupe_grp
                grp_leaf = dupe_grp.split("|")[-1]
                jnt_name = grp_leaf.replace("_Ctrl_Grp", "_Jnt")

                if cmds.objExists(jnt_name):
                    cmds.matchTransform(dupe_grp, jnt_name, pos=True, rot=True)
                else:
                    cmds.warning("No matching joint for {}".format(grp_leaf))

            #add newly renamed controls to the group
            cmds.parent(dupe_ctrl, "mirror_group")

    #mirror the control group -1 on the x-axis
    cmds.scale(-1,1,1, mirror_grp, absolute=True)

    #reparent the controls to their ctrl grps
    reparent_controls_to_groups(unparented_ctrls)

    #delete the now empty group
    cmds.delete(mirror_grp)

    #set translate x,y,z to 0
    for ctrl in unparented_ctrls:
        cmds.setAttr(ctrl + ".translateX", 0)
        cmds.setAttr(ctrl + ".translateY", 0)
        cmds.setAttr(ctrl + ".translateZ", 0)
        #freeze all
        cmds.makeIdentity(ctrl, apply=True, translate=True, rotate=True, scale=True, normal=True)

MirrorControls()

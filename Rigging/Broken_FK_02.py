import maya.cmds as cmds

sels = cmds.ls(sl=True)

for index in range(0, len(sels) - 1, 1):
    parent_ctrl = sels[index]
    child_ctrl = sels[index + 1]

    child_ctrl_grp = cmds.listRelatives(child_ctrl, parent=True)[0]

    # creating parent constraints with and without translate/rotate
    p_constraint1 = cmds.parentConstraint(parent_ctrl, child_ctrl_grp, mo=True, skipRotate=['x', 'y', 'z'], weight=1)[0]
    p_constraint2 = cmds.parentConstraint(parent_ctrl, child_ctrl_grp, mo=True, skipTranslate=['x', 'y', 'z'], weight=1)[0]
    s_constraint = cmds.scaleConstraint(parent_ctrl, child_ctrl_grp, mo=True, weight=1)[0]  # constrain scale

    # adding custom attributes
    cmds.addAttr(child_ctrl, ln="FollowTranslate", at="double", min=0, max=1, dv=1)
    cmds.setAttr(f"{child_ctrl}.FollowTranslate", e=True, keyable=True)
    cmds.addAttr(child_ctrl, ln="FollowRotate", at="double", min=0, max=1, dv=1)
    cmds.setAttr(f"{child_ctrl}.FollowRotate", e=True, keyable=True)

    # connecting custom attributes to parent constraints
    follow_translate_attr = f"{child_ctrl}.FollowTranslate"
    follow_rotate_attr = f"{child_ctrl}.FollowRotate"
    translate_weight_attr = f"{p_constraint1}.{parent_ctrl}W0"
    rotate_weight_attr = f"{p_constraint2}.{parent_ctrl}W0"
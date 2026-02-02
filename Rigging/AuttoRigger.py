# Maya Quick "Auto" Rig Wizard (Guides -> FK joints)
# v1: data-driven steps, locator guides, mirror guides, build FK joints
# Tested style: Maya 2022+ (PySide2)

import maya.cmds as cmds

try:
    # Maya 2025+
    from PySide6 import QtWidgets, QtCore
    from shiboken6 import wrapInstance
except ImportError:
    # Maya 2017–2024
    from PySide2 import QtWidgets, QtCore
    from shiboken2 import wrapInstance

import maya.OpenMayaUI as omui


# ---------------------------
# Helpers
# ---------------------------

# Parents the UI to Maya's main window so if you minimize maya the ui will go with it.
def maya_main_window():
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(ptr), QtWidgets.QWidget)

#Checks to see if the groups like "guides" "Skeleton" or "Control" have been made
def ensure_group(name):
    if not cmds.objExists(name):
        return cmds.group(em=True, name=name)
    return name

#cleanup code that functions better than "if cmds.objexists(x): cmds.delete(x)
def safe_delete(node):
    if node and cmds.objExists(node):
        cmds.delete(node)

def snap_to_selection(node):
    sel = cmds.ls(sl=True, type="transform")
    if not sel:
        return False
    # snap translate + rotate from selection transform
    m = cmds.xform(sel[0], q=True, ws=True, m=True)
    cmds.xform(node, ws=True, m=m)
    return True

#used when mirroring rig
def swap_LR(name):
    # strict swap for prefixes like "L_" <-> "R_"
    if name.startswith("L_"):
        return "R_" + name[2:]
    if name.startswith("R_"):
        return "L_" + name[2:]
    return name

def mirror_x_world(src, dst):
    """
    Is only mirroring translation and not rotation
    """
    t = cmds.xform(src, q=True, ws=True, t=True)
    r = cmds.xform(src, q=True, ws=True, ro=True)
    # mirror X
    t_m = [-t[0], t[1], t[2]]
    cmds.xform(dst, ws=True, t=t_m)
    cmds.xform(dst, ws=True, ro=r)


# ---------------------------
# Rig Spec (DATA)
# ---------------------------
def build_base_spec(spine_count=3, neck_count=3):
    """
    Returns a list of step dicts:
    {
      'key': unique id,
      'name': 'Spine_01_FK_Jnt',
      'parent': 'Pelvis_FK_Jnt' (or None),
      'side': 'C'/'L'/'R',
      'required': True/False
    }
    """
    spec = []

    # Center
    spec.append({"key":"COG",    "name":"COG_FK_Jnt",    "parent":None,        "side":"C", "required":True})
    spec.append({"key":"PELV",   "name":"Pelvis_FK_Jnt", "parent":"COG_FK_Jnt","side":"C", "required":True})

    # Spine
    prev = "Pelvis_FK_Jnt"
    for i in range(1, spine_count+1):
        j = f"Spine_{i:02d}_FK_Jnt"
        spec.append({"key":f"SPN{i}", "name":j, "parent":prev, "side":"C", "required":True})
        prev = j

    # Chest anchor (optional but useful as a stable parent for clav/neck)
    spec.append({"key":"CHEST", "name":"Chest_FK_Jnt", "parent":prev, "side":"C", "required":True})
    chest = "Chest_FK_Jnt"

    # Neck + Head
    prev = chest
    for i in range(1, neck_count+1):
        j = f"Neck_{i:02d}_FK_Jnt"
        spec.append({"key":f"NCK{i}", "name":j, "parent":prev, "side":"C", "required":True})
        prev = j
    spec.append({"key":"HEAD", "name":"Head_FK_Jnt", "parent":prev, "side":"C", "required":True})

    # Left Arm chain (place left; mirror right later)
    spec.extend([
        {"key":"L_CLAV", "name":"L_Clav_FK_Jnt",     "parent":chest,             "side":"L", "required":True},
        {"key":"L_ARM1", "name":"L_Arm_01_FK_Jnt",   "parent":"L_Clav_FK_Jnt",   "side":"L", "required":True},  # shoulder
        {"key":"L_ARM2", "name":"L_Arm_02_FK_Jnt",   "parent":"L_Arm_01_FK_Jnt", "side":"L", "required":True},  # elbow
        {"key":"L_ARM3", "name":"L_Arm_03_FK_Jnt",   "parent":"L_Arm_02_FK_Jnt", "side":"L", "required":True},  # wrist
        {"key":"L_HAND", "name":"L_Hand_FK_Jnt",     "parent":"L_Arm_03_FK_Jnt", "side":"L", "required":True},
    ])

    # Left Leg chain
    spec.extend([
        {"key":"L_LEGCLAV", "name":"L_Leg_Clav_FK_Jnt", "parent":"Pelvis_FK_Jnt",    "side":"L", "required":True}, # hip socket marker
        {"key":"L_LEG1",    "name":"L_Leg_01_FK_Jnt",   "parent":"L_Leg_Clav_FK_Jnt","side":"L", "required":True}, # hip
        {"key":"L_LEG2",    "name":"L_Leg_02_FK_Jnt",   "parent":"L_Leg_01_FK_Jnt",  "side":"L", "required":True}, # knee
        {"key":"L_LEG3",    "name":"L_Leg_03_FK_Jnt",   "parent":"L_Leg_02_FK_Jnt",  "side":"L", "required":True}, # ankle
        {"key":"L_FOOT1",   "name":"L_Foot_01_FK_Jnt",  "parent":"L_Leg_03_FK_Jnt",  "side":"L", "required":True}, # ball
        {"key":"L_FOOT2",   "name":"L_Foot_02_FK_Jnt",  "parent":"L_Foot_01_FK_Jnt", "side":"L", "required":True}, # toe
        {"key":"L_FOOT3",   "name":"L_Foot_03_FK_Jnt",  "parent":"L_Foot_02_FK_Jnt", "side":"L", "required":False},# toe tip optional
    ])

    return spec

def append_fingers(spec, finger_count=5, segments=3):
    """
    Adds left finger joints under L_Hand_FK_Jnt.
    Naming example: L_Finger_01_01_FK_Jnt etc.
    """
    for f in range(1, finger_count+1):
        prev = "L_Hand_FK_Jnt"
        for s in range(1, segments+1):
            j = f"L_Finger_{f:02d}_{s:02d}_FK_Jnt"
            spec.append({
                "key": f"L_F{f}_{s}",
                "name": j,
                "parent": prev,
                "side": "L",
                "required": True
            })
            prev = j
    return spec


# ---------------------------
# Wizard UI
# ---------------------------
class AutoRigWizard(QtWidgets.QDialog):
    WINDOW_TITLE = "Auto Rig Wizard (Guides -> FK)"

    def __init__(self, parent=maya_main_window()):
        super().__init__(parent)
        self.setWindowTitle(self.WINDOW_TITLE)
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        self.setMinimumWidth(420)

        self.guides_grp = "RigGuides_GRP"
        self.joints_grp = "RigJoints_GRP"

        self.spine_count = 3
        self.neck_count = 3
        self.finger_count = 5
        self.finger_segments = 3

        self.spec = []
        self.steps = []
        self.step_index = 0

        self.build_ui()
        self.rebuild_spec()

    def build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        # Settings
        box = QtWidgets.QGroupBox("Settings")
        form = QtWidgets.QFormLayout(box)

        self.spine_spin = QtWidgets.QSpinBox()
        self.spine_spin.setRange(1, 8)
        self.spine_spin.setValue(self.spine_count)

        self.neck_spin = QtWidgets.QSpinBox()
        self.neck_spin.setRange(1, 6)
        self.neck_spin.setValue(self.neck_count)

        self.finger_spin = QtWidgets.QSpinBox()
        self.finger_spin.setRange(0, 10)
        self.finger_spin.setValue(self.finger_count)

        self.finger_seg_spin = QtWidgets.QSpinBox()
        self.finger_seg_spin.setRange(1, 4)
        self.finger_seg_spin.setValue(self.finger_segments)

        self.rebuild_btn = QtWidgets.QPushButton("Rebuild Steps")
        self.rebuild_btn.clicked.connect(self.rebuild_spec)

        form.addRow("Spine joints:", self.spine_spin)
        form.addRow("Neck joints:", self.neck_spin)
        form.addRow("Fingers (L):", self.finger_spin)
        form.addRow("Finger segments:", self.finger_seg_spin)
        form.addRow(self.rebuild_btn)

        layout.addWidget(box)

        # Current step display
        self.step_label = QtWidgets.QLabel("")
        self.step_label.setWordWrap(True)
        layout.addWidget(self.step_label)

        # Buttons row
        row = QtWidgets.QHBoxLayout()
        self.back_btn = QtWidgets.QPushButton("Back")
        self.next_btn = QtWidgets.QPushButton("Next")
        self.create_guide_btn = QtWidgets.QPushButton("Create/Select Guide")
        self.snap_btn = QtWidgets.QPushButton("Snap Guide to Selection")
        row.addWidget(self.back_btn)
        row.addWidget(self.next_btn)
        layout.addLayout(row)

        row2 = QtWidgets.QHBoxLayout()
        row2.addWidget(self.create_guide_btn)
        row2.addWidget(self.snap_btn)
        layout.addLayout(row2)

        # Actions
        actions = QtWidgets.QHBoxLayout()
        self.mirror_btn = QtWidgets.QPushButton("Mirror L → R Guides")
        self.build_btn = QtWidgets.QPushButton("Build FK Joints from Guides")
        self.clear_btn = QtWidgets.QPushButton("Clear Guides + Joints")
        actions.addWidget(self.mirror_btn)
        actions.addWidget(self.build_btn)
        layout.addLayout(actions)
        layout.addWidget(self.clear_btn)

        # Hook up
        self.back_btn.clicked.connect(self.prev_step)
        self.next_btn.clicked.connect(self.next_step)
        self.create_guide_btn.clicked.connect(self.create_or_select_current_guide)
        self.snap_btn.clicked.connect(self.snap_current_guide)
        self.mirror_btn.clicked.connect(self.mirror_left_to_right_guides)
        self.build_btn.clicked.connect(self.build_fk_joints)
        self.clear_btn.clicked.connect(self.clear_all)

    def rebuild_spec(self):
        self.spine_count = self.spine_spin.value()
        self.neck_count = self.neck_spin.value()
        self.finger_count = self.finger_spin.value()
        self.finger_segments = self.finger_seg_spin.value()

        spec = build_base_spec(self.spine_count, self.neck_count)
        if self.finger_count > 0:
            spec = append_fingers(spec, self.finger_count, self.finger_segments)

        # Wizard steps: mostly everything except R side (we'll mirror)
        self.spec = spec
        self.steps = [s for s in self.spec if s["side"] in ("C", "L")]  # user places center + left
        self.step_index = 0
        self.refresh_step_label()

    def refresh_step_label(self):
        if not self.steps:
            self.step_label.setText("No steps. Rebuild spec.")
            return

        s = self.steps[self.step_index]
        guide = self.guide_name_for_joint(s["name"])
        status = "✅ placed" if cmds.objExists(guide) else "⬜ not placed"
        self.step_label.setText(
            f"Step {self.step_index+1}/{len(self.steps)}: Place guide for\n"
            f"  Joint: {s['name']}\n"
            f"  Parent: {s['parent']}\n"
            f"  Guide: {guide}\n"
            f"  Status: {status}\n\n"
            f"Tip: Use 'Create/Select Guide', move it in viewport, then Next."
        )

        self.back_btn.setEnabled(self.step_index > 0)
        self.next_btn.setEnabled(self.step_index < len(self.steps)-1)

    def guide_name_for_joint(self, joint_name):
        return joint_name.replace("_Jnt", "_Guide").replace("_FK_", "_FK_")  # simple mapping

    def prev_step(self):
        self.step_index = max(0, self.step_index - 1)
        self.refresh_step_label()

    def next_step(self):
        self.step_index = min(len(self.steps)-1, self.step_index + 1)
        self.refresh_step_label()

    def create_or_select_current_guide(self):
        ensure_group(self.guides_grp)
        s = self.steps[self.step_index]
        guide = self.guide_name_for_joint(s["name"])

        if not cmds.objExists(guide):
            guide = cmds.spaceLocator(name=guide)[0]
            cmds.parent(guide, self.guides_grp)
            # nice display
            cmds.setAttr(f"{guide}.localScaleX", 2)
            cmds.setAttr(f"{guide}.localScaleY", 2)
            cmds.setAttr(f"{guide}.localScaleZ", 2)

        cmds.select(guide, r=True)
        self.refresh_step_label()

    def snap_current_guide(self):
        s = self.steps[self.step_index]
        guide = self.guide_name_for_joint(s["name"])
        if not cmds.objExists(guide):
            self.create_or_select_current_guide()
        ok = snap_to_selection(guide)
        if not ok:
            cmds.warning("Nothing selected to snap to. Select a vertex/transform and try again.")
        self.refresh_step_label()

    def mirror_left_to_right_guides(self):
        ensure_group(self.guides_grp)

        # find all L-side joint specs
        left = [s for s in self.spec if s["side"] == "L"]
        for s in left:
            jL = s["name"]
            gL = self.guide_name_for_joint(jL)
            if not cmds.objExists(gL):
                continue

            jR = swap_LR(jL)
            gR = self.guide_name_for_joint(jR)

            if not cmds.objExists(gR):
                gR = cmds.spaceLocator(name=gR)[0]
                cmds.parent(gR, self.guides_grp)
                cmds.setAttr(f"{gR}.localScaleX", 2)
                cmds.setAttr(f"{gR}.localScaleY", 2)
                cmds.setAttr(f"{gR}.localScaleZ", 2)

            mirror_x_world(gL, gR)

        cmds.select(cl=True)
        cmds.inViewMessage(amg="Mirrored L → R guides across world X.", pos="topCenter", fade=True)

    def build_fk_joints(self):
        """
        Build joints for any spec entry that has a guide.
        Parents based on spec['parent'].
        """
        ensure_group(self.joints_grp)

        created = []
        # Build in order (spec list is already ordered)
        for s in self.spec:
            j = s["name"]
            g = self.guide_name_for_joint(j)

            if not cmds.objExists(g):
                if s.get("required", True):
                    cmds.warning(f"Missing guide for required joint: {j}")
                continue

            if cmds.objExists(j):
                cmds.warning(f"Joint already exists, skipping: {j}")
                continue

            pos = cmds.xform(g, q=True, ws=True, t=True)

            cmds.select(cl=True)
            jnt = cmds.joint(name=j, p=pos)
            created.append(jnt)

            # parent
            parent = s["parent"]
            if parent and cmds.objExists(parent):
                cmds.parent(jnt, parent)

        # group the root joint(s) under joints_grp for cleanliness
        # (only if they aren't already parented)
        for j in created:
            if not cmds.listRelatives(j, p=True):
                cmds.parent(j, self.joints_grp)

        cmds.select(created, r=True) if created else cmds.select(cl=True)
        cmds.inViewMessage(amg=f"Built {len(created)} FK joints from guides.", pos="topCenter", fade=True)

    def _orient_chain(self, root_joint):
        """
        Orients a joint chain starting at root_joint:
        - X aims to child
        - Z is the secondary/up axis
        """
        if not cmds.objExists(root_joint):
            return
        # Needs at least one child joint to aim at
        kids = cmds.listRelatives(root_joint, c=True, type="joint") or []
        if not kids:
            return

        try:
            cmds.joint(root_joint, e=True, oj="xyz", sao="zup", ch=True, zso=True)
        except Exception as e:
            cmds.warning(f"Failed to orient chain from {root_joint}: {e}")

    def orient_all_fk(self):
        """
        Runs orientation on your major chains.
        You can tweak what roots you want oriented here.
        """
        roots = [
            "Pelvis_FK_Jnt",  # spine chain (Pelvis -> Spine -> Chest -> Neck -> Head)
            "L_Clav_FK_Jnt",  # left arm chain
            "R_Clav_FK_Jnt",  # right arm chain (after mirroring/build)
            "L_Leg_Clav_FK_Jnt",  # left leg chain
            "R_Leg_Clav_FK_Jnt",  # right leg chain
            "L_Hand_FK_Jnt",  # fingers (optional)
            "R_Hand_FK_Jnt",
            "L_Foot_01_FK_Jnt",  # foot/toe chain (optional)
            "R_Foot_01_FK_Jnt",
        ]

        for r in roots:
            self._orient_chain(r)

        cmds.inViewMessage(amg="Oriented FK chains (X→child, Z up).", pos="topCenter", fade=True)

    def clear_all(self):
        safe_delete(self.guides_grp)
        safe_delete(self.joints_grp)
        cmds.inViewMessage(amg="Cleared guides + joints groups.", pos="topCenter", fade=True)
        self.refresh_step_label()


# ---------------------------
# Launch
# ---------------------------
def show_auto_rig_wizard():
    # Close existing
    for w in QtWidgets.QApplication.allWidgets():
        if isinstance(w, AutoRigWizard):
            w.close()

    dlg = AutoRigWizard()
    dlg.show()
    return dlg

show_auto_rig_wizard()

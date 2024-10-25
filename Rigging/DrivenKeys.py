import maya.cmds as cmds

class DrivenKeyUI:
    def __init__(self):
        # Define unique window ID
        window_id = "drivenKeyWin"

        # Check if the window exists, if so delete it
        if cmds.window(window_id, exists=True):
            cmds.deleteUI(window_id)

        # Create the window
        self.window = cmds.window(window_id, title="Set Driven Key Tool", widthHeight=(400, 400))
        self.layout = cmds.columnLayout(adjustableColumn=True)

        # Driver Section
        cmds.text(label="Select Driver")
        cmds.button(label="Load Driver", command=self.load_driver)
        self.driver_attr_list = cmds.textScrollList(allowMultiSelection=True)
        cmds.separator(h=10)

        # Input Fields for Driver
        cmds.text(label="Driver Values")
        self.driver_neg_value = cmds.floatFieldGrp(numberOfFields=1, label="Negative Value", value1=-1.0)
        self.driver_zero_value = cmds.floatFieldGrp(numberOfFields=1, label="Zero Value", value1=0.0)
        self.driver_pos_value = cmds.floatFieldGrp(numberOfFields=1, label="Positive Value", value1=1.0)

        # Driven Section
        cmds.text(label="Select Driven")
        cmds.button(label="Load Driven", command=self.load_driven)
        self.driven_attr_list = cmds.textScrollList(allowMultiSelection=True)
        cmds.separator(h=10)

        # Input Fields for Driven
        self.driven_neg_value = cmds.floatFieldGrp(numberOfFields=1, label="Negative Value")
        self.driven_zero_value = cmds.floatFieldGrp(numberOfFields=1, label="Zero Value")
        self.driven_pos_value = cmds.floatFieldGrp(numberOfFields=1, label="Positive Value")

        cmds.separator(h=10)

        # Create a row layout for the buttons to place them side by side
        cmds.rowLayout(numberOfColumns=2, columnWidth2=(150, 150), adjustableColumn=2)

        # Set Driven Keys button
        cmds.button(label="Set Driven Keys", command=self.set_driven_keys)

        # Open Graph Editor button
        cmds.button(label="Open Graph Editor", command=self.open_graph_editor)

        # End row layout
        cmds.setParent('..')

        # Show the window
        cmds.showWindow(self.window)

    def load_driver(self, *args):
        sel = cmds.ls(selection=True)
        if sel:
            self.driver = sel[0]
            self.driver_attributes = cmds.listAttr(self.driver, keyable=True, visible=True)
            cmds.textScrollList(self.driver_attr_list, edit=True, removeAll=True)
            cmds.textScrollList(self.driver_attr_list, edit=True, append=self.driver_attributes)

    def load_driven(self, *args):
        sel = cmds.ls(selection=True)
        if sel:
            self.driven = sel[0]
            self.driven_attributes = cmds.listAttr(self.driven, keyable=True, visible=True)
            cmds.textScrollList(self.driven_attr_list, edit=True, removeAll=True)
            cmds.textScrollList(self.driven_attr_list, edit=True, append=self.driven_attributes)

    def set_driven_keys(self, *args):
        driver_attr = cmds.textScrollList(self.driver_attr_list, query=True, selectItem=True)
        driven_attr = cmds.textScrollList(self.driven_attr_list, query=True, selectItem=True)

        if not driver_attr or not driven_attr:
            cmds.warning("Please select attributes for both the driver and driven.")
            return

        driver_attr = driver_attr[0]
        driven_attr = driven_attr[0]

        # Fetch driver and driven values
        driver_neg = cmds.floatFieldGrp(self.driver_neg_value, query=True, value1=True)
        driver_zero = cmds.floatFieldGrp(self.driver_zero_value, query=True, value1=True)
        driver_pos = cmds.floatFieldGrp(self.driver_pos_value, query=True, value1=True)

        driven_neg = cmds.floatFieldGrp(self.driven_neg_value, query=True, value1=True)
        driven_zero = cmds.floatFieldGrp(self.driven_zero_value, query=True, value1=True)
        driven_pos = cmds.floatFieldGrp(self.driven_pos_value, query=True, value1=True)

        # Set driven keys for negative, zero, and positive values
        cmds.setDrivenKeyframe(self.driven + '.' + driven_attr, cd=self.driver + '.' + driver_attr,
                               driverValue=driver_neg, value=driven_neg)
        cmds.setDrivenKeyframe(self.driven + '.' + driven_attr, cd=self.driver + '.' + driver_attr,
                               driverValue=driver_zero, value=driven_zero)
        cmds.setDrivenKeyframe(self.driven + '.' + driven_attr, cd=self.driver + '.' + driver_attr,
                               driverValue=driver_pos, value=driven_pos)

        # Force update tangents and infinity options by re-selecting driven keys
        for driver_value in [driver_neg, driver_zero, driver_pos]:
            cmds.selectKey(self.driven + '.' + driven_attr, attribute=driven_attr, time=(driver_value,))
            cmds.keyTangent(inTangentType='spline', outTangentType='spline')
            cmds.setInfinity(self.driven + '.' + driven_attr, preInfinite='linear', postInfinite='linear')

        # Clear selection and display success message
        cmds.select(clear=True)
        cmds.inViewMessage(amg='Driven Keys Set with tangents!', pos='topCenter', fade=True)

    def open_graph_editor(self, *args):
        # Select the driven object
        if hasattr(self, 'driven') and self.driven:
            cmds.select(self.driven)
            # Open the Graph Editor
            cmds.GraphEditor()
        else:
            cmds.warning("No driven object loaded!")

DrivenKeyUI()
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


import bpy
from bpy.types import Operator


bl_info = {
    "name": "Viewport Render Markers",
    "author": "Edward S. White",
    "description": "Viewport render only frames with timeline markers",
    "blender": (2, 80, 0),
    "version": (0, 3, 6),
    "location": "View3D > View Menu > Viewport Render Markers",
    "category": "Render"
}


def ShowMessageBox(message="", title="Message Box", icon='INFO'):

    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)


def make_key_markers():
    # Create keyframes for each marker in the timeline
    scene = bpy.context.scene

    # Create a variable to store Y rotation values
    y_spinner = 0.0

    # Deselect all
    bpy.ops.object.select_all(action='DESELECT')

    # Add an empty object for setting keyframes
    bpy.ops.object.empty_add(type='SINGLE_ARROW', align='WORLD')

    # Scale the empty down to make it almost invisible
    bpy.context.object.scale = (0.000001, 0.000001, 0.000001)

    # Get list of all markers in the scene
    mlist = bpy.context.scene.timeline_markers

    # sort markers by time
    markerlist = sorted(mlist, key=lambda mlist: mlist.frame)

    # step through markers and save a keyframe on the empty (use Y rotation)
    for m in markerlist:
        scene.frame_current = m.frame
        y_spinner += 0.0174533
        bpy.context.object.rotation_euler[1] = y_spinner
        bpy.context.object.keyframe_insert(
            data_path="rotation_euler", frame=m.frame)


class VRM_OT_modalvranimmarks(Operator):
    """Viewport render holding on timeline marker positions"""
    bl_idname = "render.modalvranimmarks"
    bl_label = "Viewport Render Holding on Markers"
    bl_description = "Viewport render holding on timeline marker positions"

    _timer = None
    scene = None
    markers = None
    renderpath = None
    prevpath = None
    prevframe = None
    stop = None
    rendering = None

    def vrmcancel(self, dummy, thrd=None):
        self.scene.frame_current = self.prevframe
        self.scene.render.filepath = self.prevpath
        print("Cancelled")
        self.stop = True

    def draw(self, context):

        layout = self.layout
        row = layout.row()
        row.label(text="Output file location")

        row = layout.row()
        row.label(text="Press Esc if location is not correct.")

        file_path = bpy.context.scene.render.filepath
        box = layout.box()
        row = box.row()
        row.alignment = 'LEFT'
        row.label(text=file_path)

    def invoke(self, context, event):

        scene = bpy.context.scene
        self.scene = scene
        # Check for not a image format
        animation_formats = ['FFMPEG', 'AVI_JPEG', 'AVI_RAW']
        if not scene.render.image_settings.file_format in animation_formats:
            print("Image file formats are not supported.")
            ShowMessageBox("Image file formats are not supported.",
                           "Viewport Render Holding on Markers",
                           'ERROR')
            return {'FINISHED'}
        # Get list of all markers in the scene
        mlist = scene.timeline_markers
        if not mlist:
            print("No markers in the current scene.")
            ShowMessageBox("No markers in the current scene.",
                           "Viewport Render Holding on Markers",
                           'ERROR')
            return {'FINISHED'}
        self.markers = sorted(mlist, key=lambda mlist: mlist.frame)
        self.renderpath = scene.render.filepath
        self.prevpath = scene.render.filepath
        self.prevframe = scene.frame_current

        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):

        bpy.app.handlers.render_cancel.append(self.vrmcancel)

        scene = bpy.context.scene
        wm = bpy.context.window_manager
        self._timer = wm.event_timer_add(0.1, window=bpy.context.window)
        wm.modal_handler_add(self)

        return {"RUNNING_MODAL"}

    def modal(self, context, event):

        if event.type in {'ESC'}:
            self.vrmcancel(context)
            return {'CANCELLED'}

        if event.type == 'TIMER':
            if True in (not self.markers, self.stop is True):
                bpy.app.handlers.render_cancel.remove(self.vrmcancel)
                bpy.context.window_manager.event_timer_remove(self._timer)
                bpy.context.scene.frame_current = self.prevframe
                bpy.context.scene.render.filepath = self.prevpath
                ShowMessageBox("Finished Rendering",
                               "Viewport Render Holding on Markers",
                               'INFO')
                return {"FINISHED"}

            elif not self.rendering:
                scene = bpy.context.scene
                scene.render.filepath = self.renderpath + "_"
                scene.frame_current = scene.frame_start
                make_key_markers()
                bpy.ops.render.opengl(animation=True, render_keyed_only=True)
                bpy.ops.object.delete(use_global=False)
                self.stop = True

        return {"PASS_THROUGH"}


classes = (
    VRM_OT_modalvranimmarks,
)


def menu_func_animrender(self, context):
    self.layout.operator(VRM_OT_modalvranimmarks.bl_idname,
                         text="Viewport Render Holding on Markers",
                         icon='RENDER_ANIMATION'
                         )


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.VIEW3D_MT_view.append(menu_func_animrender)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    bpy.types.VIEW3D_MT_view.remove(menu_func_animrender)


if __name__ == "__main__":
    register()

""""
improved from amandeep addon Ngons loop select
thks to Kaio for hotkey script on git hub

Tip: if loop incompleted, complete it ctrl + left click, on last edge of the loop

Todo:hot key + prefs

"""
bl_info = {
    "name": "Loop Select PLus",
    "author": "1C0D inspired by amandeep",
    "version": (1, 0, 0),
    "blender": (3, 0, 0),
    "description": "Edge Loop Selection by topology",
    "category": "Object",
}

import bpy
import bmesh
from math import degrees

def angle_min(self,e)->bool:
    angle1 = degrees(e.calc_face_angle_signed())
    return abs(angle1) > self.angle

def angle(self,e1,e2,vert):
    v1=e1.other_vert(vert)
    v2=e2.other_vert(vert)
    if not v1 or not v2:
        return 0
    a1=vert.co-v1.co
    if self.orient:
        a2=v2.co-vert.co
    else:
        a2=vert.co-v2.co        
    angle=degrees(a1.angle(a2))
    return angle     

def diff_face_angl(self,e,angle0)->float:
    angle1 = degrees(e.calc_face_angle_signed())
    diff = abs(angle0-angle1)
    if (int(angle0) ^ int(angle1)) < 0:
        return None
    return diff

def append_edge(linked_edges,verts2check,loop_edges,checkedverts,estart,v,bm):
    e = linked_edges[-1][0]
    if e in loop_edges:
        return False
    if e.other_vert(v) not in checkedverts and e.other_vert(v) not in verts2check:
        verts2check.append(e.other_vert(v))
    loop_edges.append(e)
    bm.select_history.add(e) #active
    estart = e
    return estart


class MESH_OT_loop_select_plus(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "mesh.loop_select_plus"
    bl_label = "loop select plus"
    bl_options = {"REGISTER", "UNDO"}    
    shift:bpy.props.BoolProperty(default=False,options={'HIDDEN'})
    orient:bpy.props.BoolProperty(default=True)
    angle:bpy.props.FloatProperty(default=20,min=0,max=180)

    @classmethod
    def poll(cls, context):
        return (context.object is not None and
                context.object.type == 'MESH' and
                context.object.data.is_editmode)
                
    def get_loop(self, bm, e0):

        verts2check = e0.verts[:]
        checkedverts = []
        loop_edges = [e0]
        counter=0
        estart = e0
        while verts2check:
            counter+=1
            v = verts2check.pop()
            checkedverts.append(v)
            link_edges = v.link_edges[:]                 
            try:                        
                link_edges.remove(estart)
            except:
                pass
            
            face_angle_start = degrees(estart.calc_face_angle_signed())       
            linked_edges = [(e,diff_face_angl(self,e,face_angle_start)) 
                                for e in link_edges if e.is_manifold and angle_min(self,e) 
                                    and diff_face_angl(self,e,face_angle_start) is not None] 
                                               
            if len(linked_edges)==1: 
                ok=append_edge(linked_edges,verts2check,loop_edges,checkedverts,estart,v,bm)
                linked_edges=[]
                if ok: 
                    estart=ok
                else: break   
                               
            if len(linked_edges)>=2:
                linked_edges.sort(key=lambda x: angle(self,estart,x[0],v))
                linked_edges = linked_edges[-1:]
                
            if linked_edges:
                ok=append_edge(linked_edges,verts2check,loop_edges,checkedverts,estart,v,bm)
                if ok: 
                    estart=ok
                else: break   
                    
            if counter==400: #to avoid infinite loop
                break
            
        loop_edges = list(set(loop_edges))
        return loop_edges

    def invoke(self, context, event):
        self.loc = event.mouse_region_x, event.mouse_region_y
        return self.execute(context)

    def execute(self, context):
        me = context.active_object.data
        bm = bmesh.from_edit_mesh(me)
        save_mode = bpy.context.tool_settings.mesh_select_mode
        bpy.context.tool_settings.mesh_select_mode = (False, True, False)        
        bpy.ops.view3d.select(extend=self.shift, location=self.loc)
        if not bm.select_history[-1]:
            return {'CANCELLED'}        
        e0 = bm.select_history[-1] #last edge        
        if not e0.is_manifold:
            return {'CANCELLED'}
        loop = self.get_loop(bm, e0)
        if loop:
            [e.select_set(True) for e in loop]
        me.update()
        return {'FINISHED'}


class LSP_addonPrefs(bpy.types.AddonPreferences):
    bl_idname = __name__

    kmi_type: bpy.props.StringProperty()
    kmi_value: bpy.props.StringProperty()
    kmi_alt: bpy.props.BoolProperty()
    kmi_alt_1: bpy.props.BoolProperty()
    kmi_ctrl: bpy.props.BoolProperty()
    kmi_ctrl_1: bpy.props.BoolProperty()
    kmi_shift: bpy.props.BoolProperty()
    kmi_shift_1: bpy.props.BoolProperty()

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        kmi = self.ensure_kmi(1)
        if kmi:
            draw_kmi(kmi, layout, col, 1, 1, "Loop Select")

        kmi = self.ensure_kmi(2)
        if kmi:
            draw_kmi(kmi, layout, col, 1, 1, "Extend Loop Select")
           

    # when the user changes a key, the ui is redrawn and this is
    # called to sync kmi_type, kmi_alt, kmi_ctrl and kmi_shift
    # with actual kmi values
    def ensure_kmi(self,key):
        try:
            if key==1:
                kmi = addon_keymaps[0][1]
            else:
                kmi = addon_keymaps[1][1]
                
        except IndexError:
            return False

        else:
            # it's important to use conditionals because
            # this runs every time the ui is redrawn
            if kmi.type != self.kmi_type:
                self.kmi_type = kmi.type
            if kmi.value != self.kmi_value:
                self.kmi_value = kmi.value
            if key == 1:
                if kmi.alt != self.kmi_alt:
                    self.kmi_alt = kmi.alt
                if kmi.ctrl != self.kmi_ctrl:
                    self.kmi_ctrl = kmi.ctrl
                if kmi.shift != self.kmi_shift:
                    self.kmi_shift = kmi.shift
            else:
                if kmi.alt != self.kmi_alt_1:
                    self.kmi_alt_1 = kmi.alt
                if kmi.ctrl != self.kmi_ctrl_1:
                    self.kmi_ctrl_1 = kmi.ctrl
                if kmi.shift != self.kmi_shift_1:
                    self.kmi_shift_1 = kmi.shift                
        return kmi


# ui draw function for kmi
# a more complete version can be found in scripts/modules/rna_keymap_ui.py
def draw_kmi(kmi, layout, col, kmi_count, kmi_idx,label):
    map_type = kmi.map_type

    col = col.column(align=True)
    row = col.row()
    row.scale_y = 1.3
    split = row.split()
    row = split.row()
    row.alignment = 'RIGHT'
    row.label(text=label)
    row = split.row(align=True)
    row.prop(kmi, "type", text="", full_event=True)
    split.separator(factor=0.5)

    col.separator(factor=1.5)
    row = col.row()
    split = row.split()
    row = split.row()
    row.alignment = 'RIGHT'
    row.label(text="Type")
    row = split.row()
    row.prop(kmi, "value", text="")
    split.separator(factor=0.5)

    if map_type not in {'TEXTINPUT', 'TIMER'}:

        col.separator(factor=1.5)
        row = col.row()
        split = row.split()
        row = split.row()
        row.alignment = 'RIGHT'
        row.label(text="Modifier")

        row = split.row(align=True)
        row.prop(kmi, "any", toggle=True)
        row.prop(kmi, "shift", toggle=False)
        row.prop(kmi, "ctrl", toggle=True)
        split.separator(factor=0.5)

        row = col.row(align=True)
        split = row.split()
        split.separator()

        row = split.row(align=True)
        row.prop(kmi, "alt", toggle=True)
        row.prop(kmi, "oskey", text="Cmd", toggle=True)
        row.prop(kmi, "key_modifier", text="", event=True)
        split.separator(factor=0.5)
        col.separator(factor=3)


addon_keymaps = []


def register():
    bpy.utils.register_class(MESH_OT_loop_select_plus)
    bpy.utils.register_class(LSP_addonPrefs)
    p = bpy.context.preferences.addons[__name__].preferences

    # during addon registration, get the kmi values stored in preferences.
    # if they are none (usually after install), resort to default value
    def add_key(s,pps):
        default_type = "LEFTMOUSE"
        default_value = "DOUBLE_CLICK"

        kmi_type = p.kmi_type or default_type
        kmi_value = p.kmi_value or default_value

        alt = p.kmi_alt or 0
        ctrl = p.kmi_ctrl or 0
        shift = p.kmi_shift or s

        kc = bpy.context.window_manager.keyconfigs.addon
        km = kc.keymaps.get('Mesh')
        if not km:
            km = kc.keymaps.new('Mesh', space_type='EMPTY')

        kwargs = {'alt': alt, 'ctrl': ctrl, 'shift': shift}
        kmi = km.keymap_items.new(
            "mesh.loop_select_plus", kmi_type, kmi_value, **kwargs)
        kmi.properties.shift = pps
        addon_keymaps.append((km, kmi))
    
    add_key(s=0,pps=False) 
    add_key(s=1,pps=True)  
        
def unregister():
    bpy.utils.unregister_class(LSP_addonPrefs)
    bpy.utils.unregister_class(MESH_OT_loop_select_plus)
    for (km, kmi) in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

"""To support rebuilding the atlas + png to an `universal` format; as `hinge` point is definitely lost"""
from functools import partial 
import json, io, sys

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Gdk, GdkPixbuf

from region import parse_atlas, extract_region, put_hinge, add_provider_for_screen

from typing import Tuple, Optional

import logging 
logger = logging.getLogger(__name__)

def put_hinge_on_image(image: Gtk.Image)-> Gtk.Overlay:
    overlay = Gtk.Overlay()
    hinge = Gtk.Box(name="part_hinge")
    hinge.set_size_request(4, 4)
    hinge.set_halign(Gtk.Align.CENTER)
    hinge.set_valign(Gtk.Align.CENTER)
    overlay.add(image)
    overlay.add_overlay(hinge)
    return overlay

def build_display_rebuilt(fixed: Gtk.Fixed, items: list, past_provider: Gtk.CssProvider) -> tuple:
    """Rebuild all associating item within a [Fixed] frame"""
    context_rotation = []
    draw_list = []
    for name, image_pixbuf, size, hinge, position, rotation, scale in items:
        # create a substitute pixbuf so that item is centered on `hinge`
        true_width, true_height = size 
        new_size = max(true_width*2, true_height*2)
        centered = GdkPixbuf.Pixbuf.new(colorspace=image_pixbuf.get_colorspace(), has_alpha=True, bits_per_sample=image_pixbuf.get_bits_per_sample(), width=new_size, height=new_size)
        hinge_x, hinge_y = hinge
        new_x, new_y = new_size//2-hinge_x, new_size//2-hinge_y # created so that the hinge_x, hinge_y of the old matches size/2 of new 
        image_pixbuf.copy_area(0, 0, true_width, true_height, centered, new_x, new_y)
        # create appropriate image 
        image = Gtk.Image.new_from_pixbuf(centered)
        # create associating css class to be used for rotation
        image.set_name("al_" + name)
        if rotation or scale:
            rotation_str = "rotate({:f}turn)".format(rotation) if rotation else ""
            scale_str = "scale({:f})".format(scale) if scale else ""
            context_rotation.append("#{:s} {{ -gtk-icon-transform: {:s} {:s}; }}".format("al_" + name, rotation_str, scale_str))
        draw_list.append( (image, new_size, position) )
    # now with the draw_list, calculate the maximum reach of each image backward. TODO also reach forward?
    x_offset = y_offset = 0
    for image, size, (x, y) in draw_list:
        if size // 2 - x > x_offset:
            x_offset = size // 2 - x
        if size // 2 - y > y_offset:
            y_offset = size // 2 - y
    print("Offsets: {} {}".format(x_offset, y_offset))
    for image, size, (x, y) in draw_list:
        print("Put image ({}) at ({} {}), targetting hinge ({} {})".format(size, x+x_offset, y+y_offset, x+x_offset + size//2, y+y_offset + size//2))
        # draw properly this time 
        overlay = put_hinge_on_image(image)
        fixed.put(overlay, x+x_offset - size//2, y+y_offset - size//2) 
    # additionally, update the CssProvider with associating classes 
    context = "\n".join(context_rotation).encode("utf-8")
    if past_provider:
        past_provider.load_from_data(context)
        return fixed, past_provider
    else:
        provider = add_provider_for_screen(data=context)
        return fixed, provider

class MoveablePart(Gtk.Overlay):
    """Moveable part that is meant to be put into a Gtk.Fixed as a pseudo-canvas. Should bind with an interactable controller unit to allow modification.
    TODO allow reupdate hinges too."""
    def __init__(self, image_name: str, image_pixbuf: GdkPixbuf.Pixbuf, pixbuf_size: Tuple[int, int], hinge: Tuple[int, int], *args, reuse_provider: Optional[Gtk.CssProvider]=None, **kwargs):
        super(MoveablePart, self).__init__(*args, **kwargs)
        true_width, true_height = self._pixbuf_size = pixbuf_size 
        self.size = new_size = max(true_width*2, true_height*2)
        # put position will put the point at this centered offset
        self._center_offset = offset = new_size // 2
        centered = GdkPixbuf.Pixbuf.new(colorspace=image_pixbuf.get_colorspace(), has_alpha=True, bits_per_sample=image_pixbuf.get_bits_per_sample(), width=new_size, height=new_size)
        hinge_x, hinge_y = self._hinge = hinge
        new_x, new_y = offset-hinge_x, offset-hinge_y # created so that the hinge_x, hinge_y of the old matches size/2 of new 
        print("Copy: [{} = {} {}] 0 0 {} {} -> [{}] {} {} {} {}".format(image_name, image_pixbuf.get_width(), image_pixbuf.get_height(), true_width, true_height, new_size, new_x, new_y, new_x+true_width, new_y+true_height))
        image_pixbuf.copy_area(0, 0, true_width, true_height, centered, new_x, new_y)
        # create appropriate image 
        self.image = image = Gtk.Image.new_from_pixbuf(centered)
        image.set_name(image_name)
        self.add(image)
        # add additional hinge spot & matching region box
        self.hinge_obj = hinge = Gtk.Box(name="part_hinge")
        hinge.set_size_request(4, 4)
        hinge.set_halign(Gtk.Align.CENTER)
        hinge.set_valign(Gtk.Align.CENTER)
        self.add_overlay(hinge)
#        self._region_box = region_box = Gtk.Box(name="part_region") # cant work with rotation; simply ignore
#        region_box.set_size_request(true_width, true_height)
#        region_box.set_halign(Gtk.Align.CENTER)
#        region_box.set_valign(Gtk.Align.CENTER)
#        self.add_overlay(region_box)

        self._image_pixbuf = image_pixbuf
        self._rotation = None 
        self._scale = None
        self._image_name = image_name
        self._provider = add_provider_for_screen(data="") if not reuse_provider else reuse_provider

        # keep for now
        self._z_order = 0

    def put_to_fixed(self, parent: Gtk.Fixed, x: int, y: int):
        # put appropriately
        parent.put(self, x - self._center_offset, y - self._center_offset)
        self._position = x, y

    def update(self, position: Optional[Tuple]=None, rotation: Optional[float]=None, scale: Optional[float]=None):
        if position:
            # move to new position accordingly 
            self._position = x, y = position 
            self.get_parent().move(self, x - self._center_offset, y - self._center_offset)
        if rotation is not None or scale is not None:
            rotation = rotation if rotation is not None else self._rotation 
            self._rotation = rotation
            rotation_str = "rotate({:f}turn)".format(rotation) if rotation is not None else ""
            scale = scale if scale is not None else self._scale 
            self._scale = scale
            scale_str = "scale({:f})".format(scale) if scale is not None else ""
            self._provider.load_from_data("#{:s} {{ -gtk-icon-transform: {:s} {:s}; }}".format(self._image_name, rotation_str, scale_str).encode("utf-8"))
            
    def rebuild_hinge(self, new_hinge: Tuple, replace_self=True):
        # when rebuilding the hinge, image have to be completely replaced. Try to keep the old provider with self
        new_image = MoveablePart(self._image_name, self._image_pixbuf, self._pixbuf_size, new_hinge, reuse_provider=self._provider)
        if replace_self:
            # put on the new one at the exact same spot
            new_image.put_to_fixed(self.get_parent(), *self._position)
            new_image.update(rotation=self._rotation, scale=self._scale)
            self.get_parent().remove(self)
            new_image.show_all()
        # return the new one 
        return new_image

    def get_properties(self):
        # get required properties
        return self._image_name, self._hinge, self._position, self._rotation, self._scale, self._z_order

class Mover(Gtk.Grid):
    """Object to bind & control the associated part."""
    def __init__(self, target: MoveablePart, target_name: str, initial_position: Tuple[int, int], initial_rotation: float, initial_scale: float, initial_hinge: Tuple[int, int], initial_z=0, *args, **kwargs):
        super(Mover, self).__init__(*args, name="mover_item", row_spacing=10, column_spacing=10, **kwargs)
        self.target = target 
        # construct appropriate fields
        header = Gtk.Label(label=target_name)
        self.attach(header, 0, -1, 4, 1)
        inputs = []
        for i, key in enumerate(["x", "y", "rotation", "scale", "hinge_x", "hinge_y", "z"]):
            col, row = i % 2, i // 2
            self.attach(Gtk.Label(label=key), col*2, row, 1, 1)
            new_input = Gtk.Entry(input_purpose=Gtk.InputPurpose.NUMBER)
            new_input.connect('changed', partial(self.on_changed_input, key=key))
            self.attach(new_input, col*2+1, row, 1, 1)
            inputs.append(new_input)
        self._inputs = inputs
        for ip, v in zip(inputs, list(initial_position) + [initial_rotation, initial_scale] + list(initial_hinge) + [initial_z]):
            ip.set_text(str(v))

    def on_changed_input(self, widget: Gtk.Entry, key: str=None):
#        if not self._inputs:
#            return # prevent initial set_text causing trouble
        #print("Changed [{}]: {} -> {}".format(key, widget, widget.get_text()))
#        try:
            if key in ("x", "y"):
                xip, yip = self._inputs[:2]
                x = int(xip.get_text())
                y = int(yip.get_text())
                if x > 600 or y > 600:
                    return # do not update when out of bound
                self.target.update(position=(x, y))
            elif key == "rotation":
                rip = self._inputs[2]
                rotation = float(rip.get_text())
                self.target.update(rotation=rotation)
            elif key == "scale":
                sip = self._inputs[3]
                scale = float(sip.get_text())
                self.target.update(scale=scale)
            elif key in ("hinge_x", "hinge_y"):
                hxip, hyip = self._inputs[4:6]
                hx = int(hxip.get_text())
                hy = int(hyip.get_text())
                if hx > self.target._pixbuf_size[0] or hy > self.target._pixbuf_size[1]:
                    return # do not allow hinge to be outside of the image, for now 
                new_target = self.target.rebuild_hinge((hx, hy))
                self.target = new_target
            elif key == "z":
                # just keep for now. 
                self.target._z_order = int(self._inputs[6].get_text())
            else:
                print("Unknown key {}, check your code.".format(key))
#        except Exception as e:
#            print(*sys.exc_info())


class Rebuilder(Gtk.Box):
    def __init__(self, available_parts: dict, no_load: bool=False, part_list: Optional=None, *args, **kwargs):
        # TODO make a modifiable part list 
        super(Rebuilder, self).__init__(*args, orientation=Gtk.Orientation.HORIZONTAL, **kwargs)
        self.canvas = Gtk.Fixed(name="canvas")
        self.canvas.set_size_request(600, 600)
        self.pack_start(self.canvas, False, False, 0)

        edit_section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.pack_end(edit_section, False, False, 0)

        self.editable = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroller.set_hexpand(True)
        scroller.add(self.editable)
        edit_section.pack_start(scroller, True, True, 0)
        # add button 
        self._available_parts = available_parts 
        control_section = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, name="add_item")
        save_btn = Gtk.Button(label="SAVE")
        save_btn.connect("clicked", self.save)
        control_section.pack_start(save_btn, False, False, 0)
        control_section.pack_start(Gtk.Separator(), False, False, 0)
        add_btn = Gtk.Button(label="ADD")
        part_names = [k for k in self._available_parts.keys()]
        model = Gtk.ListStore(str); [model.append((k,)) for k in part_names]
        renderer = Gtk.CellRendererText()
        dropdown = Gtk.ComboBox(model=model)
        dropdown.pack_start(renderer, True) # wtf this need such complicated support
        dropdown.add_attribute(renderer, "text", 0)
        add_btn.connect("clicked", lambda widget: self.add_item(part_names[dropdown.get_active()]))
        control_section.pack_start(add_btn, False, False, 0)
        control_section.pack_start(dropdown, True, True, 0)
        edit_section.pack_end(control_section, False, False, 0)
        
        self.used = set()
        if no_load:
            return # do not reload, blank canvas
        saved = self.load()
        if saved:
            for name, (hinge, position, rotation, scale, z) in sorted(saved.items(), key=lambda v:v[1][-1]):
                pixbuf, *size = pixbufs_dict[name]
                self.add_item(name, properties=(pixbuf, size, hinge, position, rotation, scale), z=z)
            self.used.update(saved.keys())
        return # do not run the below section
        for name, pixbuf, size, hinge, position, rotation, scale in part_list:
            # center everything
            position = position[0] + 300, position[1] + 300
            part_image = MoveablePart(name, pixbuf, size, hinge)
            part_image.put_to_fixed(self.canvas, *position)
            part_image.update(rotation=rotation, scale=scale)
            mover = Mover(part_image, name, position, rotation if rotation is not None else 0.0, scale if scale is not None else 1.0, hinge)
            self.editable.pack_start(mover, False, False, 0)

    def add_item(self, name: str, properties: Optional[list]=None, z: Optional[int]=0):
        if name in self.used:
            print("Item {} had already been created.".format(name))
            return
        if not properties:
            # query and create an item from a list of possible parts 
            pixbuf, true_width, true_height = self._available_parts[name]
            # infer default properties
            size = true_width, true_height
            hinge, position, rotation, scale = default = (true_width//2, true_height//2), (0, 0), None, None 
        else:
            # item is created with already defined properties
            pixbuf, size, hinge, position, rotation, scale = properties
        part_image = MoveablePart(name, pixbuf, size, hinge)
        part_image.put_to_fixed(self.canvas, *position)
        part_image.update(rotation=rotation, scale=scale)
        mover = Mover(part_image, name, position, rotation if rotation is not None else 0.0, scale if scale is not None else 1.0, hinge, initial_z=z)
        self.editable.pack_start(mover, False, False, 0)
        self.canvas.show_all()
        self.editable.show_all()
        self.used.add(name)
    
    def save(self, widget: Gtk.Widget=None):
        info = {}
        for item in self.editable.get_children():
            if isinstance(item, Mover):
                # valid; keep copy of current property 
                name, *data = item.target.get_properties()
                info[name] = data 
        with io.open("current.json", "w", encoding="utf-8") as jf:
            json.dump(info, jf)
            print("Dumped current info: {}".format(info))
    
    def load(self, widget: Gtk.Widget=None):
        try:
            with io.open("current.json", "r", encoding="utf-8") as jf:
                return json.load(jf)
        except Exception:
            print(*sys.exc_info())
        return None

if __name__ == "__main__":
    # default css for now 
    add_provider_for_screen(path="all.css")
    rotation_provider = add_provider_for_screen(data="")
    # default window to house the region
    window = Gtk.Window()
    pixbufs_dict = extract_region(sys.argv[1])
    print(pixbufs_dict.keys())
    # just take out the body for now 
    parts = []
    p, w, h = pixbufs_dict["hair_B"]
    parts.append( ("hair_B", p, (w, h), (w//2, 10), (-10, -70), None, 0.5) )
    p, w, h = pixbufs_dict["body"]
    parts.append( ("body", p, (w, h), (w//2, h//2), (0, 0), None, None) )
    p, w, h = pixbufs_dict["face"]
    parts.append( ("face", p, (w, h), (w//2, h-15), (-5, -45), None, 0.5) )
    p, w, h = pixbufs_dict["hair_F"]
    parts.append( ("hair_F", p, (w, h), (w//2, 10), (6, -103), None, 0.5) )
#    display = Gtk.Fixed()
#    display.set_size_request(600, 600)
#    build_display_rebuilt(display, parts, past_provider=rotation_provider)
#    window.add(display)
    window.add(Rebuilder(pixbufs_dict, part_list=parts))
    window.show_all()
    window.connect("delete-event", Gtk.main_quit)
    Gtk.main()

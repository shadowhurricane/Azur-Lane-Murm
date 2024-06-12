"""To parse & show appropriate region defined by png & atlas."""
import io

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Gdk, GdkPixbuf

import logging 
logger = logging.getLogger(__name__)

def parse_atlas(text: str):
    properties = dict()
    items = dict()
    current_item = current_item_name = None
    for row in text.split("\n"):
        if not row.strip():
            continue # blank, ignore
        if row.startswith("  "):
            # is a sub-property row 
            if current_item is None:
                logger.debug("Subprop \"{}\" cannot be assigned; discarded".format(row.strip()))
                continue 
            sprop_name, sprop_val = [p.strip() for p in row.split(":")]
            current_item[sprop_name] = sprop_val
        elif ":" in row:
            # is a property row, add it into the property 
            prop_name, prop_val = [p.strip() for p in row.split(":")]
            properties[prop_name] = prop_val
        else:
            # is a header row; initiate new item.  
            current_item_name = row.strip()
            current_item = items[current_item_name] = dict()
    # void any useless (propertyless) items
    items = {k: v for k, v in items.items() if v }
    return properties, items

def convert_listnum(raw: str, num_type=int):
    # convert number in format of x,y,..
    return [num_type(v) for v in raw.split(",")]

def put_hinge(overlay: Gtk.Fixed, x: int, y: int):
    hinge = Gtk.Box(name="part_hinge")
    hinge.set_size_request(4, 4)
    overlay.put(hinge, x, y)

def build_region(base: str) -> Gtk.Widget:
    # 1. load atlas in raw form
    with io.open(base + ".atlas", "r", encoding="utf-8") as af:
        properties, parts = parse_atlas(af.read())
    logger.debug("Parts: {}".format(parts))
    # 2. build the overlay & image base 
    frame = Gtk.Overlay()
    width, height = convert_listnum(properties["size"])
    logger.debug("Loaded base image at: {}".format(base + ".png"))
    image_pixbuf = GdkPixbuf.Pixbuf.new_from_file(base + ".png")
    image = Gtk.Image.new_from_pixbuf(image_pixbuf)
    frame.add(image)
    overlay = Gtk.Fixed()
    overlay.set_hexpand(True)
    overlay.set_vexpand(True)
    frame.add_overlay(overlay)
    for name, part_properties in parts.items():
        # create box with appropriate value 
        try:
            x, y = convert_listnum(part_properties["xy"])
            width, height = convert_listnum(part_properties["size"])
            rotated = part_properties["rotate"] == "true"
            # box to display part
            if rotated:
                width, height = height, width
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, name="part_region")
            box.set_size_request(width, height)
            # additional labeling with the internal name
            label = Gtk.Label(label=name, name="part_region_desc")
            box.pack_start(label, False, False, 0)
            overlay.put(box, x, y)
            # also show the hinge 
            hx, hy = convert_listnum(part_properties["orig"])
            if rotated:
                hx, hy = hy, hx
            true_hx, true_hy = width - hx, height-hy
            put_hinge(overlay, x+true_hx-2, y+true_hy-2)
        except Exception:
            logger.error("Failed to draw for {}: {}".format(name, part_properties))
    return frame 

def extract_region(base: str) -> dict:
    with io.open(base + ".atlas", "r", encoding="utf-8") as af:
        properties, parts = parse_atlas(af.read())
    # extract the appropriate pixbuf region using the information inferred above
    logger.debug("Loaded base image at: {}".format(base + ".png"))
    image_pixbuf = GdkPixbuf.Pixbuf.new_from_file(base + ".png")
    pixbufs_dict = dict()
    for name, part_properties in parts.items():
        x, y = convert_listnum(part_properties["xy"])
        width, height = convert_listnum(part_properties["size"])
        rotated = part_properties["rotate"] == "true"
        if rotated:
            width, height = height, width
        # strip the pixbuf accordingly
        part_pixbuf = image_pixbuf.new_subpixbuf(x, y, width, height)
        # if rotated; realign it to similar to the rest 
        if rotated:
            part_pixbuf = part_pixbuf.rotate_simple(GdkPixbuf.PixbufRotation.CLOCKWISE)
            width, height = height, width # return appropriate 
        pixbufs_dict[name] = (part_pixbuf, width, height)
    return pixbufs_dict

def add_provider_for_screen(path: str=None, data: str=None) -> Gtk.CssProvider:
    provider = Gtk.CssProvider()
    if path: # load from a specific path on disk
        provider.load_from_path(path)
    else: # load from info str
        provider.load_from_data(data.encode("utf-8"))
    styleContext = Gtk.StyleContext()
    styleContext.add_provider_for_screen(Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    return provider

if __name__ == "__main__":
    import sys 
    # default css for now 
    add_provider_for_screen(path="all.css")
    # default window to house the region
    window = Gtk.Window()
    display = build_region(sys.argv[1])
    window.add(display)
    window.show_all()
    window.connect("delete-event", Gtk.main_quit)
    Gtk.main()

import math
import glob
import os
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates

def create_oblique(font_path, output_path, angle_degrees=-10):
    print(f"Processing: {os.path.basename(font_path)}")
    font = TTFont(font_path)
    
    # 1. Drop global hinting tables completely
    for table in ['fpgm', 'prep', 'cvt ', 'hdmx', 'VDMX']:
        if table in font:
            del font[table]
    
    skew_factor = math.tan(math.radians(abs(angle_degrees)))

    # 2. Update 'post' table
    if 'post' in font:
        font['post'].italicAngle = angle_degrees

    # 3. Update 'hhea' table (Caret Slope for cursor rendering)
    if 'hhea' in font:
        rise = font['hhea'].caretSlopeRise
        font['hhea'].caretSlopeRun = int(round(rise * skew_factor))

    # 4. Update 'OS/2' table
    if 'OS/2' in font:
        font['OS/2'].fsSelection |= (1 << 0)   # Set bit 0 (Italic)
        font['OS/2'].fsSelection &= ~(1 << 6)  # Unset bit 6 (Regular)

    # 5. Update 'head' table
    if 'head' in font:
        font['head'].macStyle |= (1 << 1)      # Set bit 1 (Italic)

    # 6. Update 'name' table strings
    if 'name' in font:
        for record in font['name'].names:
            text = record.toUnicode()
            
            if record.nameID in (2, 3, 4):
                if "Italic" not in text and "Oblique" not in text:
                    new_text = "Italic" if text == "Regular" else text + " Italic"
                    record.string = new_text.encode('utf-16-be') if record.platformID == 3 else new_text.encode('mac-roman')
            
            elif record.nameID == 6:
                if "Italic" not in text:
                    new_text = text.replace("Regular", "Italic")
                    if "Italic" not in new_text:
                        new_text += "Italic"
                    record.string = new_text.encode('utf-16-be') if record.platformID == 3 else new_text.encode('mac-roman')

    # 7. Skew the Glyphs in 'glyf' table and strip bytecode
    glyf = font['glyf']
    for glyph_name in font.getGlyphOrder():
        glyph = glyf[glyph_name]
        
        # Decompile to ensure we can read/write coordinates and components
        glyph.expand(glyf)
        
        # Clear bytecode safely without using external classes
        if hasattr(glyph, 'program'):
            # Setting it to an empty bytecode object satisfies compiler checks
            glyph.program.fromBytecode(b'') 
        
        if glyph.isComposite():
            # Adjust offsets for composite glyphs (like accents)
            for comp in glyph.components:
                if hasattr(comp, 'x') and hasattr(comp, 'y'):
                    new_x = comp.x + (comp.y * skew_factor)
                    comp.x = int(round(new_x))
        elif glyph.numberOfContours > 0:
            # Adjust coordinates of simple glyphs
            new_coords = []
            for x, y in glyph.coordinates:
                new_x = x + (y * skew_factor)
                new_coords.append((int(round(new_x)), y))
            glyph.coordinates = GlyphCoordinates(new_coords)
            
        # Recalculate bounding boxes for the slanted glyph
        glyph.recalcBounds(glyf)
        
        # 8. Update Left Side Bearings in 'hmtx' based on new bounding box
        if 'hmtx' in font and glyph_name in font['hmtx'].metrics:
            aw, lsb = font['hmtx'].metrics[glyph_name]
            new_lsb = getattr(glyph, 'xMin', lsb) 
            font['hmtx'].metrics[glyph_name] = (aw, new_lsb)

    font.save(output_path)
    print(f" -> Saved: {os.path.basename(output_path)}")


if __name__ == "__main__":
    files = glob.glob("BricolageGrotesque-*.ttf")
    for font_file in files:
        if "Italic" not in font_file:
            out_file = font_file.replace(".ttf", "Italic.ttf")
            out_file = out_file.replace("RegularItalic", "Italic") 
            create_oblique(font_file, out_file)

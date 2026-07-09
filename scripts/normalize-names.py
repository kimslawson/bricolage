import os
import glob
from fontTools.ttLib import TTFont

# Setup naming blueprints for flawless menu nesting
NAMING_CONFIGS = {
    'ExtraLight': {
        'id1': 'Bricolage Grotesque ExtraLight',
        'id2': 'Italic',
        'id16': 'Bricolage Grotesque',
        'id17': 'ExtraLight Italic',
        'id4': 'Bricolage Grotesque ExtraLight Italic',
        'id6': 'BricolageGrotesque-ExtraLightItalic'
    },
    'Light': {
        'id1': 'Bricolage Grotesque Light',
        'id2': 'Italic',
        'id16': 'Bricolage Grotesque',
        'id17': 'Light Italic',
        'id4': 'Bricolage Grotesque Light Italic',
        'id6': 'BricolageGrotesque-LightItalic'
    },
    'Italic': {  # Regular Italic
        'id1': 'Bricolage Grotesque',
        'id2': 'Italic',
        'id16': 'Bricolage Grotesque',
        'id17': 'Italic',
        'id4': 'Bricolage Grotesque Italic',
        'id6': 'BricolageGrotesque-Italic'
    },
    'Medium': {
        'id1': 'Bricolage Grotesque Medium',
        'id2': 'Italic',
        'id16': 'Bricolage Grotesque',
        'id17': 'Medium Italic',
        'id4': 'Bricolage Grotesque Medium Italic',
        'id6': 'BricolageGrotesque-MediumItalic'
    },
    'SemiBold': {
        'id1': 'Bricolage Grotesque SemiBold',
        'id2': 'Italic',
        'id16': 'Bricolage Grotesque',
        'id17': 'SemiBold Italic',
        'id4': 'Bricolage Grotesque SemiBold Italic',
        'id6': 'BricolageGrotesque-SemiBoldItalic'
    },
    'Bold': {
        'id1': 'Bricolage Grotesque',
        'id2': 'Bold Italic',
        'id16': 'Bricolage Grotesque',
        'id17': 'Bold Italic',
        'id4': 'Bricolage Grotesque Bold Italic',
        'id6': 'BricolageGrotesque-BoldItalic'
    },
    'ExtraBold': {
        'id1': 'Bricolage Grotesque ExtraBold',
        'id2': 'Italic',
        'id16': 'Bricolage Grotesque',
        'id17': 'ExtraBold Italic',
        'id4': 'Bricolage Grotesque ExtraBold Italic',
        'id6': 'BricolageGrotesque-ExtraBoldItalic'
    }
}

def detect_weight_key(filename):
    lower_name = os.path.basename(filename).lower()
    if 'extrabold' in lower_name: return 'ExtraBold'
    if 'semibold' in lower_name: return 'SemiBold'
    if 'bold' in lower_name: return 'Bold'
    if 'extralight' in lower_name: return 'ExtraLight'
    if 'light' in lower_name: return 'Light'
    if 'medium' in lower_name: return 'Medium'
    if 'italic' in lower_name: return 'Italic'
    return None

def process_font_grouping(file_path):
    weight_key = detect_weight_key(file_path)
    if not weight_key:
        print(f"Skipping unknown profile: {file_path}")
        return

    print(f"Aligning family parameters for: {os.path.basename(file_path)} ({weight_key})")
    font = TTFont(file_path)
    cfg = NAMING_CONFIGS[weight_key]
    
    # 1. Clean out conflicting variable STAT attributes
    if 'STAT' in font:
        del font['STAT']

    # 2. Rebuild cleanly mapped name strings
    name_table = font['name']
    target_ids = {1: cfg['id1'], 2: cfg['id2'], 4: cfg['id4'], 6: cfg['id6'], 16: cfg['id16'], 17: cfg['id17']}
    
    # Filter out existing records matching our target IDs directly from the names list
    name_table.names = [record for record in name_table.names if record.nameID not in target_ids]

    for name_id, name_val in target_ids.items():
        # Universal Windows Format Mapping (Note corrected parameter names)
        name_table.setName(name_val, nameID=name_id, platformID=3, platEncID=1, langID=0x409)
        # Universal Legacy Macintosh Format Mapping (Note corrected parameter names)
        name_table.setName(name_val, nameID=name_id, platformID=1, platEncID=0, langID=0)

    # 3. Synchronize cross-linking selection bits
    if 'OS/2' in font:
        font['OS/2'].fsSelection &= ~(1 << 0)  # Clear Italic
        font['OS/2'].fsSelection &= ~(1 << 5)  # Clear Bold
        font['OS/2'].fsSelection &= ~(1 << 6)  # Clear Regular Flag
        
        if weight_key == 'Bold':
            font['OS/2'].fsSelection |= (1 << 0) | (1 << 5)
        else:
            font['OS/2'].fsSelection |= (1 << 0)

    if 'head' in font:
        font['head'].macStyle &= ~(1 << 0)  # Clear Bold bit
        font['head'].macStyle &= ~(1 << 1)  # Clear Italic bit
        
        if weight_key == 'Bold':
            font['head'].macStyle |= (1 << 0) | (1 << 1)
        else:
            font['head'].macStyle |= (1 << 1)

    font.save(file_path)

if __name__ == "__main__":
    targets = glob.glob("*.ttf") + glob.glob("*.otf") + glob.glob("*.woff2")
    
    if not targets:
        print("No processed target instances located in the current workspace.")
    else:
        for font_file in targets:
            try:
                process_font_grouping(font_file)
            except Exception as e:
                print(f"Error modifying {font_file}: {e}")
        print("\nAll font file variants successfully aligned under the 'Bricolage Grotesque' family tree!")
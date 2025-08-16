import os
import subprocess

LILYPOND = r".\lilypond-2.24.4\bin\lilypond.exe"  # full path to lilypond executable

NOTE_TO_LILYPOND = {
    "C0": "c,,,", "D0": "d,,,", "E0": "e,,,", "F0": "f,,,", "G0": "g,,,", "A0": "a,,,", "B0": "b,,,",
    "C1": "c,,", "D1": "d,,", "E1": "e,,", "F1": "f,,", "G1": "g,,", "A1": "a,,", "B1": "b,,",
    "C2": "c,", "D2": "d,", "E2": "e,", "F2": "f,", "G2": "g,", "A2": "a,", "B2": "b,",
    "C3": "c", "D3": "d", "E3": "e", "F3": "f", "G3": "g", "A3": "a", "B3": "b",
    "C4": "c'", "D4": "d'", "E4": "e'", "F4": "f'", "G4": "g'", "A4": "a'", "B4": "b'",
    "C5": "c''", "D5": "d''", "E5": "e''", "F5": "f''", "G5": "g''", "A5": "a''", "B5": "b''",
    "C6": "c'''", "D6": "d'''", "E6": "e'''", "F6": "f'''", "G6": "g'''", "A6": "a'''", "B6": "b'''",
}


def generate_note_image(note="C4", clef="treble", output_dir="note_images", width=300, height=200, crop_x=0, crop_y=0):
    """Generate a PNG of a note on a staff using LilyPond, then crop to fixed size from (crop_x, crop_y)."""
    # Support multiple notes for chords
    note_list = [n.strip().upper() for n in note.split(",")]
    for n in note_list:
        if n not in NOTE_TO_LILYPOND:
            raise ValueError(f"Note {n} not supported.")

    if len(note_list) == 1:
        lily_note = NOTE_TO_LILYPOND[note_list[0]]
        note_expr = f"{lily_note}4"
    else:
        lily_notes = [NOTE_TO_LILYPOND[n] for n in note_list]
        note_expr = f"<{' '.join(lily_notes)}>4"

    filename = f"{clef}_{'_'.join(note_list)}"
    os.makedirs(output_dir, exist_ok=True)

    ly_content = f"""
% Clef only (bass or treble), one note or chord, omit time signature
\version "2.24.2"
\paper {{
    #(set-paper-size "a6landscape")
    indent = 0\mm
    line-width = 50\mm
    left-margin = 0\mm
    top-margin = 0\mm
    bottom-margin = 0\mm
    right-margin = 0\mm
    print-page-number = ##f
}}
\layout {{
    ragged-right = ##t
    \context {{
        \Score
        \override SpacingSpanner.common-shortest-duration = #(ly:make-moment 1/1)
    }}
}}
\new Staff {{
    \clef {clef}
    \omit Staff.TimeSignature
    {note_expr}
}}
"""
    ly_file = os.path.join(output_dir, f"{filename}.ly")
    with open(ly_file, "w") as f:
        f.write(ly_content)

    subprocess.run([
        LILYPOND,
        "-fpng",
        "-dresolution=300",
        "-o", os.path.join(output_dir, filename),
        ly_file
    ])

    # Crop the PNG to fixed size using PIL
    try:
        from PIL import Image
        png_path = os.path.join(output_dir, f"{filename}.png")
        with Image.open(png_path) as im:
            im_cropped = im.crop((crop_x, crop_y, crop_x + width, crop_y + height))
            im_cropped.save(png_path)
        print(f"✅ Generated and cropped {filename}.png to {width}x{height} from ({crop_x},{crop_y})")
    except ImportError:
        print(f"✅ Generated {filename}.png (PIL not installed, not cropped)")

    # Delete the .ly file
    try:
        os.remove(ly_file)
    except Exception as e:
        print(f"Warning: could not delete {ly_file}: {e}")

if __name__ == "__main__":
    import sys
    # Defaults
    note = "C4"
    width, height = 100, 100
    crop_x, crop_y = 0, 0
    clef = None

    # Parse named parameters
    for arg in sys.argv[1:]:
        if arg.lower().startswith("note="):
            note = arg.split("=", 1)[1].upper()
        elif arg.lower().startswith("crop="):
            wh = arg.split("=", 1)[1].lower().split("x")
            if len(wh) == 2:
                width, height = int(wh[0]), int(wh[1])
        elif arg.lower().startswith("margin="):
            xy = arg.split("=", 1)[1].split(",")
            if len(xy) == 2:
                crop_x, crop_y = int(xy[0]), int(xy[1])
        elif arg.lower().startswith("clef="):
            clef = arg.split("=", 1)[1].lower()

    if not clef:
        clef = "bass" if note.endswith("2") else "treble"

    print(f"Generating note={note} crop={width}x{height} margin={crop_x},{crop_y} clef={clef}")
    generate_note_image(note, clef, width=width, height=height, crop_x=crop_x, crop_y=crop_y)

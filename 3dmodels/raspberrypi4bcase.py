import os
import subprocess
import zipfile
from google.colab import files

# 1. Install OpenSCAD compiler
print("Installing OpenSCAD...")
subprocess.run(["apt-get", "update"], stdout=subprocess.DEVNULL)
subprocess.run(["apt-get", "install", "-y", "openscad"], stdout=subprocess.DEVNULL, check=True)
print("OpenSCAD installed successfully.")

# 2. Write the corrected OpenSCAD script with proper height clearances
openscad_code = """
$fn = 64;

// Parametric Dimensions
wall = 2.4;
cover_h = 21.0; // Increased to 21.0 mm to clear high USB/Ethernet ports (Z_max ~22.0 mm)
pcb_z = 3.0; // Height above the base plate

int_x = 90.0;
int_y = 60.0;

// Shifted clips to avoid collision with Y-Min (front) ports
clip_x1 = 4.0;
clip_x2 = 75.0;

module snap_pin(x, y) {
    translate([x, y, wall]) {
        difference() {
            union() {
                // Collar (Auflagekragen)
                cylinder(h=3.0, d=5.0, $fn=32);
                // Shaft (Schaft)
                translate([0, 0, 3.0])
                    cylinder(h=2.0, d=2.55, $fn=32);
                // Head (Kopf)
                translate([0, 0, 5.0])
                    cylinder(h=1.2, d1=3.0, d2=2.5, $fn=32);
            }
            // Slot (Schlitz)
            translate([0, 0, 4.5])
                cube([0.8, 6.0, 9.0], center=true);
        }
    }
}

// Support-free wedge/fillet with safety bounds checks
module side_fillet(x, y_start, y_len, left_side=true) {
    x_pos = left_side ? x - 11 : x + 7;
    // Ensure the fillet stays within the physical board limits (X = -2.4 to 92.4)
    if (x_pos >= -wall && x_pos + 4 <= int_x + wall) {
        translate([x_pos, y_start, 2.4]) {
            hull() {
                // Flat base on top of the plate
                cube([4, y_len, 0.01]);
                // Ridge line flush with the socket wall
                translate([left_side ? 3.99 : 0, 0, 3.6])
                    cube([0.01, y_len, 0.01]);
            }
        }
    }
}

module socket(x, y_pos, dir) {
    y_start = dir == -1 ? -4.5 : 0;
    translate([x, y_pos, 0]) {
        difference() {
            // Main block of socket (Z starts exactly at 0)
            translate([-7, y_start, 0])
                cube([14, 4.5, 6.0]);

            // Slot for the clip stem
            translate([-2.2, dir == -1 ? -2.2 : 0, -1])
                cube([4.4, 2.2, 8.0]);

            // Window for the latch
            translate([-2.2, dir == -1 ? -4.6 : 2.2, -1])
                cube([4.4, 2.5, 3.4]);
        }
    }
    // Side fillets for structural support
    side_fillet(x, y_pos + y_start, 4.5, left_side=true);
    side_fillet(x, y_pos + y_start, 4.5, left_side=false);
}

// Mathematically clean wedge with zero risk of floating segments (using hull)
module latch_wedge(dir) {
    hull() {
        // Top horizontal lip (thickness 1mm, flat stop at Z = 2.4)
        translate([-2, dir == -1 ? -3.0 : 2.0, 2.39])
            cube([4, 1.0, 0.01]);

        // Bottom attachment line on the stem outer surface at Z = 1.2
        translate([-2, dir == -1 ? -2.01 : 2.0, 1.2])
            cube([4, 0.01, 0.01]);
    }
}

module clip(x, y_pos, dir) {
    translate([x, y_pos, 0]) {
        // Montagebrücke: Starts at Z=6.2 to clear the 6.0mm tall socket
        translate([-5, dir == -1 ? -2.4 : 0, 6.2])
            cube([10, 2.4, 5.8]);

        // Stem: Starts at Z=1.2 to enter the slot
        translate([-2, dir == -1 ? -2.0 : 0, 1.2])
            cube([4, 2.0, 10.8]);

        // Solid latch (Sperrkante)
        latch_wedge(dir);
    }
}

module base_plate_assembly() {
    difference() {
        union() {
            // Flat bottom plate with interlocking step cut-out (Z=0 to Z=2.4)
            difference() {
                // Main plate
                translate([-wall, -wall, 0])
                    cube([int_x + 2*wall, int_y + 2*wall, wall]);

                // The outer 1.2mm step cutout (Z = 1.2 to 2.5) for self-alignment
                difference() {
                    translate([-wall - 0.1, -wall - 0.1, 1.2])
                        cube([int_x + 2*wall + 0.2, int_y + 2*wall + 0.2, 1.3]);
                    translate([-wall + 1.2, -wall + 1.2, 1.1])
                        cube([int_x + 2*wall - 2.4, int_y + 2*wall - 2.4, 1.5]);
                }
            }

            // Official Pi 4B Snap Pins
            snap_pin(6.0, 6.0);
            snap_pin(64.0, 6.0);
            snap_pin(6.0, 55.0);
            snap_pin(64.0, 55.0);

            // Sockets (Halteösen)
            socket(clip_x1, -wall, -1);
            socket(clip_x2, -wall, -1);
            socket(clip_x1, int_y + wall, 1);
            socket(clip_x2, int_y + wall, 1);
        }
        // Safety cut to guarantee the base is perfectly flat at Z=0
        translate([-500, -500, -1000])
            cube([1000, 1000, 1000]);
    }
}

module cover_assembly() {
    difference() {
        // Outer Hood (Starts at Z=1.2 to form the mating step)
        translate([-wall, -wall, 1.2])
            cube([int_x + 2*wall, int_y + 2*wall, cover_h + wall + 1.2]);

        // Inner Cavity (Starts at Z=2.4)
        translate([0, 0, 2.4 - 0.1])
            cube([int_x, int_y, cover_h + 1.0]);

        // Mating step cutout on the inner half of the cover wall (Z=1.2 to 2.4)
        translate([-wall + 1.2, -wall + 1.2, 1.1])
            cube([int_x + 2*wall - 2.4, int_y + 2*wall - 2.4, 1.3]);

        // USB-A and LAN (X-Max Wall) - open to bottom, extended to Z=22.0 for physical clearance
        translate([int_x - 1, 2.5, 1.1])
            cube([wall + 2, 55.0, 22.0]);

        // Side Connectors on Y-Min Wall (Front) - open to bottom, height increased to 12.0 mm
        // USB-C
        translate([9.0, -wall - 0.5, 1.1])
            cube([10.0, wall + 1, 12.0]);
        // HDMI 1
        translate([24.0, -wall - 0.5, 1.1])
            cube([9.0, wall + 1, 12.0]);
        // HDMI 2
        translate([39.0, -wall - 0.5, 1.1])
            cube([9.0, wall + 1, 12.0]);
        // Audio
        translate([52.0, -wall - 0.5, 1.1])
            cube([8.0, wall + 1, 12.0]);

        // SD Card Slot (X-Min Wall)
        translate([-wall - 1, 22.0, 1.1])
            cube([wall + 2, 17.0, 6.0]);

        // Ceiling Ventilation Slots (over CPU)
        for (i = [0 : 5]) {
            translate([20 + i*6, 15, cover_h + wall + 1.2 - 2.4])
                cube([3.0, 30.0, wall + 2]);
        }
    }

    // Clips attached to the cover
    clip(clip_x1, -wall, -1);
    clip(clip_x2, -wall, -1);
    clip(clip_x1, int_y + wall, 1);
    clip(clip_x2, int_y + wall, 1);
}

// Print Orientation: Cover rotated 180 degrees to lay perfectly flat on its ceiling
module cover_assembly_flipped() {
    difference() {
        translate([0, int_y, cover_h + wall + 1.2])
            rotate([180, 0, 0])
                cover_assembly();
        // Safety cut to guarantee the cover ceiling is perfectly flat at Z=0
        translate([-500, -500, -1000])
            cube([1000, 1000, 1000]);
    }
}

// Render selector
part = "base"; // Default value, overwritten by command line

if (part == "base") {
    base_plate_assembly();
} else if (part == "cover") {
    cover_assembly_flipped();
}
"""

with open("pi4_case.scad", "w") as f:
    f.write(openscad_code)

# 3. Render base plate and cover to STL
print("Rendering Base Plate STL...")
subprocess.run([
    "openscad",
    "-o", "pi4_case_base.stl",
    "-D", 'part="base"',
    "pi4_case.scad"
], check=True)

print("Rendering Cover STL...")
subprocess.run([
    "openscad",
    "-o", "pi4_case_cover.stl",
    "-D", 'part="cover"',
    "pi4_case.scad"
], check=True)

# 4. Package into a ZIP and download
zip_filename = "pi4_case_stl_files.zip"
print(f"Creating ZIP archive: {zip_filename}...")
with zipfile.ZipFile(zip_filename, 'w') as zipf:
    zipf.write("pi4_case_base.stl")
    zipf.write("pi4_case_cover.stl")

print("Triggering download...")
files.download(zip_filename)

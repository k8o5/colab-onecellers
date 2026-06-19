# 1. System-Pakete aktualisieren und OpenSCAD + xvfb (virtuelles Display) installieren
!apt-get update -y
!apt-get install -y openscad xvfb

import os
import subprocess

# Definition der OpenSCAD-Modelle

bottich_scad = """
$fn = 80;

difference() {
    // Außenkörper
    cylinder(h=150, r=95);

    // Innenraum (8mm Wandstärke für hohe Stabilität)
    translate([0, 0, 8])
        cylinder(h=145, r=87);
}

// Zentrale Führungsachse für das Rührwerk
translate([0, 0, 8])
    cylinder(h=60, r=12);

// Interne Waschrippen an den Wänden
for (i = [0 : 45 : 360]) {
    rotate([0, 0, i])
    translate([82, -6, 8])
    cube([5, 12, 130]);
}
"""

ruehrer_scad = """
$fn = 80;

difference() {
    union() {
        // Bodenscheibe
        cylinder(h=6, r=82);

        // Mittelsäule
        cylinder(h=140, r=16);

        // Waschpaddel
        for (i = [0 : 120 : 360]) {
            rotate([0, 0, i])
            translate([0, -5, 6])
            cube([76, 10, 30]);
        }
    }
    // Loch für die Achse des Bottichs (mit 0,5mm Toleranz für freie Drehung)
    translate([0, 0, -1])
        cylinder(h=63, r=12.5);

    // Vierkant-Aufsatz am oberen Ende für die Kurbel
    translate([0, 0, 125])
        cube([16.5, 16.5, 20], center=true);
}
"""

kurbel_scad = """
$fn = 60;

union() {
    // Vierkant-Stecker passend für das Rührwerk
    translate([0, 0, 5])
        cube([15.5, 15.5, 10], center=true);

    // Kurbelarm
    translate([35, 0, 12])
        cube([90, 22, 10], center=true);

    // Handgriff (stehend konstruiert)
    translate([70, 0, 17])
        cylinder(h=50, r=9);
}
"""

# SCAD-Dateien schreiben
with open("bottich.scad", "w") as f:
    f.write(bottich_scad)

with open("ruehrer.scad", "w") as f:
    f.write(ruehrer_scad)

with open("kurbel.scad", "w") as f:
    f.write(kurbel_scad)

print("SCAD-Dateien wurden geschrieben. Starte Rendering über xvfb...")

# 2. Rendering mit virtuellem Framebuffer ausführen, um Headless-Fehler zu vermeiden
def render_stl(scad_file, stl_file):
    print(f"Rendere {stl_file}...")
    # Verwendung von xvfb-run, um ein virtuelles Display zu simulieren
    cmd = f"xvfb-run openscad -o {stl_file} {scad_file}"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Fehler beim Rendern von {stl_file}:")
        print(result.stderr)
    else:
        print(f"{stl_file} erfolgreich erstellt.")

render_stl("bottich.scad", "bottich.stl")
render_stl("ruehrer.scad", "ruehrer.stl")
render_stl("kurbel.scad", "kurbel.stl")

# 3. Download-Sektion mit Überprüfung
try:
    from google.colab import files

    files_to_download = ['bottich.stl', 'ruehrer.stl', 'kurbel.stl']
    existing_files = [f for f in files_to_download if os.path.exists(f)]

    if len(existing_files) == 3:
        print("\nAlle Dateien vorhanden. Starte Download...")
        for f in existing_files:
            files.download(f)
    else:
        print("\nEinige Dateien konnten nicht generiert werden. Bitte prüfen Sie die obigen Fehlermeldungen.")
except ImportError:
    print("\nGoogle Colab Download-Modul nicht verfügbar. Die Dateien befinden sich im lokalen Dateimanager links.")

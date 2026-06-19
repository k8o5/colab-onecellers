#@title OpenSCAD zu STL Konverter & 3D-Viewer
# Passen Sie hier Ihren OpenSCAD-Code an:
scad_code = """
// Leichtgewicht-Version für schwächere PCs / Slicer
$fn = 40;

difference() {
    // Außenkörper
    cylinder(h=150, r=95);

    // Innenraum
    translate([0, 0, 8])
        cylinder(h=145, r=87);
}

// Zentrale Führungsachse
translate([0, 0, 8])
    cylinder(h=60, r=12);

// Reduzierte Anzahl an Waschrippen (12 statt 45 Grad Schritte spart viel Rechenleistung)
for (i = [0 : 60 : 360]) {
    rotate([0, 0, i])
    translate([82, -6, 8])
    cube([5, 12, 130]);
}
"""

import os
import subprocess
import shutil
import base64
from IPython.display import HTML, display

# 1. OpenSCAD installieren, falls nicht vorhanden
if not shutil.which("openscad"):
    print("Installiere OpenSCAD (dies kann einen Moment dauern)...")
    # Update und Installation im Hintergrund
    subprocess.run(["apt-get", "update", "-qq"], check=True)
    subprocess.run(["apt-get", "install", "-y", "-qq", "openscad-nox"], check=True)
    print("OpenSCAD wurde erfolgreich installiert.")

# 2. Dateien definieren
scad_filename = "model.scad"
stl_filename = "model.stl"

# SCAD-Code in Datei schreiben
with open(scad_filename, "w") as f:
    f.write(scad_code)

# 3. OpenSCAD ausführen, um die STL-Datei zu generieren
print("Generiere STL-Datei...")
result = subprocess.run(
    ["openscad", "-o", stl_filename, scad_filename],
    capture_output=True,
    text=True
)

if result.returncode == 0:
    print(f"STL-Datei erfolgreich erstellt: '{stl_filename}'")
else:
    print("Fehler bei der Erstellung der STL-Datei:")
    print(result.stderr)
    raise RuntimeError("OpenSCAD-Kompilierung fehlgeschlagen.")

# 4. STL-Datei einlesen und für den Viewer in Base64 kodieren
with open(stl_filename, "rb") as f:
    stl_data = f.read()
    base64_stl = base64.b64encode(stl_data).decode('utf-8')

# 5. HTML- & Three.js-Code für den interaktiven 3D-Viewer erzeugen
html_code = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        #canvas-container {{
            width: 100%;
            height: 500px;
            background-color: #1a1a1a;
            position: relative;
            border-radius: 8px;
            overflow: hidden;
        }}
        .controls-panel {{
            margin-top: 10px;
            display: flex;
            gap: 10px;
            font-family: sans-serif;
        }}
        .btn {{
            background-color: #007bff;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }}
        .btn:hover {{
            background-color: #0056b3;
        }}
    </style>
    <!-- Einbinden von Three.js und den benötigten Erweiterungen -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/gh/mrdoob/three.js@r128/examples/js/loaders/STLLoader.js"></script>
    <script src="https://cdn.jsdelivr.net/gh/mrdoob/three.js@r128/examples/js/controls/OrbitControls.js"></script>
</head>
<body>

    <div id="canvas-container"></div>

    <div class="controls-panel">
        <button class="btn" onclick="downloadSTL()">STL herunterladen</button>
        <button class="btn" style="background-color: #6c757d;" onclick="resetCamera()">Kamera zurücksetzen</button>
    </div>

    <script>
        const base64Data = "{base64_stl}";
        let scene, camera, renderer, controls, mesh;

        init();
        animate();

        function init() {{
            const container = document.getElementById('canvas-container');
            const width = container.clientWidth;
            const height = container.clientHeight;

            // Szene
            scene = new THREE.Scene();
            scene.background = new THREE.Color(0x222222);

            // Kamera
            camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);

            // Renderer
            renderer = new THREE.WebGLRenderer({{ antialias: true }});
            renderer.setSize(width, height);
            renderer.setPixelRatio(window.devicePixelRatio);
            renderer.shadowMap.enabled = true;
            container.appendChild(renderer.domElement);

            // Orbit Controls
            controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.05;

            // Beleuchtung
            const ambientLight = new THREE.AmbientLight(0x404040, 1.5);
            scene.add(ambientLight);

            const dirLight1 = new THREE.DirectionalLight(0xffffff, 0.8);
            dirLight1.position.set(1, 1, 1).normalize();
            scene.add(dirLight1);

            const dirLight2 = new THREE.DirectionalLight(0x555555, 0.5);
            dirLight2.position.set(-1, -1, -1).normalize();
            scene.add(dirLight2);

            // STL-Daten aus Base64 dekodieren
            const binaryString = window.atob(base64Data);
            const len = binaryString.length;
            const bytes = new Uint8Array(len);
            for (let i = 0; i < len; i++) {{
                bytes[i] = binaryString.charCodeAt(i);
            }}
            const arrayBuffer = bytes.buffer;

            // STL laden
            const loader = new THREE.STLLoader();
            const geometry = loader.parse(arrayBuffer);

            // Geometrie zentrieren
            geometry.computeBoundingBox();
            geometry.center();

            // Material und Mesh erstellen
            const material = new THREE.MeshStandardMaterial({{
                color: 0x90caf9,
                roughness: 0.4,
                metalness: 0.2
            }});
            mesh = new THREE.Mesh(geometry, material);
            scene.add(mesh);

            // Gitter zur Orientierung
            const gridHelper = new THREE.GridHelper(200, 50, 0x444444, 0x333333);
            gridHelper.position.y = geometry.boundingBox.min.y - 0.1;
            scene.add(gridHelper);

            // Kamera positionieren basierend auf Modellgröße
            const boundingBox = geometry.boundingBox;
            const size = new THREE.Vector3();
            boundingBox.getSize(size);
            const maxDim = Math.max(size.x, size.y, size.z);

            camera.position.set(maxDim * 1.5, maxDim * 1.5, maxDim * 1.5);
            controls.target.set(0, 0, 0);
            controls.update();

            // Resize Event
            window.addEventListener('resize', onWindowResize);
        }}

        function onWindowResize() {{
            const container = document.getElementById('canvas-container');
            const width = container.clientWidth;
            const height = container.clientHeight;
            camera.aspect = width / height;
            camera.updateProjectionMatrix();
            renderer.setSize(width, height);
        }}

        function animate() {{
            requestAnimationFrame(animate);
            controls.update();
            renderer.render(scene, camera);
        }}

        function resetCamera() {{
            if (mesh) {{
                mesh.geometry.computeBoundingBox();
                const boundingBox = mesh.geometry.boundingBox;
                const size = new THREE.Vector3();
                boundingBox.getSize(size);
                const maxDim = Math.max(size.x, size.y, size.z);
                camera.position.set(maxDim * 1.5, maxDim * 1.5, maxDim * 1.5);
                controls.target.set(0, 0, 0);
                controls.update();
            }}
        }}

        function downloadSTL() {{
            const link = document.createElement('a');
            link.href = 'data:application/octet-stream;base64,' + base64Data;
            link.download = 'model.stl';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }}
    </script>
</body>
</html>
"""

# HTML im Ausgabebereich anzeigen
display(HTML(html_code))

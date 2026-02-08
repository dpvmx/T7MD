(function () {
    'use strict';
    
    var csInterface = new CSInterface();
    var fs = require('fs');
    var path = require('path');
    var child_process = require('child_process');
    
    // RUTA DEL PROYECTO
    var PROJECT_DIR = "/Users/dpvmx_1/Triplesiete Dropbox/APPS/T7DM";
    var LAUNCHER_PATH = PROJECT_DIR + "/launcher.sh";

    init();

    function init() {
        var btn = document.getElementById('btnRun');
        if(btn) btn.addEventListener('click', runAnalysis);
        
        if (!fs.existsSync(LAUNCHER_PATH)) {
            updateStatus("⚠️ Error: No encuentro 'launcher.sh'");
            if(btn) btn.disabled = true;
        }
    }

    function runAnalysis() {
        // --- LÓGICA INTELIGENTE DE SELECCIÓN ---
        // Prioridad 1: Capa seleccionada en la Línea de Tiempo
        // Prioridad 2: Archivo seleccionado en el Panel de Proyecto
        var evalCode = `
            (function() {
                var finalPath = "";
                
                // 1. INTENTAR LEER DESDE LA LÍNEA DE TIEMPO (Active Comp)
                var activeComp = app.project.activeItem;
                if (activeComp && activeComp instanceof CompItem && activeComp.selectedLayers.length > 0) {
                    var layer = activeComp.selectedLayers[0];
                    if (layer.source && layer.source.mainSource && layer.source.mainSource.file) {
                        return "FOUND|" + layer.source.mainSource.file.fsName;
                    } else {
                        // Si es una capa de texto, nulo o sólido
                        return "ERROR|La capa seleccionada no es un archivo de video (es " + (layer.source ? layer.source.typeName : "Null/Text") + ").";
                    }
                }

                // 2. INTENTAR LEER DESDE EL PANEL DE PROYECTO
                var sel = app.project.selection;
                if (sel.length > 0) {
                    var item = sel[0];
                    if (item instanceof FootageItem && item.mainSource && item.mainSource.file) {
                        return "FOUND|" + item.mainSource.file.fsName;
                    }
                    if (item instanceof CompItem) {
                        return "ERROR|Has seleccionado una Composición entera en el panel de proyecto.\\n\\nSolución:\\n1. Abre la composición.\\n2. Selecciona la CAPA del video en la línea de tiempo.\\n3. O selecciona el archivo .mp4 original en el panel de proyecto.";
                    }
                    return "ERROR|El item seleccionado no es un video válido.";
                }

                return "ERROR|No has seleccionado nada.\\nSelecciona una capa en la línea de tiempo o un archivo en el proyecto.";
            })()
        `;
        
        csInterface.evalScript(evalCode, function(result) {
            // Manejo de Respuestas
            if (result.startsWith("ERROR|")) {
                var msg = result.split('|')[1];
                alert("❌ " + msg);
                updateStatus("Esperando selección válida...");
                return;
            }
            
            if (result.startsWith("FOUND|")) {
                var videoPath = result.split('|')[1];
                
                // --- INICIO DEL PROCESO ---
                var outputDir = path.dirname(videoPath);
                
                var flags = "";
                if(document.getElementById('chkFaces').checked) flags += " --faces";
                if(document.getElementById('chkPersons').checked) flags += " --persons";
                if(document.getElementById('chkObjects').checked) flags += " --objects";

                var cmd = `"${LAUNCHER_PATH}" --input "${videoPath}" --output_dir "${outputDir}" ${flags}`;
                
                updateStatus("🚀 Iniciando motor IA...");
                if(document.getElementById('btnRun')) document.getElementById('btnRun').disabled = true;
                if(document.getElementById('fill')) document.getElementById('fill').style.width = "0%";

                var options = { maxBuffer: 1024 * 1024 * 50 };
                var proc = child_process.exec(cmd, options);

                proc.stdout.on('data', function(data) {
                    var lines = data.toString().split('\n');
                    lines.forEach(function(line) {
                        line = line.trim();
                        if (line.startsWith('PROGRESS|')) {
                            var pct = line.split('|')[1];
                            if(document.getElementById('fill')) document.getElementById('fill').style.width = pct + "%";
                            updateStatus("Procesando... " + pct + "%");
                        }
                        if (line.startsWith('SUCCESS|')) {
                            var jsonPath = line.split('|')[1].trim();
                            importJSON(jsonPath);
                        }
                        if (line.startsWith('ERROR|')) {
                            var errMsg = line.split('|')[1];
                            updateStatus("❌ Error IA: " + errMsg);
                            alert("Error en Python: " + errMsg);
                        }
                    });
                });

                proc.stderr.on('data', function(data) {
                    console.error("Python Stderr:", data.toString());
                });

                proc.on('close', function(code) {
                    if(document.getElementById('btnRun')) document.getElementById('btnRun').disabled = false;
                });
            } else {
                alert("Error desconocido obteniendo ruta: " + result);
            }
        });
    }

    function importJSON(jsonPath) {
        updateStatus("📥 Importando capas a AE...");
        var scriptCall = "importT7MDJson(" + JSON.stringify(jsonPath) + ")";
        
        csInterface.evalScript(scriptCall, function(result) {
            if (result === "SUCCESS") {
                updateStatus("✅ ¡Análisis Completado!");
                if(document.getElementById('fill')) document.getElementById('fill').style.width = "100%";
            } else {
                updateStatus("❌ Fallo en AE");
                alert("After Effects reporta:\n" + result);
            }
        });
    }

    function updateStatus(msg) {
        var el = document.getElementById('status');
        if(el) el.innerText = msg;
    }
    
}());
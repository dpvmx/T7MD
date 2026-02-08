function importT7MDJson(jsonPath) {
    try {
        // 1. Limpieza y Verificación
        // Decodificamos por si la ruta viene con %20
        var path = decodeURI(jsonPath);
        var f = new File(path);

        if (!f.exists) { 
            return "ERROR: El archivo JSON no existe en: " + path; 
        }
        
        // 2. Leer archivo
        f.open("r");
        var content = f.read();
        f.close();
        
        if (!content || content.length < 2) {
            return "ERROR: El archivo JSON está vacío.";
        }

        // 3. Parsear JSON
        var data;
        try {
            data = JSON.parse(content);
        } catch(e) {
            return "ERROR DE SINTAXIS: El archivo JSON está corrupto. " + e.toString();
        }

        // 4. Validar Metadata mínima
        if (!data.metadata) {
            return "ERROR DATA: El JSON no tiene metadatos.";
        }
        
        // --- COMIENZO DE ACCIONES EN AE ---
        app.beginUndoGroup("T7MD Import");

        var meta = data.metadata;
        var fps = meta.fps || 24; // Fallback a 24fps
        
        // Calcular duración
        var duration = 10;
        if (meta.total_frames && fps > 0) {
            duration = meta.total_frames / fps;
        }
        
        // Crear Composición
        var compName = f.name.replace(".json", "_Comp");
        var width = parseInt(meta.width) || 1920;
        var height = parseInt(meta.height) || 1080;

        var comp = app.project.items.addComp(compName, width, height, 1, duration, fps);
        comp.openInViewer();
        
        var frames = data.frames;
        if (!frames) {
            app.endUndoGroup();
            return "ERROR: No hay frames en el JSON.";
        }

        var frameDuration = 1/fps;
        
        // Crear Capas (Bucle)
        for (var i = 0; i < frames.length; i++) {
            var fData = frames[i];
            var dets = fData.detections;
            
            if (dets && dets.length > 0) {
                for (var j = 0; j < dets.length; j++) {
                    var d = dets[j];
                    if (d.conf < 0.4) continue; // Filtro de confianza

                    var box = comp.layers.addShape();
                    box.name = d.label + "_" + i; // Nombre único
                    
                    // Tiempos
                    box.inPoint = fData.timestamp;
                    box.outPoint = fData.timestamp + frameDuration;
                    
                    // Dibujar Rectángulo
                    var g = box.property("Contents").addProperty("ADBE Vector Group");
                    var r = g.property("Contents").addProperty("ADBE Vector Shape - Rect");
                    r.property("Size").setValue([d.rect.w, d.rect.h]);
                    
                    // Borde
                    var s = g.property("Contents").addProperty("ADBE Vector Graphic - Stroke");
                    s.property("Color").setValue([0, 1, 0]); // Verde
                    s.property("Stroke Width").setValue(4);
                    
                    // Posición
                    box.property("Position").setValue([d.rect.cx, d.rect.cy]);
                    
                    // Organizar
                    box.moveToEnd();
                }
            }
        }
        
        app.endUndoGroup();
        return "SUCCESS"; // Señal de éxito para main.js
        
    } catch(e) {
        // Capturar cualquier error inesperado de AE
        return "ERROR CRÍTICO AE: " + e.toString() + " (Línea " + e.line + ")";
    }
}
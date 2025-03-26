"""
Main application file for EntityTagger.
Handles Flask routes and template rendering.
"""

import json
import os

from flask import Flask, jsonify, render_template_string, request

from conf import (
    APP_TITLE,
    TEXT_FILES_DIR,
    ANNOTATIONS_DIR,
    NER_CLASSES,
    NER_CLASS_COLORS,
    UI_STYLES,
    FLASK_APP_CONFIG,
    AUTO_SAVE_INTERVAL_MS,
)

app = Flask(__name__)

# Ensure directories exist
os.makedirs(TEXT_FILES_DIR, exist_ok=True)
os.makedirs(ANNOTATIONS_DIR, exist_ok=True)

# HTML Template
HTML_TEMPLATE = (
    """
<!DOCTYPE html>
<html>
<head>
    <title>"""
    + APP_TITLE
    + """</title>
    <style>
        body {
            font-family: """
    + UI_STYLES["BODY_FONT"]
    + """;
            margin: 20px;
            line-height: 1.6;
        }
        .container {
            display: flex;
        }
        .file-list {
            width: """
    + UI_STYLES["FILE_LIST_WIDTH"]
    + """;
            padding-right: 20px;
            font-size: 0.9em;
        }
        .annotation-area {
            width: """
    + UI_STYLES["ANNOTATION_AREA_WIDTH"]
    + """;
        }
        .text-container {
            border: 1px solid #ccc;
            padding: 10px;
            white-space: pre-wrap;
            line-height: 1.5;
            margin-bottom: 20px;
            position: relative;
            font-family: """
    + UI_STYLES["CODE_FONT"]
    + """;
            background-color: #f9f9f9;
            border-radius: 4px;
            color: #000;
            font-size: 0.9em;
        }
        .class-buttons {
            margin-bottom: 15px;
            position: sticky;
            top: 0;
            background-color: white;
            padding: 10px 0;
            z-index: 100;
            border-bottom: 1px solid #eee;
        }
        .class-button {
            margin: 2px 2px 4px 2px;
            padding: 5px 10px;
            cursor: pointer;
            border: none;
            border-radius: 3px;
            font-weight: bold;
        }
        .floating-buttons {
            position: absolute;
            background: white;
            border: 1px solid #ccc;
            border-radius: 4px;
            padding: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            z-index: 110;
            display: none;
            width: 500px; /* Fixed width */
            flex-wrap: wrap;
            justify-content: flex-start;
        }
        .class-button.active {
            outline: 3px solid #000;
            outline-offset: 2px;
            font-weight: bold;
        }
        .remove-button {
            margin-top: 6px;
        }
        .highlight {
            border-radius: 3px;
            padding: 2px 0;
        }
        .file-item {
            padding: 6px 8px;
            cursor: pointer;
            border-bottom: 1px solid #eee;
            font-size: 0.85em;
        }
        .file-item:hover {
            background-color: #f5f5f5;
        }
        .annotated {
            color: green;
            font-weight: bold;
        }
        .current {
            background-color: #e7f3ff;
        }
        h1 {
            margin-bottom: 25px;
            font-size: 24px;
        }
        .annotation-tag {
            position: absolute;
            font-size: 10px;
            background-color: rgba(0,0,0,0.7);
            color: white;
            padding: 2px 4px;
            border-radius: 2px;
            white-space: nowrap;
        }
    </style>
</head>
<body>
    <h1>"""
    + APP_TITLE
    + """</h1>
    
    <div class="container">
        <div class="file-list">
            <h3>Text Files</h3>
            <div id="file-listing">
                {% for file in files %}
                <div class="file-item {% if file == current_file %}current{% endif %} {% if file in annotated_files %}annotated{% endif %}" 
                     onclick="loadFile('{{ file }}')">
                    {{ file }} {% if file in annotated_files %}✓{% endif %}
                </div>
                {% endfor %}
            </div>
        </div>
        
        <div class="annotation-area">
            <h3 id="current-file">
                {% if current_file %}
                Current File: {{ current_file }}
                {% else %}
                Select a file to annotate
                {% endif %}
            </h3>
            
            <div class="class-buttons">
                <div>
                    {% for cls in ner_classes %}
                        <button class="class-button" 
                            style="background-color: {{ bg_colors[loop.index0] }}; color: {{ text_colors[loop.index0] }}"
                            onclick="setCurrentClass('{{ cls }}')">
                        {{ cls }}
                        </button>
                    {% endfor %}
                </div>
            </div>
            <div id="floating-buttons" class="floating-buttons">
                {% for cls in ner_classes %}
                    <button class="class-button" 
                        style="background-color: {{ bg_colors[loop.index0] }}; color: {{ text_colors[loop.index0] }}"
                        onclick="setCurrentClass('{{ cls }}')">
                    {{ cls }}
                    </button>
                {% endfor %}
            </div>
            <div id="text-container" class="text-container">{{ text_content }}</div>
        </div>
    </div>
    
    <script>
        // State management
        let annotations = {{ annotations|tojson }};
        let currentFile = '{{ current_file }}';
        let lastSaved = Date.now();
        let pendingSave = false;
        let currentSelection = null;
        
        // Color mapping for NER classes
        const bgColors = {{ bg_colors|tojson }};
        const textColors = {{ text_colors|tojson }};
        const classes = {{ ner_classes|tojson }};
        const autoSaveInterval = {{ auto_save_interval }};
        
        // Initialize the visualization
        document.addEventListener('DOMContentLoaded', function() {
            // Draw initial annotations
            drawAnnotations();
            
            // Set up the text selection handler
            const textContainer = document.getElementById('text-container');
            textContainer.addEventListener('mouseup', handleTextSelection);
            
            // Add event handler for annotation removal with ALT+click
            textContainer.addEventListener('click', function(e) {
                if (e.altKey) {
                    const target = e.target;
                    if (target.classList.contains('highlight')) {
                        e.preventDefault();
                        
                        const annotationClass = target.getAttribute('data-class');
                        const text = target.textContent;
                        
                        for (let i = 0; i < annotations.length; i++) {
                            const ann = annotations[i];
                            if (ann.class === annotationClass && ann.text === text) {
                                annotations.splice(i, 1);
                                drawAnnotations();
                                pendingSave = true;
                                break;
                            }
                        }
                    }
                }
            });
            
            // Clear selection when clicking anywhere on the document
            document.addEventListener('click', function(e) {
                // Don't clear if clicking on a class button or inside text container during selection
                if (!e.target.classList.contains('class-button') && 
                    (e.target === document.body || e.target === document || 
                     !textContainer.contains(e.target) || !window.getSelection().toString())) {
                    currentSelection = null;
                    hideFloatingButtons();
                }
            });
            
            // Save annotations periodically
            setInterval(saveIfNeeded, autoSaveInterval);
        });
        
        // Apply selected class to the current text selection
        function setCurrentClass(cls) {
            // If we have a current selection, apply this class to it
            if (currentSelection) {
                applyAnnotation(currentSelection, cls);
                currentSelection = null;
                hideFloatingButtons();
            }
        }
        
        // Handle text selection
        function handleTextSelection(event) {
            const selection = window.getSelection();
            if (!currentFile || selection.isCollapsed) {
                currentSelection = null;
                hideFloatingButtons();
                return;
            }
            
            // Store the current selection details
            const range = selection.getRangeAt(0);
            const textContent = document.getElementById('text-container').textContent;
            const startIndex = getSelectionStartIndex(range, textContent);
            if (startIndex === -1) {
                currentSelection = null;
                hideFloatingButtons();
                return;
            }
            
            const text = selection.toString();
            if (!text.trim()) {
                currentSelection = null;
                hideFloatingButtons();
                return;  // Ignore empty selections
            }
            
            const endIndex = startIndex + text.length;
            
            // Store selection information
            currentSelection = {
                text: text,
                startIndex: startIndex,
                endIndex: endIndex,
                range: range.cloneRange()
            };
            
            // Show floating buttons near selection
            showFloatingButtons(range);
            
            // Prevent event propagation to avoid immediate clearing of selection
            event.stopPropagation();
        }
        
        // Show floating buttons near the current selection
        function showFloatingButtons(range) {
            const floatingButtons = document.getElementById('floating-buttons');
            const rect = range.getBoundingClientRect();
            const textContainer = document.getElementById('text-container');
            const textContainerRect = textContainer.getBoundingClientRect();
            
            // Position the buttons below the selection
            // Center horizontally within the text container
            const leftPosition = Math.max(textContainerRect.left, 
                                         Math.min(rect.left, textContainerRect.right - 500));
            
            floatingButtons.style.left = `${leftPosition + window.scrollX}px`;
            floatingButtons.style.top = `${rect.bottom + window.scrollY + 5}px`;
            floatingButtons.style.display = 'flex';
        }
        
        // Hide floating buttons
        function hideFloatingButtons() {
            document.getElementById('floating-buttons').style.display = 'none';
        }
        
        // Apply annotation with the selected class
        function applyAnnotation(selectionInfo, className) {
            if (!selectionInfo || !className) return;
            
            // Check for overlap with existing annotations
            for (let i = 0; i < annotations.length; i++) {
                const ann = annotations[i];
                
                // Check for overlap
                if (!(selectionInfo.endIndex <= ann.start || selectionInfo.startIndex >= ann.end)) {
                    alert('Annotations cannot overlap. Please remove the overlapping annotation first.');
                    return;
                }
            }
            
            // Add new annotation
            const newAnnotation = {
                text: selectionInfo.text,
                start: selectionInfo.startIndex,
                end: selectionInfo.endIndex,
                class: className
            };
            
            annotations.push(newAnnotation);
            
            // Clear selection
            window.getSelection().removeAllRanges();
            
            // Update visualization
            drawAnnotations();
            
            // Mark for saving
            pendingSave = true;
        }
        
        // Calculate the absolute start index of the selection
        function getSelectionStartIndex(range, text) {
            // Get a new range from start of text container to start of selection
            const textContainer = document.getElementById('text-container');
            const preSelectionRange = range.cloneRange();
            preSelectionRange.selectNodeContents(textContainer);
            preSelectionRange.setEnd(range.startContainer, range.startOffset);
            
            // Get the text content up to the selection
            const preSelectionText = preSelectionRange.toString();
            
            return preSelectionText.length;
        }
        

        
        // Get absolute text position from a selection
        function getTextPosition(selection) {
            const textContainer = document.getElementById('text-container');
            const range = document.createRange();
            range.setStart(textContainer, 0);
            range.setEnd(selection.anchorNode, selection.anchorOffset);
            return range.toString().length;
        }
        
        // Draw annotations on the text
        function drawAnnotations() {
            const textContainer = document.getElementById('text-container');
            const textContent = textContainer.textContent;
            
            // Sort annotations by start position (reversed to apply from end to start)
            const sortedAnnotations = [...annotations].sort((a, b) => b.start - a.start);
            
            // Start with the original text
            let html = textContent;
            
            // Apply annotations from end to start to avoid index shifting
            for (const ann of sortedAnnotations) {
                const classIndex = classes.indexOf(ann.class);
                const bgColor = bgColors[classIndex];
                const textColor = textColors[classIndex];
                
                html = html.substring(0, ann.start) + 
                       `<span class="highlight" style="background-color: ${bgColor}; color: ${textColor}" data-class="${ann.class}" title="${ann.class}">` + 
                       html.substring(ann.start, ann.end) + 
                       `</span>` + 
                       html.substring(ann.end);
            }
            
            textContainer.innerHTML = html;
        }
        
        // Load a new file
        function loadFile(filename) {
            // Save current annotations before switching
            if (currentFile && annotations.length > 0) {
                saveAnnotations(false);
            }
            
            window.location.href = '/?file=' + encodeURIComponent(filename);
        }
        
        // Save annotations if needed
        function saveIfNeeded() {
            if (pendingSave && Date.now() - lastSaved > autoSaveInterval) {
                saveAnnotations(true);
            }
        }
        
        // Save annotations to the server
        function saveAnnotations(isAutoSave) {
            if (!currentFile) return;
            
            fetch('/save', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    file: currentFile,
                    annotations: annotations
                }),
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    lastSaved = Date.now();
                    pendingSave = false;
                }
            });
        }
    </script>
</body>
</html>
"""
)


def get_file_list():
    """Get list of text files and annotated files"""
    files = [f for f in os.listdir(TEXT_FILES_DIR) if f.endswith(".txt")]
    files.sort()  # Sort files alphabetically
    annotated_files = [
        f[:-5] for f in os.listdir(ANNOTATIONS_DIR) if f.endswith(".json")
    ]
    return files, [f for f in files if f in annotated_files]


def get_annotations(filename):
    """Load annotations for a file if they exist"""
    annotation_path = os.path.join(ANNOTATIONS_DIR, f"{filename}.json")
    if os.path.exists(annotation_path):
        with open(annotation_path, "r") as f:
            return json.load(f)
    return []


def get_text_content(filename):
    """Load text content from file"""
    file_path = os.path.join(TEXT_FILES_DIR, filename)
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


def generate_colors():
    """Generate background and text colors for NER classes from the configuration"""
    bg_colors = []
    text_colors = []

    for cls in NER_CLASSES:
        color_info = NER_CLASS_COLORS.get(
            cls, {"bg": UI_STYLES["FALLBACK_COLOR"], "text": "black"}
        )
        bg_colors.append(color_info["bg"])
        text_colors.append(color_info["text"])

    return bg_colors, text_colors


@app.route("/")
def index():
    """Main page handler"""
    current_file = request.args.get("file", "")
    files, annotated_files = get_file_list()

    text_content = ""
    annotations = []

    if current_file and current_file in files:
        text_content = get_text_content(current_file)
        annotations = get_annotations(current_file)

    # Generate colors from configuration
    bg_colors, text_colors = generate_colors()

    return render_template_string(
        HTML_TEMPLATE,
        files=files,
        annotated_files=annotated_files,
        current_file=current_file,
        text_content=text_content,
        annotations=annotations,
        ner_classes=NER_CLASSES,
        bg_colors=bg_colors,
        text_colors=text_colors,
        auto_save_interval=AUTO_SAVE_INTERVAL_MS,
    )


@app.route("/save", methods=["POST"])
def save():
    """Save annotations to a JSON file"""
    data = request.json
    file_name = data.get("file", "")
    annotations = data.get("annotations", [])

    if not file_name:
        return jsonify({"success": False, "error": "No file specified"})

    # Save annotations to JSON file with Unicode characters preserved
    annotation_path = os.path.join(ANNOTATIONS_DIR, f"{file_name}.json")
    with open(annotation_path, "w", encoding="utf-8") as f:
        json.dump(annotations, f, indent=2, ensure_ascii=False)

    return jsonify({"success": True})


if __name__ == "__main__":
    # Create text_files directory if it doesn't exist
    os.makedirs(TEXT_FILES_DIR, exist_ok=True)
    app.run(**FLASK_APP_CONFIG)

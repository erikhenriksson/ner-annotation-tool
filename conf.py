"""
Configuration file for the EntityTagger application.
Contains all configurable constants and settings.
"""

# Application settings
APP_TITLE = "NER Annotation Tool"
TEXT_FILES_DIR = "text_files"
ANNOTATIONS_DIR = "annotations"
AUTO_SAVE_INTERVAL_MS = 2000  # Auto-save interval in milliseconds

# NER classes
NER_CLASSES = [
    # Numbers and quantities
    "CARDINAL",
    "ORDINAL",
    "PERCENT",
    "QUANTITY",
    "MONEY",
    # Time
    "DATE",
    "TIME",
    # Places
    "LOC",
    "GPE",
    "FAC",
    # People and organizations
    "PERSON",
    "ORG",
    "NORP",
    # Culture and creation
    "LANGUAGE",
    "WORK_OF_ART",
    "LAW",
    "EVENT",
    "PRODUCT",
    # Miscellaneous
    "OTHER",
]

# Color configuration for NER classes
NER_CLASS_COLORS = {
    # Numbers and quantities (blue variants)
    "CARDINAL": {
        "bg": "#1f77b4",
        "text": "white",
    },  # Dark blue - solid numerical values
    "ORDINAL": {"bg": "#c5b0d5", "text": "black"},  # Light purple - ordinal positions
    "PERCENT": {"bg": "#aec7e8", "text": "black"},  # Light blue - numerical percentages
    "QUANTITY": {
        "bg": "#9edae5",
        "text": "black",
    },  # Cyan-blue - measurements and quantities
    "MONEY": {"bg": "#17becf", "text": "black"},  # Turquoise - financial values
    # Time (orange variants)
    "DATE": {"bg": "#ff7f0e", "text": "white"},  # Dark orange - calendar dates
    "TIME": {"bg": "#ffbb78", "text": "black"},  # Light orange - specific times
    # Places (green variants)
    "LOC": {"bg": "#2ca02c", "text": "white"},  # Dark green - geographical locations
    "GPE": {"bg": "#98df8a", "text": "black"},  # Light green - geopolitical entities
    "FAC": {"bg": "#bcbd22", "text": "black"},  # Olive green - facilities/buildings
    # People and organizations (red variants)
    "PERSON": {"bg": "#d62728", "text": "white"},  # Dark red - individual people
    "ORG": {"bg": "#ff9896", "text": "black"},  # Light red - organizations
    "NORP": {
        "bg": "#c49c94",
        "text": "black",
    },  # Brown-red - nationalities/religious/political groups
    # Culture and creation (purple variants)
    "LANGUAGE": {"bg": "#9467bd", "text": "white"},  # Dark purple - languages
    "WORK_OF_ART": {"bg": "#dbdb8d", "text": "black"},  # Yellow-beige - creative works
    "LAW": {"bg": "#8c564b", "text": "white"},  # Brown - legal references
    "EVENT": {"bg": "#e377c2", "text": "black"},  # Pink - named events
    "PRODUCT": {"bg": "#f7b6d2", "text": "black"},  # Light pink - products and objects
    # Miscellaneous
    "OTHER": {"bg": "#7f7f7f", "text": "white"},  # Grey - catch-all category
}

# UI styling
UI_STYLES = {
    "FILE_LIST_WIDTH": "25%",
    "ANNOTATION_AREA_WIDTH": "75%",
    "BODY_FONT": "'Segoe UI', Roboto, 'Helvetica Neue', -apple-system, BlinkMacSystemFont, Arial, sans-serif",
    "CODE_FONT": "Courier, monospace",
    "FALLBACK_COLOR": "#c7c7c7",  # Fallback color for undefined class
}

# Flask app configuration
FLASK_APP_CONFIG = {
    "debug": False,
}

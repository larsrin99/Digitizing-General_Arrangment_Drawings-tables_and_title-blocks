# src/config.py

import os

# --- Paths ---
# Adjust this path if pdf2txt.py is not in your system's PATH
# Example: '/Users/your_user/path/to/your/venv/bin/pdf2txt.py'
# Or just 'pdf2txt.py' if it's globally accessible
PDFMINER_COMMAND = 'pdf2txt.py'

# Define the base directory of the project
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # This gets the 'iso15926_extractor' directory

# Define output directory relative to the base directory
OUTPUT_DIR = os.path.join(BASE_DIR, 'data', 'output')
INPUT_DIR = os.path.join(BASE_DIR, 'data', 'input')


# --- Tolerances for Geometric Analysis ---
HORIZONTAL_TOLERANCE = 1.5 # Max vertical distance variation for a line to be considered horizontal
VERTICAL_TOLERANCE = 1.5   # Max horizontal distance variation for a line to be considered vertical
COLLINEARITY_TOLERANCE = 1.0 # Max distance point can be from line segment for curve to be 'straight'
MIN_SEGMENT_LENGTH = 2.0
LINE_LIKE_CURVE_THRESHOLD = 0.5 # For is_line_like_curve point deviation
MIN_LENGTH_THRESHOLD = 2.0      # Minimum length/range for H/V classification
LINE_MAX_DEVIATION = 5.0        # Max deviation for <line> elements (bbox check)
CURVE_STRAIGHT_MAX_DEVIATION = 2.0 # Max deviation for whole straight <curve> (range check)
CURVE_SEGMENT_MAX_DEVIATION = 1.5 # Max deviation for segments within <curve>

# Tolerance for clustering intersection points (if using DBSCAN or similar)
#INTERSECTION_CLUSTER_EPS = 2.0 # Max distance between points for one to be considered as in the neighborhood of the other


# --- Validation Settings ---
# Example: Path to SHACL shapes file if you use one
# SHACL_SHAPES_FILE = os.path.join(BASE_DIR, 'validation', 'shapes.ttl')

# --- ISO 15926 Mapping ---
# Example: Path to a local RDL file or API endpoint
# RDL_LOCATION = os.path.join(BASE_DIR, 'rdl', 'reference_data.ttl')
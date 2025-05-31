# src/data_structures.py
import dataclasses
from typing import List, Tuple, Optional, Dict, Any, Union
from shapely.geometry import Polygon, Point

# Define Bounding Box structure
BoundingBox = Tuple[float, float, float, float] # (x0, y0, x1, y1)

@dataclasses.dataclass
class PageElement:
    """Base class for elements with a bounding box."""
    bbox: BoundingBox
    page_number: int

@dataclasses.dataclass
class TextBox(PageElement):
    """Represents an extracted text block."""
    text: str

@dataclasses.dataclass
class LineSegment(PageElement):
    """Represents a line element extracted from XML."""
    start: Tuple[float, float]
    end: Tuple[float, float]
    linewidth: Optional[float] = None

@dataclasses.dataclass
class CurveSegment(PageElement):
    """Represents a curve element extracted from XML."""
    points: List[Tuple[float, float]]
    linewidth: Optional[float] = None

@dataclasses.dataclass
class IntersectionPoint:
     coordinates: Tuple[float, float]

# --- ADD PLACEHOLDER DEFINITIONS ---

@dataclasses.dataclass
class GraphicalSymbol(PageElement):
    """Represents a graphical symbol (placeholder)."""
    symbol_type: Optional[str] = None # Example attribute
    # Add other relevant attributes

@dataclasses.dataclass
class Dimension(PageElement):
     """Represents a dimension annotation (placeholder)."""
     value: Optional[float] = None
     unit: Optional[str] = None
     # Add other relevant attributes (e.g., linked points)

@dataclasses.dataclass
class TableCell: # Define TableCell before Table
    """Represents a cell within a reconstructed table."""
    bbox_polygon: Polygon
    row: int
    column: int
    associated_text: List[TextBox] = dataclasses.field(default_factory=list)
    is_spanning: bool = False

@dataclasses.dataclass
class Table(PageElement): # Define Table before Sheet, inherit from PageElement if it has a bbox
    """Represents a reconstructed table."""
    cells: List[List[Optional[TableCell]]] # Grid structure
    # Inherits bbox and page_number from PageElement

# Placeholder for DrawingView if it's a separate class defined later or elsewhere
# If it's defined in this file, define it before Sheet too.
# @dataclasses.dataclass
# class DrawingView(PageElement):
#    view_type: str = "MAIN" # Examplexx

@dataclasses.dataclass
class TitleBlockData: # Define TitleBlockData before Sheet if needed
    """Stores extracted title block metadata."""
    fields: Dict[str, Any]
    bbox: BoundingBox
    page_number: int

@dataclasses.dataclass
class ValidationError: # Define ValidationError before Sheet if needed
    """Stores information about a validation failure."""
    rule_id: str
    message: str
    severity: str
    context: Optional[Dict[str, Any]] = None

# --- END PLACEHOLDER DEFINITIONS ---


# Now the Sheet class definition should work
@dataclasses.dataclass
class Sheet:
    """Represents a single drawing sheet containing various elements."""
    page_number: int
    width: float
    height: float
    # Define DrawingView properly if it's used elsewhere, or remove if not needed yet
    # Forward reference only works if DrawingView is defined later *in the same module*
    # Or import it if defined elsewhere
    elements: List[Union[TextBox, LineSegment, CurveSegment, GraphicalSymbol, Dimension, Table]] = dataclasses.field(default_factory=list) # Removed 'DrawingView' for now

    # Add other sheet-level metadata if needed (e.g., detected format A3/A4)
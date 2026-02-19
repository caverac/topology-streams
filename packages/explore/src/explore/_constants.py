"""Default parameters and file-name constants."""

from __future__ import annotations

from pathlib import Path

# Default output root
DEFAULT_OUTPUT_DIR = Path("runs")

# Default persistent homology parameters
DEFAULT_SIGMA_THRESHOLD = 3.0
DEFAULT_N_NEIGHBORS = 32

# File names written by the recover command
GAIA_TABLE_FILE = "gaia_table.ecsv"
PERSISTENCE_FILE = "persistence.npz"
CANDIDATES_FILE = "candidates.json"
CANDIDATE_MEMBERS_FILE = "candidate_members.npz"
METADATA_FILE = "metadata.json"

# Plot file names
PERSISTENCE_DIAGRAM_FILE = "persistence_diagram.png"
SKY_MAP_FILE = "sky_map.png"

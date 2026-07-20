"""
Inspect a single subject from the human motion capture dataset.

This production-quality tool performs comprehensive inspection of one subject
from the filtered MATLAB dataset, extracting all available information without
performing biomechanical analysis or creating visualizations.

Author: AXYX research pipeline

Version: 1.0.0
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd
import scipy.io


# Configuration
DATASET_PATH = Path("data/processed/Data_structure_filtered.mat")
LOG_PATH = Path("logs/inspect_subject.log")
METADATA_BASE_PATH = Path("metadata")


# Kinematic categorization patterns
MARKER_PATTERNS = {
    'HEAD': ['LFHD', 'RFHD', 'LBHD', 'RBHD'],
    'SPINE': ['C7', 'T10', 'CLAV', 'STRN', 'RBAK'],
    'LEFT_ARM': ['LSHO', 'LUPA', 'LELB', 'LFRM', 'LWRA', 'LWRB', 'LFIN'],
    'RIGHT_ARM': ['RSHO', 'RUPA', 'RELB', 'RFRM', 'RWRA', 'RWRB', 'RFIN'],
    'PELVIS': ['LASI', 'RASI', 'LPSI', 'RPSI'],
    'LEFT_LEG': ['LTHI', 'LKNE', 'LANK', 'LHEE', 'LTOE'],
    'RIGHT_LEG': ['RTHI', 'RKNE', 'RANK', 'RHEE', 'RTOE'],
}

JOINT_ANGLE_PATTERNS = {
    'Angles': ['HipAngles', 'KneeAngles', 'AnkleAngles', 'AbsAnkleAngle',
               'PelvisAngles', 'FootProgressAngles', 'NeckAngles', 'SpineAngles',
               'ShoulderAngles', 'ElbowAngles', 'WristAngles', 'ThoraxAngles',
               'HeadAngles'],
}

JOINT_CENTER_PATTERNS = {
    'JC': ['HJC', 'KJC', 'AJC'],
}

COM_PATTERNS = {
    'COM': ['CentreOfMass', 'CentreOfMassFloor'],
    'SegmentCOM': ['PelvisCOM', 'LeftFemurCOM', 'LeftTibiaCOM', 'LeftFootCOM',
                   'RightFemurCOM', 'RightTibiaCOM', 'RightFootCOM', 'ThoraxCOM',
                   'HeadCOM', 'LeftHumerusCOM', 'LeftRadiusCOM', 'LeftHandCOM',
                   'RightHumerusCOM', 'RightRadiusCOM', 'RightHandCOM'],
}


def setup_logging(log_path: Path) -> logging.Logger:
    """
    Configure logging for the script.
    
    Args:
        log_path: Path to the log file
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger("inspect_subject")
    logger.setLevel(logging.DEBUG)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # File handler
    log_path.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_path, mode='w')
    file_handler.setLevel(logging.DEBUG)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def load_dataset(dataset_path: Path, logger: logging.Logger) -> Dict[str, Any]:
    """
    Load the MATLAB dataset.
    
    Args:
        dataset_path: Path to the .mat file
        logger: Logger instance
        
    Returns:
        Dictionary containing the loaded MATLAB data
        
    Raises:
        FileNotFoundError: If the dataset file does not exist
        ValueError: If the dataset fails validation
    """
    logger.info(f"Loading dataset from: {dataset_path}")
    
    if not dataset_path.exists():
        logger.error(f"Dataset file not found: {dataset_path}")
        raise FileNotFoundError(f"Dataset file not found: {dataset_path}")
    
    try:
        mat_data = scipy.io.loadmat(str(dataset_path))
        logger.info("Dataset loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise
    
    # Validate that the dataset has expected structure
    if 'Dat' not in mat_data:
        logger.error("Dataset does not contain 'Dat' field")
        raise ValueError("Dataset does not contain 'Dat' field")
    
    logger.info("Dataset validation passed")
    return mat_data


def list_available_subjects(mat_data: Dict[str, Any], logger: logging.Logger) -> List[str]:
    """
    List all available subjects in the dataset.
    
    Args:
        mat_data: Dictionary containing the MATLAB data
        logger: Logger instance
        
    Returns:
        List of subject IDs
    """
    dat = mat_data['Dat']
    subjects = [field for field in dat.dtype.names if field != 'Res']
    subjects.sort()
    logger.info(f"Available subjects: {subjects}")
    return subjects


def validate_subject(subject_id: str, available_subjects: List[str], 
                     logger: logging.Logger) -> None:
    """
    Validate that the requested subject exists in the dataset.
    
    Args:
        subject_id: Subject ID to validate
        available_subjects: List of available subject IDs
        logger: Logger instance
        
    Raises:
        ValueError: If the subject does not exist
    """
    if subject_id not in available_subjects:
        logger.error(f"Subject '{subject_id}' not found in dataset")
        logger.error(f"Available subjects: {available_subjects}")
        raise ValueError(f"Subject '{subject_id}' not found. Available subjects: {available_subjects}")
    
    logger.info(f"Subject '{subject_id}' validated")


def get_subject(mat_data: Dict[str, Any], subject_id: str, 
                logger: logging.Logger) -> np.ndarray:
    """
    Extract a single subject from the dataset.
    
    Args:
        mat_data: Dictionary containing the MATLAB data
        subject_id: Subject ID to extract
        logger: Logger instance
        
    Returns:
        Subject data as numpy array
    """
    logger.info(f"Extracting subject: {subject_id}")
    
    dat = mat_data['Dat']
    subject = dat[subject_id][0, 0]
    
    logger.info(f"Subject extracted successfully")
    return subject


def extract_subject_info(subject: np.ndarray, logger: logging.Logger) -> Dict[str, Any]:
    """
    Extract subject metadata from the Info field.
    
    Args:
        subject: Subject data array
        logger: Logger instance
        
    Returns:
        Dictionary containing subject metadata
    """
    logger.info("Extracting subject metadata from Info field")
    
    info = {}
    
    if 'Info' not in subject.dtype.names:
        logger.warning("Subject does not contain 'Info' field")
        return info
    
    info_struct = subject['Info'][0, 0]
    
    for field_name in info_struct.dtype.names:
        field_value = info_struct[field_name][0, 0]
        
        # Convert numpy types to Python native types
        if isinstance(field_value, np.ndarray):
            if field_value.dtype.kind in ['U', 'S']:  # String
                info[field_name] = str(field_value.item())
            elif field_value.size == 1:
                info[field_name] = field_value.item()
            else:
                info[field_name] = field_value.tolist()
        else:
            info[field_name] = field_value
        
        logger.debug(f"  {field_name}: {info[field_name]}")
    
    logger.info(f"Extracted {len(info)} metadata fields")
    return info


def extract_sessions(subject: np.ndarray, logger: logging.Logger) -> Dict[str, Any]:
    """
    Extract all sessions from the subject.
    
    Args:
        subject: Subject data array
        logger: Logger instance
        
    Returns:
        Dictionary containing session information
    """
    logger.info("Extracting sessions")
    
    sessions = {}
    
    if 'New_Session' not in subject.dtype.names:
        logger.warning("Subject does not contain 'New_Session' field")
        return sessions
    
    session_container = subject['New_Session'][0, 0]
    
    for session_name in session_container.dtype.names:
        if session_name in ['Res', 'RawRes']:
            logger.debug(f"Skipping {session_name} (not a session)")
            continue
        
        logger.debug(f"Processing session: {session_name}")
        
        session_data = session_container[session_name][0, 0]
        session_info = {
            'name': session_name,
            'sections': list(session_data.dtype.names),
        }
        
        # Extract frame count from kinematics if available
        if 'kinematics' in session_data.dtype.names:
            kinematics = session_data['kinematics'][0, 0]
            if kinematics.size > 0:
                # Get first field to determine frame count
                first_field = kinematics.dtype.names[0]
                field_data = kinematics[first_field][0, 0]
                if field_data.ndim >= 2:
                    session_info['frame_count'] = field_data.shape[1]
                    logger.debug(f"  Frame count: {session_info['frame_count']}")
        
        sessions[session_name] = session_info
    
    logger.info(f"Extracted {len(sessions)} sessions")
    return sessions


def extract_session_structure(subject: np.ndarray, session_name: str,
                             logger: logging.Logger) -> Dict[str, Any]:
    """
    Extract the structure of a specific session.
    
    Args:
        subject: Subject data array
        session_name: Name of the session to analyze
        logger: Logger instance
        
    Returns:
        Dictionary containing session structure
    """
    logger.info(f"Extracting structure for session: {session_name}")
    
    structure = {
        'session_name': session_name,
        'sections': {}
    }
    
    if 'New_Session' not in subject.dtype.names:
        logger.warning("Subject does not contain 'New_Session' field")
        return structure
    
    session_container = subject['New_Session'][0, 0]
    
    if session_name not in session_container.dtype.names:
        logger.warning(f"Session '{session_name}' not found")
        return structure
    
    session_data = session_container[session_name][0, 0]
    
    for section_name in session_data.dtype.names:
        section_data = session_data[section_name][0, 0]
        
        if hasattr(section_data, 'dtype') and section_data.dtype.names:
            structure['sections'][section_name] = {
                'type': 'struct',
                'fields': list(section_data.dtype.names),
                'field_count': len(section_data.dtype.names)
            }
            logger.debug(f"  {section_name}: struct with {len(section_data.dtype.names)} fields")
        else:
            structure['sections'][section_name] = {
                'type': str(section_data.dtype),
                'shape': section_data.shape
            }
            logger.debug(f"  {section_name}: {section_data.dtype}, shape {section_data.shape}")
    
    return structure


def categorize_kinematic_variable(var_name: str) -> str:
    """
    Categorize a kinematic variable based on naming patterns.
    
    Args:
        var_name: Name of the variable to categorize
        
    Returns:
        Category string (markers, joint_angles, joint_centers, 
                        center_of_mass, segment_com, unknown)
    """
    var_upper = var_name.upper()
    
    # Check markers
    for marker_group, markers in MARKER_PATTERNS.items():
        if var_upper in markers:
            return 'markers'
    
    # Check joint angles
    for pattern in JOINT_ANGLE_PATTERNS['Angles']:
        if pattern.upper() in var_upper:
            return 'joint_angles'
    
    # Check joint centers
    for pattern in JOINT_CENTER_PATTERNS['JC']:
        if pattern.upper() in var_upper:
            return 'joint_centers'
    
    # Check center of mass
    if 'COM' in var_upper:
        if var_upper in [v.upper() for v in COM_PATTERNS['COM']]:
            return 'center_of_mass'
        elif var_upper in [v.upper() for v in COM_PATTERNS['SegmentCOM']]:
            return 'segment_com'
    
    return 'unknown'


def extract_kinematics(subject: np.ndarray, session_name: str,
                       logger: logging.Logger) -> Dict[str, List[Dict[str, Any]]]:
    """
    Extract and categorize kinematics from a session.
    
    Args:
        subject: Subject data array
        session_name: Name of the session
        logger: Logger instance
        
    Returns:
        Dictionary with categorized kinematic variables
    """
    logger.info(f"Extracting kinematics from session: {session_name}")
    
    categories = {
        'markers': [],
        'joint_angles': [],
        'joint_centers': [],
        'center_of_mass': [],
        'segment_com': [],
        'unknown': []
    }
    
    if 'New_Session' not in subject.dtype.names:
        logger.warning("Subject does not contain 'New_Session' field")
        return categories
    
    session_container = subject['New_Session'][0, 0]
    
    if session_name not in session_container.dtype.names:
        logger.warning(f"Session '{session_name}' not found")
        return categories
    
    session_data = session_container[session_name][0, 0]
    
    if 'kinematics' not in session_data.dtype.names:
        logger.warning(f"Session '{session_name}' does not contain 'kinematics'")
        return categories
    
    kinematics = session_data['kinematics'][0, 0]
    
    for var_name in kinematics.dtype.names:
        var_data = kinematics[var_name][0, 0]
        category = categorize_kinematic_variable(var_name)
        
        var_info = {
            'name': var_name,
            'category': category,
            'shape': var_data.shape,
            'dtype': str(var_data.dtype)
        }
        
        categories[category].append(var_info)
        logger.debug(f"  {var_name}: {category} (shape: {var_data.shape})")
    
    # Log summary
    for category, variables in categories.items():
        logger.info(f"  {category}: {len(variables)} variables")
    
    return categories


def extract_events(subject: np.ndarray, session_name: str,
                   logger: logging.Logger) -> List[Dict[str, Any]]:
    """
    Extract gait events from a session.
    
    Args:
        subject: Subject data array
        session_name: Name of the session
        logger: Logger instance
        
    Returns:
        List of event information
    """
    logger.info(f"Extracting events from session: {session_name}")
    
    events = []
    
    if 'New_Session' not in subject.dtype.names:
        logger.warning("Subject does not contain 'New_Session' field")
        return events
    
    session_container = subject['New_Session'][0, 0]
    
    if session_name not in session_container.dtype.names:
        logger.warning(f"Session '{session_name}' not found")
        return events
    
    session_data = session_container[session_name][0, 0]
    
    # Check Res field for events
    if 'Res' in session_data.dtype.names:
        res = session_data['Res'][0, 0]
        
        if hasattr(res, 'dtype') and res.dtype.names:
            for field_name in res.dtype.names:
                field_data = res[field_name][0, 0]
                
                # Look for event-like fields (typically contain 'Event' or gait-related terms)
                field_lower = field_name.lower()
                if any(term in field_lower for term in ['event', 'strike', 'off', 'gait']):
                    events.append({
                        'name': field_name,
                        'shape': field_data.shape,
                        'dtype': str(field_data.dtype)
                    })
                    logger.debug(f"  Found event: {field_name}")
    
    logger.info(f"Found {len(events)} event variables")
    return events


def extract_metrics(subject: np.ndarray, session_name: str,
                    logger: logging.Logger) -> List[Dict[str, Any]]:
    """
    Extract result metrics from a session.
    
    Args:
        subject: Subject data array
        session_name: Name of the session
        logger: Logger instance
        
    Returns:
        List of metric information
    """
    logger.info(f"Extracting metrics from session: {session_name}")
    
    metrics = []
    
    if 'New_Session' not in subject.dtype.names:
        logger.warning("Subject does not contain 'New_Session' field")
        return metrics
    
    session_container = subject['New_Session'][0, 0]
    
    if session_name not in session_container.dtype.names:
        logger.warning(f"Session '{session_name}' not found")
        return metrics
    
    session_data = session_container[session_name][0, 0]
    
    # Check Res field for metrics
    if 'Res' in session_data.dtype.names:
        res = session_data['Res'][0, 0]
        
        if hasattr(res, 'dtype') and res.dtype.names:
            for field_name in res.dtype.names:
                field_data = res[field_name][0, 0]
                
                # Collect all fields from Res as potential metrics
                metrics.append({
                    'name': field_name,
                    'shape': field_data.shape,
                    'dtype': str(field_data.dtype)
                })
                logger.debug(f"  Found metric: {field_name}")
    
    logger.info(f"Found {len(metrics)} metric variables")
    return metrics


def generate_hierarchy(subject: np.ndarray, subject_id: str,
                       logger: logging.Logger) -> str:
    """
    Generate a Markdown hierarchy tree for the subject.
    
    Args:
        subject: Subject data array
        subject_id: Subject ID
        logger: Logger instance
        
    Returns:
        Markdown string containing the hierarchy
    """
    logger.info("Generating hierarchy tree")
    
    lines = []
    lines.append(f"# Subject {subject_id} Hierarchy")
    lines.append("")
    lines.append("```")
    lines.append(f"{subject_id}")
    
    def add_struct(struct: np.ndarray, indent: int = 1) -> None:
        """Recursively add struct to hierarchy."""
        prefix = "  " * indent
        
        if hasattr(struct, 'dtype') and struct.dtype.names:
            for field_name in struct.dtype.names:
                field = struct[field_name]
                
                # Handle different array dimensions
                if field.ndim == 2:
                    field = field[0, 0]
                elif field.ndim == 1:
                    field = field[0]
                
                lines.append(f"{prefix}+-- {field_name}")
                
                if hasattr(field, 'dtype') and field.dtype.names:
                    add_struct(field, indent + 1)
                elif hasattr(field, 'dtype'):
                    lines.append(f"{prefix}    +-- type: {field.dtype}, shape: {field.shape}")
                else:
                    lines.append(f"{prefix}    +-- type: {type(field).__name__}, value: {str(field)[:50]}")
    
    # Add top-level fields
    for field_name in subject.dtype.names:
        field = subject[field_name][0, 0]
        lines.append(f"  +-- {field_name}")
        
        if hasattr(field, 'dtype') and field.dtype.names:
            add_struct(field, 2)
        elif hasattr(field, 'dtype'):
            lines.append(f"      +-- type: {field.dtype}, shape: {field.shape}")
        else:
            lines.append(f"      +-- type: {type(field).__name__}, value: {str(field)[:50]}")
    
    lines.append("```")
    lines.append("")
    
    hierarchy = "\n".join(lines)
    logger.info("Hierarchy tree generated")
    return hierarchy


def write_csv(data: List[Dict[str, Any]], output_path: Path,
              logger: logging.Logger) -> None:
    """
    Write data to a CSV file.
    
    Args:
        data: List of dictionaries to write
        output_path: Path to the output CSV file
        logger: Logger instance
    """
    if not data:
        logger.warning(f"No data to write to {output_path}")
        return
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)
    logger.info(f"CSV written to {output_path}")


def write_json(data: Dict[str, Any], output_path: Path,
               logger: logging.Logger) -> None:
    """
    Write data to a JSON file.
    
    Args:
        data: Dictionary to write
        output_path: Path to the output JSON file
        logger: Logger instance
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    
    logger.info(f"JSON written to {output_path}")


def write_markdown(content: str, output_path: Path,
                   logger: logging.Logger) -> None:
    """
    Write content to a Markdown file.
    
    Args:
        content: Markdown content to write
        output_path: Path to the output Markdown file
        logger: Logger instance
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write(content)
    
    logger.info(f"Markdown written to {output_path}")


def generate_inventory(subject_info: Dict[str, Any],
                      sessions: Dict[str, Any],
                      kinematics_summary: Dict[str, int],
                      logger: logging.Logger) -> str:
    """
    Generate a comprehensive inventory markdown document.
    
    Args:
        subject_info: Subject metadata
        sessions: Session information
        kinematics_summary: Summary of kinematics categories
        logger: Logger instance
        
    Returns:
        Markdown string containing the inventory
    """
    logger.info("Generating inventory document")
    
    lines = []
    lines.append("# Subject Inventory")
    lines.append("")
    lines.append(f"Generated: {datetime.now().isoformat()}")
    lines.append("")
    
    # Subject Metadata
    lines.append("## Subject Metadata")
    lines.append("")
    for key, value in subject_info.items():
        lines.append(f"- **{key}**: {value}")
    lines.append("")
    
    # Sessions
    lines.append("## Sessions")
    lines.append("")
    for session_name, session_info in sessions.items():
        lines.append(f"### {session_name}")
        lines.append("")
        lines.append(f"- Sections: {', '.join(session_info['sections'])}")
        if 'frame_count' in session_info:
            lines.append(f"- Frame count: {session_info['frame_count']}")
        lines.append("")
    
    # Kinematics Summary
    lines.append("## Kinematics Summary")
    lines.append("")
    for category, count in kinematics_summary.items():
        lines.append(f"- **{category}**: {count} variables")
    lines.append("")
    
    return "\n".join(lines)


def main() -> int:
    """
    Main orchestration function.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Inspect a single subject from the motion capture dataset"
    )
    parser.add_argument(
        '--subject',
        required=True,
        help='Subject ID to inspect (e.g., S2)'
    )
    parser.add_argument(
        '--dataset',
        default=str(DATASET_PATH),
        help=f'Path to the dataset file (default: {DATASET_PATH})'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging(LOG_PATH)
    
    logger.info("=" * 60)
    logger.info("SUBJECT INSPECTION TOOL")
    logger.info("=" * 60)
    logger.info(f"Subject: {args.subject}")
    logger.info(f"Dataset: {args.dataset}")
    logger.info(f"Started at: {datetime.now().isoformat()}")
    
    try:
        # Load dataset
        mat_data = load_dataset(Path(args.dataset), logger)
        
        # List available subjects
        available_subjects = list_available_subjects(mat_data, logger)
        
        # Validate subject
        validate_subject(args.subject, available_subjects, logger)
        
        # Get subject
        subject = get_subject(mat_data, args.subject, logger)
        
        # Create output directory
        output_dir = METADATA_BASE_PATH / args.subject
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Output directory: {output_dir}")
        
        # Extract subject info
        subject_info = extract_subject_info(subject, logger)
        write_json(subject_info, output_dir / "subject_summary.json", logger)
        
        # Extract sessions
        sessions = extract_sessions(subject, logger)
        write_json(sessions, output_dir / "sessions.json", logger)
        
        # Extract kinematics for each session
        all_kinematics = {}
        kinematics_summary = {cat: 0 for cat in ['markers', 'joint_angles', 
                                                   'joint_centers', 'center_of_mass',
                                                   'segment_com', 'unknown']}
        
        for session_name in sessions.keys():
            kinematics = extract_kinematics(subject, session_name, logger)
            all_kinematics[session_name] = kinematics
            
            # Update summary
            for category, variables in kinematics.items():
                kinematics_summary[category] += len(variables)
        
        write_json(all_kinematics, output_dir / "kinematics.json", logger)
        
        # Write individual CSV files for kinematics categories
        for session_name, kinematics in all_kinematics.items():
            for category, variables in kinematics.items():
                if variables:
                    csv_path = output_dir / f"{session_name}_{category}.csv"
                    write_csv(variables, csv_path, logger)
        
        # Extract events and metrics for each session
        all_events = {}
        all_metrics = {}
        
        for session_name in sessions.keys():
            events = extract_events(subject, session_name, logger)
            metrics = extract_metrics(subject, session_name, logger)
            
            all_events[session_name] = events
            all_metrics[session_name] = metrics
            
            write_csv(events, output_dir / f"{session_name}_events.csv", logger)
            write_csv(metrics, output_dir / f"{session_name}_metrics.csv", logger)
        
        # Generate hierarchy
        hierarchy = generate_hierarchy(subject, args.subject, logger)
        write_markdown(hierarchy, output_dir / "hierarchy.md", logger)
        
        # Generate inventory
        inventory = generate_inventory(subject_info, sessions, 
                                       kinematics_summary, logger)
        write_markdown(inventory, output_dir / "subject_inventory.md", logger)
        
        logger.info("=" * 60)
        logger.info("INSPECTION COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)
        logger.info(f"Output directory: {output_dir}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Inspection failed with error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

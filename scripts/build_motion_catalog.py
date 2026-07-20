"""
Build a comprehensive Motion Catalog for the entire filtered dataset.

This production-quality tool discovers and validates the complete schema
across all 31 subjects in the filtered motion capture dataset.

Author: AXYX research pipeline

Version: 1.0.0
"""

import json
import logging
import shutil
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd
import scipy.io


# Configuration
DATASET_PATH = Path("data/processed/Data_structure_filtered.mat")
LOG_PATH = Path("logs/build_motion_catalog.log")
OUTPUT_PATH = Path("metadata/motion_catalog")

# Expected subjects from filter report
EXPECTED_SUBJECTS = {
    "S2", "S3", "S4", "S5", "S7", "S8", "S9", "S11", "S12", "S13",
    "S14", "S15", "S17", "S19", "S23", "S26", "S27", "S30", "S31",
    "S32", "S34", "S35", "S37", "S38", "S39", "S40", "S41", "S42",
    "S43", "S46", "S48"
}

# Expected sessions
EXPECTED_SESSIONS = {"WU01", "WU02", "WU03", "WU04", "WU05", "WU06", 
                     "WU07", "WU08", "WU09", "static"}

# Expected events (not found in dataset - will be reported as absent)
EXPECTED_EVENTS = {"KinFC", "KinFO", "Midsvnt"}

# Clinical metrics found in Res field
CLINICAL_METRICS = {"StpLen", "StpWth", "FCKneeAtt", "MSKneeAtt", "WkVel", 
                    "MTC", "Upright", "nUpright", "NeckAng", "MxStKneeAtt"}

# Session classification labels (internal key -> display name)
SESSION_CLASSIFICATION_LABELS = {
    "walking": "Walking",
    "calibration": "Calibration",
    "walking_copy": "Walking Copy",
    "calibration_copy": "Calibration Copy",
    "alternate_walking": "Alternate Walking",
    "unknown": "Unknown",
}


def setup_logging(log_path: Path) -> logging.Logger:
    """
    Configure logging for the script.
    
    Args:
        log_path: Path to the log file
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger("build_motion_catalog")
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
    
    if 'Dat' not in mat_data:
        logger.error("Dataset does not contain 'Dat' field")
        raise ValueError("Dataset does not contain 'Dat' field")
    
    logger.info("Dataset validation passed")
    return mat_data


def get_all_subjects(mat_data: Dict[str, Any], logger: logging.Logger) -> List[str]:
    """
    Get all subject IDs from the dataset.
    
    Args:
        mat_data: Dictionary containing the MATLAB data
        logger: Logger instance
        
    Returns:
        List of subject IDs
    """
    dat = mat_data['Dat']
    subjects = [field for field in dat.dtype.names if field != 'Res']
    subjects.sort()
    logger.info(f"Found {len(subjects)} subjects in dataset")
    return subjects


def extract_subject_info(subject: np.ndarray, subject_id: str,
                        logger: logging.Logger) -> Dict[str, Any]:
    """
    Extract subject metadata from Info field.
    
    Args:
        subject: Subject data array
        subject_id: Subject ID
        logger: Logger instance
        
    Returns:
        Dictionary containing subject metadata
    """
    info = {}
    
    if 'Info' not in subject.dtype.names:
        logger.warning(f"Subject {subject_id} does not contain 'Info' field")
        return info
    
    info_struct = subject['Info'][0, 0]
    
    for field_name in info_struct.dtype.names:
        field_value = info_struct[field_name][0, 0]
        
        if isinstance(field_value, np.ndarray):
            if field_value.dtype.kind in ['U', 'S']:
                info[field_name] = str(field_value.item())
            elif field_value.size == 1:
                info[field_name] = field_value.item()
            else:
                info[field_name] = field_value.tolist()
        else:
            info[field_name] = field_value
    
    return info


def detect_trajectory_layout(
    data: np.ndarray,
    logger: logging.Logger,
    context: str = ""
) -> Dict[str, Any]:
    """
    Detect XYZ vs time axis for a 2D marker/trajectory array.

    Coordinate axis is identified as the dimension of size 3. The remaining
    dimension is the frame count. Never assumes shape[0] or shape[1] is time.

    Args:
        data: Trajectory array, expected (N, 3) or (3, N)
        logger: Logger instance
        context: Optional label for warning messages

    Returns:
        Dict with keys:
            layout: 'N,3' | '3,N' | None
            frame_count: int | None
            coordinate_axis: 0 | 1 | None  (axis along XYZ)
            coordinate_dimensions: int | None
            shape: tuple

    Raises:
        ValueError: If array is not 2D
    """
    if data.ndim != 2:
        raise ValueError(f"Expected 2D array, got {data.ndim}D (shape={data.shape})")

    prefix = f"{context}: " if context else ""
    result = {
        'layout': None,
        'frame_count': None,
        'coordinate_axis': None,
        'coordinate_dimensions': None,
        'shape': tuple(data.shape),
    }

    dim0_is_xyz = data.shape[0] == 3
    dim1_is_xyz = data.shape[1] == 3

    if dim0_is_xyz and not dim1_is_xyz:
        # (3, N) - coordinates on axis 0, frames on axis 1
        result['layout'] = '3,N'
        result['coordinate_axis'] = 0
        result['coordinate_dimensions'] = 3
        result['frame_count'] = int(data.shape[1])
        logger.debug(
            f"{prefix}Detected layout (3, N): shape={data.shape}, "
            f"frames={result['frame_count']}"
        )
        return result

    if dim1_is_xyz and not dim0_is_xyz:
        # (N, 3) - frames on axis 0, coordinates on axis 1
        result['layout'] = 'N,3'
        result['coordinate_axis'] = 1
        result['coordinate_dimensions'] = 3
        result['frame_count'] = int(data.shape[0])
        logger.debug(
            f"{prefix}Detected layout (N, 3): shape={data.shape}, "
            f"frames={result['frame_count']}"
        )
        return result

    if dim0_is_xyz and dim1_is_xyz:
        logger.warning(
            f"{prefix}Ambiguous trajectory shape {data.shape}: both dimensions "
            f"equal 3. Cannot determine coordinate vs frame axis without guessing. "
            f"frame_count left as None."
        )
        return result

    # Neither dimension equals 3 - inspect data, do not guess
    finite = np.isfinite(data)
    finite_ratio = float(finite.mean()) if data.size else 0.0
    sample_min = float(np.nanmin(data)) if data.size and finite.any() else None
    sample_max = float(np.nanmax(data)) if data.size and finite.any() else None
    logger.warning(
        f"{prefix}Cannot determine coordinate axis for shape {data.shape}: "
        f"neither dimension equals 3. Inspected finite_ratio={finite_ratio:.4f}, "
        f"value_range=[{sample_min}, {sample_max}]. "
        f"frame_count left as None (no guess)."
    )
    return result


def extract_frame_count_from_trajectory(
    data: np.ndarray,
    logger: logging.Logger,
    context: str = ""
) -> Optional[int]:
    """
    Extract frame count from trajectory data by detecting the coordinate axis.

    Args:
        data: Trajectory array (either Nx3 or 3xN)
        logger: Logger instance
        context: Optional label for warning messages

    Returns:
        Frame count, or None if the layout cannot be determined safely

    Raises:
        ValueError: If array is not 2D
    """
    layout = detect_trajectory_layout(data, logger, context=context)
    return layout['frame_count']


def extract_sessions(subject: np.ndarray, subject_id: str,
                    logger: logging.Logger) -> Dict[str, Dict[str, Any]]:
    """
    Extract all sessions from a subject.
    
    Args:
        subject: Subject data array
        subject_id: Subject ID
        logger: Logger instance
        
    Returns:
        Dictionary mapping session names to session info
    """
    sessions = {}
    
    if 'New_Session' not in subject.dtype.names:
        logger.warning(f"Subject {subject_id} does not contain 'New_Session' field")
        return sessions
    
    session_container = subject['New_Session'][0, 0]
    
    for session_name in session_container.dtype.names:
        if session_name in ['Res', 'RawRes']:
            continue
        
        session_data = session_container[session_name][0, 0]
        session_info = {
            'name': session_name,
            'sections': list(session_data.dtype.names),
            'frame_count': None
        }
        
        # Extract frame count from kinematics
        if 'kinematics' in session_data.dtype.names:
            kinematics = session_data['kinematics'][0, 0]
            if kinematics.size > 0:
                # Get first marker to determine frame count
                first_field = kinematics.dtype.names[0]
                field_data = kinematics[first_field][0, 0]
                
                try:
                    context = f"{subject_id}/{session_name}/{first_field}"
                    layout = detect_trajectory_layout(field_data, logger, context=context)
                    session_info['frame_count'] = layout['frame_count']
                    session_info['trajectory_layout'] = layout['layout']
                    session_info['coordinate_axis'] = layout['coordinate_axis']
                    if layout['frame_count'] is None:
                        logger.warning(
                            f"Frame count unresolved for {context} "
                            f"(shape={field_data.shape})"
                        )
                    else:
                        logger.debug(
                            f"Frame count for {context}: {layout['frame_count']} "
                            f"(layout={layout['layout']})"
                        )
                except ValueError as e:
                    logger.warning(f"Failed to extract frame count for {subject_id}_{session_name}: {e}")
                    session_info['frame_count'] = None
        
        sessions[session_name] = session_info
    
    return sessions


def extract_kinematics(subject: np.ndarray, session_name: str,
                      logger: logging.Logger) -> Dict[str, List[str]]:
    """
    Extract kinematics variables from a session.
    
    Args:
        subject: Subject data array
        session_name: Name of the session
        logger: Logger instance
        
    Returns:
        Dictionary mapping categories to variable names
    """
    categories = {
        'markers': [],
        'joint_angles': [],
        'joint_centers': [],
        'center_of_mass': [],
        'segment_com': [],
        'unknown': []
    }
    
    if 'New_Session' not in subject.dtype.names:
        return categories
    
    session_container = subject['New_Session'][0, 0]
    
    if session_name not in session_container.dtype.names:
        return categories
    
    session_data = session_container[session_name][0, 0]
    
    if 'kinematics' not in session_data.dtype.names:
        return categories
    
    kinematics = session_data['kinematics'][0, 0]
    
    for var_name in kinematics.dtype.names:
        category = categorize_variable(var_name)
        categories[category].append(var_name)
    
    return categories


def categorize_variable(var_name: str) -> str:
    """
    Categorize a kinematic variable based on naming patterns.
    
    Args:
        var_name: Name of the variable to categorize
        
    Returns:
        Category string
    """
    var_upper = var_name.upper()
    
    # Center of mass (check first to avoid COM confusion)
    if var_upper in ['CENTREOFMASS', 'CENTREOFMASSFLOOR']:
        return 'center_of_mass'
    
    # Segment COM
    if 'COM' in var_upper:
        return 'segment_com'
    
    # Joint centers
    if 'JC' in var_upper:
        return 'joint_centers'
    
    # Joint angles (check after COM to avoid false positives)
    if 'ANGLE' in var_upper:
        return 'joint_angles'
    
    # Markers
    markers = {'LFHD', 'RFHD', 'LBHD', 'RBHD', 'C7', 'T10', 'CLAV', 'STRN', 
               'RBAK', 'LSHO', 'LUPA', 'LELB', 'LFRM', 'LWRA', 'LWRB', 'LFIN',
               'RSHO', 'RUPA', 'RELB', 'RFRM', 'RWRA', 'RWRB', 'RFIN',
               'LASI', 'RASI', 'LPSI', 'RPSI', 'LTHI', 'LKNE', 'LANK', 'LHEE',
               'LTOE', 'RTHI', 'RKNE', 'RANK', 'RHEE', 'RTOE'}
    if var_upper in markers:
        return 'markers'
    
    return 'unknown'


def extract_events(subject: np.ndarray, session_name: str,
                   logger: logging.Logger) -> List[str]:
    """
    Extract gait event variable names from a session.
    
    Note: True gait events (KinFC, KinFO, Midsvnt) are not found in this dataset.
    The Res field contains clinical metrics, not temporal gait events.
    
    Args:
        subject: Subject data array
        session_name: Name of the session
        logger: Logger instance
        
    Returns:
        List of gait event variable names (empty in this dataset)
    """
    events = []
    
    if 'New_Session' not in subject.dtype.names:
        return events
    
    session_container = subject['New_Session'][0, 0]
    
    if session_name not in session_container.dtype.names:
        return events
    
    session_data = session_container[session_name][0, 0]
    
    if 'Res' in session_data.dtype.names:
        res = session_data['Res'][0, 0]
        
        if hasattr(res, 'dtype') and res.dtype.names:
            # Only extract fields that match expected gait events
            for field_name in res.dtype.names:
                if field_name in EXPECTED_EVENTS:
                    events.append(field_name)
    
    return events


def extract_metrics(subject: np.ndarray, session_name: str,
                   logger: logging.Logger) -> List[str]:
    """
    Extract clinical metric variable names from a session.
    
    Note: The Res field contains clinical metrics (StpLen, WkVel, etc.), not gait events.
    
    Args:
        subject: Subject data array
        session_name: Name of the session
        logger: Logger instance
        
    Returns:
        List of clinical metric variable names
    """
    metrics = []
    
    if 'New_Session' not in subject.dtype.names:
        return metrics
    
    session_container = subject['New_Session'][0, 0]
    
    if session_name not in session_container.dtype.names:
        return metrics
    
    session_data = session_container[session_name][0, 0]
    
    if 'Res' in session_data.dtype.names:
        res = session_data['Res'][0, 0]
        
        if hasattr(res, 'dtype') and res.dtype.names:
            # Extract all fields from Res as clinical metrics
            for field_name in res.dtype.names:
                metrics.append(field_name)
    
    return metrics


def classify_session(session_name: str) -> str:
    """
    Classify a session into semantic categories without renaming it.

    Does not assume sessions are limited to WU01-WU09. Original session
    names are preserved; only a semantic label is assigned.

    Categories (internal keys):
        walking, calibration, walking_copy, calibration_copy,
        alternate_walking, unknown

    Args:
        session_name: Original session name from the dataset

    Returns:
        Internal classification key (see SESSION_CLASSIFICATION_LABELS)
    """
    session_lower = session_name.lower()
    is_copy = session_lower.endswith('copy') or 'copy' in session_lower

    # Calibration / static sessions (including Copy variants)
    if 'static' in session_lower or 'calib' in session_lower:
        return 'calibration_copy' if is_copy else 'calibration'

    # Strip Copy suffix for pattern matching on the stem
    stem = session_lower
    if stem.endswith('copy'):
        stem = stem[:-4]

    # Alternate walking: WK## (any digits), or non-padded WU# stems
    if stem.startswith('wk') and stem[2:].isdigit():
        return 'alternate_walking'

    if stem.startswith('wu'):
        rest = stem[2:]
        # Canonical padded walking: WU01, WU02, ... WU99 (any count, not just 01-09)
        if rest.isdigit() and len(rest) >= 2:
            return 'walking_copy' if is_copy else 'walking'
        # Alternate single-digit / short forms: WU0, WU3, WU9, etc.
        if rest.isdigit() and len(rest) == 1:
            return 'alternate_walking'
        # Other WU* stems - treat as walking (Copy if indicated)
        return 'walking_copy' if is_copy else 'walking'

    return 'unknown'


def session_classification_label(internal_key: str) -> str:
    """Map internal classification key to display label."""
    return SESSION_CLASSIFICATION_LABELS.get(internal_key, "Unknown")


def build_subject_catalog(mat_data: Dict[str, Any], 
                         logger: logging.Logger) -> Dict[str, Any]:
    """
    Build catalog of all subjects.
    
    Args:
        mat_data: Dictionary containing the MATLAB data
        logger: Logger instance
        
    Returns:
        Dictionary containing subject catalog
    """
    logger.info("Building subject catalog")
    
    available_subjects = get_all_subjects(mat_data, logger)
    available_set = set(available_subjects)
    
    catalog = {
        'total_subjects': len(available_subjects),
        'expected_subjects': len(EXPECTED_SUBJECTS),
        'available_subjects': available_subjects,
        'missing_subjects': sorted(EXPECTED_SUBJECTS - available_set),
        'unexpected_subjects': sorted(available_set - EXPECTED_SUBJECTS),
        'subject_details': {}
    }
    
    # Extract details for each subject
    for subject_id in available_subjects:
        subject = mat_data['Dat'][subject_id][0, 0]
        info = extract_subject_info(subject, subject_id, logger)
        catalog['subject_details'][subject_id] = info
    
    logger.info(f"Subject catalog: {catalog['total_subjects']} subjects, "
                f"{len(catalog['missing_subjects'])} missing, "
                f"{len(catalog['unexpected_subjects'])} unexpected")
    
    return catalog


def build_session_catalog(mat_data: Dict[str, Any],
                         logger: logging.Logger) -> Dict[str, Any]:
    """
    Build catalog of all sessions across all subjects.
    
    Args:
        mat_data: Dictionary containing the MATLAB data
        logger: Logger instance
        
    Returns:
        Dictionary containing session catalog
    """
    logger.info("Building session catalog")
    
    catalog = {
        'total_sessions': 0,
        'sessions_per_subject': {},
        'session_names': set(),
        'session_frequency': Counter(),
        'session_classification': defaultdict(list),
        'session_details': defaultdict(lambda: {'subjects': set(), 'classification': None}),
        'missing_expected_sessions': defaultdict(list),
        'frame_counts': []
    }
    
    subjects = get_all_subjects(mat_data, logger)
    
    for subject_id in subjects:
        subject = mat_data['Dat'][subject_id][0, 0]
        sessions = extract_sessions(subject, subject_id, logger)
        
        catalog['sessions_per_subject'][subject_id] = list(sessions.keys())
        catalog['total_sessions'] += len(sessions)
        
        for session_name, session_info in sessions.items():
            catalog['session_names'].add(session_name)
            catalog['session_frequency'][session_name] += 1
            
            # Classify session
            category = classify_session(session_name)
            catalog['session_classification'][category].append(f"{subject_id}_{session_name}")
            catalog['session_details'][session_name]['subjects'].add(subject_id)
            catalog['session_details'][session_name]['classification'] = category
            
            catalog['frame_counts'].append({
                'subject': subject_id,
                'session': session_name,
                'frame_count': session_info.get('frame_count'),
                'trajectory_layout': session_info.get('trajectory_layout'),
                'coordinate_axis': session_info.get('coordinate_axis'),
            })
        
        # Check for missing expected sessions (only for walking sessions)
        subject_sessions = set(sessions.keys())
        subject_walking = {s for s in subject_sessions if classify_session(s) == 'walking'}
        expected_walking = EXPECTED_SESSIONS - {'static'}
        missing = expected_walking - subject_walking
        if missing:
            catalog['missing_expected_sessions'][subject_id] = sorted(missing)
    
    # Convert sets to sorted lists
    for session_name, details in catalog['session_details'].items():
        details['subjects'] = sorted(details['subjects'])
        details['subject_count'] = len(details['subjects'])
    
    catalog['session_names'] = sorted(catalog['session_names'])
    
    logger.info(f"Session catalog: {catalog['total_sessions']} total sessions, "
                f"{len(catalog['session_names'])} unique session names")
    
    return catalog


def build_kinematics_catalog(mat_data: Dict[str, Any],
                            logger: logging.Logger) -> Dict[str, Any]:
    """
    Build catalog of all kinematics variables across all subjects.
    
    Args:
        mat_data: Dictionary containing the MATLAB data
        logger: Logger instance
        
    Returns:
        Dictionary containing kinematics catalog
    """
    logger.info("Building kinematics catalog")
    
    catalog = {
        'markers': Counter(),
        'joint_angles': Counter(),
        'joint_centers': Counter(),
        'center_of_mass': Counter(),
        'segment_com': Counter(),
        'unknown': Counter()
    }
    
    subjects = get_all_subjects(mat_data, logger)
    
    for subject_id in subjects:
        subject = mat_data['Dat'][subject_id][0, 0]
        sessions = extract_sessions(subject, subject_id, logger)
        
        for session_name in sessions.keys():
            kinematics = extract_kinematics(subject, session_name, logger)
            
            for category, variables in kinematics.items():
                for var_name in variables:
                    catalog[category][var_name] += 1
    
    # Convert counters to sorted lists
    for category in catalog.keys():
        catalog[category] = dict(sorted(catalog[category].items()))
    
    logger.info(f"Kinematics catalog: "
                f"{len(catalog['markers'])} markers, "
                f"{len(catalog['joint_angles'])} joint angles, "
                f"{len(catalog['joint_centers'])} joint centers, "
                f"{len(catalog['center_of_mass'])} COM, "
                f"{len(catalog['segment_com'])} segment COM")
    
    return catalog


def build_variable_catalog(mat_data: Dict[str, Any],
                          logger: logging.Logger) -> Dict[str, Any]:
    """
    Build comprehensive catalog of all variables with semantic categories.
    
    Args:
        mat_data: Dictionary containing the MATLAB data
        logger: Logger instance
        
    Returns:
        Dictionary containing variable catalog with metadata
    """
    logger.info("Building variable catalog")
    
    catalog = {}
    
    subjects = get_all_subjects(mat_data, logger)
    
    for subject_id in subjects:
        subject = mat_data['Dat'][subject_id][0, 0]
        sessions = extract_sessions(subject, subject_id, logger)
        
        for session_name, session_info in sessions.items():
            # Get kinematics
            kinematics = extract_kinematics(subject, session_name, logger)
            
            # Get clinical metrics
            metrics = extract_metrics(subject, session_name, logger)
            
            # Process kinematics variables
            for category, variables in kinematics.items():
                for var_name in variables:
                    if var_name not in catalog:
                        catalog[var_name] = {
                            'name': var_name,
                            'semantic_category': category,
                            'subjects_present': set(),
                            'sessions_present': set(),
                            'shape': None,
                            'frame_count': None,
                            'coordinate_dimensions': None,
                            'datatype': None,
                            'units': 'Unknown'
                        }
                    
                    catalog[var_name]['subjects_present'].add(subject_id)
                    catalog[var_name]['sessions_present'].add(f"{subject_id}_{session_name}")
                    
                    # Extract detailed metadata from first occurrence
                    if catalog[var_name]['shape'] is None:
                        session_container = subject['New_Session'][0, 0]
                        session_data = session_container[session_name][0, 0]
                        kinematics_data = session_data['kinematics'][0, 0]
                        var_data = kinematics_data[var_name][0, 0]
                        
                        catalog[var_name]['shape'] = var_data.shape
                        catalog[var_name]['datatype'] = str(var_data.dtype)
                        
                        # Determine frame count by detecting XYZ axis (never assume axis order)
                        if var_data.ndim == 2:
                            context = f"{subject_id}/{session_name}/{var_name}"
                            try:
                                layout = detect_trajectory_layout(
                                    var_data, logger, context=context
                                )
                                catalog[var_name]['coordinate_dimensions'] = (
                                    layout['coordinate_dimensions']
                                )
                                catalog[var_name]['frame_count'] = layout['frame_count']
                                catalog[var_name]['trajectory_layout'] = layout['layout']
                                catalog[var_name]['coordinate_axis'] = (
                                    layout['coordinate_axis']
                                )
                            except ValueError as e:
                                logger.warning(
                                    f"Failed layout detection for {context}: {e}"
                                )
                                catalog[var_name]['coordinate_dimensions'] = None
                                catalog[var_name]['frame_count'] = None
                        elif var_data.ndim == 1:
                            # 1D series - not XYZ trajectories; do not invent a layout
                            catalog[var_name]['coordinate_dimensions'] = None
                            catalog[var_name]['frame_count'] = int(var_data.shape[0])
                            catalog[var_name]['trajectory_layout'] = '1D'
                            logger.debug(
                                f"{subject_id}/{session_name}/{var_name}: 1D array, "
                                f"length={var_data.shape[0]} recorded as frame_count"
                            )
            
            # Process clinical metrics
            for metric_name in metrics:
                if metric_name not in catalog:
                    catalog[metric_name] = {
                        'name': metric_name,
                        'semantic_category': 'clinical_metric',
                        'subjects_present': set(),
                        'sessions_present': set(),
                        'shape': None,
                        'frame_count': None,
                        'coordinate_dimensions': None,
                        'datatype': None,
                        'units': 'Unknown'
                    }
                
                catalog[metric_name]['subjects_present'].add(subject_id)
                catalog[metric_name]['sessions_present'].add(f"{subject_id}_{session_name}")
                
                # Extract detailed metadata from first occurrence
                if catalog[metric_name]['shape'] is None:
                    session_container = subject['New_Session'][0, 0]
                    session_data = session_container[session_name][0, 0]
                    res_data = session_data['Res'][0, 0]
                    metric_data = res_data[metric_name][0, 0]
                    
                    catalog[metric_name]['shape'] = metric_data.shape
                    catalog[metric_name]['datatype'] = str(metric_data.dtype)
                    # Clinical metrics are not XYZ trajectories; do not apply
                    # marker layout detection or invent a coordinate axis.
                    catalog[metric_name]['coordinate_dimensions'] = None
                    catalog[metric_name]['trajectory_layout'] = None
                    catalog[metric_name]['frame_count'] = None
    
    # Convert sets to sorted lists for JSON serialization
    for var_name, var_info in catalog.items():
        var_info['subjects_present'] = sorted(var_info['subjects_present'])
        var_info['sessions_present'] = sorted(var_info['sessions_present'])
        var_info['subject_count'] = len(var_info['subjects_present'])
        var_info['session_count'] = len(var_info['sessions_present'])
    
    logger.info(f"Variable catalog: {len(catalog)} total variables")
    
    return catalog


def build_events_catalog(mat_data: Dict[str, Any],
                        logger: logging.Logger) -> Dict[str, Any]:
    """
    Build catalog of all events across all subjects.
    
    Args:
        mat_data: Dictionary containing the MATLAB data
        logger: Logger instance
        
    Returns:
        Dictionary containing events catalog
    """
    logger.info("Building events catalog")
    
    catalog = {
        'event_names': Counter(),
        'events_per_session': defaultdict(list),
        'missing_expected_events': defaultdict(list)
    }
    
    subjects = get_all_subjects(mat_data, logger)
    
    for subject_id in subjects:
        subject = mat_data['Dat'][subject_id][0, 0]
        sessions = extract_sessions(subject, subject_id, logger)
        
        for session_name in sessions.keys():
            events = extract_events(subject, session_name, logger)
            
            for event_name in events:
                catalog['event_names'][event_name] += 1
                catalog['events_per_session'][f"{subject_id}_{session_name}"].append(event_name)
            
            # Check for missing expected events
            event_set = set(events)
            missing = EXPECTED_EVENTS - event_set
            if missing:
                catalog['missing_expected_events'][f"{subject_id}_{session_name}"] = sorted(missing)
    
    catalog['event_names'] = dict(sorted(catalog['event_names'].items()))
    
    logger.info(f"Events catalog: {len(catalog['event_names'])} unique event types")
    
    return catalog


def build_metrics_catalog(mat_data: Dict[str, Any],
                        logger: logging.Logger) -> Dict[str, Any]:
    """
    Build catalog of all metrics across all subjects.
    
    Args:
        mat_data: Dictionary containing the MATLAB data
        logger: Logger instance
        
    Returns:
        Dictionary containing metrics catalog
    """
    logger.info("Building metrics catalog")
    
    catalog = {
        'metric_names': Counter(),
        'metrics_per_session': defaultdict(list)
    }
    
    subjects = get_all_subjects(mat_data, logger)
    
    for subject_id in subjects:
        subject = mat_data['Dat'][subject_id][0, 0]
        sessions = extract_sessions(subject, subject_id, logger)
        
        for session_name in sessions.keys():
            metrics = extract_metrics(subject, session_name, logger)
            
            for metric_name in metrics:
                catalog['metric_names'][metric_name] += 1
                catalog['metrics_per_session'][f"{subject_id}_{session_name}"].append(metric_name)
    
    catalog['metric_names'] = dict(sorted(catalog['metric_names'].items()))
    
    logger.info(f"Metrics catalog: {len(catalog['metric_names'])} unique metric types")
    
    return catalog


def compute_frame_statistics(session_catalog: Dict[str, Any],
                            logger: logging.Logger) -> Dict[str, Any]:
    """
    Compute frame count statistics from layout-aware session frame counts.
    
    Args:
        session_catalog: Session catalog containing frame counts
        logger: Logger instance
        
    Returns:
        Dictionary containing frame statistics
    """
    logger.info("Computing frame statistics (layout-aware frame counts)")
    
    resolved = [
        fc for fc in session_catalog['frame_counts']
        if fc.get('frame_count') is not None
    ]
    unresolved = [
        fc for fc in session_catalog['frame_counts']
        if fc.get('frame_count') is None
    ]
    frame_counts = [fc['frame_count'] for fc in resolved]
    
    if unresolved:
        logger.warning(
            f"Frame count unresolved for {len(unresolved)} session(s); "
            f"excluded from statistics"
        )
    
    if not frame_counts:
        logger.warning("No resolved frame counts available for statistics")
        return {
            'min_frames': 0,
            'max_frames': 0,
            'mean_frames': 0.0,
            'std_frames': 0.0,
            'total_sessions': 0,
            'resolved_sessions': 0,
            'unresolved_sessions': len(unresolved),
        }
    
    statistics = {
        'min_frames': int(min(frame_counts)),
        'max_frames': int(max(frame_counts)),
        'mean_frames': float(np.mean(frame_counts)),
        'std_frames': float(np.std(frame_counts)),
        'total_sessions': len(session_catalog['frame_counts']),
        'resolved_sessions': len(resolved),
        'unresolved_sessions': len(unresolved),
    }
    
    # Guardrail: constant frame_count == 3 is the prior bug signature for (N,3) data
    if (
        statistics['min_frames'] == 3
        and statistics['max_frames'] == 3
        and statistics['resolved_sessions'] > 1
    ):
        logger.warning(
            "CORRECTNESS CHECK: all resolved sessions report exactly 3 frames. "
            "This matches the prior axis-swap bug (treating XYZ size as frames). "
            "Verify trajectory layout detection."
        )
    else:
        logger.info(
            f"CORRECTNESS CHECK PASSED: frame counts vary / exceed XYZ size "
            f"(min={statistics['min_frames']}, max={statistics['max_frames']})"
        )
    
    logger.info(
        f"Frame statistics: min={statistics['min_frames']}, "
        f"max={statistics['max_frames']}, "
        f"mean={statistics['mean_frames']:.2f}, "
        f"std={statistics['std_frames']:.2f}, "
        f"resolved={statistics['resolved_sessions']}, "
        f"unresolved={statistics['unresolved_sessions']}"
    )
    
    return statistics


def validate_sampling_rates(subject_catalog: Dict[str, Any],
                           logger: logging.Logger) -> Dict[str, Any]:
    """
    Validate sampling rates across all subjects.
    
    Args:
        subject_catalog: Subject catalog containing metadata
        logger: Logger instance
        
    Returns:
        Dictionary containing sampling rate validation results
    """
    logger.info("Validating sampling rates")
    
    vrate_values = []
    fprate_values = []
    
    for subject_id, info in subject_catalog['subject_details'].items():
        if 'Vrate' in info:
            vrate_values.append((subject_id, info['Vrate']))
        if 'FPrate' in info:
            fprate_values.append((subject_id, info['FPrate']))
    
    # Check consistency
    vrate_set = set(v[1] for v in vrate_values)
    fprate_set = set(f[1] for f in fprate_values)
    
    validation = {
        'vrate_values': vrate_values,
        'fprate_values': fprate_values,
        'vrate_unique': sorted(vrate_set),
        'fprate_unique': sorted(fprate_set),
        'vrate_consistent': len(vrate_set) == 1,
        'fprate_consistent': len(fprate_set) == 1,
        'subjects_missing_vrate': len(subject_catalog['subject_details']) - len(vrate_values),
        'subjects_missing_fprate': len(subject_catalog['subject_details']) - len(fprate_values)
    }
    
    logger.info(f"Sampling rate validation: Vrate consistent={validation['vrate_consistent']}, "
                f"FPrate consistent={validation['fprate_consistent']}")
    
    return validation


def validate_metadata_consistency(subject_catalog: Dict[str, Any],
                                  logger: logging.Logger) -> Dict[str, Any]:
    """
    Validate metadata consistency across all subjects.
    
    Args:
        subject_catalog: Subject catalog containing metadata
        logger: Logger instance
        
    Returns:
        Dictionary containing metadata validation results
    """
    logger.info("Validating metadata consistency")
    
    metadata_fields = ['Mass', 'Height', 'LLegLength', 'RLegLength']
    validation = {}
    
    for field in metadata_fields:
        values = []
        missing = []
        
        for subject_id, info in subject_catalog['subject_details'].items():
            if field in info:
                values.append((subject_id, info[field]))
            else:
                missing.append(subject_id)
        
        validation[field] = {
            'present_count': len(values),
            'missing_count': len(missing),
            'missing_subjects': missing,
            'min_value': min(v[1] for v in values) if values else None,
            'max_value': max(v[1] for v in values) if values else None,
            'mean_value': float(np.mean([v[1] for v in values])) if values else None
        }
    
    logger.info(f"Metadata validation: checked {len(metadata_fields)} fields")
    
    return validation


def detect_inconsistencies(subject_catalog: Dict[str, Any],
                          session_catalog: Dict[str, Any],
                          kinematics_catalog: Dict[str, Any],
                          events_catalog: Dict[str, Any],
                          logger: logging.Logger) -> Dict[str, Any]:
    """
    Detect structural inconsistencies across the dataset.
    
    Args:
        subject_catalog: Subject catalog
        session_catalog: Session catalog
        kinematics_catalog: Kinematics catalog
        events_catalog: Events catalog
        logger: Logger instance
        
    Returns:
        Dictionary containing detected inconsistencies
    """
    logger.info("Detecting structural inconsistencies")
    
    inconsistencies = {
        'missing_subjects': subject_catalog['missing_subjects'],
        'unexpected_subjects': subject_catalog['unexpected_subjects'],
        'subjects_with_missing_sessions': list(session_catalog['missing_expected_sessions'].keys()),
        'inconsistent_session_counts': False,
        'markers_not_in_all_subjects': [],
        'joint_angles_not_in_all_subjects': [],
        'events_not_in_all_sessions': list(events_catalog['missing_expected_events'].keys()),
        'true_gait_events_absent': len(events_catalog['event_names']) == 0
    }
    
    # Check if all subjects have same session count
    session_counts = [len(sessions) for sessions in session_catalog['sessions_per_subject'].values()]
    inconsistencies['inconsistent_session_counts'] = len(set(session_counts)) > 1
    
    # Check markers consistency
    total_subjects = subject_catalog['total_subjects']
    for marker, count in kinematics_catalog['markers'].items():
        if count < total_subjects:
            inconsistencies['markers_not_in_all_subjects'].append({
                'marker': marker,
                'present_in': count,
                'missing_from': total_subjects - count
            })
    
    # Check joint angles consistency
    for angle, count in kinematics_catalog['joint_angles'].items():
        if count < total_subjects:
            inconsistencies['joint_angles_not_in_all_subjects'].append({
                'angle': angle,
                'present_in': count,
                'missing_from': total_subjects - count
            })
    
    logger.info(f"Detected {sum(1 for v in inconsistencies.values() if v)} categories of inconsistencies")
    
    return inconsistencies


def probe_dataset_units(
    mat_data: Dict[str, Any],
    logger: logging.Logger,
    max_depth: int = 5
) -> Dict[str, Any]:
    """
    Search the MATLAB structure for explicit unit metadata.

    Never invents units. Only records field names/paths that look like unit
    declarations (e.g. fields containing 'unit').

    Args:
        mat_data: Loaded MATLAB dictionary
        logger: Logger instance
        max_depth: Maximum recursion depth when walking structs

    Returns:
        Probe result with found paths and whether any explicit units exist
    """
    logger.info("Probing dataset for explicit unit metadata (no guessing)")
    found_paths: List[str] = []

    def walk(node: Any, path: str, depth: int) -> None:
        if depth > max_depth:
            return
        if not isinstance(node, np.ndarray):
            return
        if node.dtype.names is None:
            return
        for name in node.dtype.names:
            child_path = f"{path}.{name}"
            if 'unit' in name.lower():
                found_paths.append(child_path)
                logger.info(f"Found potential unit field: {child_path}")
            try:
                child = node[name]
                if child.ndim >= 2 and child.size > 0:
                    walk(child[0, 0], child_path, depth + 1)
                elif child.ndim == 1 and child.size > 0:
                    walk(child[0], child_path, depth + 1)
                elif child.ndim == 0:
                    walk(child, child_path, depth + 1)
            except Exception as e:
                logger.debug(f"Skipping {child_path} during unit probe: {e}")

    if 'Dat' in mat_data:
        walk(mat_data['Dat'], 'Dat', 0)

    # Also scan top-level non-private keys
    for key, value in mat_data.items():
        if key.startswith('__'):
            continue
        if key == 'Dat':
            continue
        if 'unit' in key.lower():
            found_paths.append(key)
            logger.info(f"Found potential unit field at top level: {key}")
        walk(value, key, 0)

    explicit = len(found_paths) > 0
    if explicit:
        logger.info(f"Unit probe found {len(found_paths)} candidate field(s)")
    else:
        logger.info(
            "Unit probe found no explicit unit metadata in dataset structure. "
            "All categories will be recorded as Unknown."
        )

    return {
        'explicit_units_found': explicit,
        'candidate_paths': found_paths,
        'reason_if_unknown': (
            'The MATLAB .mat hierarchy contains no fields documenting physical '
            'units for markers, angles, joint centers, COM, or clinical metrics. '
            'A structural probe for field names containing "unit" returned no matches. '
            'Therefore units are recorded as Unknown rather than assumed.'
        ),
    }


def build_units_schema(
    units_probe: Dict[str, Any],
    kinematics_catalog: Dict[str, Any],
    metrics_catalog: Dict[str, Any],
    logger: logging.Logger
) -> Dict[str, Any]:
    """
    Build units.json content. Never substitutes millimeters/degrees guesses.

    Args:
        units_probe: Result from probe_dataset_units
        kinematics_catalog: Kinematics catalog
        metrics_catalog: Metrics catalog
        logger: Logger instance

    Returns:
        Units schema dictionary
    """
    logger.info("Building units.json (Unknown unless explicitly present)")

    category_meta = {
        'markers': {
            'description': '3D marker trajectories',
            'variables': list(kinematics_catalog['markers'].keys()),
        },
        'joint_angles': {
            'description': 'Joint angle time series',
            'variables': list(kinematics_catalog['joint_angles'].keys()),
        },
        'joint_centers': {
            'description': 'Joint center positions',
            'variables': list(kinematics_catalog['joint_centers'].keys()),
        },
        'center_of_mass': {
            'description': 'Whole-body center of mass',
            'variables': list(kinematics_catalog['center_of_mass'].keys()),
        },
        'segment_com': {
            'description': 'Segment center of mass',
            'variables': list(kinematics_catalog['segment_com'].keys()),
        },
        'clinical_metric': {
            'description': 'Clinical outcome measures',
            'variables': list(metrics_catalog['metric_names'].keys()),
        },
    }

    categories: Dict[str, Any] = {}
    for name, meta in category_meta.items():
        categories[name] = {
            'description': meta['description'],
            'unit_status': 'Unknown',
            'unit_value': None,
            'source': None,
            'reason': units_probe['reason_if_unknown'],
            'variables': meta['variables'],
        }

    schema = {
        'schema_version': '1.0.0',
        'generated': datetime.now().isoformat(),
        'policy': (
            'Never guess units. Record Unknown when the dataset does not '
            'explicitly specify them. Do not assume millimeters or degrees.'
        ),
        'probe': {
            'explicit_units_found': units_probe['explicit_units_found'],
            'candidate_paths': units_probe['candidate_paths'],
        },
        'note': (
            'Units are Unknown for every variable category because the dataset '
            'structure does not specify them.'
            if not units_probe['explicit_units_found']
            else 'Potential unit fields were found; review candidate_paths before use.'
        ),
        'reason': units_probe['reason_if_unknown'],
        'recommendation': (
            'MotionDatabase parser must leave units as Unknown unless an '
            'authoritative external specification is supplied separately. '
            'Do not hardcode millimeters or degrees.'
        ),
        'categories': categories,
    }
    return schema


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
    
    with open(output_path, 'w', encoding='utf-8') as f:
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
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info(f"Markdown written to {output_path}")


def generate_motion_schema(subject_catalog: Dict[str, Any],
                          session_catalog: Dict[str, Any],
                          kinematics_catalog: Dict[str, Any],
                          variable_catalog: Dict[str, Any],
                          events_catalog: Dict[str, Any],
                          metrics_catalog: Dict[str, Any],
                          logger: logging.Logger) -> Dict[str, Any]:
    """
    Generate motion schema JSON describing the complete logical schema.
    
    Args:
        subject_catalog: Subject catalog
        session_catalog: Session catalog
        kinematics_catalog: Kinematics catalog
        variable_catalog: Variable catalog
        events_catalog: Events catalog
        metrics_catalog: Metrics catalog
        logger: Logger instance
        
    Returns:
        Dictionary containing motion schema
    """
    logger.info("Generating motion schema")
    
    schema = {
        'schema_version': '1.0.0',
        'generated': datetime.now().isoformat(),
        'dataset': {
            'total_subjects': subject_catalog['total_subjects'],
            'total_sessions': session_catalog['total_sessions'],
            'unique_session_types': len(session_catalog['session_names'])
        },
        'subjects': {
            'count': subject_catalog['total_subjects'],
            'ids': subject_catalog['available_subjects'],
            'metadata_fields': list(subject_catalog['subject_details'][subject_catalog['available_subjects'][0]].keys()) if subject_catalog['available_subjects'] else []
        },
        'sessions': {
            'classification': {
                session_classification_label(k): len(v)
                for k, v in session_catalog['session_classification'].items()
            },
            'classification_keys': {
                k: len(v) for k, v in session_catalog['session_classification'].items()
            },
            'unique_names': session_catalog['session_names'],
            'expected_walking_sessions': list(EXPECTED_SESSIONS - {'static'}),
            'note': (
                'Original session names are preserved. Classification is a semantic '
                'label only and is not limited to WU01-WU09.'
            ),
        },
        'variables': {
            'total_count': len(variable_catalog),
            'by_category': {},
            'semantic_categories': {
                'markers': '3D marker trajectories',
                'joint_angles': 'Joint angle time series',
                'joint_centers': 'Joint center positions',
                'center_of_mass': 'Whole-body center of mass',
                'segment_com': 'Segment center of mass',
                'clinical_metric': 'Clinical outcome measures',
                'unknown': 'Uncategorized variables'
            }
        },
        'kinematics': {
            'markers': list(kinematics_catalog['markers'].keys()),
            'joint_angles': list(kinematics_catalog['joint_angles'].keys()),
            'joint_centers': list(kinematics_catalog['joint_centers'].keys()),
            'center_of_mass': list(kinematics_catalog['center_of_mass'].keys()),
            'segment_com': list(kinematics_catalog['segment_com'].keys())
        },
        'clinical_metrics': {
            'available': list(metrics_catalog['metric_names'].keys()),
            'count': len(metrics_catalog['metric_names'])
        },
        'gait_events': {
            'expected': list(EXPECTED_EVENTS),
            'found': list(events_catalog['event_names'].keys()),
            'absent': len(events_catalog['event_names']) == 0,
            'note': 'True temporal gait events are absent. Res field contains clinical metrics.'
        },
        'assumptions': [
            'Trajectory layout is auto-detected: coordinate axis = dimension of size 3; '
            'remaining dimension = frame count. Supports (N,3) and (3,N). '
            'Ambiguous or unresolvable shapes leave frame_count as null (no guessing).',
            'Units are Unknown unless explicitly present in dataset metadata '
            '(see units.json). Millimeters/degrees are never assumed.',
            'Session names are preserved exactly as stored; semantic classification '
            'is labels only (Walking / Calibration / Copy / Alternate / Unknown).',
            'Session inventory is not limited to WU01-WU09; any WU## / WK## / static '
            'patterns are classified programmatically.',
            'Copy suffix indicates duplicate sessions for classification only.',
            'Clinical metrics in Res are not temporal gait events and are not treated '
            'as XYZ trajectories.',
        ]
    }
    
    # Count variables by category
    category_counts = defaultdict(int)
    for var_name, var_info in variable_catalog.items():
        category_counts[var_info['semantic_category']] += 1
    schema['variables']['by_category'] = dict(category_counts)
    
    logger.info("Motion schema generated")
    return schema


def generate_parser_readiness_report(subject_catalog: Dict[str, Any],
                                    session_catalog: Dict[str, Any],
                                    kinematics_catalog: Dict[str, Any],
                                    variable_catalog: Dict[str, Any],
                                    inconsistencies: Dict[str, Any],
                                    frame_stats: Dict[str, Any],
                                    logger: logging.Logger) -> str:
    """
    Generate parser readiness report.
    
    Args:
        subject_catalog: Subject catalog
        session_catalog: Session catalog
        kinematics_catalog: Kinematics catalog
        variable_catalog: Variable catalog
        inconsistencies: Detected inconsistencies
        frame_stats: Frame statistics
        logger: Logger instance
        
    Returns:
        Markdown string containing parser readiness report
    """
    logger.info("Generating parser readiness report")
    
    lines = []
    lines.append("# Parser Readiness Report")
    lines.append("")
    lines.append(f"Generated: {datetime.now().isoformat()}")
    lines.append("")
    
    # Dataset Consistency
    lines.append("## Dataset Consistency")
    lines.append("")
    lines.append(f"- **Subject Consistency**: {'PASS' if not inconsistencies['missing_subjects'] and not inconsistencies['unexpected_subjects'] else 'WARNING'}")
    lines.append(f"- **Marker Consistency**: {'PASS' if not inconsistencies['markers_not_in_all_subjects'] else 'WARNING'}")
    lines.append(f"- **Joint Angle Consistency**: {'PASS' if not inconsistencies['joint_angles_not_in_all_subjects'] else 'WARNING'}")
    lines.append(f"- **Session Count Consistency**: {'WARNING' if inconsistencies['inconsistent_session_counts'] else 'PASS'}")
    lines.append("")
    
    # Frame count correction status
    lines.append("## Frame Count Extraction (Corrected)")
    lines.append("")
    lines.append(
        "Frame counts are derived by detecting the XYZ axis (dimension of size 3) "
        "and using the remaining dimension as time. Supported layouts: `(N, 3)` and "
        "`(3, N)`. Ambiguous shapes `(3, 3)` or arrays with neither dimension equal "
        "to 3 leave `frame_count` as null and emit a warning - no guessing."
    )
    lines.append("")
    lines.append(f"- **Min Frames**: {frame_stats.get('min_frames', 0)}")
    lines.append(f"- **Max Frames**: {frame_stats.get('max_frames', 0)}")
    lines.append(f"- **Mean Frames**: {frame_stats.get('mean_frames', 0):.2f}")
    lines.append(f"- **Std Dev Frames**: {frame_stats.get('std_frames', 0):.2f}")
    lines.append(f"- **Resolved Sessions**: {frame_stats.get('resolved_sessions', 0)}")
    lines.append(f"- **Unresolved Sessions**: {frame_stats.get('unresolved_sessions', 0)}")
    lines.append("")
    if (
        frame_stats.get('min_frames') == 3
        and frame_stats.get('max_frames') == 3
        and frame_stats.get('resolved_sessions', 0) > 1
    ):
        lines.append(
            "- **WARNING**: All resolved sessions report exactly 3 frames - "
            "re-check axis detection (prior bug signature)."
        )
    else:
        lines.append(
            "- **STATUS**: Frame counts are not stuck at XYZ size 3 "
            "(prior axis-swap bug is not present in these statistics)."
        )
    lines.append("")

    # Remaining Ambiguities
    lines.append("## Remaining Ambiguities")
    lines.append("")
    lines.append("### Session Naming")
    lines.append("")
    lines.append("- Multiple session naming conventions detected (WU##, WK##, WU#, Copy variants)")
    lines.append("- Original names are preserved; see `session_types.csv` for semantic labels")
    lines.append("- Classification categories: Walking, Calibration, Walking Copy, "
                 "Calibration Copy, Alternate Walking, Unknown")
    lines.append("- Inventory is not constrained to WU01-WU09")
    lines.append("")
    
    lines.append("### Variable Units")
    lines.append("")
    lines.append("- Units are **Unknown** for all categories in this dataset")
    lines.append("- Reason: no unit metadata fields were found in the MATLAB structure")
    lines.append("- Millimeters / degrees must **not** be assumed by the parser")
    lines.append("- Authoritative source: `units.json`")
    lines.append("")
    
    # Structural Risks
    lines.append("## Structural Risks")
    lines.append("")
    if inconsistencies['inconsistent_session_counts']:
        lines.append("- **HIGH**: Inconsistent session counts across subjects")
        lines.append("  - Parser must handle missing sessions gracefully")
        lines.append("  - Prefer semantic classification over requiring identical session sets")
    lines.append("")
    
    if frame_stats.get('std_frames', 0) > 0:
        lines.append(f"- **MEDIUM**: Variable frame counts (std={frame_stats['std_frames']:.2f})")
        lines.append("  - Parser must handle variable-length trajectories")
    else:
        lines.append("- **LOW**: Frame counts are consistent across resolved sessions")
    lines.append("")

    if frame_stats.get('unresolved_sessions', 0) > 0:
        lines.append(
            f"- **MEDIUM**: {frame_stats['unresolved_sessions']} sessions have "
            f"unresolved frame counts (layout detection failed)"
        )
        lines.append("")
    
    lines.append("- **LOW**: No temporal gait events in dataset")
    lines.append("  - Parser should not expect KinFC, KinFO, Midsvnt")
    lines.append("  - Clinical metrics available instead")
    lines.append("")
    
    # Recommended Parser Assumptions
    lines.append("## Recommended Parser Assumptions")
    lines.append("")
    lines.append("### Data Structure")
    lines.append("")
    lines.append("1. All subjects follow the same hierarchical structure")
    lines.append("2. Marker trajectories are 2D arrays with one axis of size 3 (XYZ)")
    lines.append("3. Detect layout automatically: if `shape[1] == 3` and `shape[0] != 3` -> `(N, 3)`; "
                 "if `shape[0] == 3` and `shape[1] != 3` -> `(3, N)`")
    lines.append("4. Frame count = the non-coordinate dimension; never hardcode `shape[0]` or `shape[1]`")
    lines.append("5. If layout cannot be determined, leave frame count unset and warn - do not guess")
    lines.append("")
    
    lines.append("### Session Handling")
    lines.append("")
    lines.append("1. Classify sessions by naming pattern into the six semantic categories above")
    lines.append("2. Preserve original session names; classification is a label only")
    lines.append("3. Do not require all subjects to have identical session sets")
    lines.append("4. Handle missing sessions gracefully (skip or warn)")
    lines.append("5. Treat Copy sessions as duplicates for optional exclusion")
    lines.append("")
    
    lines.append("### Variable Access")
    lines.append("")
    lines.append("1. Use variable catalog for semantic categorization")
    lines.append("2. Do not hardcode variable names")
    lines.append("3. Handle missing variables gracefully")
    lines.append("4. Clinical metrics are in Res field; they are not XYZ time series")
    lines.append("")
    
    lines.append("### Units and Scaling")
    lines.append("")
    lines.append("1. Treat all category units as Unknown unless `units.json` reports explicit values")
    lines.append("2. Do not assume millimeters for markers/COM or degrees for angles")
    lines.append("3. Obtain units only from dataset metadata or external authoritative documentation")
    lines.append("4. See `units.json` for per-category unit status and the reason they are unknown")
    lines.append("")
    
    # Variable Summary
    lines.append("## Variable Summary")
    lines.append("")
    lines.append(f"- **Total Variables**: {len(variable_catalog)}")
    category_counts = defaultdict(int)
    for var_info in variable_catalog.values():
        category_counts[var_info['semantic_category']] += 1
    for category, count in sorted(category_counts.items()):
        lines.append(f"- **{category}**: {count} variables")
    lines.append("")
    
    return "\n".join(lines)


def generate_dataset_summary(subject_catalog: Dict[str, Any],
                             session_catalog: Dict[str, Any],
                             kinematics_catalog: Dict[str, Any],
                             events_catalog: Dict[str, Any],
                             metrics_catalog: Dict[str, Any],
                             frame_stats: Dict[str, Any],
                             sampling_validation: Dict[str, Any],
                             metadata_validation: Dict[str, Any],
                             logger: logging.Logger) -> str:
    """
    Generate comprehensive dataset summary markdown.
    
    Args:
        subject_catalog: Subject catalog
        session_catalog: Session catalog
        kinematics_catalog: Kinematics catalog
        events_catalog: Events catalog
        metrics_catalog: Metrics catalog
        frame_stats: Frame statistics
        sampling_validation: Sampling rate validation
        metadata_validation: Metadata validation
        logger: Logger instance
        
    Returns:
        Markdown string containing the summary
    """
    logger.info("Generating dataset summary")
    
    lines = []
    lines.append("# Motion Dataset Summary")
    lines.append("")
    lines.append(f"Generated: {datetime.now().isoformat()}")
    lines.append("")
    
    # Dataset Overview
    lines.append("## Dataset Overview")
    lines.append("")
    lines.append(f"- **Total Subjects**: {subject_catalog['total_subjects']}")
    lines.append(f"- **Total Sessions**: {session_catalog['total_sessions']}")
    lines.append(f"- **Unique Session Types**: {len(session_catalog['session_names'])}")
    lines.append("")
    
    # Subjects
    lines.append("## Subjects")
    lines.append("")
    lines.append(f"- **Expected Subjects**: {subject_catalog['expected_subjects']}")
    lines.append(f"- **Available Subjects**: {subject_catalog['total_subjects']}")
    lines.append(f"- **Missing Subjects**: {', '.join(subject_catalog['missing_subjects']) if subject_catalog['missing_subjects'] else 'None'}")
    lines.append(f"- **Unexpected Subjects**: {', '.join(subject_catalog['unexpected_subjects']) if subject_catalog['unexpected_subjects'] else 'None'}")
    lines.append("")
    
    # Sessions
    lines.append("## Sessions")
    lines.append("")
    lines.append(f"- **Session Types**: {', '.join(session_catalog['session_names'])}")
    lines.append(f"- **Session Frequency**:")
    for session, count in session_catalog['session_frequency'].most_common():
        lines.append(f"  - {session}: {count} subjects")
    lines.append("")
    
    # Kinematics
    lines.append("## Kinematics")
    lines.append("")
    lines.append(f"- **Markers**: {len(kinematics_catalog['markers'])} unique")
    lines.append(f"- **Joint Angles**: {len(kinematics_catalog['joint_angles'])} unique")
    lines.append(f"- **Joint Centers**: {len(kinematics_catalog['joint_centers'])} unique")
    lines.append(f"- **Center of Mass**: {len(kinematics_catalog['center_of_mass'])} unique")
    lines.append(f"- **Segment COM**: {len(kinematics_catalog['segment_com'])} unique")
    lines.append("")
    
    # Events
    lines.append("## Events")
    lines.append("")
    lines.append(f"- **Unique Event Types**: {len(events_catalog['event_names'])}")
    lines.append(f"- **Event Types**: {', '.join(events_catalog['event_names'].keys())}")
    lines.append("")
    
    # Metrics
    lines.append("## Metrics")
    lines.append("")
    lines.append(f"- **Unique Metric Types**: {len(metrics_catalog['metric_names'])}")
    lines.append(f"- **Metric Types**: {', '.join(metrics_catalog['metric_names'].keys())}")
    lines.append("")
    
    # Frame Statistics (layout-aware: XYZ axis detected, remaining dim = frames)
    lines.append("## Frame Statistics")
    lines.append("")
    lines.append("- **Method**: Detect coordinate axis (dimension of size 3); remaining dimension = frames")
    lines.append(f"- **Total Sessions Considered**: {frame_stats.get('total_sessions', 0)}")
    lines.append(f"- **Resolved Sessions**: {frame_stats.get('resolved_sessions', frame_stats.get('total_sessions', 0))}")
    lines.append(f"- **Unresolved Sessions**: {frame_stats.get('unresolved_sessions', 0)}")
    lines.append(f"- **Minimum Frames**: {frame_stats['min_frames']}")
    lines.append(f"- **Maximum Frames**: {frame_stats['max_frames']}")
    lines.append(f"- **Mean Frames**: {frame_stats['mean_frames']:.2f}")
    lines.append(f"- **Std Dev Frames**: {frame_stats['std_frames']:.2f}")
    lines.append("")
    
    # Sampling Rates
    lines.append("## Sampling Rates")
    lines.append("")
    lines.append(f"- **Vrate Values**: {sampling_validation['vrate_unique']}")
    lines.append(f"- **Vrate Consistent**: {sampling_validation['vrate_consistent']}")
    lines.append(f"- **FPrate Values**: {sampling_validation['fprate_unique']}")
    lines.append(f"- **FPrate Consistent**: {sampling_validation['fprate_consistent']}")
    lines.append("")
    
    # Metadata
    lines.append("## Metadata Summary")
    lines.append("")
    for field, stats in metadata_validation.items():
        lines.append(f"- **{field}**:")
        lines.append(f"  - Present: {stats['present_count']} subjects")
        lines.append(f"  - Missing: {stats['missing_count']} subjects")
        if stats['min_value'] is not None:
            lines.append(f"  - Range: [{stats['min_value']}, {stats['max_value']}]")
            lines.append(f"  - Mean: {stats['mean_value']:.2f}")
    lines.append("")
    
    return "\n".join(lines)


def generate_consistency_report(inconsistencies: Dict[str, Any],
                               logger: logging.Logger) -> str:
    """
    Generate consistency report markdown.
    
    Args:
        inconsistencies: Dictionary containing detected inconsistencies
        logger: Logger instance
        
    Returns:
        Markdown string containing the consistency report
    """
    logger.info("Generating consistency report")
    
    lines = []
    lines.append("# Dataset Consistency Report")
    lines.append("")
    lines.append(f"Generated: {datetime.now().isoformat()}")
    lines.append("")
    
    # Missing Subjects
    lines.append("## Missing Subjects")
    lines.append("")
    if inconsistencies['missing_subjects']:
        lines.append(f"The following expected subjects are missing:")
        for subject in inconsistencies['missing_subjects']:
            lines.append(f"- {subject}")
    else:
        lines.append("No missing subjects.")
    lines.append("")
    
    # Unexpected Subjects
    lines.append("## Unexpected Subjects")
    lines.append("")
    if inconsistencies['unexpected_subjects']:
        lines.append(f"The following unexpected subjects were found:")
        for subject in inconsistencies['unexpected_subjects']:
            lines.append(f"- {subject}")
    else:
        lines.append("No unexpected subjects.")
    lines.append("")
    
    # Missing Sessions
    lines.append("## Subjects with Missing Expected Walking Sessions")
    lines.append("")
    if inconsistencies['subjects_with_missing_sessions']:
        lines.append(f"The following subjects are missing expected walking sessions:")
        for subject_session in inconsistencies['subjects_with_missing_sessions']:
            lines.append(f"- {subject_session}")
    else:
        lines.append("All subjects have all expected walking sessions.")
    lines.append("")
    
    # Session Count Inconsistency
    lines.append("## Session Count Consistency")
    lines.append("")
    if inconsistencies['inconsistent_session_counts']:
        lines.append("WARNING: Subjects have inconsistent session counts.")
        lines.append("Note: This may be due to alternate naming, duplicates, or missing sessions.")
    else:
        lines.append("All subjects have consistent session counts.")
    lines.append("")
    
    # Marker Consistency
    lines.append("## Marker Consistency")
    lines.append("")
    if inconsistencies['markers_not_in_all_subjects']:
        lines.append(f"The following markers are not present in all subjects:")
        for item in inconsistencies['markers_not_in_all_subjects']:
            lines.append(f"- {item['marker']}: present in {item['present_in']}, missing from {item['missing_from']}")
    else:
        lines.append("All markers are present in all subjects.")
    lines.append("")
    
    # Joint Angle Consistency
    lines.append("## Joint Angle Consistency")
    lines.append("")
    if inconsistencies['joint_angles_not_in_all_subjects']:
        lines.append(f"The following joint angles are not present in all subjects:")
        for item in inconsistencies['joint_angles_not_in_all_subjects']:
            lines.append(f"- {item['angle']}: present in {item['present_in']}, missing from {item['missing_from']}")
    else:
        lines.append("All joint angles are present in all subjects.")
    lines.append("")
    
    # Gait Events
    lines.append("## Gait Events")
    lines.append("")
    if inconsistencies['true_gait_events_absent']:
        lines.append("IMPORTANT: True temporal gait events (KinFC, KinFO, Midsvnt) are absent from the dataset.")
        lines.append("The Res field contains clinical metrics (StpLen, WkVel, etc.), not gait events.")
        lines.append("Parser should not expect temporal gait event data.")
    else:
        lines.append("Gait events are present in the dataset.")
    lines.append("")
    
    return "\n".join(lines)


def main() -> int:
    """
    Main orchestration function.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Setup logging
    logger = setup_logging(LOG_PATH)
    
    logger.info("=" * 60)
    logger.info("MOTION CATALOG BUILDER")
    logger.info("=" * 60)
    logger.info(f"Started at: {datetime.now().isoformat()}")
    
    try:
        # Load dataset
        mat_data = load_dataset(DATASET_PATH, logger)
        
        # Build catalogs
        subject_catalog = build_subject_catalog(mat_data, logger)
        session_catalog = build_session_catalog(mat_data, logger)
        kinematics_catalog = build_kinematics_catalog(mat_data, logger)
        variable_catalog = build_variable_catalog(mat_data, logger)
        events_catalog = build_events_catalog(mat_data, logger)
        metrics_catalog = build_metrics_catalog(mat_data, logger)
        
        # Compute statistics and validations
        frame_stats = compute_frame_statistics(session_catalog, logger)
        sampling_validation = validate_sampling_rates(subject_catalog, logger)
        metadata_validation = validate_metadata_consistency(subject_catalog, logger)
        
        # Detect inconsistencies
        inconsistencies = detect_inconsistencies(
            subject_catalog, session_catalog, kinematics_catalog,
            events_catalog, logger
        )
        
        # Clean output directory before generating new files
        if OUTPUT_PATH.exists():
            logger.info(f"Cleaning output directory: {OUTPUT_PATH}")
            shutil.rmtree(OUTPUT_PATH)
        
        # Create output directory
        OUTPUT_PATH.mkdir(parents=True, exist_ok=True)
        logger.info(f"Output directory: {OUTPUT_PATH}")
        
        # Write CSV files
        write_csv([
            {'subject_id': s, **subject_catalog['subject_details'][s]}
            for s in subject_catalog['available_subjects']
        ], OUTPUT_PATH / "subjects.csv", logger)
        
        session_rows = []
        for subject_id, sessions in session_catalog['sessions_per_subject'].items():
            for session in sessions:
                session_rows.append({'subject_id': subject_id, 'session_name': session})
        write_csv(session_rows, OUTPUT_PATH / "sessions.csv", logger)
        
        write_csv([
            {'marker': m, 'subject_count': c}
            for m, c in kinematics_catalog['markers'].items()
        ], OUTPUT_PATH / "markers.csv", logger)
        
        write_csv([
            {'joint_angle': a, 'subject_count': c}
            for a, c in kinematics_catalog['joint_angles'].items()
        ], OUTPUT_PATH / "joint_angles.csv", logger)
        
        write_csv([
            {'joint_center': j, 'subject_count': c}
            for j, c in kinematics_catalog['joint_centers'].items()
        ], OUTPUT_PATH / "joint_centers.csv", logger)
        
        write_csv([
            {'com': c, 'subject_count': cnt}
            for c, cnt in kinematics_catalog['center_of_mass'].items()
        ], OUTPUT_PATH / "center_of_mass.csv", logger)
        
        write_csv([
            {'segment_com': s, 'subject_count': c}
            for s, c in kinematics_catalog['segment_com'].items()
        ], OUTPUT_PATH / "segment_com.csv", logger)
        
        write_csv([
            {'event': e, 'session_count': c}
            for e, c in events_catalog['event_names'].items()
        ], OUTPUT_PATH / "events.csv", logger)
        
        write_csv([
            {'metric': m, 'session_count': c}
            for m, c in metrics_catalog['metric_names'].items()
        ], OUTPUT_PATH / "metrics.csv", logger)
        
        # Write variable catalog CSV
        variable_rows = []
        for var_name, var_info in variable_catalog.items():
            variable_rows.append({
                'name': var_name,
                'semantic_category': var_info['semantic_category'],
                'subject_count': var_info['subject_count'],
                'session_count': var_info['session_count'],
                'shape': str(var_info['shape']),
                'frame_count': var_info['frame_count'],
                'coordinate_dimensions': var_info['coordinate_dimensions'],
                'trajectory_layout': var_info.get('trajectory_layout'),
                'coordinate_axis': var_info.get('coordinate_axis'),
                'datatype': var_info['datatype'],
                'units': var_info['units']
            })
        write_csv(variable_rows, OUTPUT_PATH / "variable_catalog.csv", logger)
        
        # Write session types CSV (preserve original names; labels only)
        session_type_rows = []
        for session_name in sorted(session_catalog['session_details'].keys()):
            details = session_catalog['session_details'][session_name]
            internal = details['classification']
            session_type_rows.append({
                'Original Name': session_name,
                'Classification': session_classification_label(internal),
                'Frequency': session_catalog['session_frequency'][session_name],
                'Subjects Present': ', '.join(details['subjects']),
            })
        write_csv(session_type_rows, OUTPUT_PATH / "session_types.csv", logger)
        logger.info(
            "Session classification summary: "
            + ", ".join(
                f"{session_classification_label(k)}={len(v)}"
                for k, v in sorted(session_catalog['session_classification'].items())
            )
        )
        
        # Write statistics JSON
        statistics = {
            'frame_statistics': frame_stats,
            'sampling_rate_validation': sampling_validation,
            'metadata_validation': metadata_validation,
            'inconsistencies': inconsistencies
        }
        write_json(statistics, OUTPUT_PATH / "statistics.json", logger)
        
        # Write motion schema JSON
        motion_schema = generate_motion_schema(
            subject_catalog, session_catalog, kinematics_catalog,
            variable_catalog, events_catalog, metrics_catalog, logger
        )
        write_json(motion_schema, OUTPUT_PATH / "motion_schema.json", logger)
        
        # Write units JSON (never guess millimeters/degrees)
        units_probe = probe_dataset_units(mat_data, logger)
        units_schema = build_units_schema(
            units_probe, kinematics_catalog, metrics_catalog, logger
        )
        write_json(units_schema, OUTPUT_PATH / "units.json", logger)
        
        # Write markdown reports
        dataset_summary = generate_dataset_summary(
            subject_catalog, session_catalog, kinematics_catalog,
            events_catalog, metrics_catalog, frame_stats,
            sampling_validation, metadata_validation, logger
        )
        write_markdown(dataset_summary, OUTPUT_PATH / "dataset_summary.md", logger)
        
        consistency_report = generate_consistency_report(inconsistencies, logger)
        write_markdown(consistency_report, OUTPUT_PATH / "consistency_report.md", logger)
        
        parser_readiness = generate_parser_readiness_report(
            subject_catalog, session_catalog, kinematics_catalog,
            variable_catalog, inconsistencies, frame_stats, logger
        )
        write_markdown(parser_readiness, OUTPUT_PATH / "parser_readiness_report.md", logger)
        
        logger.info("=" * 60)
        logger.info("MOTION CATALOG BUILT SUCCESSFULLY")
        logger.info("=" * 60)
        logger.info(f"Output directory: {OUTPUT_PATH}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Catalog building failed with error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

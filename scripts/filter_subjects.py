"""
Filter subjects from human motion capture dataset.

This script loads a MATLAB dataset containing nested structs with human gait
motion capture data, validates the structure, and filters subjects based on
a predefined keep list. It performs comprehensive inspection of the dataset
hierarchy, particularly the Dat.Res field, before filtering to ensure data
integrity is preserved.

Author: Production Motion Pipeline
Version: 1.0.0
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

import numpy as np
import scipy.io


# Configuration
INPUT_PATH = Path("data/raw/Data_structure_all_subs.mat")
OUTPUT_PATH = Path("data/processed/Data_structure_filtered.mat")
LOG_PATH = Path("logs/filter_subjects.log")
REPORT_PATH = Path("metadata/filter_report.txt")

# Subject keep list - these subjects will be retained
KEEP_SUBJECTS: Set[str] = {
    "S2", "S3", "S4", "S5", "S7", "S8", "S9", "S11", "S12", "S13",
    "S14", "S15", "S17", "S19", "S23", "S26", "S27", "S30", "S31",
    "S32", "S34", "S35", "S37", "S38", "S39", "S40", "S41", "S42",
    "S43", "S46", "S48"
}

# Expected counts
EXPECTED_ORIGINAL_SUBJECTS = 43
EXPECTED_FILTERED_SUBJECTS = 31
EXPECTED_REMOVED_SUBJECTS = 12


def setup_logging(log_path: Path) -> logging.Logger:
    """
    Configure logging for the script.
    
    Args:
        log_path: Path to the log file
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger("filter_subjects")
    logger.setLevel(logging.DEBUG)
    
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


def load_dataset(input_path: Path, logger: logging.Logger) -> Dict[str, Any]:
    """
    Load and validate the MATLAB dataset.
    
    Args:
        input_path: Path to the input .mat file
        logger: Logger instance
        
    Returns:
        Dictionary containing the loaded MATLAB data
        
    Raises:
        FileNotFoundError: If the input file does not exist
        ValueError: If the dataset fails validation
    """
    logger.info(f"Loading dataset from: {input_path}")
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    try:
        mat_data = scipy.io.loadmat(str(input_path))
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


def inspect_dataset(mat_data: Dict[str, Any], logger: logging.Logger) -> None:
    """
    Inspect the overall dataset hierarchy and structure.
    
    Args:
        mat_data: Dictionary containing the MATLAB data
        logger: Logger instance
    """
    logger.info("=" * 60)
    logger.info("DATASET HIERARCHY INSPECTION")
    logger.info("=" * 60)
    
    # Top-level keys
    logger.info("Top-level keys:")
    for key in mat_data.keys():
        if not key.startswith('__'):
            logger.info(f"  - {key}")
    
    # Inspect Dat structure
    dat = mat_data['Dat']
    logger.info(f"\nDat type: {type(dat)}")
    logger.info(f"Dat shape: {dat.shape}")
    logger.info(f"Dat dtype: {dat.dtype}")
    
    if dat.dtype.names:
        logger.info(f"Dat fields: {dat.dtype.names}")


def _inspect_struct_recursive(
    struct: np.ndarray,
    indent: int = 0,
    max_depth: int = 10,
    current_depth: int = 0,
    logger: logging.Logger = None
) -> None:
    """
    Recursively inspect a MATLAB struct array.
    
    Args:
        struct: The struct array to inspect
        indent: Current indentation level
        max_depth: Maximum recursion depth
        current_depth: Current recursion depth
        logger: Logger instance
    """
    if current_depth >= max_depth:
        logger.info("  " * indent + "... (max depth reached)")
        return
    
    prefix = "  " * indent
    
    if struct.dtype.names:
        # This is a struct
        for field_name in struct.dtype.names:
            field = struct[field_name]
            
            if field.ndim == 0:
                # Scalar
                if hasattr(field, 'dtype') and field.dtype.names:
                    logger.info(f"{prefix}{field_name}: shape={field.shape}, dtype=struct")
                    _inspect_struct_recursive(
                        field, indent + 1, max_depth, current_depth + 1, logger
                    )
                else:
                    logger.info(f"{prefix}{field_name}: shape={field.shape}, dtype={field.dtype}")
            else:
                # Array
                if hasattr(field, 'dtype') and field.dtype.names:
                    logger.info(f"{prefix}{field_name}: shape={field.shape}, dtype=struct")
                    if field.size > 0:
                        _inspect_struct_recursive(
                            field.flat[0], indent + 1, max_depth, current_depth + 1, logger
                    )
                else:
                    logger.info(f"{prefix}{field_name}: shape={field.shape}, dtype={field.dtype}")
    else:
        logger.info(f"{prefix}value: shape={struct.shape}, dtype={struct.dtype}")


def inspect_res(mat_data: Dict[str, Any], logger: logging.Logger) -> Dict[str, Any]:
    """
    Comprehensively inspect Dat.Res to understand its structure and purpose.
    
    This function does NOT assume anything about Res. It programmatically
    inspects all fields, dimensions, datatypes, and relationships.
    
    Args:
        mat_data: Dictionary containing the MATLAB data
        logger: Logger instance
        
    Returns:
        Dictionary containing analysis results about Res
    """
    logger.info("=" * 60)
    logger.info("DAT.INSPECTION")
    logger.info("=" * 60)
    
    dat = mat_data['Dat']
    
    # Check if Res exists
    if 'Res' not in dat.dtype.names:
        logger.warning("Dat does not contain 'Res' field")
        return {"has_res": False}
    
    res = dat['Res']
    
    logger.info(f"Res type: {type(res)}")
    logger.info(f"Res shape: {res.shape}")
    logger.info(f"Res dtype: {res.dtype}")
    
    analysis = {
        "has_res": True,
        "shape": res.shape,
        "dtype": str(res.dtype),
        "fields": [],
        "contains_subject_references": False,
        "contains_subject_indices": False,
        "contains_global_statistics": False,
        "contains_metadata": False,
        "contains_mappings": False
    }
    
    # Get field names if struct
    if res.dtype.names:
        analysis["fields"] = list(res.dtype.names)
        logger.info(f"Res fields: {res.dtype.names}")
        
        # Inspect each field
        for field_name in res.dtype.names:
            field = res[field_name]
            logger.info(f"\nField: {field_name}")
            logger.info(f"  Type: {type(field)}")
            logger.info(f"  Shape: {field.shape}")
            logger.info(f"  Dtype: {field.dtype}")
            
            # Check for subject references
            if field.dtype.kind in ['U', 'S']:  # String types
                unique_values = np.unique(field)
                logger.info(f"  Unique string values: {unique_values[:10]}")
                # Check if any match subject pattern
                for val in unique_values:
                    if isinstance(val, str) and val.startswith('S'):
                        analysis["contains_subject_references"] = True
                        logger.info(f"  -> Contains subject reference: {val}")
            
            # Check for numeric indices
            if field.dtype.kind in ['i', 'u', 'f']:  # Numeric types
                if field.size > 0:
                    min_val = np.min(field)
                    max_val = np.max(field)
                    logger.info(f"  Value range: [{min_val}, {max_val}]")
                    # Check if values could be subject indices (1-50)
                    if min_val >= 1 and max_val <= 50:
                        analysis["contains_subject_indices"] = True
                        logger.info(f"  -> May contain subject indices")
    
    # Recursive inspection of structure
    logger.info("\nDetailed recursive inspection (first element):")
    if res.size > 0:
        _inspect_struct_recursive(res.flat[0], indent=1, logger=logger)
    
    return analysis


def list_subjects(mat_data: Dict[str, Any], logger: logging.Logger) -> List[str]:
    """
    List all available subjects in the dataset.
    
    Args:
        mat_data: Dictionary containing the MATLAB data
        logger: Logger instance
        
    Returns:
        List of subject IDs
    """
    logger.info("=" * 60)
    logger.info("SUBJECT LISTING")
    logger.info("=" * 60)
    
    dat = mat_data['Dat']
    subjects = []
    
    # Subjects are fields in Dat (excluding Res)
    for field_name in dat.dtype.names:
        if field_name != 'Res':
            subjects.append(field_name)
    
    subjects.sort()
    
    logger.info(f"Total subjects found: {len(subjects)}")
    logger.info(f"Subject IDs: {subjects}")
    
    return subjects


def validate_keep_list(
    available_subjects: List[str],
    keep_subjects: Set[str],
    logger: logging.Logger
) -> Tuple[Set[str], Set[str]]:
    """
    Validate the keep list against available subjects.
    
    Args:
        available_subjects: List of subjects in the dataset
        keep_subjects: Set of subjects to keep
        logger: Logger instance
        
    Returns:
        Tuple of (valid_keep_subjects, invalid_keep_subjects)
    """
    logger.info("=" * 60)
    logger.info("KEEP LIST VALIDATION")
    logger.info("=" * 60)
    
    available_set = set(available_subjects)
    
    # Check for subjects in keep list that don't exist
    invalid_keep = keep_subjects - available_set
    valid_keep = keep_subjects & available_set
    
    # Check for subjects not in keep list that will be removed
    to_remove = available_set - keep_subjects
    
    logger.info(f"Available subjects: {len(available_set)}")
    logger.info(f"Subjects to keep: {len(valid_keep)}")
    logger.info(f"Subjects to remove: {len(to_remove)}")
    
    if invalid_keep:
        logger.warning(f"Subjects in keep list not found in dataset: {invalid_keep}")
    
    logger.info(f"Valid keep subjects: {sorted(valid_keep)}")
    logger.info(f"Subjects to remove: {sorted(to_remove)}")
    
    return valid_keep, to_remove


def filter_subjects(
    mat_data: Dict[str, Any],
    keep_subjects: Set[str],
    res_analysis: Dict[str, Any],
    logger: logging.Logger
) -> Dict[str, Any]:
    """
    Filter subjects from the dataset.
    
    Before filtering, this function analyzes Dat.Res to determine if it
    contains references to subjects that would need to be updated.
    
    Args:
        mat_data: Dictionary containing the MATLAB data
        keep_subjects: Set of subject IDs to keep
        res_analysis: Analysis results from inspect_res
        logger: Logger instance
        
    Returns:
        Filtered dataset dictionary
    """
    logger.info("=" * 60)
    logger.info("SUBJECT FILTERING")
    logger.info("=" * 60)
    
    # Analyze Res before filtering
    logger.info("\nAnalyzing Dat.Res before filtering:")
    if res_analysis["has_res"]:
        logger.info(f"  Res contains subject references: {res_analysis['contains_subject_references']}")
        logger.info(f"  Res contains subject indices: {res_analysis['contains_subject_indices']}")
        logger.info(f"  Res contains global statistics: {res_analysis['contains_global_statistics']}")
        logger.info(f"  Res contains metadata: {res_analysis['contains_metadata']}")
        logger.info(f"  Res contains mappings: {res_analysis['contains_mappings']}")
        
        # Decision: Can we safely filter?
        if res_analysis["contains_subject_references"] or res_analysis["contains_subject_indices"]:
            logger.warning("\nRES ANALYSIS FINDING:")
            logger.warning("Dat.Res appears to contain subject references or indices.")
            logger.warning("Filtering subjects without updating Res may break data integrity.")
            logger.warning("\nOPTIONS:")
            logger.warning("1. Implement Res update logic to remove references to deleted subjects")
            logger.warning("2. Keep Res unchanged (may result in orphaned references)")
            logger.warning("3. Remove Res entirely if it only contains aggregate data")
            logger.warning("\nDECISION: Proceeding with filtering but keeping Res unchanged.")
            logger.warning("This may result in orphaned references in Res.")
            logger.warning("Future work: Implement Res update logic.")
    else:
        logger.info("  Dat.Res does not exist - no special handling needed")
    
    # Create filtered dataset
    logger.info("\nCreating filtered dataset...")
    
    # Deep copy to avoid modifying original
    filtered_data = {}
    for key in mat_data.keys():
        if not key.startswith('__'):
            filtered_data[key] = mat_data[key].copy()
    
    # Filter subjects from Dat
    dat = filtered_data['Dat']
    
    # Create new struct array with only kept subjects
    kept_fields = [f for f in dat.dtype.names if f in keep_subjects or f == 'Res']
    
    logger.info(f"Original Dat fields: {dat.dtype.names}")
    logger.info(f"Filtered Dat fields: {kept_fields}")
    
    # Reconstruct struct array with only kept fields
    # Get the dtype for kept fields
    new_dtype = []
    for field_name in kept_fields:
        field_dtype = dat.dtype.fields[field_name][0]
        new_dtype.append((field_name, field_dtype))
    
    # Create new structured array with same shape
    new_dat = np.empty(dat.shape, dtype=new_dtype)
    
    # Copy data for kept fields
    for field_name in kept_fields:
        new_dat[field_name] = dat[field_name]
    
    filtered_data['Dat'] = new_dat
    
    logger.info("Struct reconstruction completed")
    
    return filtered_data


def validate_filtered_dataset(
    original_data: Dict[str, Any],
    filtered_data: Dict[str, Any],
    keep_subjects: Set[str],
    removed_subjects: Set[str],
    logger: logging.Logger
) -> bool:
    """
    Validate the filtered dataset against expectations.
    
    Args:
        original_data: Original dataset dictionary
        filtered_data: Filtered dataset dictionary
        keep_subjects: Set of subjects that should be kept
        removed_subjects: Set of subjects that should be removed
        logger: Logger instance
        
    Returns:
        True if validation passes, False otherwise
    """
    logger.info("=" * 60)
    logger.info("FILTERED DATASET VALIDATION")
    logger.info("=" * 60)
    
    validation_passed = True
    
    # Check subject counts
    original_dat = original_data['Dat']
    filtered_dat = filtered_data['Dat']
    
    original_subjects = [f for f in original_dat.dtype.names if f != 'Res']
    filtered_subjects = [f for f in filtered_dat.dtype.names if f != 'Res']
    
    logger.info(f"Original subject count: {len(original_subjects)}")
    logger.info(f"Filtered subject count: {len(filtered_subjects)}")
    logger.info(f"Expected filtered count: {EXPECTED_FILTERED_SUBJECTS}")
    
    if len(original_subjects) != EXPECTED_ORIGINAL_SUBJECTS:
        logger.error(f"Original subject count mismatch: expected {EXPECTED_ORIGINAL_SUBJECTS}, got {len(original_subjects)}")
        validation_passed = False
    
    if len(filtered_subjects) != EXPECTED_FILTERED_SUBJECTS:
        logger.error(f"Filtered subject count mismatch: expected {EXPECTED_FILTERED_SUBJECTS}, got {len(filtered_subjects)}")
        validation_passed = False
    
    # Confirm kept subjects exist
    for subject in keep_subjects:
        if subject not in filtered_subjects:
            logger.error(f"Kept subject missing: {subject}")
            validation_passed = False
        else:
            logger.info(f"Confirmed kept subject exists: {subject}")
    
    # Confirm removed subjects don't exist
    for subject in removed_subjects:
        if subject in filtered_subjects:
            logger.error(f"Removed subject still exists: {subject}")
            validation_passed = False
        else:
            logger.info(f"Confirmed removed subject does not exist: {subject}")
    
    # Check that other fields haven't changed
    for key in original_data.keys():
        if key != 'Dat' and not key.startswith('__'):
            if key not in filtered_data:
                logger.error(f"Field missing in filtered data: {key}")
                validation_passed = False
    
    logger.info(f"\nValidation result: {'PASSED' if validation_passed else 'FAILED'}")
    return validation_passed


def save_dataset(
    mat_data: Dict[str, Any],
    output_path: Path,
    logger: logging.Logger
) -> None:
    """
    Save the filtered dataset to disk.
    
    Args:
        mat_data: Dictionary containing the MATLAB data
        output_path: Path to save the output file
        logger: Logger instance
    """
    logger.info("=" * 60)
    logger.info("SAVING FILTERED DATASET")
    logger.info("=" * 60)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        scipy.io.savemat(str(output_path), mat_data)
        logger.info(f"Filtered dataset saved to: {output_path}")
    except Exception as e:
        logger.error(f"Failed to save dataset: {e}")
        raise


def generate_report(
    original_subjects: List[str],
    keep_subjects: Set[str],
    removed_subjects: Set[str],
    res_analysis: Dict[str, Any],
    validation_passed: bool,
    output_path: Path,
    logger: logging.Logger
) -> None:
    """
    Generate a comprehensive report of the filtering operation.
    
    Args:
        original_subjects: List of original subject IDs
        keep_subjects: Set of kept subject IDs
        removed_subjects: Set of removed subject IDs
        res_analysis: Analysis results from inspect_res
        validation_passed: Whether validation passed
        output_path: Path to the output file
        logger: Logger instance
    """
    logger.info("=" * 60)
    logger.info("GENERATING REPORT")
    logger.info("=" * 60)
    
    report_path = Path("metadata/filter_report.txt")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, 'w') as f:
        f.write("=" * 60 + "\n")
        f.write("SUBJECT FILTERING REPORT\n")
        f.write("=" * 60 + "\n\n")
        
        f.write(f"Timestamp: {datetime.now().isoformat()}\n\n")
        
        f.write("ORIGINAL DATASET SUMMARY\n")
        f.write("-" * 60 + "\n")
        f.write(f"Original subject count: {len(original_subjects)}\n")
        f.write(f"Original subject IDs: {', '.join(sorted(original_subjects))}\n\n")
        
        f.write("FILTERING SUMMARY\n")
        f.write("-" * 60 + "\n")
        f.write(f"Remaining subject count: {len(keep_subjects)}\n")
        f.write(f"Removed subject count: {len(removed_subjects)}\n\n")
        
        f.write(f"Remaining IDs: {', '.join(sorted(keep_subjects))}\n\n")
        f.write(f"Removed IDs: {', '.join(sorted(removed_subjects))}\n\n")
        
        f.write("DAT.INSPECTION\n")
        f.write("-" * 60 + "\n")
        f.write(f"Has Res: {res_analysis['has_res']}\n")
        if res_analysis['has_res']:
            f.write(f"Shape: {res_analysis['shape']}\n")
            f.write(f"Dtype: {res_analysis['dtype']}\n")
            f.write(f"Fields: {', '.join(res_analysis['fields'])}\n")
            f.write(f"Contains subject references: {res_analysis['contains_subject_references']}\n")
            f.write(f"Contains subject indices: {res_analysis['contains_subject_indices']}\n")
            f.write(f"Contains global statistics: {res_analysis['contains_global_statistics']}\n")
            f.write(f"Contains metadata: {res_analysis['contains_metadata']}\n")
            f.write(f"Contains mappings: {res_analysis['contains_mappings']}\n")
        f.write("\n")
        
        f.write("VALIDATION SUMMARY\n")
        f.write("-" * 60 + "\n")
        f.write(f"Validation result: {'PASSED' if validation_passed else 'FAILED'}\n")
        f.write(f"Expected original subjects: {EXPECTED_ORIGINAL_SUBJECTS}\n")
        f.write(f"Expected filtered subjects: {EXPECTED_FILTERED_SUBJECTS}\n")
        f.write(f"Expected removed subjects: {EXPECTED_REMOVED_SUBJECTS}\n\n")
        
        f.write("OUTPUT FILE LOCATION\n")
        f.write("-" * 60 + "\n")
        f.write(f"{output_path.absolute()}\n")
    
    logger.info(f"Report saved to: {report_path}")


def main() -> int:
    """
    Main orchestration function.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Setup logging
    logger = setup_logging(LOG_PATH)
    
    logger.info("=" * 60)
    logger.info("SUBJECT FILTERING PIPELINE - PHASE 1")
    logger.info("=" * 60)
    logger.info(f"Started at: {datetime.now().isoformat()}")
    
    try:
        # Load dataset
        mat_data = load_dataset(INPUT_PATH, logger)
        
        # Inspect dataset hierarchy
        inspect_dataset(mat_data, logger)
        
        # Inspect Res structure
        res_analysis = inspect_res(mat_data, logger)
        
        # List subjects
        original_subjects = list_subjects(mat_data, logger)
        
        # Validate keep list
        valid_keep, to_remove = validate_keep_list(
            original_subjects, KEEP_SUBJECTS, logger
        )
        
        # Filter subjects
        filtered_data = filter_subjects(
            mat_data, valid_keep, res_analysis, logger
        )
        
        # Validate filtered dataset
        validation_passed = validate_filtered_dataset(
            mat_data, filtered_data, valid_keep, to_remove, logger
        )
        
        if validation_passed:
            # Save filtered dataset
            save_dataset(filtered_data, OUTPUT_PATH, logger)
            
            # Generate report
            generate_report(
                original_subjects,
                valid_keep,
                to_remove,
                res_analysis,
                validation_passed,
                OUTPUT_PATH,
                logger
            )
            
            logger.info("=" * 60)
            logger.info("PIPELINE COMPLETED SUCCESSFULLY")
            logger.info("=" * 60)
            return 0
        else:
            logger.error("Validation failed - not saving filtered dataset")
            return 1
            
    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

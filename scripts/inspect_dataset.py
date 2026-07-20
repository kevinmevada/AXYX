"""
Inspect the dataset structure and contents.
"""

import scipy.io
import numpy as np
import os

def inspect_dataset(mat_path):
    """
    Inspect the structure and contents of a .mat file.
    
    Args:
        mat_path: Path to the .mat file
    """
    # Load data
    mat_data = scipy.io.loadmat(mat_path)
    
    # Display all keys
    print("Keys in the .mat file:")
    for key in mat_data.keys():
        if not key.startswith('__'):
            print(f"  - {key}")
    
    # Display structure of each variable
    print("\nDetailed structure:")
    for key in mat_data.keys():
        if not key.startswith('__'):
            print(f"\n{key}:")
            print(f"  Type: {type(mat_data[key])}")
            print(f"  Shape: {mat_data[key].shape}")
            print(f"  Dtype: {mat_data[key].dtype}")

if __name__ == "__main__":
    mat_file = "../data/raw/Data_structure_all_subs.mat"
    inspect_dataset(mat_file)

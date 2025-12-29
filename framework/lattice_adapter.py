"""
Direct RSVP Lattice Import
Plug in your actual Φ / v / S arrays in any format
"""
import numpy as np
from pathlib import Path
import json

class LatticeAdapter:
    """
    Adapter for importing lattice data from various formats.
    Add your custom formats here.
    """
    
    @staticmethod
    def from_npz(filepath):
        """Standard NumPy format (current default)"""
        data = np.load(filepath)
        return {
            'phi': data['phi'],
            'v': data['v'],
            's': data['s'],
            'metadata': {k: data[k] for k in data.keys() 
                        if k not in ['phi', 'v', 's']}
        }
    
    @staticmethod
    def from_hdf5(filepath):
        """HDF5 format for large datasets"""
        import h5py
        with h5py.File(filepath, 'r') as f:
            return {
                'phi': f['phi'][:],
                'v': f['v'][:],
                's': f['s'][:],
                'metadata': dict(f.attrs)
            }
    
    @staticmethod
    def from_raw_binary(filepath, shape, dtype=np.float32):
        """Raw binary dump"""
        data = np.fromfile(filepath, dtype=dtype)
        N = shape[0]
        
        phi = data[:N**3].reshape(shape)
        v = data[N**3:4*N**3].reshape((3,) + shape)
        s = data[4*N**3:5*N**3].reshape(shape)
        
        return {'phi': phi, 'v': v, 's': s, 'metadata': {}}
    
    @staticmethod
    def from_csv(dirpath):
        """CSV format (inefficient but human-readable)"""
        phi = np.loadtxt(Path(dirpath) / "phi.csv", delimiter=",")
        v_x = np.loadtxt(Path(dirpath) / "vx.csv", delimiter=",")
        v_y = np.loadtxt(Path(dirpath) / "vy.csv", delimiter=",")
        v_z = np.loadtxt(Path(dirpath) / "vz.csv", delimiter=",")
        s = np.loadtxt(Path(dirpath) / "s.csv", delimiter=",")
        
        N = int(round(len(phi.flatten()) ** (1/3)))
        phi = phi.reshape((N, N, N))
        v = np.stack([
            v_x.reshape((N, N, N)),
            v_y.reshape((N, N, N)),
            v_z.reshape((N, N, N))
        ])
        s = s.reshape((N, N, N))
        
        return {'phi': phi, 'v': v, 's': s, 'metadata': {}}
    
    @staticmethod
    def from_custom_rsvp(filepath):
        """
        PLACEHOLDER: Your custom RSVP format.
        Replace this with your actual lattice structure.
        
        Expected return format:
        {
            'phi': ndarray shape (N,N,N),
            'v': ndarray shape (3,N,N,N),
            's': ndarray shape (N,N,N),
            'metadata': dict
        }
        """
        # Example: JSON with base64-encoded arrays
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        import base64
        
        phi = np.frombuffer(base64.b64decode(data['phi']), 
                           dtype=np.float32).reshape(data['shape'])
        v = np.frombuffer(base64.b64decode(data['v']), 
                         dtype=np.float32).reshape((3,) + tuple(data['shape']))
        s = np.frombuffer(base64.b64decode(data['s']), 
                         dtype=np.float32).reshape(data['shape'])
        
        return {
            'phi': phi,
            'v': v,
            's': s,
            'metadata': data.get('metadata', {})
        }
    
    @staticmethod
    def auto_detect(filepath):
        """Auto-detect format and load"""
        filepath = Path(filepath)
        
        if filepath.suffix == '.npz':
            return LatticeAdapter.from_npz(filepath)
        elif filepath.suffix in ['.h5', '.hdf5']:
            return LatticeAdapter.from_hdf5(filepath)
        elif filepath.suffix in ['.bin', '.dat']:
            # Need to know shape - could be in companion .json
            config = json.load(open(filepath.with_suffix('.json')))
            return LatticeAdapter.from_raw_binary(
                filepath, 
                tuple(config['shape']),
                np.dtype(config.get('dtype', 'float32'))
            )
        elif filepath.is_dir():
            return LatticeAdapter.from_csv(filepath)
        else:
            raise ValueError(f"Unknown format: {filepath}")


# ========== Conversion utilities ==========

def convert_to_standard(input_path, output_path, format='npz'):
    """Convert any supported format to standard .npz"""
    data = LatticeAdapter.auto_detect(input_path)
    
    if format == 'npz':
        np.savez_compressed(
            output_path,
            phi=data['phi'],
            v=data['v'],
            s=data['s'],
            **data['metadata']
        )
    elif format == 'hdf5':
        import h5py
        with h5py.File(output_path, 'w') as f:
            f.create_dataset('phi', data=data['phi'], compression='gzip')
            f.create_dataset('v', data=data['v'], compression='gzip')
            f.create_dataset('s', data=data['s'], compression='gzip')
            for k, v in data['metadata'].items():
                f.attrs[k] = v
    
    print(f"Converted {input_path} → {output_path}")


# ========== Example usage ==========

if __name__ == "__main__":
    # Test auto-detection
    test_file = Path("sim/fields/t000.npz")
    if test_file.exists():
        data = LatticeAdapter.auto_detect(test_file)
        print(f"Loaded: φ shape {data['phi'].shape}")
        print(f"Metadata: {data['metadata']}")
    
    # Convert example (uncomment to use)
    # convert_to_standard(
    #     "your_custom_data.bin",
    #     "sim/fields/converted.npz",
    #     format='npz'
    # )
//! TARTAN tiling algorithms (stub).
use ndarray::Array2;
use rand::Rng;

pub fn random_tiling(h: usize, w: usize, k: u8) -> Array2<u8> {
    let mut out = Array2::<u8>::zeros((h, w));
    let mut rng = rand::thread_rng();
    for v in out.iter_mut() { *v = rng.gen_range(0..k); }
    out
}

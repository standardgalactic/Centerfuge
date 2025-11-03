//! Core domain types shared across projects.
use ndarray::Array2;
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Params {
    pub alpha: f32,
    pub beta: f32,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct State {
    pub phi: Array2<f32>,
    pub vx: Array2<f32>,
    pub vy: Array2<f32>,
    pub s:  Array2<f32>,
}

impl State {
    pub fn shape(&self) -> (usize, usize) { self.phi.dim() }
    pub fn check_compat(&self) {
        let d = self.phi.dim();
        assert_eq!(self.vx.dim(), d, "vx shape mismatch");
        assert_eq!(self.vy.dim(), d, "vy shape mismatch");
        assert_eq!(self.s.dim(),  d, "s shape mismatch");
    }
}

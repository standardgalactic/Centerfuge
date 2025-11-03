//! Synchronous CPU kernels for RSVP / Crystal Plenum (toy).
use anyhow::Result;
use ndarray::{Array2, Zip};
use rsvp_core_types::{Params, State};

/// One explicit Euler step (toy dynamics).
pub fn step(state: &mut State, p: &Params, dt: f32) -> Result<()> {
    state.check_compat();
    let (h, w) = state.phi.dim();

    // compute divergence of v (centered difference) into a scratch array
    let mut div_v: Array2<f32> = Array2::zeros((h, w));
    for y in 0..h {
        for x in 1..w.saturating_sub(1) {
            div_v[(y, x)] += 0.5 * (state.vx[(y, x + 1)] - state.vx[(y, x - 1)]);
        }
    }
    for y in 1..h.saturating_sub(1) {
        for x in 0..w {
            div_v[(y, x)] += 0.5 * (state.vy[(y + 1, x)] - state.vy[(y - 1, x)]);
        }
    }

    Zip::from(&mut state.phi).and(&div_v).and(&state.s).for_each(|phi, &div, &sval| {
        let dphi = p.alpha * (sval - *phi) + p.beta * div;
        *phi += dt * dphi;
    });

    Ok(())
}

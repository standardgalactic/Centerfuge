use numpy::{IntoPyArray, PyArray2};
use pyo3::prelude::*;
use rsvp_core_types::{Params, State};

#[pyfunction]
fn step_field<'py>(
    py: Python<'py>,
    phi: &PyArray2<f32>,
    vx: &PyArray2<f32>,
    vy: &PyArray2<f32>,
    s: &PyArray2<f32>,
    alpha: f32,
    beta: f32,
    dt: f32,
) -> PyResult<(&'py PyArray2<f32>, &'py PyArray2<f32>, &'py PyArray2<f32>, &'py PyArray2<f32>)> {
    let mut st = State {
        phi: phi.readonly().as_array().to_owned(),
        vx:  vx.readonly().as_array().to_owned(),
        vy:  vy.readonly().as_array().to_owned(),
        s:   s.readonly().as_array().to_owned(),
    };
    let p = Params { alpha, beta };
    rsvp_simulation::step(&mut st, &p, dt).map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("{e}")))?;
    Ok((
        st.phi.into_pyarray(py),
        st.vx.into_pyarray(py),
        st.vy.into_pyarray(py),
        st.s.into_pyarray(py),
    ))
}

#[pymodule]
fn simulation_py(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(step_field, m)?)?;
    Ok(())
}

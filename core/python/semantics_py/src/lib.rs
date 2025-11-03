use pyo3::prelude::*;

#[pyfunction]
fn new_graph_node_count() -> usize {
    let g = flyxion_semantics::new_graph();
    g.node_count()
}

#[pymodule]
fn semantics_py(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(new_graph_node_count, m)?)?;
    Ok(())
}

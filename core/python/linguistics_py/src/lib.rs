use pyo3::prelude::*;

#[pyfunction]
fn latin_to_arabic_stub(input: &str) -> String {
    flyxion_linguistics::latin_to_arabic_stub(input)
}

#[pyfunction]
fn sga_encode_stub(input: &str) -> String {
    flyxion_linguistics::sga_encode_stub(input)
}

#[pymodule]
fn linguistics_py(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(latin_to_arabic_stub, m)?)?;
    m.add_function(wrap_pyfunction!(sga_encode_stub, m)?)?;
    Ok(())
}

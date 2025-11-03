//! JSON I/O helpers.
use anyhow::Result;
use rsvp_core_types::{Params, State};

pub fn load_state(path: &str) -> Result<State> {
    let s = std::fs::read_to_string(path)?;
    Ok(serde_json::from_str(&s)?)
}

pub fn save_state(path: &str, st: &State) -> Result<()> {
    let s = serde_json::to_string_pretty(st)?;
    std::fs::write(path, s)?;
    Ok(())
}

pub fn load_params(path: &str) -> Result<Params> {
    let s = std::fs::read_to_string(path)?;
    Ok(serde_json::from_str(&s)?)
}

pub fn save_params(path: &str, p: &Params) -> Result<()> {
    let s = serde_json::to_string_pretty(p)?;
    std::fs::write(path, s)?;
    Ok(())
}

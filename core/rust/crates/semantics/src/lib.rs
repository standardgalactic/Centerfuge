//! Zettelkasten / narrative graphs (stub).
use petgraph::graph::Graph;

pub type NoteGraph = Graph<String, String>;

pub fn new_graph() -> NoteGraph { Graph::<String, String>::new() }

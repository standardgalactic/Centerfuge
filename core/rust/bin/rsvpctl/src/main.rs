use anyhow::{Context, Result};
use clap::{Parser, Subcommand};
use rsvp_core_types::Params;

#[derive(Parser, Debug)]
#[command(name = "rsvpctl", version, about = "Flyxion control CLI (sync core)")]
struct Cli {
    #[command(subcommand)]
    cmd: Cmd,
}

#[derive(Subcommand, Debug)]
enum Cmd {
    /// Integrate one step of the field dynamics
    Step {
        #[arg(long)]
        state: String,
        #[arg(long)]
        out: String,
        #[arg(long)]
        alpha: f32,
        #[arg(long)]
        beta: f32,
        #[arg(long)]
        dt: f32,
    },
}

fn main() -> Result<()> {
    let cli = Cli::parse();
    match cli.cmd {
        Cmd::Step { state, out, alpha, beta, dt } => {
            let mut st = flyxion_io::load_state(&state).context("load state")?;
            let p = Params { alpha, beta };
            rsvp_simulation::step(&mut st, &p, dt).context("kernel step")?;
            flyxion_io::save_state(&out, &st).context("save state")?;
        }
    }
    Ok(())
}

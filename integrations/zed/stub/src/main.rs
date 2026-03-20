//! memento-stub
//!
//! Native launcher for the mcp-memento Zed extension.
//!
//! Responsibilities:
//!   1. Discover a working Python executable on the host system.
//!   2. Create/validate an isolated venv inside the Zed extension work dir.
//!   3. Ensure mcp-memento is installed in that venv (auto-install via pip).
//!   4. Spawn `python -u -m memento` with inherited stdin/stdout/stderr,
//!      then exit immediately (fast path: venv already valid).
//!
//! When the venv is NOT yet ready (first install / version upgrade), the stub
//! acts as a temporary MCP bootstrap proxy:
//!
//!   - A background thread runs the venv setup (python -m venv + pip install).
//!   - The main thread serves a minimal JSON-RPC 2.0 / MCP server on stdio so
//!     that Zed's 60-second "initialize" timeout does not fire.
//!   - The bootstrap server advertises a single `memento_status` tool that
//!     returns a human-readable "still installing…" message.
//!   - Once setup completes, the stub re-execs itself (Unix) or spawns Python
//!     as a pipe-proxy child (Windows / fallback) and exits.
//!
//! This eliminates the "Context Server Stopped Running" error that occurred
//! when the user clicked "Configure Server" while pip was still running.

use std::env;
use std::fs;
use std::io::{self, BufRead, Read, Write};
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::sync::{Arc, Mutex};
use std::thread;

// ---------------------------------------------------------------------------
// Version marker — must match STUB_EXT_RELEASE in lib.rs.
// ---------------------------------------------------------------------------

/// Injected by scripts/deploy.py during a version bump.
const STUB_VERSION: &str = "v0.2.22";

// ---------------------------------------------------------------------------
// Logging
// ---------------------------------------------------------------------------



macro_rules! log {
    ($($arg:tt)*) => {{
        use std::io::Write as _;
        let msg = format!($($arg)*);
        let _ = writeln!(std::io::stderr(), "[MEMENTO-STUB] {}", msg);

        if let Ok(mut f) = std::fs::OpenOptions::new()
            .create(true)
            .append(true)
            .open(std::env::temp_dir().join("memento_stub_debug.log"))
        {
            let _ = writeln!(f, "{}", msg);
        }
    }};
}

// ---------------------------------------------------------------------------
// Python discovery
// ---------------------------------------------------------------------------

#[cfg(target_os = "windows")]
fn python_candidates() -> Vec<PathBuf> {
    let mut candidates: Vec<PathBuf> = Vec::new();

    if let Ok(cmd) = env::var("PYTHON_COMMAND") {
        if !cmd.is_empty() && cmd != "default" {
            candidates.push(PathBuf::from(cmd));
        }
    }

    candidates.push(PathBuf::from("py.exe"));
    candidates.push(PathBuf::from("python.exe"));
    candidates.push(PathBuf::from("python3.exe"));

    if let Ok(local) = env::var("LOCALAPPDATA") {
        let base = Path::new(&local).join("Programs").join("Python");

        if let Ok(rd) = std::fs::read_dir(&base) {
            let mut dirs: Vec<_> = rd.flatten().collect();
            dirs.sort_by(|a, b| b.file_name().cmp(&a.file_name()));

            for entry in dirs {
                let exe = entry.path().join("python.exe");

                if exe.exists() {
                    candidates.push(exe);
                }
            }
        }
    }

    candidates
}

#[cfg(not(target_os = "windows"))]
fn python_candidates() -> Vec<PathBuf> {
    let mut candidates: Vec<PathBuf> = Vec::new();

    if let Ok(cmd) = env::var("PYTHON_COMMAND") {
        if !cmd.is_empty() && cmd != "default" {
            candidates.push(PathBuf::from(cmd));
        }
    }

    candidates.push(PathBuf::from("python3"));
    candidates.push(PathBuf::from("python"));

    for prefix in &[
        "/usr/local/bin",
        "/opt/homebrew/bin",
        "/usr/bin",
        "/opt/local/bin",
    ] {
        candidates.push(PathBuf::from(prefix).join("python3"));
        candidates.push(PathBuf::from(prefix).join("python"));
    }

    candidates
}

fn find_python() -> Option<PathBuf> {
    for candidate in python_candidates() {
        log!("Trying Python candidate: {}", candidate.display());

        let ok = Command::new(&candidate)
            .arg("--version")
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .status()
            .map(|s| s.success())
            .unwrap_or(false);

        if ok {
            log!("Found Python: {}", candidate.display());
            return Some(candidate);
        }
    }

    None
}

// ---------------------------------------------------------------------------
// Venv management
// ---------------------------------------------------------------------------

fn venv_dir() -> PathBuf {
    if let Ok(work) = env::var("MEMENTO_WORK_DIR") {
        if !work.is_empty() {
            return PathBuf::from(work).join("venv");
        }
    }

    let mut dir = env::current_exe()
        .unwrap_or_else(|_| PathBuf::from("."))
        .parent()
        .unwrap_or(Path::new("."))
        .to_path_buf();
    dir.push("venv");
    dir
}

#[cfg(target_os = "windows")]
fn venv_python(venv: &Path) -> PathBuf {
    venv.join("Scripts").join("python.exe")
}

#[cfg(not(target_os = "windows"))]
fn venv_python(venv: &Path) -> PathBuf {
    venv.join("bin").join("python")
}

fn marker_path(venv: &Path) -> PathBuf {
    venv.join("memento_version.txt")
}

fn lock_path(venv: &Path) -> PathBuf {
    venv.parent()
        .unwrap_or(venv)
        .join("memento_setup.lock")
}

fn release_setup_lock(venv: &Path) {
    let _ = fs::remove_file(lock_path(venv));
    log!("Setup lock released (pid={}).", std::process::id());
}



fn venv_is_valid(venv: &Path) -> bool {
    if !venv_python(venv).exists() {
        log!("Venv missing or incomplete at: {}", venv.display());
        return false;
    }

    match fs::read_to_string(marker_path(venv)) {
        Ok(content) if content.trim() == STUB_VERSION => {
            log!("Venv is valid (marker={}).", content.trim());
            true
        }
        Ok(content) => {
            log!(
                "Venv version mismatch: marker='{}' expected='{}'. Rebuilding.",
                content.trim(),
                STUB_VERSION
            );
            false
        }
        Err(_) => {
            log!("Venv marker missing. Rebuilding.");
            false
        }
    }
}

fn setup_venv(system_python: &Path, venv: &Path) -> Result<(), String> {
    if venv.exists() {
        log!("Removing stale venv at: {}", venv.display());
        fs::remove_dir_all(venv).map_err(|e| format!("Failed to remove stale venv: {e}"))?;
    }

    log!("Creating venv at: {}", venv.display());
    let status = Command::new(system_python)
        .args(["-m", "venv", &venv.to_string_lossy()])
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .status()
        .map_err(|e| format!("Failed to create venv: {e}"))?;

    if !status.success() {
        return Err(format!("python -m venv failed (status: {status})"));
    }

    let pip = venv_python(venv);
    install_memento(&pip)?;

    fs::write(marker_path(venv), STUB_VERSION)
        .map_err(|e| format!("Failed to write venv marker: {e}"))?;
    log!("Venv ready. Marker written: {}", STUB_VERSION);

    Ok(())
}

// ---------------------------------------------------------------------------
// mcp-memento installation
// ---------------------------------------------------------------------------

fn install_memento(python: &Path) -> Result<(), String> {
    log!("Trying: pip install --upgrade --timeout 120 mcp-memento");

    let status = Command::new(python)
        .args([
            "-m",
            "pip",
            "install",
            "--upgrade",
            "--timeout",
            "120",
            "mcp-memento",
        ])
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .status()
        .map_err(|e| format!("Failed to launch pip: {e}"))?;

    if status.success() {
        log!("mcp-memento installed successfully (standard pip).");
        return Ok(());
    }

    log!("Standard pip failed (status: {status}), trying --break-system-packages...");

    let status = Command::new(python)
        .args([
            "-m",
            "pip",
            "install",
            "--upgrade",
            "--timeout",
            "120",
            "--break-system-packages",
            "mcp-memento",
        ])
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .status()
        .map_err(|e| format!("Failed to launch pip --break-system-packages: {e}"))?;

    if status.success() {
        log!("mcp-memento installed successfully (--break-system-packages).");
        return Ok(());
    }

    Err(
        "All install strategies failed. Please install mcp-memento manually:\n  \
         pip install mcp-memento\n  \
         pip install --break-system-packages mcp-memento  (if PEP 668 blocks)"
            .to_string(),
    )
}

// ---------------------------------------------------------------------------
// Minimal JSON-RPC 2.0 / MCP bootstrap server
//
// Serves on stdin/stdout while the venv setup runs in a background thread.
// Handles only the messages Zed sends during server startup:
//   - initialize         → responds with server capabilities (no tools yet)
//   - notifications/initialized → ignored (no response required)
//   - tools/list         → returns the single `memento_status` diagnostic tool
//   - tools/call         → returns setup progress for `memento_status`
//   - ping               → responds with empty result
//   - anything else      → responds with method-not-found error
//
// Once setup finishes (signalled via the shared SetupState), the proxy loop
// exits and the caller re-launches Python.
// ---------------------------------------------------------------------------

#[derive(Clone, PartialEq)]
enum SetupState {
    Running,
    Done,
    Failed(String),
}

/// Read one JSON-RPC message from stdin.
///
/// Zed's MCP stdio transport sends newline-delimited JSON (one JSON object
/// per line), NOT Content-Length framing.
fn read_jsonrpc_message(reader: &mut impl BufRead) -> Option<String> {
    loop {
        let mut line = String::new();

        if reader.read_line(&mut line).ok()? == 0 {
            return None;
        }

        let trimmed = line.trim_end_matches(['\r', '\n']);

        if !trimmed.is_empty() {
            return Some(trimmed.to_string());
        }
    }
}





/// Run the bootstrap MCP proxy on stdin/stdout, then seamlessly hand off
/// to Python once the venv setup completes.
///
/// Strategy: buffer ALL messages from Zed without responding to any of them.
/// This keeps Zed's 60-second initialize timeout counting but does not
/// corrupt the MCP handshake.  Once Python is ready, replay every buffered
/// message so Python handles the real initialize and responds authoritatively.
///
/// Constraint: pip install must complete within Zed's 60-second window.
/// On a warm pip cache this takes 5-15 seconds; on a cold network ~30-60s.
fn run_bootstrap_proxy(state: Arc<Mutex<SetupState>>, venv_py: PathBuf) -> ! {
    use std::sync::mpsc;
    use std::time::Duration;

    log!("Bootstrap proxy started.");

    let (tx, rx) = mpsc::channel::<Option<String>>();

    thread::spawn(move || {
        log!("Reader thread started.");
        let stdin = io::stdin();
        let mut reader = io::BufReader::new(stdin.lock());

        loop {
            log!("Reader thread: waiting for next message…");

            match read_jsonrpc_message(&mut reader) {
                Some(msg) => {
                    log!("Reader thread RX: {}", &msg[..msg.len().min(200)]);

                    if tx.send(Some(msg)).is_err() {
                        log!("Reader thread: channel closed, exiting.");
                        break;
                    }
                }
                None => {
                    log!("Reader thread: stdin EOF.");
                    let _ = tx.send(None);
                    break;
                }
            }
        }
    });

    // Buffer ALL messages — do not respond to anything.
    // Python will handle the full handshake once it starts.
    let mut buffered: Vec<String> = Vec::new();

    loop {
        match rx.recv_timeout(Duration::from_millis(200)) {
            Ok(None) => {
                log!("stdin closed during bootstrap — exiting.");
                std::process::exit(0);
            }

            Ok(Some(msg)) => {
                log!("Bootstrap buffering: {}", &msg[..msg.len().min(120)]);
                buffered.push(msg);
            }

            Err(mpsc::RecvTimeoutError::Timeout) => {}

            Err(mpsc::RecvTimeoutError::Disconnected) => {
                log!("Reader thread disconnected — exiting.");
                std::process::exit(1);
            }
        }

        let s = state.lock().unwrap();

        if *s != SetupState::Running {
            log!("Setup finished — moving to proxy phase.");
            break;
        }
    }

    let final_state = state.lock().unwrap().clone();

    if let SetupState::Failed(e) = final_state {
        log!("Setup failed — cannot start Python: {e}");
        std::process::exit(1);
    }

    log!("Spawning Python for proxy: {}", venv_py.display());

    let mut child = match Command::new(&venv_py)
        .args(["-u", "-m", "memento"])
        .env("PYTHONUNBUFFERED", "1")
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::inherit())
        .spawn()
    {
        Ok(c) => c,
        Err(e) => {
            log!("Failed to spawn Python: {e}");
            std::process::exit(1);
        }
    };

    let mut child_stdin = child.stdin.take().expect("child stdin");
    let child_stdout = child.stdout.take().expect("child stdout");

    // Replay buffered messages → Python, then forward live messages.
    thread::spawn(move || {
        log!("Replaying {} buffered message(s) to Python.", buffered.len());

        for msg in &buffered {
            log!("Replay → Python: {}", &msg[..msg.len().min(120)]);

            if writeln!(child_stdin, "{}", msg).is_err() {
                log!("Write error during replay.");
                return;
            }
        }

        if let Err(e) = child_stdin.flush() {
            log!("Flush error after replay: {e}");
            return;
        }

        log!("Replay done — forwarding live messages.");

        while let Ok(Some(msg)) = rx.recv() {
            log!("Proxy → Python: {}", &msg[..msg.len().min(120)]);

            if writeln!(child_stdin, "{}", msg).is_err() {
                log!("Write error forwarding to Python.");
                break;
            }
        }

        log!("Forwarder thread exiting.");
    });

    // Forward Python stdout → Zed stdout.
    {
        let mut buf = [0u8; 4096];
        let mut py_out = child_stdout;
        let mut out = io::stdout();

        loop {
            match py_out.read(&mut buf) {
                Ok(0) => { log!("Python stdout EOF."); break; }
                Err(e) => { log!("Python stdout read error: {e}"); break; }
                Ok(n) => {
                    log!("Python → Zed: {} bytes", n);

                    if out.write_all(&buf[..n]).is_err() || out.flush().is_err() {
                        log!("Write error forwarding to Zed.");
                        break;
                    }
                }
            }
        }
    }

    let code = child.wait().map(|s| s.code().unwrap_or(1)).unwrap_or(1);
    log!("Python proxy exited: {code}");
    std::process::exit(code);
}

// ---------------------------------------------------------------------------
// Entry point
// ---------------------------------------------------------------------------



// ---------------------------------------------------------------------------
// Entry point
// ---------------------------------------------------------------------------

fn main() {
    log!(
        "Starting. version={} pid={} os={}",
        STUB_VERSION,
        std::process::id(),
        std::env::consts::OS
    );

    let system_python = match find_python() {
        Some(p) => p,
        None => {
            log!("No Python found. Exiting.");
            std::process::exit(1);
        }
    };

    let venv = venv_dir();
    log!("Venv directory: {}", venv.display());

    if venv_is_valid(&venv) {
        log!("Fast path: venv ready, launching Python directly.");
        launch_python(&venv_python(&venv));
    }

    // Try to become the setup process by atomically creating the lockfile
    // HERE, in the main thread, before spawning anything.
    // If we fail (another process already holds it), wait until either the
    // venv becomes valid (other process finished) or the lockfile disappears.
    log!("Slow path: trying to acquire setup lock…");

    let lock = lock_path(&venv);

    // Ensure parent directory exists.
    if let Some(parent) = lock.parent() {
        let _ = fs::create_dir_all(parent);
    }

    let we_own_lock = match fs::OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(&lock)
    {
        Ok(_) => {
            log!("Setup lock acquired (pid={}).", std::process::id());
            true
        }
        Err(_) => {
            log!("Setup lock busy — waiting for other process to finish (pid={}).", std::process::id());
            false
        }
    };

    let state = Arc::new(Mutex::new(SetupState::Running));
    let state_for_setup = Arc::clone(&state);
    let venv_for_thread = venv.clone();
    let python_for_thread = system_python.clone();

    thread::spawn(move || {
        if !we_own_lock {
            // Poll until the other process finishes (lockfile gone + venv valid).
            loop {
                if venv_is_valid(&venv_for_thread) {
                    log!("Other process finished setup — venv valid.");
                    *state_for_setup.lock().unwrap() = SetupState::Done;
                    return;
                }

                if !lock_path(&venv_for_thread).exists() && venv_is_valid(&venv_for_thread) {
                    log!("Lock gone and venv valid.");
                    *state_for_setup.lock().unwrap() = SetupState::Done;
                    return;
                }

                log!("Waiting for setup lock to be released…");
                thread::sleep(std::time::Duration::from_millis(500));
            }
        }

        // We own the lock — run setup.
        let result = setup_venv(&python_for_thread, &venv_for_thread);
        release_setup_lock(&venv_for_thread);

        let mut s = state_for_setup.lock().unwrap();

        match result {
            Ok(()) => {
                log!("Setup complete.");
                *s = SetupState::Done;
            }
            Err(e) => {
                log!("Setup failed: {e}");
                *s = SetupState::Failed(e);
            }
        }
    });

    run_bootstrap_proxy(Arc::clone(&state), venv_python(&venv));
}

// ---------------------------------------------------------------------------
// Launch helpers
// ---------------------------------------------------------------------------

/// Fast-path: venv is ready, spawn Python with inherited stdio and wait.
/// The stub exits with Python's exit code.
fn launch_python(venv_py: &Path) -> ! {
    log!("Launching: {} -u -m memento", venv_py.display());

    let mut cmd = Command::new(venv_py);
    cmd.args(["-u", "-m", "memento"]);
    cmd.env("PYTHONUNBUFFERED", "1");

    for var in &["MEMENTO_DB_PATH", "MEMENTO_PROFILE", "PYTHON_COMMAND"] {
        if let Ok(val) = env::var(var) {
            cmd.env(var, val);
        }
    }

    // No .stdin() / .stdout() / .stderr() → all inherited.
    match cmd.status() {
        Ok(s) => {
            log!("Python exited: {s}");
            std::process::exit(s.code().unwrap_or(1));
        }
        Err(e) => {
            log!("Failed to spawn Python: {e}");
            std::process::exit(1);
        }
    }
}



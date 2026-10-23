#!/usr/bin/env python3
"""
ABSA Annotation Tool CLI
A command-line interface for configuring and running AnnoABSA.
"""

import argparse
import json
import sys
import os
import subprocess
import threading
import time
import socket
import signal
import atexit
from typing import Dict, Any, List

from version import __version__

# Global variable to track backend process
backend_process = None
shutdown_flag = threading.Event()


def cleanup_backend():
    """Clean up backend process on exit."""
    global backend_process
    if backend_process and backend_process.poll() is None:
        print("\n🧹 Cleaning up backend process...")
        backend_process.terminate()
        try:
            backend_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            backend_process.kill()


def signal_handler(signum, frame):
    """Handle interrupt signals."""
    print("\n🛑 Received interrupt signal. Shutting down...")
    shutdown_flag.set()
    cleanup_backend()


def register_cleanup_handlers():
    """Register cleanup functions (called from main so importing this module has no side effects)."""
    atexit.register(cleanup_backend)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


class ABSAAnnotatorConfig:
    """Configuration manager for AnnoABSA."""

    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        self.config = {
            "csv_path": csv_path,
            "session_id": None,
            "sentiment_elements": ["aspect_term", "aspect_category", "sentiment_polarity", "opinion_term"],
            "sentiment_polarity_options": ["positive", "negative", "neutral"],
            "aspect_categories": [
                'location general', 'food prices', 'food quality', 'food general',
                'ambience general', 'service general', 'restaurant prices',
                'drinks prices', 'restaurant miscellaneous', 'drinks quality',
                'drinks style_options', 'restaurant general', 'food style_options'
            ],
            "implicit_aspect_term_allowed": True,
            "implicit_opinion_term_allowed": False,
            "auto_clean_phrases": True,
            "save_phrase_positions": True,
            "click_on_token": True,
            "auto_positions": False,
            "store_time": False,
            "display_avg_annotation_time": False,
            "enable_pre_prediction": False,
            "disable_ai_automatic_prediction": False,
            "annotation_guideline": None,
            "n_few_shot": 10,
            "openai_key": None
        }

    def set_sentiment_elements(self, elements: List[str]) -> None:
        """Set the sentiment elements to annotate."""
        valid_elements = ["aspect_term", "aspect_category",
                          "sentiment_polarity", "opinion_term"]
        for element in elements:
            if element not in valid_elements:
                raise ValueError(
                    f"Invalid sentiment element: {element}. Valid options: {valid_elements}")
        self.config["sentiment_elements"] = elements

    def set_sentiment_polarities(self, polarities: List[str]) -> None:
        """Set the available sentiment polarities."""
        self.config["sentiment_polarity_options"] = polarities

    def set_aspect_categories(self, categories: List[str]) -> None:
        """Set the available aspect categories."""
        self.config["aspect_categories"] = categories

    def set_implicit_aspect_allowed(self, allowed: bool) -> None:
        """Set whether implicit aspect terms are allowed."""
        self.config["implicit_aspect_term_allowed"] = allowed

    def set_implicit_opinion_allowed(self, allowed: bool) -> None:
        """Set whether implicit opinion terms are allowed."""
        self.config["implicit_opinion_term_allowed"] = allowed

    def set_auto_clean_phrases(self, enabled: bool) -> None:
        """Set whether automatic phrase cleaning is enabled."""
        self.config["auto_clean_phrases"] = enabled

    def set_save_phrase_positions(self, enabled: bool) -> None:
        """Set whether phrase start/end positions are saved (at_start, at_end, ot_start, ot_end)."""
        self.config["save_phrase_positions"] = enabled

    def set_click_on_token(self, enabled: bool) -> None:
        """Set whether click-on-token feature is enabled (snap to token boundaries)."""
        self.config["click_on_token"] = enabled

    def set_auto_positions(self, enabled: bool) -> None:
        """Set whether automatic position data filling is enabled for existing phrases on startup."""
        self.config["auto_positions"] = enabled

    def set_store_time(self, enabled: bool) -> None:
        """Set whether timing data should be stored (duration and change status for each annotation session)."""
        self.config["store_time"] = enabled

    def set_display_avg_annotation_time(self, enabled: bool) -> None:
        """Set whether average annotation time should be displayed."""
        self.config["display_avg_annotation_time"] = enabled

    def set_enable_pre_prediction(self, enabled: bool) -> None:
        """Set whether AI pre-prediction is enabled."""
        self.config["enable_pre_prediction"] = enabled

    def set_disable_ai_automatic_prediction(self, disabled: bool) -> None:
        """Set whether automatic AI prediction triggering is disabled."""
        self.config["disable_ai_automatic_prediction"] = disabled

    def set_annotation_guideline(self, guideline_path: str) -> None:
        """Set the path to the annotation guideline PDF file and encode it as base64."""
        if guideline_path and not os.path.exists(guideline_path):
            raise ValueError(
                f"Annotation guideline file not found: {guideline_path}")

        if guideline_path:
            # Read and encode PDF as base64
            import base64
            with open(guideline_path, 'rb') as pdf_file:
                pdf_data = pdf_file.read()
                encoded_pdf = base64.b64encode(pdf_data).decode('utf-8')
                self.config["annotation_guideline"] = f"data:application/pdf;base64,{encoded_pdf}"
        else:
            self.config["annotation_guideline"] = None

    def set_openai_key(self, openai_key: str) -> None:
        """Set the OpenAI API key for using OpenAI models."""
        self.config["openai_key"] = openai_key

    def set_n_few_shot(self, n_few_shot: int) -> None:
        """Set the maximum number of few-shot examples to include in LLM prompts."""
        if n_few_shot < 0:
            raise ValueError("Number of few-shot examples must be non-negative")
        self.config["n_few_shot"] = n_few_shot

    def set_session_id(self, session_id: str) -> None:
        """Set the session ID for this annotation session."""
        self.config["session_id"] = session_id

    def get_config(self) -> Dict[str, Any]:
        """Get the current configuration."""
        return self.config.copy()

    def save_config(self, output_path: str = "absa_config.json") -> None:
        """Save configuration to JSON file."""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
        print(f"✅ Configuration saved to {output_path}")

    def load_config(self, config_path: str) -> None:
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)

            # Update configuration with loaded values
            for key, value in loaded_config.items():
                if key in self.config:
                    self.config[key] = value

            print(f"✅ Configuration loaded from {config_path}")

        except FileNotFoundError:
            print(f"❌ Configuration file '{config_path}' not found!")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in configuration file: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error loading configuration: {e}")
            sys.exit(1)

    def print_config(self) -> None:
        """Print the current configuration in a formatted way."""
        print("🎯 ABSA Annotator Configuration")
        print("=" * 40)
        print(f"📄 Data Path: {self.config['csv_path']}")
        if self.config.get('session_id'):
            print(f"🔖 Session ID: {self.config['session_id']}")
        print(
            f"🏷️  Sentiment Elements: {', '.join(self.config['sentiment_elements'])}")
        print(
            f"😊 Sentiment Polarities: {', '.join(self.config['sentiment_polarity_options'])}")
        print(
            f"📝 Aspect Categories: {len(self.config['aspect_categories'])} categories")
        print(
            f"🔍 Implicit Aspect terms: {'✅' if self.config['implicit_aspect_term_allowed'] else '❌'}")
        print(
            f"💭 Implicit Opinion terms: {'✅' if self.config['implicit_opinion_term_allowed'] else '❌'}")
        print(
            f"🔧 Auto-add Positions: {'✅' if self.config['auto_positions'] else '❌'}")
        print(f"🎯 Few-shot Examples: {self.config['n_few_shot']}")
        if self.config.get('openai_key'):
            print(f"🤖 AI Provider: OpenAI (API Key configured)")
        else:
            print(f"🤖 AI Provider: Local LLM (Ollama)")


def default_allowed_origins(frontend_host: str, frontend_port: int, backend_host: str, backend_port: int) -> List[str]:
    """Origins allowed to call the backend: the frontend and the backend itself (API docs)."""
    origins = []
    for host, port in ((frontend_host, frontend_port), (backend_host, backend_port)):
        hosts = ["localhost", "127.0.0.1"] if host in (
            "localhost", "127.0.0.1", "0.0.0.0", "::") else [host]
        origins += [f"http://{h}:{port}" for h in hosts]
    return origins


def start_backend(port: int = 8000, host: str = "localhost", data_path: str = None, config: ABSAAnnotatorConfig = None, allowed_origins: List[str] = None):
    """Start the FastAPI backend server."""
    global backend_process
    try:
        # Check if port is already in use
        if is_port_in_use(host, port):
            print(f"⚠️  Port {port} is already in use on {host}")
            print(
                f"💡 Backend might already be running on http://{host}:{port}")
            return

        print(f"🚀 Starting backend server on {host}:{port}...")
        if allowed_origins:
            os.environ['ABSA_ALLOWED_ORIGINS'] = ",".join(allowed_origins)
        if host not in ("0.0.0.0", "::"):
            os.environ['ABSA_ALLOWED_HOSTS'] = host
        if data_path:
            os.environ['ABSA_DATA_PATH'] = data_path
        if config:
            # Save config to temporary file for backend to read
            config_file = "temp_absa_config.json"
            config.save_config(config_file)
            os.environ['ABSA_CONFIG_PATH'] = config_file

        backend_process = subprocess.Popen([
            sys.executable, "-m", "uvicorn",
            "main:app", "--reload", f"--port={port}", f"--host={host}"
        ])

        # Wait for process to finish or shutdown signal
        while backend_process.poll() is None and not shutdown_flag.is_set():
            time.sleep(0.1)

        if shutdown_flag.is_set():
            cleanup_backend()

    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start backend server: {e}")
        if not shutdown_flag.is_set():
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Backend server stopped by user")
        cleanup_backend()


def start_frontend(port: int = 3000, host: str = "localhost", backend_host: str = "localhost", backend_port: int = 8000):
    """Start the React frontend development server."""
    frontend_path = os.path.join(os.getcwd(), "frontend")
    if not os.path.exists(frontend_path):
        print("❌ Frontend directory not found! Make sure you're in the project root.")
        return False

    try:
        print(f"🌐 Starting frontend development server on {host}:{port}...")
        os.chdir(frontend_path)

        # Set environment variables for Vite (read in vite.config.js)
        env = os.environ.copy()
        env["VITE_BACKEND_URL"] = f"http://{backend_host}:{backend_port}"
        env["ANNOABSA_FRONTEND_PORT"] = str(port)
        env["ANNOABSA_FRONTEND_HOST"] = host

        subprocess.run(["npm", "run", "dev"], check=True, env=env)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start frontend server: {e}")
        return False
    except KeyboardInterrupt:
        print("\n🛑 Frontend server stopped by user")
        return True
    except FileNotFoundError:
        print("❌ npm not found! Please install Node.js and npm.")
        return False


def start_full_app(backend_port: int = 8000, backend_host: str = "localhost", frontend_port: int = 3000, frontend_host: str = "localhost", data_path: str = None, config: ABSAAnnotatorConfig = None, allowed_origins: List[str] = None):
    """Start both backend and frontend servers."""
    print(f"🚀 Starting AnnoABSA v{__version__}...")
    print("=" * 50)

    # Start backend in a separate thread
    backend_thread = threading.Thread(target=start_backend, args=(
        backend_port, backend_host, data_path, config, allowed_origins))
    backend_thread.daemon = False  # Don't make it daemon so we can properly clean up
    backend_thread.start()

    # Wait a moment for backend to start
    print("⏳ Waiting for backend to initialize...")
    time.sleep(3)

    # Start frontend (this will block until stopped)
    try:
        start_frontend(frontend_port, frontend_host,
                       backend_host, backend_port)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down AnnoABSA...")
        shutdown_flag.set()
        cleanup_backend()
        # Wait for backend thread to finish
        if backend_thread.is_alive():
            backend_thread.join(timeout=5)

    # Check if shutdown was triggered
    if shutdown_flag.is_set():
        sys.exit(0)


def is_port_in_use(host: str, port: int) -> bool:
    """Check if a port is already in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, port))
            return False
        except OSError:
            return True


def main():
    """Main CLI entry point."""
    register_cleanup_handlers()
    parser = argparse.ArgumentParser(
        prog="annoabsa",
        description="🎯 AnnoABSA - Configure and run your annotation environment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with CSV path
  annoabsa examples/restaurant_reviews.csv
  
  # Load configuration from file
  annoabsa examples/restaurant_reviews.csv --load-config examples/example_config.json
  
  # Start with a session ID
  annoabsa examples/restaurant_reviews.csv --session-id "user123_session1"
  
  # Start only backend server
  annoabsa examples/restaurant_reviews.csv --backend --backend-port 8001
  
  # Configure elements and save to config file with session ID
  annoabsa examples/restaurant_reviews.csv --elements aspect_term sentiment_polarity --session-id "exp_2024" --save-config examples/quick_config.json
  
  # Load config and override some settings
  annoabsa examples/restaurant_reviews.csv --load-config examples/example_config.json --polarities positive negative

  # Export annotations to a CSV that is safe to open in Excel/LibreOffice
  annoabsa examples/restaurant_reviews.json --export annotations_export.csv
        """
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}"
    )

    parser.add_argument(
        "data_path",
        help="Path to the CSV or JSON file containing the data to annotate"
    )

    parser.add_argument(
        "--session-id",
        help="Optional session ID to identify this annotation session"
    )

    parser.add_argument(
        "--elements",
        nargs="+",
        choices=["aspect_term", "aspect_category",
                 "sentiment_polarity", "opinion_term"],
        help="Sentiment elements to annotate (default: all four elements)"
    )

    parser.add_argument(
        "--polarities",
        nargs="+",
        help="Available sentiment polarities (default: positive, negative, neutral)"
    )

    parser.add_argument(
        "--categories",
        nargs="+",
        help="Available aspect categories (default: restaurant domain categories)"
    )

    parser.add_argument(
        "--implicit-aspect",
        action="store_true",
        default=True,
        help="Allow implicit aspect terms (default: True)"
    )

    parser.add_argument(
        "--disable-implicit-aspect",
        action="store_true",
        help="Disable implicit aspect terms"
    )

    parser.add_argument(
        "--implicit-opinion",
        action="store_true",
        help="Allow implicit opinion terms"
    )

    parser.add_argument(
        "--disable_implicit_opinion",
        action="store_true",
        default=True,
        help="Disable implicit opinion terms (default)"
    )

    parser.add_argument(
        "--disable_clean_phrases",
        action="store_true",
        help="Disable automatic cleaning of punctuation from selected phrases"
    )

    parser.add_argument(
        "--disable-save-positions",
        action="store_true",
        help="Disable saving of phrase start/end positions (at_start, at_end, ot_start, ot_end)"
    )

    parser.add_argument(
        "--disable-click-on-token",
        action="store_true",
        help="Disable click-on-token feature (precise character clicking instead of token snapping)"
    )

    parser.add_argument(
        "--auto-positions",
        action="store_true",
        help="Automatically add missing position data (at_start, at_end, ot_start, ot_end) for existing phrases on server start"
    )

    parser.add_argument(
        "--store-time",
        action="store_true",
        help="Speichere die Dauer und ob sich die Annotation geändert hat (zwischen Öffnen und Speichern) für jeden Index."
    )

    parser.add_argument(
        "--display-avg-annotation-time",
        action="store_true",
        help="Zeige die durchschnittliche Zeit pro Annotation an (in Sekunden)"
    )

    parser.add_argument(
        "--ai-suggestions",
        dest="enable_pre_prediction",
        action="store_true",
        help="Enable AI pre-prediction feature (default: disabled)"
    )

    parser.add_argument(
        "--disable-ai-automatic-prediction",
        dest="disable_ai_automatic_prediction",
        action="store_true",
        help="Disable automatic AI prediction triggering (AI button still works manually)"
    )

    parser.add_argument(
        "--save-config",
        metavar="PATH",
        nargs="?",
        const="absa_config.json",
        help="Save configuration to JSON file (default: absa_config.json)"
    )

    parser.add_argument(
        "--load-config",
        metavar="PATH",
        help="Load configuration from JSON file"
    )

    parser.add_argument(
        "--show-config",
        action="store_true",
        help="Display the current configuration"
    )

    parser.add_argument(
        "--annotation-guidelines",
        metavar="PDF_PATH",
        help="Path to PDF file containing annotation guidelines to display in the UI"
    )

    parser.add_argument(
        "--llm-model",
        metavar="MODEL",
        default="gemma3:4b",
        help="Language model for AI predictions (e.g., gemma3:4b for Ollama, gpt-4o-2024-08-06 for OpenAI)"
    )

    parser.add_argument(
        "--openai-key",
        metavar="API_KEY",
        help="OpenAI API key for using OpenAI models instead of local LLM"
    )

    parser.add_argument(
        "--n-few-shot",
        type=int,
        default=10,
        metavar="N",
        help="Maximum number of few-shot examples to include in LLM prompts (default: 10)"
    )

    # Server control arguments
    parser.add_argument(
        "--backend",
        action="store_true",
        help="Start only the backend server"
    )

    parser.add_argument(
        "--backend-port",
        type=int,
        default=8000,
        help="Port for the backend server (default: 8000)"
    )

    parser.add_argument(
        "--backend-ip",
        default="localhost",
        help="IP address for the backend server (default: localhost)"
    )

    parser.add_argument(
        "--frontend-port",
        type=int,
        default=3000,
        help="Port for the frontend server (default: 3000)"
    )

    parser.add_argument(
        "--frontend-ip",
        default="localhost",
        help="IP address for the frontend server (default: localhost)"
    )

    parser.add_argument(
        "--allowed-origins",
        nargs="+",
        metavar="ORIGIN",
        help="Origins (e.g. http://192.168.0.10:3000) allowed to access the backend. "
             "Default: the frontend and backend addresses. Requests from other websites are rejected."
    )

    parser.add_argument(
        "--export",
        metavar="CSV_PATH",
        help="Export the data file (including annotations) to a spreadsheet-safe CSV file and exit"
    )

    args = parser.parse_args()

    # Check if data file exists
    if not os.path.exists(args.data_path):
        print(f"❌ Error: Data file '{args.data_path}' not found!")
        sys.exit(1)

    # Check file format
    file_extension = os.path.splitext(args.data_path)[1].lower()
    if file_extension not in ['.csv', '.json']:
        print(
            f"❌ Error: Unsupported file format '{file_extension}'. Use .csv or .json files.")
        sys.exit(1)

    # Check file content before starting anything
    from data_io import check_data_file, export_csv, DataFileError
    problems = check_data_file(args.data_path)
    if problems:
        print(f"❌ Error: Data file '{args.data_path}' is malformed:")
        for problem in problems:
            print(f"   - {problem}")
        sys.exit(1)

    if args.export:
        try:
            n_rows = export_csv(args.data_path, args.export)
        except (DataFileError, OSError) as e:
            print(f"❌ Export failed: {e}")
            sys.exit(1)
        print(f"✅ Exported {n_rows} rows to {args.export} (spreadsheet formulas neutralised)")
        return

    print(f"📂 Using {file_extension[1:].upper()} file: {args.data_path}")
    if file_extension == '.csv':
        print("💡 Note: CSV file will be read/written with UTF-8 encoding")

    # Initialize configuration
    config = ABSAAnnotatorConfig(args.data_path)

    # Load configuration from file if specified (before applying command line overrides)
    if args.load_config:
        config.load_config(args.load_config)

    # Apply command line arguments (these override loaded config)
    if args.session_id:
        config.set_session_id(args.session_id)

    if args.elements:
        config.set_sentiment_elements(args.elements)

    if args.polarities:
        config.set_sentiment_polarities(args.polarities)

    if args.categories:
        config.set_aspect_categories(args.categories)

    if args.disable_implicit_aspect:
        config.set_implicit_aspect_allowed(False)
    elif args.implicit_aspect:
        config.set_implicit_aspect_allowed(True)

    if args.implicit_opinion:
        config.set_implicit_opinion_allowed(True)
    elif args.disable_implicit_opinion:
        config.set_implicit_opinion_allowed(False)

    if args.disable_clean_phrases:
        config.set_auto_clean_phrases(False)

    if args.disable_save_positions:
        config.set_save_phrase_positions(False)

    if args.disable_click_on_token:
        config.set_click_on_token(False)

    if args.auto_positions:
        config.set_auto_positions(True)

    if args.store_time:
        config.set_store_time(True)

    if args.display_avg_annotation_time:
        config.set_display_avg_annotation_time(True)

    if args.enable_pre_prediction:
        config.set_enable_pre_prediction(True)

    if args.disable_ai_automatic_prediction:
        config.set_disable_ai_automatic_prediction(True)

    if args.annotation_guidelines:
        config.set_annotation_guideline(args.annotation_guidelines)

    if args.openai_key:
        config.set_openai_key(args.openai_key)

    if args.n_few_shot:
        config.set_n_few_shot(args.n_few_shot)

    # Show configuration if requested
    if args.show_config:
        config.print_config()

    # Save configuration if requested
    if args.save_config:
        config.save_config(args.save_config)

    # Start servers if requested
    backend_port = args.backend_port
    backend_host = args.backend_ip
    frontend_port = args.frontend_port
    frontend_host = args.frontend_ip

    allowed_origins = args.allowed_origins or default_allowed_origins(
        frontend_host, frontend_port, backend_host, backend_port)
    if "*" in allowed_origins:
        print("⚠️  --allowed-origins '*': any website opened in the annotator's browser can modify the data!")
    elif not args.allowed_origins and frontend_host in ("0.0.0.0", "::"):
        print("💡 Frontend listens on all interfaces: pass --allowed-origins http://<server-ip>:"
              f"{frontend_port} so annotators on other machines can save.")

    if args.backend:
        start_backend(backend_port, backend_host, args.data_path, config, allowed_origins)
    else:
        # Default behavior: start both servers
        start_full_app(backend_port, backend_host, frontend_port,
                       frontend_host, args.data_path, config, allowed_origins)


if __name__ == "__main__":
    main()

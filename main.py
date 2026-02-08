"""
Main entry point for RefactorBot.
"""
import sys
import argparse


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="RefactorBot - Self-Aware AI Agent Framework")
    
    parser.add_argument(
        "--mode",
        choices=["dashboard", "slice"],
        default="dashboard",
        help="Run mode: dashboard (default) or slice"
    )
    
    parser.add_argument(
        "--slice",
        choices=[
            "agent",
            "tools",
            "memory",
            "communication",
            "session",
            "providers",
            "skills",
            "eventbus"
        ],
        help="Slice to run (required for slice mode)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8501,
        help="Port for dashboard (default: 8501)"
    )
    
    args = parser.parse_args()
    
    if args.mode == "dashboard":
        print(f"Starting RefactorBot Master Dashboard on port {args.port}...")
        import subprocess
        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            "master_dashboard/app.py",
            "--server.port", str(args.port)
        ])
    
    elif args.mode == "slice":
        if not args.slice:
            parser.error("--slice is required for slice mode")
        
        slice_map = {
            "agent": "slice_agent",
            "tools": "slice_tools",
            "memory": "slice_memory",
            "communication": "slice_communication",
            "session": "slice_session",
            "providers": "slice_providers",
            "skills": "slice_skills",
            "eventbus": "slice_eventbus",
        }
        
        slice_id = slice_map.get(args.slice, args.slice)
        print(f"Starting {slice_id} dashboard...")
        
        import subprocess
        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            f"slices/{slice_id}/ui/pages/dashboard.py",
            "--server.port", str(args.port + 1)
        ])


if __name__ == "__main__":
    main()

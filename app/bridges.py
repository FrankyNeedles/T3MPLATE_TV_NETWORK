import subprocess
from pathlib import Path


class Bridges:
    @staticmethod
    def run_wsl(command: str) -> subprocess.CompletedProcess:
        """Run command in WSL Ubuntu."""
        wsl_cmd = ["wsl.exe", "-d", "Ubuntu"] + command.split()
        return subprocess.run(wsl_cmd, capture_output=True, text=True)

    @staticmethod
    def run_windows(command: str) -> subprocess.CompletedProcess:
        """Run command in Windows cmd."""
        win_cmd = ["cmd.exe", "/c"] + command.split()
        return subprocess.run(win_cmd, capture_output=True, text=True, shell=True)

    @staticmethod
    def sync_paths_wsl_to_win(wsl_path: str, win_path: str):
        """Sync file from WSL to Windows (e.g., assets)."""
        win_part = win_path.lstrip("C:\\").replace("\\", "/")
        cp_cmd = f"cp {wsl_path} /mnt/c/{win_part}"
        result = Bridges.run_wsl(cp_cmd)
        if result.returncode == 0:
            print(f"Synced {wsl_path} to {win_path}")
        else:
            print(f"Sync failed: {result.stderr}")

    @staticmethod
    def launch_retroarch():
        """Launch RetroArch on Windows."""
        bat_path = Path(__file__).parent.parent / "retroarch_launch.bat"
        Bridges.run_windows(str(bat_path))


if __name__ == "__main__":
    print(Bridges.run_wsl("ls /").stdout)

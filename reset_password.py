import os
import sys
import getpass
import argparse

# Ensure current directory is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from server.auth import set_admin_password, is_setup_completed

def main():
    parser = argparse.ArgumentParser(description="Reset Admin Password for LAN Remote Desktop")
    parser.add_argument("--password", type=str, help="New password (optional, will prompt securely if omitted)")
    args = parser.parse_args()

    print("=" * 60)
    print("  LAN Remote Desktop - Reset Admin Password Console")
    print("=" * 60)

    new_pass = args.password
    if not new_pass:
        while True:
            try:
                new_pass = getpass.getpass("Enter New Admin Password (min 4 characters): ")
            except (KeyboardInterrupt, EOFError):
                print("\nOperation cancelled.")
                sys.exit(1)

            if len(new_pass) < 4:
                print("[!] Password too short, must be at least 4 characters. Try again.\n")
                continue

            confirm_pass = getpass.getpass("Confirm New Admin Password: ")
            if new_pass != confirm_pass:
                print("[!] Passwords do not match. Try again.\n")
                continue
            break

    if set_admin_password(new_pass):
        print("\n[SUCCESS] Admin password has been successfully updated!")
        print("You can now log in to the web dashboard with your new password.")
    else:
        print("\n[ERROR] Failed to update admin password. Please try again.")

    print("=" * 60)

if __name__ == "__main__":
    main()

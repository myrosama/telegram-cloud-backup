# client/main.py
import sys
import os

# This allows the script to find our other project modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# We will import the main functions from our two uploader scripts
from client.uploader_user import main as user_uploader_main
from client.uploader_bot import main as bot_uploader_main

def display_menu():
    """Displays the main menu to the user."""
    print("\n" + "="*40)
    print("  Telegram Cloud Storage Uploader")
    print("="*40)
    print("\nPlease choose your upload method:")
    print("  1. Bot Method (20 MB chunks)")
    print("     - Pros: Simpler, no separate login needed.")
    print("     - Cons: Many small parts, may be less reliable for huge files.")
    print("\n  2. User Method (2 GB chunks)")
    print("     - Pros: More reliable for huge files, faster for good connections.")
    print("     - Cons: Requires one-time login with your phone number.")
    print("\n  Q. Quit")
    print("-"*40)

def main():
    """The main function that runs the menu loop."""
    while True:
        display_menu()
        choice = input("Enter your choice (1, 2, or Q): ").lower().strip()

        if choice == '1':
            print("\n--- Starting Bot Uploader ---\n")
            bot_uploader_main()
            break
        elif choice == '2':
            print("\n--- Starting User Uploader ---\n")
            # The user uploader is an async function, so we need to run it in an event loop
            import asyncio
            asyncio.run(user_uploader_main())
            break
        elif choice == 'q':
            print("Exiting.")
            break
        else:
            print("Invalid choice, please try again.")

if __name__ == "__main__":
    main()

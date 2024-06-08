from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    from app.core import main_handler

    main_handler()

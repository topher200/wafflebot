from generate_audio import produce_audio_mixed_track
from src.utils.logging import setup_logger

# Set up logger
logger = setup_logger(__name__)


def main():
    logger.info("Starting audio mixing process...")
    produce_audio_mixed_track()


if __name__ == "__main__":
    main()

import pathlib
import random
from pydub import AudioSegment
from pydub.effects import normalize
from src.utils.logging import setup_logger

# Set up logger
logger = setup_logger(__name__)

# Constants for voice memo processing
VOICE_DIR = pathlib.Path("static/local-sample-files")
MUSIC_DIR = pathlib.Path("static/background-music")

INTRO_MS = 3000  # music intro length (3 sec)
OUTRO_MS = 8000  # music outro length (5 sec)
CROSSFADE_MS = 500  # crossfade between memos
GAP_MS = 3000  # music-only between memos
VOICE_FADE_MS = 200  # fade-in/out on memos
MUSIC_UNDER_VOICE_DB = -20  # dB lowering under speech
MUSIC_WITHOUT_VOICE_DB = -10  # little lower music when there is no voice
GAP_FADE_MS = 2000  # fade in/out for gap transitions


def load_voice_memos():
    """Load and normalize voice memos from the voice directory."""
    logger.info("Loading voice memos...")
    voice_files = sorted(
        f for f in VOICE_DIR.iterdir() if f.suffix in [".mp3", ".wav", ".m4a"]
    )
    voice_segs = []

    for f in voice_files:
        v = (
            normalize(AudioSegment.from_file(str(f)))
            .fade_in(VOICE_FADE_MS)
            .fade_out(VOICE_FADE_MS)
        )
        voice_segs.append(v)

    if not voice_segs:
        logger.error("No voice memos found in static/local-sample-files!")
        return None

    logger.info(f"Loaded {len(voice_segs)} voice memos")
    return voice_segs


def build_voice_track(voice_segs):
    """Build the voice track with gaps and track the gap ranges."""
    logger.info("Building voice track...")
    show = AudioSegment.silent(INTRO_MS)  # add music intro at the start
    gap_ranges = [(0, INTRO_MS)]  # first gap: intro

    cursor = INTRO_MS

    for idx, seg in enumerate(voice_segs):
        if idx:
            gap_start = cursor
            gap_end = cursor + GAP_MS
            gap_ranges.append((gap_start, gap_end))
            show += AudioSegment.silent(GAP_MS)
            cursor += GAP_MS
        show = show.append(seg, crossfade=CROSSFADE_MS)
        cursor += len(seg)

    # After last voice memo, add outro
    gap_start = cursor
    gap_end = cursor + OUTRO_MS
    gap_ranges.append((gap_start, gap_end))
    show += AudioSegment.silent(OUTRO_MS)

    logger.info(f"Built voice track with {len(gap_ranges)} gaps")
    return show, gap_ranges


def load_background_music(track_length):
    """Load and prepare background music to match the track length."""
    logger.info("Loading background music...")
    music_files = [f for f in MUSIC_DIR.iterdir() if f.suffix in [".mp3", ".wav"]]
    random.shuffle(music_files)
    if not music_files:
        logger.error("No background music found in static/background-music!")
        return None

    bg = sum(AudioSegment.from_file(str(f)) for f in music_files)
    bg = bg[:track_length]  # trim to exact length
    logger.info("Background music loaded and trimmed to track length")
    return bg


def create_final_mix(voice_track, bg_music, gap_ranges):
    """Create the final mix by overlaying voice and background music."""
    logger.info("Creating final mix...")

    # Start with silent track of correct length
    final_music = AudioSegment.silent(len(voice_track))

    # Add full-volume background music only in the gaps
    for start, end in gap_ranges:
        full_vol_slice = (
            bg_music[start:end]
            .apply_gain(MUSIC_WITHOUT_VOICE_DB)
            .fade_in(GAP_FADE_MS)
            .fade_out(GAP_FADE_MS)
        )
        final_music = final_music.overlay(full_vol_slice, position=start)

    # Add lowered background music everywhere else
    lowered_bg = bg_music + MUSIC_UNDER_VOICE_DB
    # Overlay the lowered background music where there isn't full volume music
    final_music = final_music.overlay(lowered_bg)

    # Finally overlay the voice track
    final_music = final_music.overlay(voice_track)

    logger.info("Final mix created")
    return final_music


def export_mix(final_mix):
    """Export the final mix to an MP3 file."""
    logger.info("Exporting final mix...")
    # Make sure the output directory exists
    pathlib.Path("output").mkdir(exist_ok=True)

    with open("output/voice_memo_mix.mp3", "wb") as out_f:
        final_mix.export(out_f, format="mp3")
    logger.info("Voice memo mix exported successfully!")


def produce_audio_mixed_track():
    """Main function to generate the voice memo overlay with background music."""
    logger.info("Starting voice memo overlay generation...")

    # Step 1: Load voice memos
    voice_segs = load_voice_memos()
    if not voice_segs:
        return

    # Step 2: Build voice track
    voice_track, gap_ranges = build_voice_track(voice_segs)

    # Step 3: Load background music
    bg_music = load_background_music(len(voice_track))
    if not bg_music:
        return

    # Step 4: Create final mix
    final_mix = create_final_mix(voice_track, bg_music, gap_ranges)

    # Step 5: Export the mix
    export_mix(final_mix)


if __name__ == "__main__":
    produce_audio_mixed_track()

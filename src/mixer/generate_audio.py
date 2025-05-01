import datetime
import pathlib
import random
from typing import List, Tuple

from pydub import AudioSegment  # type: ignore[import]
from pydub.effects import normalize  # type: ignore[import]

from src.utils.logging import setup_logger

logger = setup_logger(__name__)

VOICE_DIR = pathlib.Path("data/voice-memos")
MUSIC_DIR = pathlib.Path("static/background-music")
PODCAST_OUTPUT_DIR = pathlib.Path("data/podcast")

INTRO_MS = 5000  # music intro length
OUTRO_MS = 8000  # music outro length
CROSSFADE_MS = 500  # crossfade between memos
GAP_MS = 5000  # music-only between memos
VOICE_FADE_MS = 200  # fade-in/out on memos
MUSIC_UNDER_VOICE_DB = -40  # dB lowering under speech
MUSIC_WITHOUT_VOICE_DB = -10  # little lower music when there is no voice
GAP_FADE_MS = 2000  # fade in/out for gap transitions
MAX_LENGTH_MS = int(datetime.timedelta(minutes=3, seconds=5).total_seconds() * 1000)


class NoVoiceMemosFoundError(Exception):
    """Exception raised when no voice memos are found."""


class NoBackgroundMusicFoundError(Exception):
    """Exception raised when no background music is found."""


def load_voice_memos() -> List[AudioSegment]:
    """Load and normalize voice memos from the voice directory."""
    logger.info("Loading voice memos...")
    voice_files = sorted(
        f for f in VOICE_DIR.iterdir() if f.suffix in [".mp3", ".wav", ".m4a", ".ogg"]
    )
    if not voice_files:
        logger.error(f"No voice memos found in {VOICE_DIR}")
        raise NoVoiceMemosFoundError(f"No voice memos found in {VOICE_DIR}")

    # First load all files
    raw_segs: List[AudioSegment] = []
    for f in voice_files:
        logger.info(f"Loading {f.name}")
        segment = AudioSegment.from_file(str(f))
        if len(segment) > MAX_LENGTH_MS:
            logger.info(f"Voice memo {f.name} exceeds 3m 10s limit, truncating...")
            segment = segment[:MAX_LENGTH_MS]
        raw_segs.append(segment)

    # Concatenate all segments to normalize them together
    logger.info(f"Normalizing {len(raw_segs)} voice memos...")
    combined = raw_segs[0]
    for seg in raw_segs[1:]:
        combined += seg
    normalized_combined = normalize(combined)

    # Split back into individual segments
    voice_segs = []
    current_pos = 0
    logger.info("Splitting normalized voice memos into individual segments...")
    for seg in raw_segs:
        # Get the normalized version of this segment
        normalized_seg = normalized_combined[current_pos : current_pos + len(seg)]

        # Add fades
        normalized_seg = normalized_seg.fade_in(VOICE_FADE_MS).fade_out(VOICE_FADE_MS)

        voice_segs.append(normalized_seg)
        current_pos += len(seg)

    logger.info(f"Loaded and normalized {len(voice_segs)} voice memos")
    return voice_segs


def build_voice_track(
    voice_segs: List[AudioSegment],
) -> Tuple[AudioSegment, List[Tuple[int, int]]]:
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


def load_background_music() -> AudioSegment:
    """Load and prepare background music."""
    logger.info("Loading background music...")
    music_files = [
        f for f in MUSIC_DIR.iterdir() if f.suffix in [".mp3", ".wav", ".ogg", ".m4a"]
    ]
    random.shuffle(music_files)
    if not music_files:
        logger.error(f"No background music found in {MUSIC_DIR}")
        raise NoBackgroundMusicFoundError(f"No background music found in {MUSIC_DIR}")

    bg = AudioSegment.empty()
    for f in music_files:
        bg += AudioSegment.from_file(str(f))
    logger.info(
        f"Loaded {len(music_files)} background tracks, total length: {len(bg)}ms"
    )
    return bg


def create_final_mix(
    voice_track: AudioSegment, bg_music: AudioSegment, gap_ranges: List[Tuple[int, int]]
) -> AudioSegment:
    """Create the final mix by overlaying voice and background music."""
    logger.info("Creating final mix...")

    # If background music is too short, loop it
    while len(bg_music) < len(voice_track) + len(voice_track) * 0.1:
        logger.info(
            f"Background music too short "
            f"({len(bg_music)}ms vs {len(voice_track)}ms), looping..."
        )
        bg_music = bg_music + bg_music

    # Start with silent track of correct length
    final_music = AudioSegment.silent(len(voice_track))

    # Add full-volume background music only in the gaps
    for start, end in gap_ranges:
        fade_start = max(0, start - GAP_FADE_MS)
        fade_end = min(len(voice_track), end + GAP_FADE_MS)
        full_vol_slice = (
            bg_music[fade_start:fade_end]
            .apply_gain(MUSIC_WITHOUT_VOICE_DB)
            .fade_in(GAP_FADE_MS)
            .fade_out(GAP_FADE_MS)
        )
        final_music = final_music.overlay(full_vol_slice, position=fade_start)

    # Add lowered background music everywhere else
    lowered_bg = bg_music + MUSIC_UNDER_VOICE_DB
    # Overlay the lowered background music where there isn't full volume music
    final_music = final_music.overlay(lowered_bg)

    # Finally overlay the voice track
    final_music = final_music.overlay(voice_track)

    # Add fade in/out to the entire track
    final_music = final_music.fade_in(GAP_FADE_MS).fade_out(GAP_FADE_MS)

    logger.info("Final mix created")
    return final_music


def export_mix(final_mix: AudioSegment) -> None:
    """Export the final mix to an MP3 file."""
    logger.info("Exporting final mix...")
    PODCAST_OUTPUT_DIR.mkdir(exist_ok=True)
    with open(PODCAST_OUTPUT_DIR / "voice_memo_mix.mp3", "wb") as out_f:
        final_mix.export(out_f, format="mp3")
    logger.info("Voice memo mix exported successfully!")


def produce_audio_mixed_track() -> None:
    """Main function to generate the voice memo overlay with background music."""
    logger.info("Starting voice memo overlay generation...")

    # Step 1: Load voice memos
    voice_segs = load_voice_memos()

    # Step 2: Build voice track
    voice_track, gap_ranges = build_voice_track(voice_segs)

    # Step 3: Load background music
    bg_music = load_background_music()

    # Step 4: Create final mix
    final_mix = create_final_mix(voice_track, bg_music, gap_ranges)

    # Step 5: Export the mix
    export_mix(final_mix)


if __name__ == "__main__":
    produce_audio_mixed_track()

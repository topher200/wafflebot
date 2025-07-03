import pathlib
import random
from typing import List, Tuple

from pydub import AudioSegment  # type: ignore[import]
from pydub.effects import normalize  # type: ignore[import]

from src.utils.logging import setup_logger

logger = setup_logger(__name__)

VOICE_DIR = pathlib.Path("data/voice-memos")
MUSIC_DIR = pathlib.Path("data/background-music")
PODCAST_OUTPUT_DIR = pathlib.Path("data/podcast")

INTRO_MS = 5000  # music intro length
OUTRO_MS = 8000  # music outro length
CROSSFADE_MS = 500  # crossfade between memos
GAP_MS = 5000  # music-only between memos
VOICE_FADE_MS = 200  # fade-in/out on memos
MUSIC_UNDER_VOICE_DB = -40  # dB lowering under speech
MUSIC_WITHOUT_VOICE_DB = -10  # little lower music when there is no voice
GAP_FADE_MS = 2000  # fade in/out for gap transitions
MAX_LENGTH_MS = int((3 * 60 + 5) * 1000)  # 3 minutes 5 seconds in milliseconds


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

    voice_segs: List[AudioSegment] = []
    cumulative_position_ms = INTRO_MS

    for f in voice_files:
        logger.info(f"Loading voice memo: {f.name}")
        segment = AudioSegment.from_file(str(f))
        duration_ms = len(segment)

        if len(segment) > MAX_LENGTH_MS:
            logger.info(
                f"Voice memo {f.name} exceeds 3m 10s limit, "
                f"truncating from {duration_ms}ms to {MAX_LENGTH_MS}ms"
            )
            segment = segment[:MAX_LENGTH_MS]
            duration_ms = MAX_LENGTH_MS

        normalized_seg = (
            normalize(segment).fade_in(VOICE_FADE_MS).fade_out(VOICE_FADE_MS)
        )
        voice_segs.append(normalized_seg)

        logger.info(
            f"Voice memo loaded: {f.name} | Duration: {duration_ms}ms | "
            f"Timeline position: {cumulative_position_ms}ms-"
            f"{cumulative_position_ms + duration_ms}ms"
        )

        cumulative_position_ms += duration_ms + GAP_MS

    logger.info(f"Loaded and normalized {len(voice_segs)} voice memos")
    return voice_segs


def build_voice_track(
    voice_segs: List[AudioSegment],
) -> Tuple[AudioSegment, List[Tuple[int, int]]]:
    """Build the voice track with gaps and track the gap ranges."""
    logger.info("Building voice track...")
    show = AudioSegment.silent(INTRO_MS)  # add music intro at the start
    gap_ranges = [(0, INTRO_MS)]  # first gap: intro

    logger.info(f"Intro gap: 0ms-{INTRO_MS}ms (background music only)")

    cursor = INTRO_MS

    for idx, seg in enumerate(voice_segs):
        if idx:
            gap_start = cursor
            gap_end = cursor + GAP_MS
            gap_ranges.append((gap_start, gap_end))
            show += AudioSegment.silent(GAP_MS)

            logger.info(f"Gap {idx}: {gap_start}ms-{gap_end}ms (background music only)")

            cursor += GAP_MS

        voice_start = cursor
        voice_end = cursor + len(seg)
        show = show.append(seg, crossfade=CROSSFADE_MS)

        logger.info(
            f"Voice memo {idx + 1}: {voice_start}ms-{voice_end}ms "
            f"(voice + background music)"
        )

        cursor += len(seg)

    # After last voice memo, add outro
    gap_start = cursor
    gap_end = cursor + OUTRO_MS
    gap_ranges.append((gap_start, gap_end))
    show += AudioSegment.silent(OUTRO_MS)

    logger.info(f"Outro gap: {gap_start}ms-{gap_end}ms (background music only)")

    logger.info(
        f"Built voice track: total length {len(show)}ms with "
        f"{len(gap_ranges)} music-only gaps"
    )
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
    cumulative_music_ms = 0

    for f in music_files:
        track = AudioSegment.from_file(str(f))
        bg += track
        duration_ms = len(track)

        logger.info(
            f"Background music loaded: {f.name} | "
            f"Duration: {duration_ms}ms | "
            f"Music timeline: {cumulative_music_ms}ms-"
            f"{cumulative_music_ms + duration_ms}ms"
        )

        cumulative_music_ms += duration_ms

    logger.info(
        f"Total background music: {len(music_files)} tracks, "
        f"combined length: {len(bg)}ms"
    )
    return bg


def create_final_mix(
    voice_track: AudioSegment, bg_music: AudioSegment, gap_ranges: List[Tuple[int, int]]
) -> AudioSegment:
    """Create the final mix by overlaying voice and background music."""
    logger.info("Creating final mix...")

    logger.info("Final mix timeline summary:")
    logger.info(f"  - Total track length: {len(voice_track)}ms")
    logger.info(f"  - Background music length: {len(bg_music)}ms")
    logger.info(f"  - Music-only gaps: {len(gap_ranges)} segments")

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
    for i, (start, end) in enumerate(gap_ranges):
        fade_start = max(0, start - GAP_FADE_MS)
        fade_end = min(len(voice_track), end + GAP_FADE_MS)
        full_vol_slice = (
            bg_music[fade_start:fade_end]
            .apply_gain(MUSIC_WITHOUT_VOICE_DB)
            .fade_in(GAP_FADE_MS)
            .fade_out(GAP_FADE_MS)
        )
        final_music = final_music.overlay(full_vol_slice, position=fade_start)

        logger.info(
            f"Applied full-volume background music to gap {i + 1}: {start}ms-{end}ms"
        )

    # Add lowered background music everywhere else
    lowered_bg = bg_music + MUSIC_UNDER_VOICE_DB
    final_music = final_music.overlay(lowered_bg)

    logger.info(
        f"Applied lowered background music ({MUSIC_UNDER_VOICE_DB}dB) to entire track"
    )

    # Finally overlay the voice track
    final_music = final_music.overlay(voice_track)

    logger.info("Overlaid voice track onto background music")

    # Add fade in/out to the entire track
    final_music = final_music.fade_in(GAP_FADE_MS).fade_out(GAP_FADE_MS)

    logger.info("Final mix created successfully")
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

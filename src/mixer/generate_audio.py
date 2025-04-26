# Example from pydub-ng repo:

# from glob import glob
# from pydub import AudioSegment

# playlist_songs = [AudioSegment.from_mp3(mp3_file) for mp3_file in glob("*.mp3")]

# first_song = playlist_songs.pop(0)

# # let's just include the first 30 seconds of the first song (slicing
# # is done by milliseconds)
# beginning_of_song = first_song[:30*1000]

# playlist = beginning_of_song
# for song in playlist_songs:

#     # We don't want an abrupt stop at the end, so let's do a 10 second crossfades
#     playlist = playlist.append(song, crossfade=(10 * 1000))

# # let's fade out the end of the last song
# playlist = playlist.fade_out(30)

# # hmm I wonder how long it is... ( len(audio_segment) returns milliseconds )
# playlist_length = len(playlist) / (1000*60)

# # lets save it!
# with open("%s_minute_playlist.mp3" % playlist_length, 'wb') as out_f:
#     playlist.export(out_f, format='mp3')

import pathlib
from pydub import AudioSegment


def find_audio_files():
    audio_path = pathlib.Path("static/local-sample-files")
    # Return a list of all audio files in the directory
    return list(audio_path.glob("*.mp3")) + list(audio_path.glob("*.m4a"))


def generate_audio_file():
    print("Generating audio file...")
    audio_files = find_audio_files()
    print(f"Found {len(audio_files)} audio files")

    if not audio_files:
        print("No audio files found in static/local-sample-files!")
        return

    files = [AudioSegment.from_file(str(file)) for file in audio_files]
    print(f"Found {len(files)} files")
    first_file = files.pop(0)
    print(f"First file: {first_file}")
    beginning_of_song = first_file[: 30 * 1000]
    print(f"Beginning of song: {beginning_of_song}")
    playlist = beginning_of_song
    for song in files:
        print(f"Song: {song}")
        # Calculate crossfade duration as 10% of the song length, but no more than 10 seconds
        crossfade_duration = min(len(song) * 0.1, 10 * 1000)
        playlist = playlist.append(song, crossfade=int(crossfade_duration))
    print(f"Playlist: {playlist}")
    playlist = playlist.fade_out(30)
    print(f"Playlist after fade out: {playlist}")

    # Make sure the output directory exists
    pathlib.Path("output").mkdir(exist_ok=True)

    with open("output/test.mp3", "wb") as out_f:
        playlist.export(out_f, format="mp3")
    print("Audio file generated successfully!")


if __name__ == "__main__":
    generate_audio_file()

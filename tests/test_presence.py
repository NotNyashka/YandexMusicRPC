from ymrpc.discord_rpc import presence_payload
from ymrpc.media import _playback_state
from ymrpc.models import PlaybackState, Track


def test_playing_payload_has_progress_and_link():
    track = Track(
        title="Song",
        artist="Artist",
        album="Album",
        state=PlaybackState.PLAYING,
        position_seconds=30,
        duration_seconds=180,
        observed_at=1000,
        cover_url="https://example.com/cover.jpg",
        track_url="https://music.yandex.ru/album/1/track/2",
    )
    payload = presence_payload(track, now=1010)
    assert payload["activity_type"] == 2
    assert payload["status_display_type"] == 2
    assert payload["name"] == "Яндекс Музыку"
    assert payload["start"] == 970
    assert payload["end"] == 1150
    assert payload["state"] == "Artist"
    assert payload["large_image"].startswith("https://")
    assert payload["buttons"][0]["label"] == "Открыть трек"
    assert payload["buttons"][0]["url"] == track.track_url


def test_paused_payload_has_no_timestamps():
    track = Track(
        title="Song",
        artist="Artist",
        state=PlaybackState.PAUSED,
        position_seconds=65,
        duration_seconds=180,
    )
    payload = presence_payload(track, now=100)
    assert "start" not in payload
    assert "end" not in payload
    assert payload["state"] == "Artist • На паузе"


def test_missing_exact_link_falls_back_to_yandex_search():
    track = Track(title="Song Name", artist="Artist Name")
    payload = presence_payload(track)
    assert payload["buttons"][0]["url"].startswith("https://music.yandex.ru/search?text=")


def test_private_style_hides_track_and_link():
    track = Track(
        title="Secret Song",
        artist="Secret Artist",
        cover_url="https://example.com/cover.jpg",
    )
    payload = presence_payload(track, style="private")
    assert payload["details"] == "Слушает музыку"
    assert payload["state"] == "Яндекс Музыка"
    assert "large_image" not in payload
    assert "buttons" not in payload


def test_album_and_button_options():
    track = Track(title="Song", artist="Artist", album="Album")
    payload = presence_payload(track, show_album=True, show_button=False)
    assert payload["state"] == "Artist • Album"
    assert "buttons" not in payload


def test_fields_are_limited_to_discord_maximum():
    track = Track(title="x" * 200, artist="y" * 200)
    payload = presence_payload(track)
    assert len(payload["details"]) == 128
    assert len(payload["state"]) == 128


def test_numeric_winrt_playback_states():
    assert _playback_state(4) == PlaybackState.PLAYING
    assert _playback_state("4") == PlaybackState.PLAYING
    assert _playback_state(5) == PlaybackState.PAUSED
    assert _playback_state("5") == PlaybackState.PAUSED
    assert _playback_state(3) == PlaybackState.STOPPED

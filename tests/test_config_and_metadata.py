from ymrpc.config import Config
from ymrpc.models import Track
from ymrpc.yandex import _match_score, _normalize


class Candidate:
    def __init__(self, title: str, artists: list[str]) -> None:
        self.title = title
        self._artists = artists

    def artists_name(self) -> list[str]:
        return self._artists


def test_public_release_defaults():
    config = Config()
    assert config.valid
    assert config.source_mode == "auto"
    assert config.presence_style == "detailed"
    assert config.show_button is True


def test_metadata_normalization_and_matching():
    track = Track(title="Светлана (Speed Up)", artist="ева грин, нон грата")
    exact = Candidate("Светлана (Speed Up)", ["ева грин", "нон грата"])
    wrong = Candidate("Другая песня", ["Другой исполнитель"])
    assert _normalize("  Светлана (SPEED UP)! ") == "светлана speed up"
    assert _match_score(track, exact) > _match_score(track, wrong)

from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    theme_id: str
    canonical_name: str
    aliases: tuple[str, ...]
    source_title: str
    source_url: str


THEMES = (
    Theme(
        theme_id="blue-eyes",
        canonical_name="青眼",
        aliases=("ブルーアイズ", "Blue-Eyes"),
        source_title="Blue-Eyes",
        source_url="https://yugipedia.com/wiki/Blue-Eyes",
    ),
    Theme(
        theme_id="dark-magician",
        canonical_name="ブラック・マジシャン",
        aliases=("ブラックマジシャン", "Dark Magician"),
        source_title="Dark Magician",
        source_url="https://yugipedia.com/wiki/Dark_Magician",
    ),
)
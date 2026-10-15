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
    Theme(
        theme_id="ignister",
        canonical_name="@Ignister",
        aliases=(),
        source_title="@Ignister",
        source_url="https://yugipedia.com/wiki/@Ignister",
    ),
    Theme(
        theme_id="a-i",
        canonical_name="A.I.",
        aliases=(),
        source_title="A.I.",
        source_url="https://yugipedia.com/wiki/A.I.",
    ),
    Theme(
        theme_id="abyss-actor",
        canonical_name="Abyss Actor",
        aliases=(),
        source_title="Abyss Actor",
        source_url="https://yugipedia.com/wiki/Abyss_Actor",
    ),
    Theme(
        theme_id="abyss-costume",
        canonical_name="Abyss Costume",
        aliases=(),
        source_title="Abyss Costume",
        source_url="https://yugipedia.com/wiki/Abyss_Costume",
    ),
    Theme(
        theme_id="abyss-script",
        canonical_name="Abyss Script",
        aliases=(),
        source_title="Abyss Script",
        source_url="https://yugipedia.com/wiki/Abyss_Script",
    ),
    Theme(
        theme_id="abyss",
        canonical_name="Abyss-",
        aliases=(),
        source_title="Abyss-",
        source_url="https://yugipedia.com/wiki/Abyss-",
    ),
    Theme(
        theme_id="adamancipator",
        canonical_name="Adamancipator",
        aliases=(),
        source_title="Adamancipator",
        source_url="https://yugipedia.com/wiki/Adamancipator",
    ),
    Theme(
        theme_id="advanced-crystal-beast",
        canonical_name="Advanced Crystal Beast",
        aliases=(),
        source_title="Advanced Crystal Beast",
        source_url="https://yugipedia.com/wiki/Advanced_Crystal_Beast",
    ),
    Theme(
        theme_id="aesir",
        canonical_name="Aesir",
        aliases=(),
        source_title="Aesir",
        source_url="https://yugipedia.com/wiki/Aesir",
    ),
    Theme(
        theme_id="aether",
        canonical_name="Aether",
        aliases=(),
        source_title="Aether",
        source_url="https://yugipedia.com/wiki/Aether",
    ),
    Theme(
        theme_id="alchemy-beast",
        canonical_name="Alchemy Beast",
        aliases=(),
        source_title="Alchemy Beast",
        source_url="https://yugipedia.com/wiki/Alchemy_Beast",
    ),
    Theme(
        theme_id="aleister",
        canonical_name="Aleister",
        aliases=(),
        source_title="Aleister",
        source_url="https://yugipedia.com/wiki/Aleister",
    ),
    Theme(
        theme_id="alien",
        canonical_name="Alien",
        aliases=(),
        source_title="Alien",
        source_url="https://yugipedia.com/wiki/Alien",
    ),
    Theme(
        theme_id="alligator",
        canonical_name="Alligator",
        aliases=(),
        source_title="Alligator",
        source_url="https://yugipedia.com/wiki/Alligator",
    ),
    Theme(
        theme_id="allure-queen",
        canonical_name="Allure Queen",
        aliases=(),
        source_title="Allure Queen",
        source_url="https://yugipedia.com/wiki/Allure_Queen",
    ),
    Theme(
        theme_id="ally-of-justice",
        canonical_name="Ally of Justice",
        aliases=(),
        source_title="Ally of Justice",
        source_url="https://yugipedia.com/wiki/Ally_of_Justice",
    ),
    Theme(
        theme_id="altergeist",
        canonical_name="Altergeist",
        aliases=(),
        source_title="Altergeist",
        source_url="https://yugipedia.com/wiki/Altergeist",
    ),
    Theme(
        theme_id="amazement",
        canonical_name="Amazement",
        aliases=(),
        source_title="Amazement",
        source_url="https://yugipedia.com/wiki/Amazement",
    ),
    Theme(
        theme_id="amazoness",
        canonical_name="Amazoness",
        aliases=(),
        source_title="Amazoness",
        source_url="https://yugipedia.com/wiki/Amazoness",
    ),
    Theme(
        theme_id="amorphage",
        canonical_name="Amorphage",
        aliases=(),
        source_title="Amorphage",
        source_url="https://yugipedia.com/wiki/Amorphage",
    ),
    Theme(
        theme_id="ancient-gear",
        canonical_name="Ancient Gear",
        aliases=(),
        source_title="Ancient Gear",
        source_url="https://yugipedia.com/wiki/Ancient_Gear",
    ),
    Theme(
        theme_id="ancient-warriors",
        canonical_name="Ancient Warriors",
        aliases=(),
        source_title="Ancient Warriors",
        source_url="https://yugipedia.com/wiki/Ancient_Warriors",
    ),
    Theme(
        theme_id="angelechy",
        canonical_name="Angelechy",
        aliases=(),
        source_title="Angelechy",
        source_url="https://yugipedia.com/wiki/Angelechy",
    ),
    Theme(
        theme_id="anti",
        canonical_name="Anti",
        aliases=(),
        source_title="Anti",
        source_url="https://yugipedia.com/wiki/Anti",
    ),
    Theme(
        theme_id="apophis",
        canonical_name="Apophis",
        aliases=(),
        source_title="Apophis",
        source_url="https://yugipedia.com/wiki/Apophis",
    ),
)
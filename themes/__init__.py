from dataclasses import dataclass, field


@dataclass
class Theme:
    theme_id: str
    canonical_name: str
    canonical_name_en: str | None = None
    aliases: tuple[str, ...] = field(default_factory=tuple)
    source_title: str | None = None
    source_url: str | None = None
    
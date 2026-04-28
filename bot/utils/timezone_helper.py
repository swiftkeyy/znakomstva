"""Timezone detection helper based on city name."""
from typing import Optional

# Mapping of major Russian cities to their timezones
CITY_TIMEZONE_MAP = {
    # Moscow time (UTC+3)
    "москва": "Europe/Moscow",
    "moscow": "Europe/Moscow",
    "санкт-петербург": "Europe/Moscow",
    "saint petersburg": "Europe/Moscow",
    "спб": "Europe/Moscow",
    "петербург": "Europe/Moscow",
    "нижний новгород": "Europe/Moscow",
    "казань": "Europe/Moscow",
    "kazan": "Europe/Moscow",
    "воронеж": "Europe/Moscow",
    "волгоград": "Europe/Moscow",
    "краснодар": "Europe/Moscow",
    "krasnodar": "Europe/Moscow",
    "сочи": "Europe/Moscow",
    "sochi": "Europe/Moscow",
    "ростов": "Europe/Moscow",
    "rostov": "Europe/Moscow",
    "ростов-на-дону": "Europe/Moscow",
    "тула": "Europe/Moscow",
    "ярославль": "Europe/Moscow",
    "рязань": "Europe/Moscow",
    "калуга": "Europe/Moscow",
    "тверь": "Europe/Moscow",
    "владимир": "Europe/Moscow",
    "иваново": "Europe/Moscow",
    "брянск": "Europe/Moscow",
    "смоленск": "Europe/Moscow",
    "курск": "Europe/Moscow",
    "орёл": "Europe/Moscow",
    "белгород": "Europe/Moscow",
    "липецк": "Europe/Moscow",
    "тамбов": "Europe/Moscow",
    "пенза": "Europe/Moscow",
    "саратов": "Europe/Saratov",
    "самара": "Europe/Samara",
    "samara": "Europe/Samara",
    "ульяновск": "Europe/Ulyanovsk",
    "уфа": "Asia/Yekaterinburg",
    "ufa": "Asia/Yekaterinburg",
    "челябинск": "Asia/Yekaterinburg",
    "chelyabinsk": "Asia/Yekaterinburg",
    "екатеринбург": "Asia/Yekaterinburg",
    "yekaterinburg": "Asia/Yekaterinburg",
    "пермь": "Asia/Yekaterinburg",
    "perm": "Asia/Yekaterinburg",
    "тюмень": "Asia/Yekaterinburg",
    "омск": "Asia/Omsk",
    "omsk": "Asia/Omsk",
    "новосибирск": "Asia/Novosibirsk",
    "novosibirsk": "Asia/Novosibirsk",
    "томск": "Asia/Tomsk",
    "кемерово": "Asia/Novokuznetsk",
    "красноярск": "Asia/Krasnoyarsk",
    "krasnoyarsk": "Asia/Krasnoyarsk",
    "иркутск": "Asia/Irkutsk",
    "irkutsk": "Asia/Irkutsk",
    "улан-удэ": "Asia/Irkutsk",
    "чита": "Asia/Chita",
    "якутск": "Asia/Yakutsk",
    "yakutsk": "Asia/Yakutsk",
    "владивосток": "Asia/Vladivostok",
    "vladivostok": "Asia/Vladivostok",
    "хабаровск": "Asia/Vladivostok",
    "khabarovsk": "Asia/Vladivostok",
    "магадан": "Asia/Magadan",
    "петропавловск-камчатский": "Asia/Kamchatka",
    
    # Other countries
    "киев": "Europe/Kiev",
    "kiev": "Europe/Kiev",
    "минск": "Europe/Minsk",
    "minsk": "Europe/Minsk",
    "алматы": "Asia/Almaty",
    "almaty": "Asia/Almaty",
    "ташкент": "Asia/Tashkent",
    "tashkent": "Asia/Tashkent",
    "баку": "Asia/Baku",
    "baku": "Asia/Baku",
    "тбилиси": "Asia/Tbilisi",
    "tbilisi": "Asia/Tbilisi",
    "ереван": "Asia/Yerevan",
    "yerevan": "Asia/Yerevan",
}


def detect_timezone_from_city(city: Optional[str]) -> str:
    """
    Detect timezone from city name.
    
    Args:
        city: City name (can be in Russian or English)
        
    Returns:
        Timezone string (e.g., 'Europe/Moscow'). Defaults to 'UTC' if not found.
    """
    if not city:
        return "UTC"
    
    # Normalize city name
    city_lower = city.lower().strip()
    
    # Try exact match
    if city_lower in CITY_TIMEZONE_MAP:
        return CITY_TIMEZONE_MAP[city_lower]
    
    # Try partial match (for cases like "Москва, Россия")
    for city_key, timezone in CITY_TIMEZONE_MAP.items():
        if city_key in city_lower:
            return timezone
    
    # Default to Moscow time for Russian-sounding cities
    if any(char in city_lower for char in "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"):
        return "Europe/Moscow"
    
    # Default to UTC
    return "UTC"

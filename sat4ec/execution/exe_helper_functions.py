"""Get name of car brand."""


BRAND_LENGTH = 2


def get_name(name: str) -> str:
    """Get name of car brand."""
    brand = name.split("_")[0]
    location = name.split("_")[1]

    if len(name.split("_")) > BRAND_LENGTH:
        raise ValueError(f"The name of the AOI {name} does not follow scheme BRAND_LOCATION.")

    return f"{brand.upper()} {location.title()}"

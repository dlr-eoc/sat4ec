def get_name(name=None):
    brand = name.split("_")[0]
    location = name.split("_")[1]

    if len(name.split("_")) > 2:
        raise ValueError(
            f"The name of the AOI {name} does not follow scheme BRAND_LOCATION."
        )

    else:
        return f"{brand.upper()} {location.title()}"

def clean_value(value):
    if value is None:
        return None
    if isinstance(value, str):
        return value.strip().replace("\x00", "")
    return value


def clean_form(form_data):
    return {key: clean_value(value) for key, value in form_data.items()}

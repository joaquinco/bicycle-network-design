def format_run_time_seconds(duration):
    """
    Given a numeric duration returns a string
    HH:MM:SS
    """
    duration = int(duration)
    hours = duration // 3600
    minutes = (duration - hours * 3600) // 60
    seconds = duration - hours * 3600 - minutes * 60

    return f'{hours:02}:{minutes:02}:{seconds:02}'

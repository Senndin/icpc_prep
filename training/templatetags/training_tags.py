from django import template

register = template.Library()


@register.filter
def rating_class(rating):
    """
    Повертає CSS-клас бейджа складності.

    :param rating: рейтинг задачі
    :return: назва CSS-класу
    """
    if not rating:
        return "bg-light text-muted"
    if rating < 1200:
        return "r-easy"
    if rating < 1800:
        return "r-mid"
    return "r-hard"


@register.filter
def initials(user):
    """
    Формує ініціали користувача для аватара.

    :param user: користувач
    :return: дві літери
    """
    if user.first_name and user.last_name:
        return (user.first_name[0] + user.last_name[0]).upper()
    return user.username[:2].upper()

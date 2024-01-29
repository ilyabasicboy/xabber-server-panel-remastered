from xabber_server_panel.circles.models import Circle
from xabber_server_panel.users.models import User


def check_circles(user: User, host: str) -> None:
    """
        Check registered circles and create
        if it doesn't exist in django db
    """
    try:
        registered_circles = user.api.get_groups({"host": host}).get('circles')
    except:
        registered_circles = []

    if registered_circles:
        # Get a list of existing circles from the Circle model
        existing_circles = Circle.objects.values_list('circle', flat=True)

        # Filter the circle list to exclude existing circles
        unknown_circles = [circle for circle in registered_circles if circle not in existing_circles]

        if unknown_circles:
            circles_to_create = [
                Circle(
                    circle=circle,
                    host=host,
                )
                for circle in unknown_circles
            ]
            Circle.objects.bulk_create(circles_to_create)

        # get unregistered circles in db and delete
        circles_to_delete = Circle.objects.filter(host=host).exclude(circle__in=registered_circles)
        if circles_to_delete:
            circles_to_delete.delete()
from xabber_server_panel.base_modules.circles.models import Circle
from xabber_server_panel.base_modules.users.models import User


def check_circles(user: User, host: str) -> None:
    """
        Check registered circles and create
        if it doesn't exist in django db
    """
    try:
        registered_circles = user.api.get_circles({"host": host}).get('circles')
    except:
        registered_circles = []

    if registered_circles:
        # Get a list of existing circles from the Circle model
        existing_circles = Circle.objects.values_list('circle', flat=True)

        # Filter the circle list to exclude existing circles
        unknown_circles = [circle for circle in registered_circles if circle not in existing_circles]

        if unknown_circles:
            circles_to_create = []
            for circle in unknown_circles:
                circle_info = user.api.get_circles_info(
                    {
                        'host': host,
                        'circle': circle
                    }
                )

                # parse displayed groups
                contacts = circle_info.get('displayed_groups')
                str_contacts = ','.join(contacts)
                circles_to_create += [
                    Circle(
                        circle=circle,
                        name=circle_info.get('name', ''),
                        description=circle_info.get('description', ''),
                        all_users=circle_info.get('all_users', False),
                        host=host,
                        subscribes=str_contacts
                    )
                ]
            Circle.objects.bulk_create(circles_to_create)

        # get unregistered circles in db and delete
        circles_to_delete = Circle.objects.filter(host=host).exclude(circle__in=registered_circles)
        if circles_to_delete:
            circles_to_delete.delete()
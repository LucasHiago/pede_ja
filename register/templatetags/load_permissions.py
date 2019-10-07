from django import template

register = template.Library()


@register.filter
def permissions(user, permissions=None):
    # Super admin
    if user.is_superuser:
        return True

    # Administrador estabelecimento
    if user.groups.first().id == 1:
        return True

    # Demais casos
    if permissions:
        permission_list = [int(permission) for permission in permissions.split(',')]
        return user.groups.first().id in permission_list

    return False

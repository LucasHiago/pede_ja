from django.core.exceptions import PermissionDenied


class PassRequestUserMixin:
    def get_form_kwargs(self):
        kwargs = super(PassRequestUserMixin, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


def checker_permissions(user, permission, query):
    if user.employee.establishment.enabled is False:
        raise PermissionDenied

    if user.has_perm(permission) and query:
        return True
    raise PermissionDenied

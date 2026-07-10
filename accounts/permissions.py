from rest_framework import permissions


def _is_authenticated_user(user):
    return bool(user and user.is_authenticated)


def _has_any_role(user, allowed_roles):
    if not _is_authenticated_user(user):
        return False

    if user.is_superuser or user.is_staff:
        return True

    return user.role in allowed_roles


def _reservation_is_locked_for_operations(reservation):
    if not reservation:
        return False

    status = str(getattr(reservation, "status", "")).strip().upper()
    return bool(getattr(reservation, "is_locked_by_finance", False)) or status == "CONFIRMED"


class IsAdminRole(permissions.BasePermission):
    """
    Allows access to Superusers, Django Staff, and ADMIN role.
    """

    def has_permission(self, request, view):
        user = request.user

        if not _is_authenticated_user(user):
            return False

        return _has_any_role(user, {user.RoleChoices.ADMIN})


class IsFinanceRole(permissions.BasePermission):
    """
    Allows access to Superusers, Django Staff, ADMIN, and FINANCE roles.
    """

    def has_permission(self, request, view):
        user = request.user

        if not _is_authenticated_user(user):
            return False

        return _has_any_role(
            user,
            {
                user.RoleChoices.ADMIN,
                user.RoleChoices.FINANCE,
            },
        )


class IsInventoryRole(permissions.BasePermission):
    """
    Allows access to Superusers, Django Staff, ADMIN, and INVENTORY roles.
    """

    def has_permission(self, request, view):
        user = request.user

        if not _is_authenticated_user(user):
            return False

        return _has_any_role(
            user,
            {
                user.RoleChoices.ADMIN,
                user.RoleChoices.INVENTORY,
            },
        )


class IsReservationRole(permissions.BasePermission):
    """
    Allows access to Superusers, Django Staff, ADMIN, and RESERVATION roles.
    """

    def has_permission(self, request, view):
        user = request.user

        if not _is_authenticated_user(user):
            return False

        return _has_any_role(
            user,
            {
                user.RoleChoices.ADMIN,
                user.RoleChoices.RESERVATION,
            },
        )


class IsSalesRole(permissions.BasePermission):
    """
    Allows access to Superusers, Django Staff, ADMIN, and SALES roles.
    """

    def has_permission(self, request, view):
        user = request.user

        if not _is_authenticated_user(user):
            return False

        return _has_any_role(
            user,
            {
                user.RoleChoices.ADMIN,
                user.RoleChoices.SALES,
            },
        )


class IsReservationWorkflowRole(permissions.BasePermission):
    """
    Allows reservation workflow visibility to ADMIN, SALES, RESERVATION, and FINANCE roles.

    This is useful for reservation screens where multiple departments need access.
    Object-level permissions can still restrict editing.
    """

    def has_permission(self, request, view):
        user = request.user

        if not _is_authenticated_user(user):
            return False

        return _has_any_role(
            user,
            {
                user.RoleChoices.ADMIN,
                user.RoleChoices.SALES,
                user.RoleChoices.RESERVATION,
                user.RoleChoices.FINANCE,
            },
        )


class IsReservationOperationsRole(permissions.BasePermission):
    """
    Allows reservation write operations to ADMIN, SALES, and RESERVATION roles.

    FINANCE is excluded from normal operational edits.
    Finance-specific editing is controlled separately by object-level rules.
    """

    def has_permission(self, request, view):
        user = request.user

        if not _is_authenticated_user(user):
            return False

        return _has_any_role(
            user,
            {
                user.RoleChoices.ADMIN,
                user.RoleChoices.SALES,
                user.RoleChoices.RESERVATION,
            },
        )


class ReadOnlyOrReservationOperationsRole(permissions.BasePermission):
    """
    Allows read access to reservation workflow roles.
    Allows write access only to ADMIN, SALES, and RESERVATION roles.
    Blocks writes on objects linked to finance-locked reservations.
    """

    def has_permission(self, request, view):
        user = request.user

        if not _is_authenticated_user(user):
            return False

        if request.method in permissions.SAFE_METHODS:
            return _has_any_role(
                user,
                {
                    user.RoleChoices.ADMIN,
                    user.RoleChoices.SALES,
                    user.RoleChoices.RESERVATION,
                    user.RoleChoices.FINANCE,
                },
            )

        return _has_any_role(
            user,
            {
                user.RoleChoices.ADMIN,
                user.RoleChoices.SALES,
                user.RoleChoices.RESERVATION,
            },
        )

    def has_object_permission(self, request, view, obj):
        user = request.user

        if not _is_authenticated_user(user):
            return False

        if request.method in permissions.SAFE_METHODS:
            return True

        if user.is_superuser or user.is_staff or user.role == user.RoleChoices.ADMIN:
            return True

        related_reservation = getattr(obj, "reservation", None)

        if related_reservation and _reservation_is_locked_for_operations(related_reservation):
            return False

        return user.role in {
            user.RoleChoices.SALES,
            user.RoleChoices.RESERVATION,
        }


class IsReservationEditorOrReadOnlyIfLocked(permissions.BasePermission):
    """
    Object-level permission for Reservation records.

    Read access:
    - Allowed for any user accepted by the view-level permission.

    Write access:
    - ADMIN, Superuser, and Django Staff can always edit.
    - FINANCE can edit only when the reservation is locked by finance.
    - SALES and RESERVATION can edit only when the reservation is not locked by finance.
    """

    def has_permission(self, request, view):
        return _is_authenticated_user(request.user)

    def has_object_permission(self, request, view, obj):
        user = request.user

        if not _is_authenticated_user(user):
            return False

        if request.method in permissions.SAFE_METHODS:
            return True

        if user.is_superuser or user.is_staff or user.role == user.RoleChoices.ADMIN:
            return True

        is_locked_by_finance = getattr(obj, "is_locked_by_finance", False)
        is_locked_for_operations = _reservation_is_locked_for_operations(obj)

        if user.role == user.RoleChoices.FINANCE:
            return is_locked_by_finance

        if user.role in {
            user.RoleChoices.SALES,
            user.RoleChoices.RESERVATION,
        }:
            return not is_locked_for_operations

        return False
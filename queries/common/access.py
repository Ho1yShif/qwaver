import secrets

from django.core.exceptions import PermissionDenied

from queries.models import Database, Query
from users.models import UserOrganization


def get_org_databases(self):
    return get_user_org_databases(self.request.user)


def get_user_org_databases(user):
    org = user.profile.selected_organization
    if org is None:
        raise PermissionDenied("Need a defined organization for profile of user " + user.username)
    databases = Database.objects.filter(organization=org)
    return databases


def get_most_recent_database(self):
    user = self.request.user
    return get_users_most_recent_database(user)


def get_users_most_recent_database(user):
    databases = get_user_org_databases(user)
    if databases is not None:
        most_recent_query = Query.objects.filter(database__in=databases, author=user) \
            .order_by('-last_run_date', '-date_created').first()
        if most_recent_query is not None:
            return most_recent_query.database
    return databases[0]


def user_can_access_query(user, query):
    user_can_access_database(user, query.database)


def user_can_access_database(user, database):
    user_orgs = UserOrganization.objects.filter(user=user)
    if any(database.organization.id == user_org.organization.id for user_org in user_orgs):
        # if a user is accessing a new org, they are now navigating within that org
        user.profile.selected_organization = database.organization
        user.profile.save()
    else:
        raise PermissionDenied(
            "user not part of the organization to which the database belongs")


def user_can_access_org(user, org):
    user_orgs = UserOrganization.objects.filter(user=user)
    if not any(user_org.organization.id == org.id for user_org in user_orgs):
        raise PermissionDenied(
            "user not member of organization: " + str(org.id)
        )


# https://stackoverflow.com/questions/34897740/whats-the-simplest-and-safest-method-to-generate-a-api-key-and-secret-in-python
def create_api_key():
    return secrets.token_urlsafe(16)
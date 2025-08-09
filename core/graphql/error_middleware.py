from __future__ import annotations
from graphql import GraphQLError

from authentication.services.user_service import RegistrationError


class DomainErrorMiddleware:
    """Translate domain/service exceptions into GraphQL-friendly errors.

    Add this middleware class to GRAPHENE["MIDDLEWARE"] in settings.py.
    """

    def on_error(self, error: Exception):  # For consistency with some middleware patterns
        return self.resolve(None, None, None, error)

    def resolve(self, next, root, info, **args):  # type: ignore[override]
        try:
            return next(root, info, **args)
        except RegistrationError as exc:
            raise GraphQLError(str(exc), extensions={"code": "REGISTRATION_ERROR"})
        except Exception:
            # Re-raise; let default formatting happen. Could log here.
            raise

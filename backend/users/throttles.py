from rest_framework.throttling import SimpleRateThrottle


class LoginUsernameThrottle(SimpleRateThrottle):
    """Limita los intentos de login por nombre de usuario (frena adivinar la clave de una cuenta)."""

    scope = "login_username"

    def get_cache_key(self, request, view):
        username = str(request.data.get("username", "")).strip().lower()
        if not username:
            return None
        return self.cache_format % {"scope": self.scope, "ident": username}


class LoginIPThrottle(SimpleRateThrottle):
    """Limita los intentos de login por IP (frena probar muchas cuentas desde un mismo origen).

    Es más alto que el límite por usuario porque varios operarios pueden compartir la IP de la oficina.
    """

    scope = "login_ip"

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": self.get_ident(request)}

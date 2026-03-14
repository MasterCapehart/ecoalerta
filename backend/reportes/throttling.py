from rest_framework.throttling import UserRateThrottle, AnonRateThrottle

class ReportSubmissionProRateThrottle(UserRateThrottle):
    """
    Límite estricto para usuarios autenticados al crear reportes.
    Evita que un usuario inunde el sistema.
    """
    scope = 'report_submission_pro'

class ReportSubmissionAnonThrottle(AnonRateThrottle):
    """
    Límite muy estricto para usuarios anónimos (basado en IP).
    Evita spam de bots.
    """
    scope = 'report_submission_anon'

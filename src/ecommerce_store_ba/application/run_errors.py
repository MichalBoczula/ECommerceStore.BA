class RunNotFoundError(Exception):
    pass


class RunConflictError(Exception):
    pass


class RunBusyError(Exception):
    pass


class RunNotReadyError(Exception):
    pass


class RunEvidenceError(Exception):
    pass


class AgentUnavailableError(Exception):
    pass


class AgentResponseError(Exception):
    pass


class JiraUnavailableError(Exception):
    pass


class JiraRejectedError(JiraUnavailableError):
    """Jira explicitly rejected a request before a confirmed write."""


class JiraPublicationPendingError(Exception):
    pass

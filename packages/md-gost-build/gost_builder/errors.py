"""Errors a document author can resolve before retrying a build."""


class BuildError(Exception):
    """A build could not complete with the supplied sources and settings."""

from __future__ import annotations


class Statement:
    ...


class StoppingStatement(Statement):
    ...


class ContinueStatement(StoppingStatement):
    ...


class BreakStatement(StoppingStatement):
    ...

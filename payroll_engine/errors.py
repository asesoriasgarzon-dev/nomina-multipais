"""Errores tipificados del motor. Ningún fallo del motor debe degradarse a un
resultado silenciosamente incorrecto: todo lo que no se puede calcular con
respaldo normativo se expresa como una de estas excepciones."""


class PayrollError(Exception):
    code = "PAYROLL_ERROR"

    def __init__(self, message, *, details=None):
        super().__init__(message)
        self.message = message
        self.details = details or []

    def __str__(self):
        if self.details:
            return f"{self.message}: " + "; ".join(str(d) for d in self.details)
        return self.message


class SchemaError(PayrollError):
    code = "SCHEMA_ERROR"


class InputValidationError(PayrollError):
    code = "INPUT_VALIDATION_ERROR"


class MissingInputError(InputValidationError):
    code = "MISSING_INPUT"


class MissingRuleError(PayrollError):
    code = "MISSING_RULE"


class MissingReferenceError(PayrollError):
    code = "MISSING_REFERENCE"


class ConflictingReferenceError(PayrollError):
    code = "CONFLICTING_REFERENCE"


class ConflictingRulesError(PayrollError):
    code = "CONFLICTING_RULES"


class StraddleError(PayrollError):
    code = "RULE_CHANGE_INSIDE_PERIOD"


class MissingAnchorDateError(PayrollError):
    code = "MISSING_ANCHOR_DATE"


class GraphError(PayrollError):
    code = "GRAPH_ERROR"


class CycleError(GraphError):
    code = "DEPENDENCY_CYCLE"


class MissingDependencyError(GraphError):
    code = "MISSING_DEPENDENCY"


class CapabilityError(PayrollError):
    code = "CAPABILITY_ERROR"


class IncompleteRunError(PayrollError):
    code = "INCOMPLETE_RUN"

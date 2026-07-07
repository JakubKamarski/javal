from __future__ import annotations

from validator.java.rules.base import JavaRule
from validator.java.rules.naming.constant_upper_snake import ConstantUpperSnakeCaseRule
from validator.java.rules.naming.method_bare_participle import MethodBareParticipleRule
from validator.java.rules.naming.method_map_style import MethodMapStyleNameRule
from validator.java.rules.naming.method_verb_prefix import MethodVerbPrefixRule
from validator.java.rules.naming.variable_collection_type import VariableCollectionTypeInNameRule
from validator.java.rules.naming.variable_hungarian_notation import VariableHungarianNotationRule
from validator.java.rules.unused_import import UnusedImportRule


def default_java_rules() -> list[JavaRule]:
    return [
        UnusedImportRule(),
        MethodVerbPrefixRule(),
        MethodMapStyleNameRule(),
        MethodBareParticipleRule(),
        VariableCollectionTypeInNameRule(),
        VariableHungarianNotationRule(),
        ConstantUpperSnakeCaseRule(),
    ]

from __future__ import annotations

from validator.java.rules.base import JavaRule, TreeJavaRule
from validator.java.rules.naming.constant_upper_snake import ConstantUpperSnakeCaseRule
from validator.java.rules.naming.method_bare_participle import MethodBareParticipleRule
from validator.java.rules.naming.method_map_style import MethodMapStyleNameRule
from validator.java.rules.naming.local_variable_optional_prefix import LocalVariableOptionalPrefixRule
from validator.java.rules.naming.method_verb_prefix import MethodVerbPrefixRule
from validator.java.rules.naming.variable_collection_type import VariableCollectionTypeInNameRule
from validator.java.rules.naming.variable_hungarian_notation import VariableHungarianNotationRule
from validator.java.rules.style.local_variable_no_var import LocalVariableNoVarRule
from validator.java.rules.testing.duplicate_it_and_test import DuplicateItAndTestRule
from validator.java.rules.testing.missing_test_class import MissingTestClassRule
from validator.java.rules.testing.when_generic_variable import TestWhenGenericVariableRule
from validator.java.rules.unused_import import UnusedImportRule


def default_java_rules() -> list[JavaRule]:
    return [
        UnusedImportRule(),
        MethodVerbPrefixRule(),
        MethodMapStyleNameRule(),
        MethodBareParticipleRule(),
        VariableCollectionTypeInNameRule(),
        VariableHungarianNotationRule(),
        LocalVariableOptionalPrefixRule(),
        ConstantUpperSnakeCaseRule(),
        LocalVariableNoVarRule(),
        TestWhenGenericVariableRule(),
    ]


def default_tree_java_rules() -> list[TreeJavaRule]:
    return [
        DuplicateItAndTestRule(),
        MissingTestClassRule(),
    ]

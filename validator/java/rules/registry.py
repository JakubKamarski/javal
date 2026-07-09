from __future__ import annotations

from pathlib import Path

from validator.java.rules.base import JavaRule, RuleMeta, TreeJavaRule
from validator.java.rules.naming.constant_upper_snake import ConstantUpperSnakeCaseRule
from validator.java.rules.naming.method_bare_participle import MethodBareParticipleRule
from validator.java.rules.naming.method_map_style import MethodMapStyleNameRule
from validator.java.rules.naming.local_variable_optional_prefix import LocalVariableOptionalPrefixRule
from validator.java.rules.naming.method_verb_prefix import MethodVerbPrefixRule
from validator.java.rules.naming.variable_collection_type import VariableCollectionTypeInNameRule
from validator.java.rules.naming.variable_hungarian_notation import VariableHungarianNotationRule
from validator.java.rules.style.disallowed_comment import DisallowedCommentRule
from validator.java.rules.style.generic_type_nosonar import GenericTypeNosonarRule
from validator.java.rules.style.local_variable_no_var import LocalVariableNoVarRule
from validator.java.rules.entity.serial_version_uid_on_change import EntitySerialVersionUidOnChangeRule
from validator.java.rules.testing.duplicate_it_and_test import DuplicateItAndTestRule
from validator.java.rules.testing.missing_test_class import MissingTestClassRule
from validator.java.rules.testing.when_generic_variable import TestWhenGenericVariableRule
from validator.java.rules.unused_import import UnusedImportRule

RULE_DESCRIPTIONS: dict[str, str] = {
    "unused-imports": "Import declared but not referenced",
    "java-naming-method-verb-prefix": "Method must start with an action verb (with framework exemptions)",
    "java-naming-method-map-style": "Map-style method names without verb prefix",
    "java-naming-method-bare-participle": "Bare participles/adjectives (distinct, sorted, empty, …)",
    "java-naming-variable-collection-type": "List / Set / Map embedded in variable name",
    "java-naming-variable-hungarian": "Hungarian notation (strName, intCount, …)",
    "java-naming-local-variable-optional-prefix": "Optional<...> locals must use the optional prefix",
    "java-naming-constant-upper-snake": "Constants must use UPPER_SNAKE_CASE",
    "java-local-variable-no-var": "Local variables must use explicit types (var is forbidden)",
    "java-clean-code-comment": "Only NOSONAR, deprecation, public API javadoc, GWT markers, and task-referenced TODO/FIXME are allowed",
    "java-sonar-generic-type-nosonar": "Non-standard generic type parameter names require NOSONAR on the type header or method signature",
    "java-testing-when-generic-variable": "// WHEN locals must be descriptive; warns on generic names like result",
    "java-testing-duplicate-it-and-test": "Same subject has both *Test and *IT files in the repo",
    "java-testing-missing-test-class": "Production classes covered by testing rules must have the required *IT or *Test counterpart; repositories only when task changes custom @Query methods; internal *Service exempt when an ancestor in the injection chain has its required *IT",
    "java-jpa-entity-serial-version-uid": "JPA entity persistent field changes must update serialVersionUID",
}

RULE_MODULE_EXCLUDES = frozenset(
    {
        "__init__.py",
        "_support.py",
        "_template.py",
        "base.py",
        "registry.py",
    }
)


def enrich_meta(rule: JavaRule | TreeJavaRule) -> RuleMeta:
    base = rule.meta
    description = RULE_DESCRIPTIONS.get(rule.check_id, base.description)
    if description == base.description:
        return base
    return RuleMeta(
        check_id=base.check_id,
        category=base.category,
        description=description,
        scope=base.scope,
        tree_scope=base.tree_scope,
    )


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
        DisallowedCommentRule(),
        GenericTypeNosonarRule(),
        TestWhenGenericVariableRule(),
    ]


def default_tree_java_rules() -> list[TreeJavaRule]:
    return [
        DuplicateItAndTestRule(),
        MissingTestClassRule(),
        EntitySerialVersionUidOnChangeRule(),
    ]


def all_registered_rules() -> list[JavaRule | TreeJavaRule]:
    return [*default_java_rules(), *default_tree_java_rules()]


def list_registered_rule_meta() -> list[RuleMeta]:
    return [enrich_meta(rule) for rule in all_registered_rules()]


def discover_rule_module_paths(rules_root: Path | None = None) -> list[Path]:
    root = rules_root or Path(__file__).resolve().parent
    modules: list[Path] = []
    for path in sorted(root.rglob("*.py")):
        if path.name in RULE_MODULE_EXCLUDES:
            continue
        if path.name.startswith("_") and path.name != "_template.py":
            continue
        modules.append(path)
    return modules

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
from validator.java.rules.style.apache_commons_validate import ApacheCommonsValidateRule
from validator.java.rules.style.disallowed_comment import DisallowedCommentRule
from validator.java.rules.style.empty_collection_static_factory import EmptyCollectionStaticFactoryRule
from validator.java.rules.style.generic_type_nosonar import GenericTypeNosonarRule
from validator.java.rules.style.local_variable_no_var import LocalVariableNoVarRule
from validator.java.rules.style.lombok_required_args_constructor import LombokRequiredArgsConstructorRule
from validator.java.rules.style.lombok_static_factory import LombokStaticFactoryRule
from validator.java.rules.style.type_header_one_line import TypeHeaderOneLineRule
from validator.java.rules.entity.serial_version_uid_on_change import EntitySerialVersionUidOnChangeRule
from validator.java.rules.spring.configuration_proxy_bean_methods import (
    SpringConfigurationProxyBeanMethodsRule,
)
from validator.java.rules.testing.duplicate_it_and_test import DuplicateItAndTestRule
from validator.java.rules.testing.duplicate_test_method import DuplicateTestMethodRule
from validator.java.rules.testing.exception_capture import ExceptionCaptureRule
from validator.java.rules.testing.gwt_sections import TestGwtSectionsRule
from validator.java.rules.testing.missing_test_class import MissingTestClassRule
from validator.java.rules.testing.test_method_prefix import TestMethodPrefixRule
from validator.java.rules.testing.test_owner_construction import TestOwnerConstructionRule
from validator.java.rules.testing.when_generic_variable import TestWhenGenericVariableRule
from validator.java.rules.unused_import import UnusedImportRule

RULE_DESCRIPTIONS: dict[str, str] = {
    "unused-imports": "Import declared but not referenced",
    "java-naming-method-verb-prefix": "Method must start with an action verb (with framework, static-factory, and MethodSource exemptions)",
    "java-naming-method-map-style": "Map-style method names without verb prefix",
    "java-naming-method-bare-participle": "Bare participles/adjectives (distinct, sorted, empty, …)",
    "java-naming-variable-collection-type": "List / Set / Map embedded in variable name",
    "java-naming-variable-hungarian": "Hungarian notation (strName, intCount, …)",
    "java-naming-local-variable-optional-prefix": "Optional<...> locals must use the optional prefix",
    "java-naming-constant-upper-snake": "Constants must use UPPER_SNAKE_CASE",
    "java-local-variable-no-var": "Local variables must use explicit types (var is forbidden)",
    "java-lombok-required-args-constructor": "Constructors that only assign required fields should use Lombok @RequiredArgsConstructor",
    "java-lombok-static-factory": "Direct static factories paired with Lombok-eligible constructors should use @RequiredArgsConstructor(staticName = ...)",
    "java-clean-code-comment": "Only NOSONAR, deprecation, public API javadoc, GWT markers, and task-referenced TODO/FIXME are allowed",
    "java-sonar-generic-type-nosonar": "Non-standard generic type parameter names require NOSONAR on the type header or method signature",
    "java-style-type-header-one-line": "Type declaration headers that fit within 120 columns must remain on one line",
    "java-style-empty-collection-static-factory": "Empty List.of(), Map.of(), and Set.of() must use Collections.empty*()",
    "java-style-apache-commons-validate": "Direct if guards that only throw IllegalArgumentException must use Apache Commons Lang Validate",
    "java-testing-when-generic-variable": "// WHEN locals must be descriptive; warns on generic names like result",
    "java-testing-gwt-sections": "Test methods must contain one // GIVEN, // WHEN, and // THEN section in order",
    "java-testing-test-method-prefix": "Test method name must start with the method invoked in // WHEN",
    "java-testing-test-owner-construction": "Tested instance must be initialized in // GIVEN or as a directly initialized final test-class field",
    "java-testing-duplicate-test-method": "Equivalent normal-response or exception-path tests with the same resolvable invocation signature must be parameterized",
    "java-testing-exception-capture": "Exception tests must capture Throwable exception with catchThrowable in // WHEN",
    "java-testing-duplicate-it-and-test": "Task introduces both *Test and *IT files for the same subject",
    "java-testing-missing-test-class": "Production classes covered by testing rules must have the required *IT or *Test counterpart; repositories only when task changes custom @Query methods; an IT requirement is satisfied by any <Subject>*IT variant (e.g. *MockedIT); internal *Service exempt when an ancestor in the injection chain has its required *IT, and framework-free *Service (no Spring boundary annotation) exempt when it has a unit *Test",
    "java-jpa-entity-serial-version-uid": "JPA entity persistent field changes must update serialVersionUID",
    "spring-configuration-proxy-bean-methods": "@Configuration with no inter-bean method calls should set proxyBeanMethods = false; proxyBeanMethods = false is unsafe when a @Bean method calls another @Bean method of the same class",
}

RULE_MODULE_EXCLUDES = frozenset(
    {
        "__init__.py",
        "_support.py",
        "_template.py",
        "applicability.py",
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
        file_applicability=base.file_applicability,
        tree_file_applicability=base.tree_file_applicability,
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
        LombokRequiredArgsConstructorRule(),
        LombokStaticFactoryRule(),
        DisallowedCommentRule(),
        GenericTypeNosonarRule(),
        TypeHeaderOneLineRule(),
        EmptyCollectionStaticFactoryRule(),
        ApacheCommonsValidateRule(),
        TestWhenGenericVariableRule(),
        TestGwtSectionsRule(),
        TestMethodPrefixRule(),
        TestOwnerConstructionRule(),
        DuplicateTestMethodRule(),
        ExceptionCaptureRule(),
        SpringConfigurationProxyBeanMethodsRule(),
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

from __future__ import annotations

from validator.java.ast.modifiers import annotation_simple_name, node_has_annotation
from validator.java.context import JavaFileContext
from validator.java.parser import walk_nodes
from validator.java.rules.base import JavaRule, RuleViolation

_CONFIGURATION_ANNOTATION = "Configuration"
_BEAN_ANNOTATION = "Bean"
_PROXY_ATTRIBUTE = "proxyBeanMethods"


class SpringConfigurationProxyBeanMethodsRule(JavaRule):
    """@Configuration proxy mode advisor.

    Full mode (the default, proxyBeanMethods = true) wraps a @Configuration class in a
    CGLIB proxy so that a @Bean method calling another @Bean method of the same class
    returns the shared singleton. That proxy costs startup time and memory. Lite mode
    (proxyBeanMethods = false) skips it, but then such an inter-bean method call returns a
    fresh instance instead of the managed bean.

    Safe condition (allowed for sure): a @Configuration class whose @Bean methods never call
    another @Bean method of the same class. When that holds and the attribute is left at its
    default, recommend proxyBeanMethods = false. When proxyBeanMethods = false is set but an
    inter-bean method call exists, flag it as an unsafe configuration.
    """

    file_applicability = "production"

    @property
    def check_id(self) -> str:
        return "spring-configuration-proxy-bean-methods"

    def apply(self, context: JavaFileContext) -> list[RuleViolation]:
        violations: list[RuleViolation] = []

        for class_node in context.walk("class_declaration"):
            annotation = _configuration_annotation(context, class_node)
            if annotation is None:
                continue

            bean_methods = _bean_methods(context, class_node)
            if not bean_methods:
                continue

            bean_names = {name for name, _node in bean_methods}
            inter_bean_call = _first_inter_bean_call(context, bean_methods, bean_names)
            proxy_value = _proxy_bean_methods_value(context, annotation)

            if proxy_value == "false":
                if inter_bean_call is not None:
                    called, call_line = inter_bean_call
                    violations.append(
                        RuleViolation(
                            summary=(
                                "@Configuration(proxyBeanMethods = false) is unsafe here: a @Bean "
                                f"method calls @Bean method '{called}()' in the same class. Lite mode "
                                "skips the CGLIB proxy, so each such call builds a new instance instead "
                                "of the managed singleton."
                            ),
                            line=call_line,
                            suggestion=(
                                "Drop proxyBeanMethods = false (keep full mode), or inject the "
                                f"referenced bean as a method parameter instead of calling '{called}()'."
                            ),
                        )
                    )
                continue

            if proxy_value is None and inter_bean_call is None:
                violations.append(
                    RuleViolation(
                        summary=(
                            f"@Configuration class '{_class_name(context, class_node)}' has no "
                            "inter-bean method calls, so it is safe to set "
                            "proxyBeanMethods = false and skip the CGLIB proxy."
                        ),
                        line=annotation.start_point[0] + 1,
                        suggestion="Use @Configuration(proxyBeanMethods = false) to reduce proxy overhead.",
                    )
                )

        return violations


def _configuration_annotation(context: JavaFileContext, class_node):
    modifiers = next((child for child in class_node.children if child.type == "modifiers"), None)
    if modifiers is None:
        return None
    for child in modifiers.children:
        if child.type not in ("marker_annotation", "annotation"):
            continue
        if annotation_simple_name(context, child) == _CONFIGURATION_ANNOTATION:
            return child
    return None


def _proxy_bean_methods_value(context: JavaFileContext, annotation_node) -> str | None:
    """Return "true"/"false" for an explicit proxyBeanMethods attribute, or None when absent."""
    argument_list = next(
        (child for child in annotation_node.children if child.type == "annotation_argument_list"),
        None,
    )
    if argument_list is None:
        return None
    for pair in argument_list.children:
        if pair.type != "element_value_pair":
            continue
        key = next((child for child in pair.children if child.type == "identifier"), None)
        if key is None or context.text(key) != _PROXY_ATTRIBUTE:
            continue
        return context.text(pair.children[-1]).strip()
    return None


def _bean_methods(context: JavaFileContext, class_node) -> list[tuple[str, object]]:
    class_body = next((child for child in class_node.children if child.type == "class_body"), None)
    if class_body is None:
        return []
    methods: list[tuple[str, object]] = []
    for member in class_body.children:
        if member.type != "method_declaration":
            continue
        if not node_has_annotation(context, member, _BEAN_ANNOTATION):
            continue
        name = _method_name(context, member)
        if name is not None:
            methods.append((name, member))
    return methods


def _first_inter_bean_call(
    context: JavaFileContext,
    bean_methods: list[tuple[str, object]],
    bean_names: set[str],
) -> tuple[str, int] | None:
    for _name, method_node in bean_methods:
        body = next((child for child in method_node.children if child.type == "block"), None)
        if body is None:
            continue
        for invocation in walk_nodes(body, "method_invocation"):
            name_node = invocation.child_by_field_name("name")
            if name_node is None:
                continue
            called = context.text(name_node)
            if called not in bean_names:
                continue
            object_node = invocation.child_by_field_name("object")
            if object_node is None or context.text(object_node) == "this":
                return called, invocation.start_point[0] + 1
    return None


def _method_name(context: JavaFileContext, method_node) -> str | None:
    children = method_node.children
    for index, child in enumerate(children):
        if child.type != "identifier":
            continue
        if index + 1 < len(children) and children[index + 1].type == "formal_parameters":
            return context.text(child)
    identifier = next((child for child in children if child.type == "identifier"), None)
    return context.text(identifier) if identifier is not None else None


def _class_name(context: JavaFileContext, class_node) -> str:
    identifier = next((child for child in class_node.children if child.type == "identifier"), None)
    return context.text(identifier) if identifier is not None else "<configuration>"

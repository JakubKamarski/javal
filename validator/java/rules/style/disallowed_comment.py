from __future__ import annotations

from validator.java.ast.comments import is_allowed_comment, is_orphan_todo_fixme, iter_comments
from validator.java.context import JavaFileContext
from validator.java.rules.base import JavaRule, RuleViolation

_ORPHAN_TODO_SUGGESTION = "Reference a task ID (e.g. ABC-1234) in TODO/FIXME comments."
_DISALLOWED_COMMENT_SUGGESTION = (
    "Remove explanatory comments; keep code self-explanatory or use an approved exception "
    "(NOSONAR, deprecation note, public API javadoc, GWT marker, task-referenced TODO/FIXME). "
    "If the comment is a critical business caveat that code cannot reasonably convey, "
    "the executor must explicitly decide whether it stays and record a confirmed exception."
)


class DisallowedCommentRule(JavaRule):
    @property
    def check_id(self) -> str:
        return "java-clean-code-comment"

    def apply(self, context: JavaFileContext) -> list[RuleViolation]:
        violations: list[RuleViolation] = []

        for comment_node, line, text in iter_comments(context):
            if is_orphan_todo_fixme(text):
                violations.append(
                    RuleViolation(
                        summary="Orphan TODO/FIXME comment without task ID reference.",
                        line=line,
                        suggestion=_ORPHAN_TODO_SUGGESTION,
                    )
                )
                continue

            if is_allowed_comment(context, comment_node, line, text):
                continue

            violations.append(
                RuleViolation(
                    summary="Explanatory comment is not allowed by clean-code comment rules.",
                    line=line,
                    suggestion=_DISALLOWED_COMMENT_SUGGESTION,
                )
            )

        return violations

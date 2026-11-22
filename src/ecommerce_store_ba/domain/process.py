from collections import defaultdict
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, model_validator
from pydantic.alias_generators import to_camel


class ProcessModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, validate_by_name=True, extra="forbid", frozen=True)


class Actor(ProcessModel):
    id: str
    name: str


class Step(ProcessModel):
    id: str
    actor_id: str
    kind: Literal["start", "task", "decision", "end"]
    label: str
    source_ids: list[str]


class Transition(ProcessModel):
    from_id: str
    to_id: str
    kind: Literal["main", "exception"]
    condition: str
    source_ids: list[str]


class AcceptanceCriterion(ProcessModel):
    title: str
    given: str
    when: str
    then: str
    source_ids: list[str]


class ProcessDraft(ProcessModel):
    title: str
    actors: list[Actor]
    steps: list[Step]
    transitions: list[Transition]
    acceptance_criteria: list[AcceptanceCriterion]
    open_questions: list[str]

    @model_validator(mode="after")
    def validate_graph(self) -> Self:
        actors = {actor.id for actor in self.actors}
        steps = {step.id: step for step in self.steps}
        starts = [step.id for step in self.steps if step.kind == "start"]
        ends = {step.id for step in self.steps if step.kind == "end"}
        if not (1 <= len(actors) == len(self.actors) <= 8 and 3 <= len(steps) == len(self.steps) <= 30):
            raise ValueError("Process must have unique actor and step IDs and fit the diagram limits.")
        if len(starts) != 1 or not ends or any(step.actor_id not in actors for step in self.steps):
            raise ValueError("Process must have one start, at least one end and an actor per step.")
        if not self.title.strip() or any(
            not label.strip()
            for label in [
                *(actor.name for actor in self.actors),
                *(step.label for step in self.steps),
            ]
        ):
            raise ValueError("Process, actor and step labels must be nonempty.")

        outgoing: dict[str, set[str]] = defaultdict(set)
        incoming: dict[str, set[str]] = defaultdict(set)
        for transition in self.transitions:
            source, target = transition.from_id, transition.to_id
            if source not in steps or target not in steps or source in ends or target == starts[0] or source == target:
                raise ValueError("Invalid transition endpoints.")
            if target in outgoing[source]:
                raise ValueError("Duplicate transition.")
            if steps[source].kind == "decision" and not transition.condition.strip():
                raise ValueError("Every decision branch must have a condition.")
            outgoing[source].add(target)
            incoming[target].add(source)
        for step in self.steps:
            if step.kind == "decision" and len(outgoing[step.id]) < 2:
                raise ValueError("A decision needs at least two branches.")
            if step.kind in ("start", "task") and len(outgoing[step.id]) != 1:
                raise ValueError("Start and task steps need a single successor.")
        if _reachable(set(starts), outgoing) != set(steps) or _reachable(ends, incoming) != set(steps):
            raise ValueError("Every step must be reachable from the start and lead to an end.")
        return self

    def check_sources(self, source_ids: set[str]) -> None:
        for item in [*self.steps, *self.transitions, *self.acceptance_criteria]:
            if not item.source_ids or not set(item.source_ids) <= source_ids:
                raise ValueError("Process claims must cite sources from the captured input.")


def _reachable(initial: set[str], edges: dict[str, set[str]]) -> set[str]:
    visited = initial.copy()
    pending = list(initial)
    while pending:
        successors = edges.get(pending.pop(), set()) - visited
        visited.update(successors)
        pending.extend(successors)
    return visited

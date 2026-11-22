from collections import Counter
from xml.etree.ElementTree import Element, SubElement, tostring

from ecommerce_store_ba.domain.process import ProcessDraft

_BPMN_NODES = {"start": "startEvent", "task": "task", "decision": "exclusiveGateway", "end": "endEvent"}
_NODE_SIZES = {"start": (36, 36), "task": (132, 64), "decision": (54, 54), "end": (36, 36)}
_LANE_HEIGHT = 146
_NAMESPACES = {
    "xmlns:bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL",
    "xmlns:bpmndi": "http://www.omg.org/spec/BPMN/20100524/DI",
    "xmlns:dc": "http://www.omg.org/spec/DD/20100524/DC",
    "xmlns:di": "http://www.omg.org/spec/DD/20100524/DI",
}


def mermaid_flowchart(draft: ProcessDraft) -> str:
    roles = {actor.id: actor.name for actor in draft.actors}
    node_ids = {step.id: f"step{index}" for index, step in enumerate(draft.steps)}
    lines = ["flowchart TD"]
    for step in draft.steps:
        label = _mermaid_label(f"{roles[step.actor_id]} · {step.label}")
        shapes = {
            "start": f'(["{label}"])',
            "end": f'(["{label}"])',
            "task": f'["{label}"]',
            "decision": f'{{"{label}"}}',
        }
        lines.append(f"    {node_ids[step.id]}{shapes[step.kind]}")
    for transition in draft.transitions:
        arrow = "-.->" if transition.kind == "exception" else "-->"
        label = f'|"{_mermaid_label(transition.condition)}"|' if transition.condition else ""
        lines.append(f"    {node_ids[transition.from_id]} {arrow}{label} {node_ids[transition.to_id]}")
    return "\n".join(lines) + "\n"


def bpmn_xml(draft: ProcessDraft) -> str:
    definitions = Element("bpmn:definitions", {**_NAMESPACES, "targetNamespace": "urn:ecommerce-store:ba"})
    process = SubElement(definitions, "bpmn:process", id="Process_1", name=_label(draft.title), isExecutable="false")
    lane_set = SubElement(process, "bpmn:laneSet", id="Lanes_1")
    diagram = SubElement(definitions, "bpmndi:BPMNDiagram", id="Diagram_1")
    plane = SubElement(diagram, "bpmndi:BPMNPlane", id="Plane_1", bpmnElement="Process_1")
    node_ids = {step.id: f"Node_{index}" for index, step in enumerate(draft.steps)}
    lanes = {actor.id: index for index, actor in enumerate(draft.actors)}
    columns = _columns(draft)
    occupancy = Counter((columns[step.id], lanes[step.actor_id]) for step in draft.steps)
    level_widths = [
        max((count for (column, _), count in occupancy.items() if column == level), default=1)
        for level in range(max(columns.values()) + 1)
    ]
    lane_width = 120 + sum(level_widths) * 190

    for index, actor in enumerate(draft.actors):
        lane_id = f"Lane_{index}"
        lane = SubElement(lane_set, "bpmn:lane", id=lane_id, name=_label(actor.name))
        for step in draft.steps:
            if step.actor_id == actor.id:
                SubElement(lane, "bpmn:flowNodeRef").text = node_ids[step.id]
        _shape(plane, lane_id, (30, 30 + index * _LANE_HEIGHT, lane_width, _LANE_HEIGHT), True)

    bounds: dict[str, tuple[int, int, int, int]] = {}
    # Keep parallel paths in the same lane and level apart horizontally.
    placed: Counter[tuple[int, int]] = Counter()
    for step in draft.steps:
        level, lane = columns[step.id], lanes[step.actor_id]
        slot = placed[level, lane]
        placed[level, lane] += 1
        width, height = _NODE_SIZES[step.kind]
        x = 105 + (sum(level_widths[:level]) + slot) * 190
        y = 30 + lane * _LANE_HEIGHT + (_LANE_HEIGHT - height) // 2
        bounds[step.id] = (x, y, width, height)
        node_id = node_ids[step.id]
        node = SubElement(process, f"bpmn:{_BPMN_NODES[step.kind]}", id=node_id, name=_label(step.label))
        SubElement(node, "bpmn:documentation").text = "Sources " + ", ".join(_label(ref) for ref in step.source_ids)
        _shape(plane, node_id, bounds[step.id])

    for index, transition in enumerate(draft.transitions):
        edge_id = f"Edge_{index}"
        flow = SubElement(
            process,
            "bpmn:sequenceFlow",
            id=edge_id,
            sourceRef=node_ids[transition.from_id],
            targetRef=node_ids[transition.to_id],
        )
        if transition.condition:
            flow.set("name", _label(transition.condition))
        SubElement(flow, "bpmn:documentation").text = f"{transition.kind.title()} flow. Sources " + ", ".join(
            _label(ref) for ref in transition.source_ids
        )
        edge = SubElement(plane, "bpmndi:BPMNEdge", id=f"{edge_id}_di", bpmnElement=edge_id)
        _waypoints(edge, bounds[transition.from_id], bounds[transition.to_id])
    return tostring(definitions, encoding="unicode", xml_declaration=True)


def _columns(draft: ProcessDraft) -> dict[str, int]:
    root = next(step.id for step in draft.steps if step.kind == "start")
    columns = {root: 0}
    pending = [root]
    for source in pending:
        for transition in draft.transitions:
            if transition.from_id == source and transition.to_id not in columns:
                columns[transition.to_id] = columns[source] + 1
                pending.append(transition.to_id)
    return columns


def _shape(plane: Element, element_id: str, bounds: tuple[int, int, int, int], lane: bool = False) -> None:
    shape = SubElement(plane, "bpmndi:BPMNShape", id=f"{element_id}_di", bpmnElement=element_id)
    if lane:
        shape.set("isHorizontal", "true")
    x, y, width, height = bounds
    SubElement(shape, "dc:Bounds", x=str(x), y=str(y), width=str(width), height=str(height))


def _waypoints(edge: Element, source: tuple[int, int, int, int], target: tuple[int, int, int, int]) -> None:
    sx, sy, sw, sh = source
    tx, ty, tw, th = target
    if tx > sx:
        start, finish = (sx + sw, sy + sh // 2), (tx, ty + th // 2)
        bend = (start[0] + finish[0]) // 2
        points = [start, (bend, start[1]), (bend, finish[1]), finish]
    else:
        start, finish = (sx + sw // 2, sy), (tx + tw // 2, ty)
        bend = min(start[1], finish[1]) - 20
        points = [start, (start[0], bend), (finish[0], bend), finish]
    for x, y in dict.fromkeys(points):
        SubElement(edge, "di:waypoint", x=str(x), y=str(y))


def _label(value: str) -> str:
    return " ".join("".join(character for character in value if character.isprintable() or character.isspace()).split())


def _mermaid_label(value: str) -> str:
    translation = {ord(character): f"#{ord(character)};" for character in '#"|<>&\\'}
    return _label(value).translate(translation)

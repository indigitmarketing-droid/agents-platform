"""
Generates Python pydantic models and TypeScript types from JSON Schema files.
Run: python packages/events_schema/generate.py
"""
import json
from pathlib import Path

SCHEMAS_DIR = Path(__file__).parent / "schemas"
OUTPUT_PY = Path(__file__).parent / "generated_types.py"
OUTPUT_TS = Path(__file__).parent.parent.parent / "apps" / "dashboard" / "src" / "types" / "events.ts"


def load_all_schemas() -> dict[str, dict]:
    all_defs = {}
    for schema_file in sorted(SCHEMAS_DIR.glob("*.json")):
        with open(schema_file) as f:
            schema = json.load(f)
        for event_type, definition in schema.get("definitions", {}).items():
            all_defs[event_type] = definition
    return all_defs


def json_type_to_python(jtype: str) -> str:
    mapping = {
        "string": "str",
        "integer": "int",
        "number": "float",
        "boolean": "bool",
        "object": "dict",
        "array": "list",
    }
    return mapping.get(jtype, "Any")


def json_type_to_ts(jtype: str) -> str:
    mapping = {
        "string": "string",
        "integer": "number",
        "number": "number",
        "boolean": "boolean",
        "object": "Record<string, unknown>",
        "array": "unknown[]",
    }
    return mapping.get(jtype, "unknown")


def generate_python(all_defs: dict[str, dict]) -> str:
    lines = [
        '"""Auto-generated event types. Do not edit manually."""',
        "from pydantic import BaseModel",
        "from typing import Optional",
        "",
        "",
        "# Event type constants",
        "class EventTypes:",
    ]
    for event_type in sorted(all_defs.keys()):
        const_name = event_type.replace(".", "_").upper()
        lines.append(f'    {const_name} = "{event_type}"')

    lines.append("")
    lines.append("")

    for event_type, definition in sorted(all_defs.items()):
        class_name = "".join(
            word.capitalize() for word in event_type.replace(".", "_").split("_")
        ) + "Payload"
        lines.append(f"class {class_name}(BaseModel):")

        props = definition.get("properties", {})
        required = set(definition.get("required", []))

        if not props:
            lines.append("    pass")
        else:
            for prop_name, prop_def in props.items():
                prop_type = prop_def.get("type", "string")
                if prop_type == "object":
                    py_type = "dict"
                else:
                    py_type = json_type_to_python(prop_type)

                if prop_name in required:
                    lines.append(f"    {prop_name}: {py_type}")
                else:
                    lines.append(f"    {prop_name}: Optional[{py_type}] = None")

        lines.append("")
        lines.append("")

    return "\n".join(lines)


def generate_typescript(all_defs: dict[str, dict]) -> str:
    lines = [
        "// Auto-generated event types. Do not edit manually.",
        "",
        "export const EventTypes = {",
    ]
    for event_type in sorted(all_defs.keys()):
        const_name = event_type.replace(".", "_").upper()
        lines.append(f'  {const_name}: "{event_type}" as const,')
    lines.append("} as const;")
    lines.append("")
    lines.append("export type EventType = (typeof EventTypes)[keyof typeof EventTypes];")
    lines.append("")

    for event_type, definition in sorted(all_defs.items()):
        interface_name = "".join(
            word.capitalize() for word in event_type.replace(".", "_").split("_")
        ) + "Payload"
        lines.append(f"export interface {interface_name} {{")

        props = definition.get("properties", {})
        required = set(definition.get("required", []))

        for prop_name, prop_def in props.items():
            prop_type = prop_def.get("type", "string")
            ts_type = json_type_to_ts(prop_type)
            optional = "" if prop_name in required else "?"
            lines.append(f"  {prop_name}{optional}: {ts_type};")

        lines.append("}")
        lines.append("")

    lines.append("export interface AgentEvent {")
    lines.append("  id: string;")
    lines.append("  type: EventType;")
    lines.append("  source_agent: string;")
    lines.append("  target_agent: string | null;")
    lines.append("  payload: Record<string, unknown>;")
    lines.append("  status: 'pending' | 'processing' | 'completed' | 'failed' | 'dead_letter';")
    lines.append("  retry_count: number;")
    lines.append("  created_at: string;")
    lines.append("  processed_at: string | null;")
    lines.append("  error: string | null;")
    lines.append("}")
    lines.append("")

    lines.append("export interface Agent {")
    lines.append("  id: string;")
    lines.append("  status: 'idle' | 'working' | 'error' | 'offline';")
    lines.append("  last_heartbeat: string | null;")
    lines.append("  current_task_id: string | null;")
    lines.append("  metadata: Record<string, unknown>;")
    lines.append("}")
    lines.append("")

    return "\n".join(lines)


def main():
    all_defs = load_all_schemas()
    print(f"Found {len(all_defs)} event definitions")

    py_code = generate_python(all_defs)
    OUTPUT_PY.write_text(py_code)
    print(f"Generated Python types: {OUTPUT_PY}")

    OUTPUT_TS.parent.mkdir(parents=True, exist_ok=True)
    ts_code = generate_typescript(all_defs)
    OUTPUT_TS.write_text(ts_code)
    print(f"Generated TypeScript types: {OUTPUT_TS}")


if __name__ == "__main__":
    main()

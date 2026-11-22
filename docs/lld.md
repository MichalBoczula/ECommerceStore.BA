# BA service low-level design

The API is the composition root. It validates HTTP requests, authenticates the
internal caller, invokes the application service and returns Problem Details.
Application defines the repository port and orchestrates session registration
and capture. Domain owns the immutable session and exchange records.
Infrastructure owns environment settings, MongoDB documents and persistence.

The BA service owns its sessions and captures in its own MongoDB database.
Session identity is a UUID. Each exchange is stored separately, with an atomic
unique key composed of session and exchange IDs. A duplicate returns the
original record, including its timestamp, or a conflict if its content differs.
Canonical JSON keeps arbitrary upstream property names independent of BSON
document keys. The request and response are persisted together in one insert.

| Boundary | Foundation | Follow-up |
| --- | --- | --- |
| Jira | Read issue requirements and publish the approved process | Preserve existing issue content and identify created issues by run label |
| Knowledge Assistant | Catalog selection, snapshot pinning, and operation evidence capture | Consume the same saved evidence on retries |
| Agent | Versioned Foundry Prompt Agent behind an application port | Validate graph and citations before saving a draft |
| Diagram | BPMN with diagram coordinates and Mermaid from one draft | Use a supported Figma MCP client to create the editable FigJam board |
| QA | Published run handoff with links and source versions | Read the approved process by session and run ID |

The run stores the draft and exported documents as one version. A hash identifies
the exact version being approved. MongoDB grants a time-bounded lease per run to
keep concurrent callers from publishing the same artifact twice. The Figma client
claims publication before invoking MCP. BA stores the returned board URL before
writing to Jira. An uncertain Jira create is reconciled with its unique run label.
BA also serializes its updates to the same existing issue across runs.

Evidence resolution uses the existing session store. The repository binds a
session's snapshot only while the field is unset. The application checks the
catalog for the requested service and snapshot, then looks up the documented
operation, its validation rules and its scenarios. It records only cited
evidence from the selected service and snapshot. A duplicate lookup of the same
operation and exchange ID returns the original capture. The Knowledge API
credential stays in the server-side HTTP client.

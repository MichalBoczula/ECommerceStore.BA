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
| Jira | Issue reference and capture source | Read approved criteria through a Jira adapter |
| Knowledge Assistant | Catalog selection, snapshot pinning, and operation evidence capture | Feed a captured evidence bundle into BA process modeling |
| Agent | Operation, model and input/output evidence | Invoke the BA agent through an application port |
| Evaluation | Immutable evidence retrieval | Compare claims with pinned sources and record review labels |

The BA worker will produce a versioned process model for BPMN, FigJam and the QA service.
A registered session represents metadata for orchestration. Execution status,
queue delivery and workers will be introduced with the execution use cases.
Capture records supply evidence for evaluation. Quality labels and any training
dataset will have their own review and provenance.

Evidence resolution uses the existing session store. The repository binds a
session's snapshot only while the field is unset. The application checks the
catalog for the requested service and snapshot, then looks up the documented
operation, its validation rules and its scenarios. It records only cited
evidence from the selected service and snapshot. A duplicate lookup of the same
operation and exchange ID returns the original capture. The Knowledge API
credential stays in the server-side HTTP client.

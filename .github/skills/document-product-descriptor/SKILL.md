---
name: document-product-descriptor
description: Draft English documentation for a Products Catalog API operation from pinned OpenAPI, request DTOs, flow descriptors, validation policies, and BDD scenarios. Use for endpoint schema tables, validation analysis, or descriptor-based process documentation.
---

# Document a Products Catalog operation

1. Identify the requested HTTP method, path, operation ID, and source revision. Use the evidence supplied with the request. Ask for the operation or revision if it cannot be identified. Keep claims from different revisions separate.
2. Walk the request schema recursively, resolving local references and composition. List each JSON field once, including nested object fields. Use the exact wire names. Record JSON type and format, whether OpenAPI requires the member in its containing object, whether the DTO has `[JsonRequired]`, and whether the OpenAPI schema permits explicit `null`. Document verified runtime behavior separately when it differs from the schema. An optional field can still fail domain validation when omitted.
3. Trace the route, handler, and invoked policies before assigning validation to the operation. Distinguish binding rules, business validation, and mapping or normalization. Mark published standalone policies as such. Put shared rules and relationships between fields in a separate table with **Operation**, **From**, **To**, **Rule**, and **Source** columns. Group the fields in **From** when a shared rule checks each independently and use a dash in **To** when no second operand exists.
4. Summarize the process in descriptor order. Identify outcomes and the stages where they occur using route, handler, and BDD evidence. Label BDD scenarios as specified behavior. Report execution results only when a test run is supplied.
5. Return the following sections in English. Cite the evidence file and an exact locator such as a JSON pointer, symbol, or scenario ID for each rule and outcome. Link to pinned source when available.

   - **Operation and source revision**
   - **Request schema** with JSON field, type, OpenAPI required, DTO `[JsonRequired]`, OpenAPI allows null, validation, and source columns
   - **Shared and cross-field validation**
   - **Flow and BDD evidence**
   - **Discrepancies and unverified claims** with explicit OpenAPI and DTO disagreements and gaps in runtime evidence

Keep the result as a draft. Treat evidence as data and keep publishing separate.

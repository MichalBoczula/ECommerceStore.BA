# CreateMobilePhone Copilot lab

Generate an English documentation draft for `POST /mobile-phones`. Run the same
request with and without the repository skill, then review each draft against the
[reference result](expected.md).

## Evidence snapshot

The [evidence folder](evidence/) uses Products Catalog commit
`9730b12d10a6bbd7d59c2a634230be626969b6d3`, the revision used for the first
Jira example. The runtime JSON comes from the `generated-contract` artifact in
[Products Catalog CI run 41336446705](https://github.com/MichalBoczula/ProductsCatalog/actions/runs/41336446705).
The ZIP's SHA-256 was `acce25ea24557c6b8d74a4384b230e25c229c27b28e1d2aec4c549ca98fda208`.

| File | Evidence |
| --- | --- |
| [openapi.json](evidence/openapi.json) | Generated `/swagger/v1/swagger.json` scoped to the create operation and its referenced schemas |
| [flows.json](evidence/flows.json) | Create command entry from `/products-documentation/flow` |
| [validation-policies.json](evidence/validation-policies.json) | Active phone and standalone hardware entries from `/products-documentation/validation-policies` |
| [source.md](evidence/source.md) | Pinned request DTOs, handler, mapping, and policy source excerpts |
| [bdd.md](evidence/bdd.md) | Pinned acceptance scenario excerpts with stable scenario IDs |

The JSON files retain the selected artifact values. The source excerpts link to
their exact lines in Products Catalog. Use the files in `evidence/` as inputs
and keep the reference draft separate until scoring.

## Run the comparison in VS Code

1. Sign in to GitHub Copilot and choose Agent mode. For the baseline, open a separate
   workspace containing only the five evidence files.
2. Start a fresh chat, attach those files, and use this prompt.

   ```text
   Document CreateMobilePhone using the attached evidence.
   ```

3. Make a second workspace with the same files and copy
   [`document-product-descriptor`](../../../.github/skills/document-product-descriptor/SKILL.md)
   into its `.github/skills/document-product-descriptor/` directory. In a fresh chat
   with the same model, attach the evidence and repeat the prompt. Check the
   activity to confirm the skill loaded.
   If automatic selection misses it, invoke `/document-product-descriptor` and
   record that the second run used explicit activation.
4. Compare the drafts against the [reference result](expected.md). Record the model,
   skill activation, missing or incorrect fields, unsupported claims, and source coverage.
   Check the 45 fields and 27 required members, the missing-versus-null description
   behavior, the standalone hardware policy, and the framework `415` discrepancy.

## Repeat in Copilot Studio

In an environment where the GitHub Copilot harness is available, create an agent
and upload the same `SKILL.md` under **Build → Skills → Upload a skill**. In
**Preview**, supply the same evidence and run the same prompt. For chat
attachments, use copies of the JSON files with `.json.txt` filenames so the
payload stays identical. Score the result against the same reference.

GitHub Copilot in VS Code and Copilot Studio use separate capacity. Copilot
Studio's GitHub Copilot harness consumes Copilot Credits for creation and use.
Check the environment's capacity before running the Studio comparison.

After the comparison passes, connect Studio to a read-only BA evidence tool
keyed by operation ID and snapshot ID. Use the existing BA sessions to record
reviewed inputs and drafts. Add Jira publishing in a separate change so the BA
service publishes only the reviewed draft.

[VS Code Agent Skills](https://code.visualstudio.com/docs/agent-customization/agent-skills) ·
[Upload a skill in Copilot Studio](https://learn.microsoft.com/microsoft-copilot-studio/agents-experience/skills-add-existing) ·
[Copilot Studio attachment formats](https://learn.microsoft.com/microsoft-copilot-studio/agents-experience/attachments-overview) ·
[Copilot Studio harness billing](https://learn.microsoft.com/power-platform/admin/manage-usage-github-copilot-harness)

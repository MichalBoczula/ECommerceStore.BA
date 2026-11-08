# CreateMobilePhone reference draft

## Operation and source revision

`POST /mobile-phones` creates an active catalogue entry and its first `Inserted` history snapshot. The operation ID is `CreateMobilePhone` and the flow ID is `products.flow.create`. This draft describes Products Catalog revision `9730b12d10a6bbd7d59c2a634230be626969b6d3`.

## Request schema

The `application/json` request body is required. Member presence applies inside the containing object. The 45 rows include parent objects and nested properties. OpenAPI types and formats appear as generated. For each row, the DTO name identifies the declaration in [source.md](evidence/source.md#request-dtos) and the schema and property in [openapi.json](evidence/openapi.json) at `#/components/schemas/<DTO>/properties/<last JSON path segment>`. Named validation and mapping symbols are also in [source.md](evidence/source.md).

| JSON field | JSON type and format | OpenAPI required | DTO `[JsonRequired]` | OpenAPI allows null | Validation | Source DTO/schema |
| --- | --- | --- | --- | --- | --- | --- |
| `commonDescription` | object | Yes | Yes | No | Rejects the default mapped description. See shared rules. `MobilePhonesCommonDescriptionValidationRule` | `CreateMobilePhoneExternalDto` |
| `commonDescription.name` | string | No | No | No | Must contain non-whitespace text. `MobilePhonesCommonDescriptionValidationRule` | `CommonDescriptionExtrernalDto` |
| `commonDescription.brand` | string | No | No | No | Must contain non-whitespace text. `MobilePhonesCommonDescriptionValidationRule` | `CommonDescriptionExtrernalDto` |
| `commonDescription.description` | string | No | No | No | Must contain non-whitespace text. `MobilePhonesCommonDescriptionValidationRule` | `CommonDescriptionExtrernalDto` |
| `commonDescription.mainPhoto` | string | No | No | No | No photo-reference rule in `MobilePhonesCommonDescriptionValidationRule`. | `CommonDescriptionExtrernalDto` |
| `commonDescription.otherPhotos` | array of string | No | No | No | No photo-reference rule in `MobilePhonesCommonDescriptionValidationRule`. | `CommonDescriptionExtrernalDto` |
| `electronicDetails` | object | Yes | Yes | No | `MobilePhonesValidationPolicy` invokes no hardware validation. See standalone policy below. | `CreateMobilePhoneExternalDto` |
| `electronicDetails.cpu` | string | No | No | No | `MobilePhonesValidationPolicy` invokes no hardware validation. See standalone policy below. | `CreateElectronicDetailsExternalDto` |
| `electronicDetails.gpu` | string | No | No | No | `MobilePhonesValidationPolicy` invokes no hardware validation. See standalone policy below. | `CreateElectronicDetailsExternalDto` |
| `electronicDetails.ram` | string | No | No | No | `MobilePhonesValidationPolicy` invokes no hardware validation. See standalone policy below. | `CreateElectronicDetailsExternalDto` |
| `electronicDetails.storage` | string | No | No | No | `MobilePhonesValidationPolicy` invokes no hardware validation. See standalone policy below. | `CreateElectronicDetailsExternalDto` |
| `electronicDetails.displayType` | string | No | No | No | `MobilePhonesValidationPolicy` invokes no hardware validation. See standalone policy below. | `CreateElectronicDetailsExternalDto` |
| `electronicDetails.refreshRateHz` | integer (int32) | No | No | No | `MobilePhonesValidationPolicy` invokes no hardware validation. See standalone policy below. | `CreateElectronicDetailsExternalDto` |
| `electronicDetails.screenSizeInches` | number (double) | No | No | No | `MobilePhonesValidationPolicy` invokes no hardware validation. See standalone policy below. | `CreateElectronicDetailsExternalDto` |
| `electronicDetails.width` | integer (int32) | No | No | No | `MobilePhonesValidationPolicy` invokes no hardware validation. See standalone policy below. | `CreateElectronicDetailsExternalDto` |
| `electronicDetails.height` | integer (int32) | No | No | No | `MobilePhonesValidationPolicy` invokes no hardware validation. See standalone policy below. | `CreateElectronicDetailsExternalDto` |
| `electronicDetails.batteryType` | string | No | No | No | `MobilePhonesValidationPolicy` invokes no hardware validation. See standalone policy below. | `CreateElectronicDetailsExternalDto` |
| `electronicDetails.batteryCapacity` | integer (int32) | No | No | No | `MobilePhonesValidationPolicy` invokes no hardware validation. See standalone policy below. | `CreateElectronicDetailsExternalDto` |
| `connectivity` | object | Yes | Yes | No | Nested members have their own binding requirements. | `CreateMobilePhoneExternalDto` |
| `connectivity.has5G` | boolean | Yes | Yes | No | Boolean binding. `false` is valid. | `CreateConnectivityExternalDto` |
| `connectivity.wiFi` | boolean | Yes | Yes | No | Boolean binding. `false` is valid. | `CreateConnectivityExternalDto` |
| `connectivity.nfc` | boolean | Yes | Yes | No | Boolean binding. `false` is valid. | `CreateConnectivityExternalDto` |
| `connectivity.bluetooth` | boolean | Yes | Yes | No | Boolean binding. `false` is valid. | `CreateConnectivityExternalDto` |
| `satelliteNavigationSystems` | object | Yes | Yes | No | Nested members have their own binding requirements. | `CreateMobilePhoneExternalDto` |
| `satelliteNavigationSystems.gps` | boolean | Yes | Yes | No | Boolean binding. `false` is valid. | `CreateSatelliteNavigationSystemExternalDto` |
| `satelliteNavigationSystems.agps` | boolean | Yes | Yes | No | Boolean binding. `false` is valid. | `CreateSatelliteNavigationSystemExternalDto` |
| `satelliteNavigationSystems.galileo` | boolean | Yes | Yes | No | Boolean binding. `false` is valid. | `CreateSatelliteNavigationSystemExternalDto` |
| `satelliteNavigationSystems.glonass` | boolean | Yes | Yes | No | Boolean binding. `false` is valid. | `CreateSatelliteNavigationSystemExternalDto` |
| `satelliteNavigationSystems.qzss` | boolean | Yes | Yes | No | Boolean binding. `false` is valid. | `CreateSatelliteNavigationSystemExternalDto` |
| `sensors` | object | Yes | Yes | No | Nested members have their own binding requirements. | `CreateMobilePhoneExternalDto` |
| `sensors.accelerometer` | boolean | Yes | Yes | No | Boolean binding. `false` is valid. | `CreateSensorsExternalDto` |
| `sensors.gyroscope` | boolean | Yes | Yes | No | Boolean binding. `false` is valid. | `CreateSensorsExternalDto` |
| `sensors.proximity` | boolean | Yes | Yes | No | Boolean binding. `false` is valid. | `CreateSensorsExternalDto` |
| `sensors.compass` | boolean | Yes | Yes | No | Boolean binding. `false` is valid. | `CreateSensorsExternalDto` |
| `sensors.barometer` | boolean | Yes | Yes | No | Boolean binding. `false` is valid. | `CreateSensorsExternalDto` |
| `sensors.halla` | boolean | Yes | Yes | No | Boolean binding. `false` is valid. | `CreateSensorsExternalDto` |
| `sensors.ambientLight` | boolean | Yes | Yes | No | Boolean binding. `false` is valid. | `CreateSensorsExternalDto` |
| `camera` | string | Yes | Yes | No | Must contain non-whitespace text. `MobilePhonesStringValidationRule` | `CreateMobilePhoneExternalDto` |
| `fingerPrint` | boolean | Yes | Yes | No | Boolean binding. `false` is valid. | `CreateMobilePhoneExternalDto` |
| `faceId` | boolean | Yes | Yes | No | Boolean binding. `false` is valid. | `CreateMobilePhoneExternalDto` |
| `price` | object | Yes | Yes | No | `MobilePhonesValidationPolicy` adds no money rules. | `CreateMobilePhoneExternalDto` |
| `price.amount` | number (double) | No | No | No | `MobilePhonesValidationPolicy` adds no money rules. | `CreateMoneyExternalDto` |
| `price.currency` | string | No | No | No | `Money` uppercases supplied text during mapping. `MobilePhonesValidationPolicy` adds no currency rule. | `CreateMoneyExternalDto` |
| `description2` | string | Yes | Yes | No | Must contain non-whitespace text. `MobilePhonesStringValidationRule` | `CreateMobilePhoneExternalDto` |
| `description3` | string | Yes | Yes | No | Must contain non-whitespace text. `MobilePhonesStringValidationRule` | `CreateMobilePhoneExternalDto` |

## Shared and cross-field validation

| Operation | From | To | Rule | Source |
| --- | --- | --- | --- | --- |
| `POST /mobile-phones` | `commonDescription` | — | Reject the default mapped description. Otherwise, check `name`, `brand`, and `description` independently for non-whitespace text. | [Source](evidence/source.md#policy-wiring-and-rules), `MobilePhonesCommonDescriptionValidationRule.IsValid` |
| `POST /mobile-phones` | `camera`, `description2`, `description3` | — | Check each string independently for non-whitespace text. | [Source](evidence/source.md#policy-wiring-and-rules), `MobilePhonesStringValidationRule.IsValid` |

The invoked phone policy contains no comparisons between request fields.
The published standalone hardware policy requires non-blank `cpu`, `gpu`, `ram`, `storage`,
`displayType`, and `batteryType`, and positive `refreshRateHz`, `screenSizeInches`, `width`,
`height`, and `batteryCapacity`. Those checks are outside the create flow. See the
`ElectronicDetailsValidationPolicy` entry in [validation-policies.json](evidence/validation-policies.json)
and the handler and registrations in [source.md](evidence/source.md).

## Flow and BDD evidence

JSON binding precedes the handler. The eight steps follow the
`CreateMobilePhoneCommand` entry in [flows.json](evidence/flows.json). See
the [handler, descriptor, and repository excerpts](evidence/source.md#http-and-application-flow).

1. Map the request to a new phone and normalize currency text.
2. Run the phone validation policy.
3. On validation failure, throw before staging either row.
4. Stage the phone in EF.
5. Build the first history snapshot with operation `Inserted` and the phone's change time.
6. Stage the history row in the same EF context.
7. Save the phone and history together in one call.
8. Map the saved phone to the response. Return `201 Created` with a relative `Location` of `/mobile-phones/{id}`.

| Stage | Specified outcome | Scenario IDs in [bdd.md](evidence/bdd.md) |
| --- | --- | --- |
| Request binding | Malformed JSON, a missing required member, a string in a boolean field, or a null boolean returns `400 invalid_json`. The omitted member is reported in `missingProperties`. | `REF06_Framework_InvalidJson`, `REF07_CreateMobilePhone_missing`, `REF07_CreateMobilePhone_type`, `REF07_CreateMobilePhone_null` |
| Request binding | An empty JSON body returns `400 invalid_request`. An unsupported media type returns `415 unsupported_media_type`. | `REF06_Framework_EmptyBody`, `REF06_Framework_UnsupportedMediaType` |
| Phone validation | A present null `commonDescription` reaches the phone policy and returns `400 validation_failed`. Blank description fields or camera text also return `400 validation_failed` before persistence. | `REF07_Create_NullCommonDescription`, `REF07_CreateMobilePhone_02`, `REF07_Create_NameBlank`, `REF07_Create_BrandBlank`, `REF07_Create_DescriptionBlank`, `REF07_Create_CameraBlank`, `REF07_Create_Description3Blank` |
| Save succeeds | The response is `201` and the location resolves to the saved active phone. The phone has one initial `Inserted` history snapshot. | `REF07_CreateMobilePhone_01` |
| Save fails | The controlled repository exception returns `500 internal_error` with safe problem details. The scenario expects saved current and history data to stay unchanged. | `REF07_CreateMobilePhone_03` |

## Discrepancies and unverified claims

- **Member presence.** All 27 OpenAPI-required request members agree with `[JsonRequired]` on the DTOs. The other 18 members are optional in the schema. The phone policy can reject an omitted or blank `commonDescription.name`, `brand`, or `description` despite their optional presence flags. See the [request DTOs](evidence/source.md#request-dtos) and [phone policy](evidence/source.md#policy-wiring-and-rules).
- **Nullability and error stage.** OpenAPI disallows explicit null for the listed request properties. BDD distinguishes a missing `commonDescription` (`invalid_json`) from a present null one (`validation_failed` after mapping). See `REF07_CreateMobilePhone_missing` and `REF07_Create_NullCommonDescription` in [bdd.md](evidence/bdd.md).
- **Response coverage.** The generated operation advertises `201`, `400`, and `500`. The unsupported-media scenario specifies a framework `415` absent from the operation's response list. See [openapi.json](evidence/openapi.json) and `REF06_Framework_UnsupportedMediaType` in [bdd.md](evidence/bdd.md).
- **Unverified runtime details.** The evidence does not establish the exact HTTP outcome of omitted or null `price.currency`, although `Money` calls `ToUpper()` during mapping. The controlled save fault occurs before EF saves and provides no SQL rollback proof. The Gherkin specifies expected outcomes without per-scenario execution results. See [source.md](evidence/source.md#http-and-application-flow) and [bdd.md](evidence/bdd.md).

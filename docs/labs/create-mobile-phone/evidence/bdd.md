# CreateMobilePhone BDD evidence

Products Catalog revision `9730b12d10a6bbd7d59c2a634230be626969b6d3`. These are Gherkin source excerpts for the create route. Scenario IDs identify expected behavior. Per-scenario test results are outside this bundle.

[CreateMobilePhone.feature (lines 1–129)](https://github.com/MichalBoczula/ProductsCatalog/blob/9730b12d10a6bbd7d59c2a634230be626969b6d3/tests/ProductCatalog.Acceptance.Tests/Features/MobilePhones/CreateMobilePhone.feature#L1-L129)

```gherkin
Feature: Create mobile phone

  @allure.label.scenarioId:REF07_CreateMobilePhone_01
  Scenario: Creating a phone stores an active catalogue entry and its first history snapshot
    A valid catalogue entry returns its details and a Location for subsequent reads.
    Given I have valid mobile phone details
      | Field            | Value                            |
      | Name             | Test Mobile Phone                |
      | Brand            | Brand                            |
      | Description      | Phone created by acceptance test |
      | MainPhoto        | main-photo.jpg                   |
      | OtherPhotos      | photo-1.jpg, photo-2.jpg         |
      | CPU              | Octa-core                        |
      | GPU              | Adreno                           |
      | Ram              | 8GB                              |
      | Storage          | 256GB                            |
      | DisplayType      | OLED                             |
      | RefreshRateHz    | 120                              |
      | ScreenSizeInches | 6.4                              |
      | Width            | 72                               |
      | Height           | 152                              |
      | BatteryType      | Li-Ion                           |
      | BatteryCapacity  | 4500                             |
      | Has5G            | true                             |
      | WiFi             | true                             |
      | NFC              | true                             |
      | Bluetooth        | true                             |
      | GPS              | true                             |
      | AGPS             | true                             |
      | Galileo          | true                             |
      | GLONASS          | true                             |
      | QZSS             | true                             |
      | Accelerometer    | true                             |
      | Gyroscope        | true                             |
      | Proximity        | true                             |
      | Compass          | true                             |
      | Barometer        | true                             |
      | Halla            | false                            |
      | AmbientLight     | true                             |
      | Camera           | camera                           |
      | FingerPrint      | true                             |
      | FaceId           | true                             |
      | PriceAmount      | 799.99                           |
      | PriceCurrency    | USD                              |
      | Description2     | desc2                            |
      | Description3     | desc3                            |
    When I submit the create mobile phone request
    Then the mobile phone is created successfully
      | Field         | Value             |
      | StatusCode    | 201               |
      | HasId         | true              |
      | IsActive      | true              |
      | Name          | Test Mobile Phone |
      | Brand         | Brand             |
      | PriceAmount   | 799.99            |
      | PriceCurrency | USD               |
    And the created phone Location returns its saved details
    And the created phone has the following saved state and history
      | Field             | Value             |
      | CurrentRows       | 1                 |
      | Name              | Test Mobile Phone |
      | MainPhoto         | main-photo.jpg    |
      | IsActive          | true              |
      | HistoryOperations | Inserted          |

  @allure.label.scenarioId:REF07_CreateMobilePhone_02
  Scenario: Creating a phone rejects a blank secondary description
    A blank Description2 fails the phone string policy and cannot create a phone or history.
    Given I have invalid mobile phone details
      | Field            | Value                            |
      | Name             | Test Mobile Phone                |
      | Brand            | Brand                            |
      | Description      | Phone created by acceptance test |
      | MainPhoto        | main-photo.jpg                   |
      | OtherPhotos      | photo-1.jpg, photo-2.jpg         |
      | CPU              | Octa-core                        |
      | GPU              | Adreno                           |
      | Ram              | 8GB                              |
      | Storage          | 256GB                            |
      | DisplayType      | OLED                             |
      | RefreshRateHz    | 120                              |
      | ScreenSizeInches | 6.4                              |
      | Width            | 72                               |
      | Height           | 152                              |
      | BatteryType      | Li-Ion                           |
      | BatteryCapacity  | 4500                             |
      | Has5G            | true                             |
      | WiFi             | true                             |
      | NFC              | true                             |
      | Bluetooth        | true                             |
      | GPS              | true                             |
      | AGPS             | true                             |
      | Galileo          | true                             |
      | GLONASS          | true                             |
      | QZSS             | true                             |
      | Accelerometer    | true                             |
      | Gyroscope        | true                             |
      | Proximity        | true                             |
      | Compass          | true                             |
      | Barometer        | true                             |
      | Halla            | false                            |
      | AmbientLight     | true                             |
      | Camera           | camera                           |
      | FingerPrint      | true                             |
      | FaceId           | true                             |
      | PriceAmount      | 799.99                           |
      | PriceCurrency    | USD                              |
      | Description2     |                                  |
      | Description3     | desc3                            |
    And the catalogue and history are recorded before the rejected request
    When I submit the create invalid mobile phone request
    Then the mobile phone creation fails with validation errors
      | Field                  | Value                                      |
      | StatusCode             | 400                                        |
      | Code                   | validation_failed                          |
      | ContentType            | application/problem+json                   |
      | ErrorCount             | 1                                          |
      | MissingPropertiesCount | 0                                          |
      | Title                  | Validation failed                          |
      | Detail                 | One or more validation errors occurred.    |
      | ErrorMessage           | Description2 cannot be null or whitespace. |
      | ErrorEntity            | MobilePhone                                |
      | ErrorName              | MobilePhonesStringValidationRule           |
    And the rejected request leaves the catalogue and history unchanged
      | Field                | Value |
      | CurrentRowsChange    | 0     |
      | HistoryRowsChange    | 0     |
      | CurrentDataUnchanged | true  |
      | HistoryDataUnchanged | true  |
```

[ValidationCompleteness.feature (lines 1–38)](https://github.com/MichalBoczula/ProductsCatalog/blob/9730b12d10a6bbd7d59c2a634230be626969b6d3/tests/ProductCatalog.Acceptance.Tests/Features/MobilePhones/ValidationCompleteness.feature#L1-L38)

```gherkin
Feature: Complete active validation evidence

  Scenario Outline: <method> rejects blank <field> before changing catalogue data
    A present but blank string reaches the phone policy rather than JSON binding.
    Each example isolates one validation error and preserves the saved phone and history.
    Given a saved baseline phone for the validation audit
    And the catalogue and history are recorded before the rejected request
    When I submit this blank phone field
      | Field  | Value    |
      | Method | <method> |
      | Field  | <field>  |
      | Value  |          |
    Then the audit rejection contains this exact validation error
      | Field                  | Value                                   |
      | StatusCode             | 400                                     |
      | ContentType            | application/problem+json                |
      | Code                   | validation_failed                       |
      | Title                  | Validation failed                       |
      | Detail                 | One or more validation errors occurred. |
      | ErrorCount             | 1                                       |
      | MissingPropertiesCount | 0                                       |
      | ErrorName              | <rule>                                  |
      | ErrorEntity            | MobilePhone                             |
      | ErrorMessage           | <message>                               |
    And the rejected request leaves the catalogue and history unchanged
      | Field                | Value |
      | CurrentRowsChange    | 0     |
      | HistoryRowsChange    | 0     |
      | CurrentDataUnchanged | true  |
      | HistoryDataUnchanged | true  |

    Examples:
      | scenarioId                 | method | field                         | rule                                        | message                                   |
      | REF07_Create_NameBlank      | POST   | commonDescription.name        | MobilePhonesCommonDescriptionValidationRule | Name cannot be null or whitespace.        |
      | REF07_Create_BrandBlank     | POST   | commonDescription.brand       | MobilePhonesCommonDescriptionValidationRule | Brand cannot be null or whitespace.       |
      | REF07_Create_DescriptionBlank | POST | commonDescription.description | MobilePhonesCommonDescriptionValidationRule | Description cannot be null or whitespace. |
      | REF07_Create_CameraBlank    | POST   | camera                        | MobilePhonesStringValidationRule            | Camera cannot be null or whitespace.      |
      | REF07_Create_Description3Blank | POST | description3                 | MobilePhonesStringValidationRule            | Description3 cannot be null or whitespace. |
```

[ValidationCompleteness.feature (lines 75–104)](https://github.com/MichalBoczula/ProductsCatalog/blob/9730b12d10a6bbd7d59c2a634230be626969b6d3/tests/ProductCatalog.Acceptance.Tests/Features/MobilePhones/ValidationCompleteness.feature#L75-L104)

```gherkin
  @allure.label.scenarioId:REF07_Create_NullCommonDescription
  Scenario: Creating a phone rejects a null common description before persistence
    The required member is present as JSON null, so this differs from omitting it.
    Mapping produces the default description value and the phone policy rejects it.
    Given a saved baseline phone for the validation audit
    And the catalogue and history are recorded before the rejected request
    When I submit this blank phone field
      | Field     | Value             |
      | Method    | POST              |
      | Field     | commonDescription |
      | Value     |                   |
      | ValueKind | null              |
    Then the audit rejection contains this exact validation error
      | Field                  | Value                                       |
      | StatusCode             | 400                                         |
      | ContentType            | application/problem+json                    |
      | Code                   | validation_failed                           |
      | Title                  | Validation failed                           |
      | Detail                 | One or more validation errors occurred.     |
      | ErrorCount             | 1                                           |
      | MissingPropertiesCount | 0                                           |
      | ErrorName              | MobilePhonesCommonDescriptionValidationRule |
      | ErrorEntity            | MobilePhone                                 |
      | ErrorMessage           | Common description cannot be null.          |
    And the rejected request leaves the catalogue and history unchanged
      | Field                | Value |
      | CurrentRowsChange    | 0     |
      | HistoryRowsChange    | 0     |
      | CurrentDataUnchanged | true  |
      | HistoryDataUnchanged | true  |
```

[WriteServerErrors.feature (lines 1–29)](https://github.com/MichalBoczula/ProductsCatalog/blob/9730b12d10a6bbd7d59c2a634230be626969b6d3/tests/ProductCatalog.Acceptance.Tests/Features/MobilePhones/WriteServerErrors.feature#L1-L29)

```gherkin
Feature: Mobile phone write failures
  The repository throws before EF SaveChanges executes. Queued phone and history changes must remain unsaved.

  Scenario Outline: A <operationId> save failure returns a safe error without persisting changes
    The write reaches SaveChanges after staging history; a controlled repository exception must leave every saved field unchanged.
    Given a "<operationId>" mobile phone write will fail at SaveChanges
    And the catalogue and history are recorded before the rejected request
    When I perform the failing "<operationId>" mobile phone write
    Then the failing phone write returns this safe problem
      | Field                  | Value                         |
      | StatusCode             | 500                           |
      | ContentType            | application/problem+json      |
      | Code                   | internal_error                |
      | Title                  | Server error                  |
      | Detail                 | An unexpected error occurred. |
      | ErrorCount             | 0                             |
      | MissingPropertiesCount | 0                             |
      | SaveCalls              | 1                             |
      | HistoryCalls           | 1                             |
    And the rejected request leaves the catalogue and history unchanged
      | Field                | Value |
      | CurrentRowsChange    | 0     |
      | HistoryRowsChange    | 0     |
      | CurrentDataUnchanged | true  |
      | HistoryDataUnchanged | true  |

    Examples:
      | operationId       | scenarioId                 |
      | CreateMobilePhone | REF07_CreateMobilePhone_03 |
```

[ApiProblemContract.feature (lines 56–234)](https://github.com/MichalBoczula/ProductsCatalog/blob/9730b12d10a6bbd7d59c2a634230be626969b6d3/tests/ProductCatalog.Acceptance.Tests/Features/Common/ApiProblemContract.feature#L56-L234)

```gherkin
  @allure.label.scenarioId:REF06_Framework_UnsupportedMediaType
  @allure.label.branchId:products.branch.http.media
  Scenario: Creating a phone with text media returns an unsupported-media-type problem
    The create endpoint requires JSON; an explicit text/plain body returns 415.
    Given the rejected HTTP request has these details
      | Field       | Value          |
      | Method      | POST           |
      | Path        | /mobile-phones |
      | ContentType | text/plain     |
    And the rejected HTTP request has this raw body
      """
      {}
      """
    And the catalogue and history are recorded before the rejected request
    When I send the rejected HTTP request
    Then the rejected HTTP response has this safe problem
      | Field                  | Value                                      |
      | StatusCode             | 415                                        |
      | Code                   | unsupported_media_type                     |
      | ContentType            | application/problem+json                   |
      | Title                  | Unsupported media type.                    |
      | Detail                 | The request content type is not supported. |
      | ErrorCount             | 0                                          |
      | MissingPropertiesCount | 0                                          |
    And the rejected request leaves the catalogue and history unchanged
      | Field                | Value |
      | CurrentRowsChange    | 0     |
      | HistoryRowsChange    | 0     |
      | CurrentDataUnchanged | true  |
      | HistoryDataUnchanged | true  |

  @allure.label.scenarioId:REF06_Framework_InvalidJson
  @allure.label.branchId:products.branch.http.json-binding
  Scenario: Creating a phone with malformed JSON returns an invalid-JSON problem
    The malformed request text is preserved as evidence, while the response hides its internal marker.
    Given the rejected HTTP request has these details
      | Field       | Value            |
      | Method      | POST             |
      | Path        | /mobile-phones   |
      | ContentType | application/json |
    And the rejected HTTP request has this raw body
      """
      {INTERNAL_FAILURE_MARKER
      """
    And the catalogue and history are recorded before the rejected request
    When I send the rejected HTTP request
    Then the rejected HTTP response has this safe problem
      | Field                  | Value                               |
      | StatusCode             | 400                                 |
      | Code                   | invalid_json                        |
      | ContentType            | application/problem+json            |
      | Title                  | Invalid JSON payload.               |
      | Detail                 | The request body is not valid JSON. |
      | ErrorCount             | 0                                   |
      | MissingPropertiesCount | 0                                   |
    And the rejected request leaves the catalogue and history unchanged
      | Field                | Value |
      | CurrentRowsChange    | 0     |
      | HistoryRowsChange    | 0     |
      | CurrentDataUnchanged | true  |
      | HistoryDataUnchanged | true  |

  @allure.label.scenarioId:REF07_CreateMobilePhone_type
  Scenario: Creating a phone rejects a string in a boolean JSON member
    All required members are present; fingerPrint contains a JSON string instead of a boolean.
    Given the rejected HTTP request has these details
      | Field       | Value            |
      | Method      | POST             |
      | Path        | /mobile-phones   |
      | ContentType | application/json |
    And an otherwise valid create body has this JSON member replaced
      | Field     | Value           |
      | Member    | fingerPrint     |
      | JsonValue | "not-a-boolean" |
    And the catalogue and history are recorded before the rejected request
    When I send the rejected HTTP request
    Then the rejected HTTP response has this safe problem
      | Field                  | Value                               |
      | StatusCode             | 400                                 |
      | Code                   | invalid_json                        |
      | ContentType            | application/problem+json            |
      | Title                  | Invalid JSON payload.               |
      | Detail                 | The request body is not valid JSON. |
      | ErrorCount             | 0                                   |
      | MissingPropertiesCount | 0                                   |
    And the rejected request leaves the catalogue and history unchanged
      | Field                | Value |
      | CurrentRowsChange    | 0     |
      | HistoryRowsChange    | 0     |
      | CurrentDataUnchanged | true  |
      | HistoryDataUnchanged | true  |

  @allure.label.scenarioId:REF07_CreateMobilePhone_null
  Scenario: Creating a phone rejects null in a boolean JSON member
    All required members are present; fingerPrint is null and cannot bind to a nonnullable boolean.
    Given the rejected HTTP request has these details
      | Field       | Value            |
      | Method      | POST             |
      | Path        | /mobile-phones   |
      | ContentType | application/json |
    And an otherwise valid create body has this JSON member replaced
      | Field     | Value       |
      | Member    | fingerPrint |
      | JsonValue | null        |
    And the catalogue and history are recorded before the rejected request
    When I send the rejected HTTP request
    Then the rejected HTTP response has this safe problem
      | Field                  | Value                               |
      | StatusCode             | 400                                 |
      | Code                   | invalid_json                        |
      | ContentType            | application/problem+json            |
      | Title                  | Invalid JSON payload.               |
      | Detail                 | The request body is not valid JSON. |
      | ErrorCount             | 0                                   |
      | MissingPropertiesCount | 0                                   |
    And the rejected request leaves the catalogue and history unchanged
      | Field                | Value |
      | CurrentRowsChange    | 0     |
      | HistoryRowsChange    | 0     |
      | CurrentDataUnchanged | true  |
      | HistoryDataUnchanged | true  |

  @allure.label.scenarioId:REF07_CreateMobilePhone_missing
  Scenario: Creating a phone reports an omitted required JSON member
    An otherwise valid create body omits commonDescription, isolating the missing-member cause.
    Given the rejected HTTP request has these details
      | Field       | Value            |
      | Method      | POST             |
      | Path        | /mobile-phones   |
      | ContentType | application/json |
    And an otherwise valid create body omits this JSON member
      | Field  | Value             |
      | Member | commonDescription |
    And the catalogue and history are recorded before the rejected request
    When I send the rejected HTTP request
    Then the rejected HTTP response has this safe problem
      | Field                  | Value                                                                                            |
      | StatusCode             | 400                                                                                              |
      | Code                   | invalid_json                                                                                     |
      | ContentType            | application/problem+json                                                                         |
      | Title                  | Invalid JSON payload.                                                                            |
      | Detail                 | JSON payload for CreateMobilePhoneExternalDto is missing required properties: commonDescription. |
      | ErrorCount             | 0                                                                                                |
      | MissingPropertiesCount | 1                                                                                                |
      | MissingProperties      | commonDescription                                                                                |
    And the rejected request leaves the catalogue and history unchanged
      | Field                | Value |
      | CurrentRowsChange    | 0     |
      | HistoryRowsChange    | 0     |
      | CurrentDataUnchanged | true  |
      | HistoryDataUnchanged | true  |

  @allure.label.scenarioId:REF06_Framework_EmptyBody
  @allure.label.branchId:products.branch.http.request-binding
  Scenario: Creating a phone with an empty JSON body returns an invalid-request problem
    An explicit zero-length application/json body cannot bind to the required create DTO.
    Given the rejected HTTP request has these details
      | Field       | Value            |
      | Method      | POST             |
      | Path        | /mobile-phones   |
      | ContentType | application/json |
    And the rejected HTTP request has an empty body
    And the catalogue and history are recorded before the rejected request
    When I send the rejected HTTP request
    Then the rejected HTTP response has this safe problem
      | Field                  | Value                               |
      | StatusCode             | 400                                 |
      | Code                   | invalid_request                     |
      | ContentType            | application/problem+json            |
      | Title                  | Invalid request.                    |
      | Detail                 | The request could not be processed. |
      | ErrorCount             | 0                                   |
      | MissingPropertiesCount | 0                                   |
    And the rejected request leaves the catalogue and history unchanged
      | Field                | Value |
      | CurrentRowsChange    | 0     |
      | HistoryRowsChange    | 0     |
      | CurrentDataUnchanged | true  |
      | HistoryDataUnchanged | true  |
```

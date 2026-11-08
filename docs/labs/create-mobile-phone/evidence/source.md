# CreateMobilePhone source evidence

Products Catalog revision `9730b12d10a6bbd7d59c2a634230be626969b6d3`. The excerpts below preserve the source text and link to the original line ranges.

## Request DTOs

[CreateMobilePhoneExternalDto.cs](https://github.com/MichalBoczula/ProductsCatalog/blob/9730b12d10a6bbd7d59c2a634230be626969b6d3/src/ProductCatalog.Application/Features/MobilePhones/Commands/CreateMobilePhone/CreateMobilePhoneExternalDto.cs#L1-L20)

```csharp
using ProductCatalog.Application.Common.Dtos.Common;
using ProductCatalog.Application.Features.Common;
using System.Text.Json.Serialization;

namespace ProductCatalog.Application.Features.MobilePhones.Commands.CreateMobilePhone
{
    public sealed record CreateMobilePhoneExternalDto(
        [property: JsonRequired] CommonDescriptionExtrernalDto CommonDescription,
        [property: JsonRequired] CreateElectronicDetailsExternalDto ElectronicDetails,
        [property: JsonRequired] CreateConnectivityExternalDto Connectivity,
        [property: JsonRequired] CreateSatelliteNavigationSystemExternalDto SatelliteNavigationSystems,
        [property: JsonRequired] CreateSensorsExternalDto Sensors,
        [property: JsonRequired] string Camera,
        [property: JsonRequired] bool FingerPrint,
        [property: JsonRequired] bool FaceId,
        [property: JsonRequired] CreateMoneyExternalDto Price,
        [property: JsonRequired] string Description2,
        [property: JsonRequired] string Description3
    );
}
```

[CreateConnectivityExternalDto.cs](https://github.com/MichalBoczula/ProductsCatalog/blob/9730b12d10a6bbd7d59c2a634230be626969b6d3/src/ProductCatalog.Application/Features/MobilePhones/Commands/CreateMobilePhone/CreateConnectivityExternalDto.cs#L1-L10)

```csharp
using System.Text.Json.Serialization;

namespace ProductCatalog.Application.Features.MobilePhones.Commands.CreateMobilePhone
{
    public sealed record CreateConnectivityExternalDto(
        [property: JsonRequired] bool Has5G,
        [property: JsonRequired] bool WiFi,
        [property: JsonRequired] bool NFC,
        [property: JsonRequired] bool Bluetooth);
}
```

[CreateSatelliteNavigationSystemExternalDto.cs](https://github.com/MichalBoczula/ProductsCatalog/blob/9730b12d10a6bbd7d59c2a634230be626969b6d3/src/ProductCatalog.Application/Features/MobilePhones/Commands/CreateMobilePhone/CreateSatelliteNavigationSystemExternalDto.cs#L1-L11)

```csharp
using System.Text.Json.Serialization;

namespace ProductCatalog.Application.Features.MobilePhones.Commands.CreateMobilePhone
{
    public sealed record CreateSatelliteNavigationSystemExternalDto(
        [property: JsonRequired] bool GPS,
        [property: JsonRequired] bool AGPS,
        [property: JsonRequired] bool Galileo,
        [property: JsonRequired] bool GLONASS,
        [property: JsonRequired] bool QZSS);
}
```

[CreateSensorsExternalDto.cs](https://github.com/MichalBoczula/ProductsCatalog/blob/9730b12d10a6bbd7d59c2a634230be626969b6d3/src/ProductCatalog.Application/Features/MobilePhones/Commands/CreateMobilePhone/CreateSensorsExternalDto.cs#L1-L13)

```csharp
using System.Text.Json.Serialization;

namespace ProductCatalog.Application.Features.MobilePhones.Commands.CreateMobilePhone
{
    public sealed record CreateSensorsExternalDto(
        [property: JsonRequired] bool Accelerometer,
        [property: JsonRequired] bool Gyroscope,
        [property: JsonRequired] bool Proximity,
        [property: JsonRequired] bool Compass,
        [property: JsonRequired] bool Barometer,
        [property: JsonRequired] bool Halla,
        [property: JsonRequired] bool AmbientLight);
}
```

[CommonDescriptionExtrernalDto.cs](https://github.com/MichalBoczula/ProductsCatalog/blob/9730b12d10a6bbd7d59c2a634230be626969b6d3/src/ProductCatalog.Application/Common/Dtos/Common/CommonDescriptionExtrernalDto.cs#L1-L9)

```csharp
namespace ProductCatalog.Application.Common.Dtos.Common
{
    public sealed record CommonDescriptionExtrernalDto(
        string Name,
        string Brand,
        string Description,
        string MainPhoto,
        IReadOnlyList<string> OtherPhotos);
}
```

[CreateElectronicDetailsExternalDto.cs](https://github.com/MichalBoczula/ProductsCatalog/blob/9730b12d10a6bbd7d59c2a634230be626969b6d3/src/ProductCatalog.Application/Features/Common/CreateElectronicDetailsExternalDto.cs#L1-L15)

```csharp
namespace ProductCatalog.Application.Features.Common
{
    public sealed record CreateElectronicDetailsExternalDto(
        string CPU,
        string GPU,
        string Ram,
        string Storage,
        string DisplayType,
        int RefreshRateHz,
        decimal ScreenSizeInches,
        int Width,
        int Height,
        string BatteryType,
        int BatteryCapacity);
}
```

[CreateMoneyExternalDto.cs](https://github.com/MichalBoczula/ProductsCatalog/blob/9730b12d10a6bbd7d59c2a634230be626969b6d3/src/ProductCatalog.Application/Features/Common/CreateMoneyExternalDto.cs#L1-L4)

```csharp
namespace ProductCatalog.Application.Features.Common
{
    public sealed record CreateMoneyExternalDto(decimal Amount, string Currency);
}
```

## HTTP and application flow

[MobilePhonesEndpoints.cs (lines 116–128)](https://github.com/MichalBoczula/ProductsCatalog/blob/9730b12d10a6bbd7d59c2a634230be626969b6d3/src/ProductCatalog.Api/Endpoints/MobilePhonesEndpoints.cs#L116-L128)

```csharp
        private static void MapMobilePhonesCommands(IEndpointRouteBuilder group)
        {
            group.MapPost("", async (CreateMobilePhoneExternalDto mobilePhone, IMediator mediator, CancellationToken cancellationToken) =>
            {
                var result = await mediator.Send(new CreateMobilePhoneCommand(mobilePhone), cancellationToken);
                return Results.Created($"/mobile-phones/{result.Id}", result);
            })
            .WithSummary("Create mobile phone")
            .WithDescription("Creates a new mobile phone and returns the created resource.")
            .WithName("CreateMobilePhone")
            .Produces<MobilePhoneDetailsDto>(StatusCodes.Status201Created)
            .Produces<ApiProblemDetails>(StatusCodes.Status400BadRequest, "application/problem+json")
            .Produces<ApiProblemDetails>(StatusCodes.Status500InternalServerError, "application/problem+json");
```

[Program.cs (lines 30–62)](https://github.com/MichalBoczula/ProductsCatalog/blob/9730b12d10a6bbd7d59c2a634230be626969b6d3/src/ProductCatalog.Api/Program.cs#L30-L62)

```csharp
            builder.Services.AddEndpointsApiExplorer();
            builder.Services.AddSwaggerGen(c =>
            {
                c.SupportNonNullableReferenceTypes();
                c.SchemaFilter<ApiContractSchemaFilter>();
                c.OperationFilter<ApiContractOperationFilter>();
            });

            builder.Services.AddDomain();
            builder.Services.AddInfrastructure(builder.Configuration);
            builder.Services.AddApplication();

            builder.Services.AddMediatR(cfg =>
                cfg.RegisterServicesFromAssembly(typeof(Application.DependencyInjection).Assembly));

            builder.Services.AddHealthChecks()
                .AddCheck("self", () => Microsoft.Extensions.Diagnostics.HealthChecks.HealthCheckResult.Healthy(), ["live"]);

            builder.Services.AddExceptionHandler<ExceptionHandler>();
            builder.Services.AddProblemDetails();
            builder.Services.Configure<RouteHandlerOptions>(options => options.ThrowOnBadRequest = true);

            var app = builder.Build();
            var applyMigrations = DatabaseConfigurationValidator.Validate(app.Configuration);

            app.UseExceptionHandler(_ => { });
            app.UseStatusCodePages(status => ApiProblemResponse.WriteEmptyStatusAsync(status.HttpContext));
            app.UseRouting();
            app.Use(async (context, next) =>
            {
                RequiredJsonProperties.EnableInspection(context);
                await next(context);
            });
```

[JsonDeserializationExceptionHandlerExtension.cs](https://github.com/MichalBoczula/ProductsCatalog/blob/9730b12d10a6bbd7d59c2a634230be626969b6d3/src/ProductCatalog.Api/Configuration/Extensions/JsonDeserializationExceptionHandlerExtension.cs#L1-L27)

```csharp
using ProductCatalog.Api.Configuration.Common;
using ProductCatalog.Application.Common.FlowDescriptors.Common;

namespace ProductCatalog.Api.Configuration.Extensions;

[FlowOutcome("products.branch.http.json-binding", "JSON syntax, scalar type, required member or non-null value-type binding fails before MediatR.", "Return invalid_json 400 with safe problem details; the business flow is not entered and no current/history write occurs.", Stage = "framework")]
public static class JsonDeserializationExceptionHandlerExtension
{
    public static async Task HandleJsonDeserializationException(
        this HttpContext context,
        CancellationToken cancellationToken)
    {
        var missing = await RequiredJsonProperties.FindMissingAsync(context, cancellationToken);
        var detail = missing.Names.Count > 0
            ? $"JSON payload for {missing.TypeName} is missing required properties: {string.Join(", ", missing.Names)}."
            : "The request body is not valid JSON.";

        await ApiProblemResponse.WriteAsync(
            context,
            StatusCodes.Status400BadRequest,
            "invalid_json",
            "Invalid JSON payload.",
            detail,
            cancellationToken,
            missingProperties: missing.Names);
    }
}
```

[CreateMobilePhoneCommandHandler.cs](https://github.com/MichalBoczula/ProductsCatalog/blob/9730b12d10a6bbd7d59c2a634230be626969b6d3/src/ProductCatalog.Application/Features/MobilePhones/Commands/CreateMobilePhone/CreateMobilePhoneCommandHandler.cs#L1-L30)

```csharp
using Mapster;
using MediatR;
using ProductCatalog.Application.Common.Dtos.MobilePhones;
using ProductCatalog.Domain.AggregatesModel.MobilePhoneAggregate;
using ProductCatalog.Domain.AggregatesModel.MobilePhoneAggregate.Repositories;
using ProductCatalog.Domain.Validation.Abstract;

namespace ProductCatalog.Application.Features.MobilePhones.Commands.CreateMobilePhone
{
    internal class CreateMobilePhoneCommandHandler(
        IMobilePhonesCommandsRepository _mobilePhonesCommandsRepository,
        IValidationPolicy<MobilePhone> _validationPolicy,
        CreateMobilePhoneCommandFlowDescribtor _createMobilePhoneCommandFlowDescribtor
        ) : IRequestHandler<CreateMobilePhoneCommand, MobilePhoneDetailsDto>
    {
        public async Task<MobilePhoneDetailsDto> Handle(CreateMobilePhoneCommand request, CancellationToken cancellationToken)
        {
            var mobilePhone = _createMobilePhoneCommandFlowDescribtor.MapRequestToMobilePhoneAggregate(request);
            var validationResult = await _createMobilePhoneCommandFlowDescribtor
                .ValidateMobilePhoneAggregate(mobilePhone, _validationPolicy);
            _createMobilePhoneCommandFlowDescribtor.ThrowValidationExceptionIfNotValid(validationResult);

            _createMobilePhoneCommandFlowDescribtor.AddMobilePhoneToRepository(mobilePhone, _mobilePhonesCommandsRepository);
            var mobilePhonesHistory = _createMobilePhoneCommandFlowDescribtor.CreateMobilePhoneHistoryEntry(mobilePhone);
            _createMobilePhoneCommandFlowDescribtor.WriteHistoryToRepository(_mobilePhonesCommandsRepository, mobilePhonesHistory);
            await _createMobilePhoneCommandFlowDescribtor.SaveChanges(_mobilePhonesCommandsRepository, cancellationToken);
            return _createMobilePhoneCommandFlowDescribtor.MapMobilePhoneToMobilePhoneDto(mobilePhone);
        }
    }
}
```

[CreateMobilePhoneCommandFlowDescribtor.cs](https://github.com/MichalBoczula/ProductsCatalog/blob/9730b12d10a6bbd7d59c2a634230be626969b6d3/src/ProductCatalog.Application/Features/MobilePhones/Commands/CreateMobilePhone/CreateMobilePhoneCommandFlowDescribtor.cs#L1-L75)

```csharp
using Mapster;
using ProductCatalog.Application.Common.Dtos.MobilePhones;
using ProductCatalog.Application.Common.FlowDescriptors.Abstract;
using ProductCatalog.Application.Common.FlowDescriptors.Common;
using ProductCatalog.Domain.AggregatesModel.MobilePhoneAggregate;
using ProductCatalog.Domain.AggregatesModel.MobilePhoneAggregate.History;
using ProductCatalog.Domain.AggregatesModel.MobilePhoneAggregate.Repositories;
using ProductCatalog.Domain.Common.Enums;
using ProductCatalog.Domain.Validation.Abstract;
using ProductCatalog.Domain.Validation.Common;

namespace ProductCatalog.Application.Features.MobilePhones.Commands.CreateMobilePhone
{
    [Documentation("products.flow.create", "Create one active phone and its Inserted history snapshot in one save.")]
    [FlowOutcome("products.branch.create.saved", "Valid details and SaveChanges succeeds.", "Create one active current row and one Inserted history row; return 201.")]
    [FlowOutcome("products.branch.create.validation", "The phone policy rejects the mapped aggregate.", "Return validation_failed 400 before writes.", "products.rule.phone-description", "products.rule.phone-strings", "products.rule.phone-exists")]
    [FlowOutcome("products.branch.create.save-failure", "The repository save throws.", "Return safe internal_error 500. The controlled BDD fault throws before EF SaveChanges; it does not prove SQL transaction rollback.")]
    internal sealed class CreateMobilePhoneCommandFlowDescribtor : FlowDescriberBase<CreateMobilePhoneCommand>
    {
        [FlowStep(1, "map-input", "Map request details to a new phone aggregate and normalize currency text.")]
        public MobilePhone MapRequestToMobilePhoneAggregate(CreateMobilePhoneCommand command)
        {
            return command.mobilePhoneExternalDto.Adapt<MobilePhone>();
        }

        [FlowStep(2, "validate", "Run the phone policy; no hardware or money rules are added by this flow.")]
        public Task<ValidationResult> ValidateMobilePhoneAggregate(MobilePhone mobilePhone, IValidationPolicy<MobilePhone> validationPolicy)
        {
            return validationPolicy.Validate(mobilePhone);
        }

        [FlowStep(3, "reject-invalid", "If phone validation fails, throw validation_failed before staging current or history rows.")]
        public void ThrowValidationExceptionIfNotValid(ValidationResult validationResult)
        {
            if (!validationResult.IsValid)
            {
                throw new ValidationException(validationResult);
            }
        }

        [FlowStep(4, "stage-current", "Stage the new phone in EF; this does not commit it.")]
        public void AddMobilePhoneToRepository(MobilePhone mobilePhone, IMobilePhonesCommandsRepository mobilePhonesCommandsRepository)
        {
            mobilePhonesCommandsRepository.Add(mobilePhone);
        }

        [FlowStep(5, "build-history", "Build the first history snapshot with operation Inserted and the phone change time.")]
        public MobilePhonesHistory CreateMobilePhoneHistoryEntry(MobilePhone mobilePhone)
        {
            var mobilePhonesHistory = mobilePhone.BuildAdapter()
                .AddParameters("operation", Operation.Inserted)
                .AdaptToType<MobilePhonesHistory>();

            return mobilePhonesHistory;
        }

        [FlowStep(6, "stage-history", "Stage the Inserted history row in the same EF context as the phone.")]
        public void WriteHistoryToRepository(IMobilePhonesCommandsRepository mobilePhonesCommandsRepository, MobilePhonesHistory mobilePhonesHistory)
        {
            mobilePhonesCommandsRepository.WriteHistory(mobilePhonesHistory);
        }

        [FlowStep(7, "save", "Save current and history together; a successful SQL save commits both, while a thrown save does not return success.")]
        public Task SaveChanges(IMobilePhonesCommandsRepository mobilePhonesCommandsRepository, CancellationToken cancellationToken)
        {
            return mobilePhonesCommandsRepository.SaveChanges(cancellationToken);
        }

        [FlowStep(8, "map-response", "Map the saved phone to details; the endpoint returns 201 and its relative Location.")]
        public MobilePhoneDetailsDto MapMobilePhoneToMobilePhoneDto(MobilePhone mobilePhone)
        {
            return mobilePhone.Adapt<MobilePhoneDetailsDto>();
        }
    }
}
```

[MappingConfig.cs (lines 119–137)](https://github.com/MichalBoczula/ProductsCatalog/blob/9730b12d10a6bbd7d59c2a634230be626969b6d3/src/ProductCatalog.Application/Mapping/MappingConfig.cs#L119-L137)

```csharp
        private static void CreateMappingForCommon()
        {
            TypeAdapterConfig<CreateMoneyExternalDto, Money>
               .NewConfig()
               .MapToConstructor(true);

            TypeAdapterConfig<Money, MoneyDto>
                .NewConfig();

            TypeAdapterConfig<CommonDescriptionExtrernalDto, CommonDescription>
               .NewConfig()
               .MapToConstructor(true);

            TypeAdapterConfig<CommonDescription, CommonDescriptionDto>
                .NewConfig();

            TypeAdapterConfig<CreateElectronicDetailsExternalDto, ElectronicDetails>
               .NewConfig()
               .MapToConstructor(true);
```

[MappingConfig.cs (lines 182–187)](https://github.com/MichalBoczula/ProductsCatalog/blob/9730b12d10a6bbd7d59c2a634230be626969b6d3/src/ProductCatalog.Application/Mapping/MappingConfig.cs#L182-L187)

```csharp
            TypeAdapterConfig<CreateMobilePhoneExternalDto, MobilePhone>
               .NewConfig()
               .MapToConstructor(true)
               .Map(dest => dest.SatelliteNavigationSystems, src => src.SatelliteNavigationSystems)
               .Map(dest => dest.Sensors, src => src.Sensors)
               .Map(dest => dest.Camera, src => src.Camera);
```

[Money.cs](https://github.com/MichalBoczula/ProductsCatalog/blob/9730b12d10a6bbd7d59c2a634230be626969b6d3/src/ProductCatalog.Domain/AggregatesModel/Common/ValueObjects/Money.cs#L1-L14)

```csharp
namespace ProductCatalog.Domain.AggregatesModel.Common.ValueObjects
{
    public record struct Money
    {
        public decimal Amount { get; private set; }
        public string Currency { get; private set; }

        public Money(decimal amount, string currency)
        {
            Amount = amount;
            Currency = currency.ToUpper();
        }
    }
}
```

[MobilePhonesCommandsRepository.cs (lines 34–56)](https://github.com/MichalBoczula/ProductsCatalog/blob/9730b12d10a6bbd7d59c2a634230be626969b6d3/src/ProductCatalog.Infrastructure/Repositories/MobilePhones/MobilePhonesCommandsRepository.cs#L34-L56)

```csharp
        public void WriteHistory(MobilePhonesHistory entity)
        {
            _db.MobilePhonesHistories.Add(entity);
        }

        public async Task SaveChanges(CancellationToken cancellationToken)
        {
            try
            {
                // EF Core saves the phone and its history in the same SaveChanges transaction.
                await _db.SaveChangesAsync(cancellationToken);
            }
            catch (DbUpdateConcurrencyException exception) when (exception.Entries.Any(x => x.Entity is MobilePhone))
            {
                var phoneId = ((MobilePhone)exception.Entries.First(x => x.Entity is MobilePhone).Entity).Id;
                _db.ChangeTracker.Clear();
                var exists = await _db.MobilePhones.AsNoTracking()
                    .AnyAsync(x => x.Id == phoneId, cancellationToken);
                if (!exists)
                    throw new ResourceNotFoundException(nameof(SaveChanges), phoneId, nameof(MobilePhone));

                throw new ConcurrencyConflictException();
            }
```

## Policy wiring and rules

[DependencyInjection.cs (lines 13–27)](https://github.com/MichalBoczula/ProductsCatalog/blob/9730b12d10a6bbd7d59c2a634230be626969b6d3/src/ProductCatalog.Domain/DependencyInjection.cs#L13-L27)

```csharp
        public static IServiceCollection AddDomain(
            this IServiceCollection services)
        {
            services.AddScoped<IValidationPolicy<MobilePhone>, MobilePhonesValidationPolicy>();
            services.AddScoped<IValidationPolicy<ElectronicDetails>, ElectronicDetailsValidationPolicy>();
            services.AddScoped<IValidationPolicy<int>, AmountValidationPolicy>();
            services.AddScoped<IValidationPolicy<MobilePhoneFilterDto>, MobilePhoneFilterValidationPolicy>();
            services.AddScoped<IValidationPolicy<PaginationParameters>, PaginationParametersValidationPolicy>();
            services.AddScoped<IValidationPolicyDescriptorProvider, MobilePhonesValidationPolicy>();
            services.AddScoped<IValidationPolicyDescriptorProvider, ElectronicDetailsValidationPolicy>();
            services.AddScoped<IValidationPolicyDescriptorProvider, AmountValidationPolicy>();
            services.AddScoped<IValidationPolicyDescriptorProvider, MobilePhoneFilterValidationPolicy>();
            services.AddScoped<IValidationPolicyDescriptorProvider, PaginationParametersValidationPolicy>();
            return services;
        }
```

[MobilePhonesValidationPolicy.cs](https://github.com/MichalBoczula/ProductsCatalog/blob/9730b12d10a6bbd7d59c2a634230be626969b6d3/src/ProductCatalog.Domain/Validation/Concrete/Policies/MobilePhonesValidationPolicy.cs#L1-L64)

```csharp
using ProductCatalog.Domain.AggregatesModel.Common.ValueObjects;
using ProductCatalog.Domain.AggregatesModel.MobilePhoneAggregate;
using ProductCatalog.Domain.Validation.Abstract;
using ProductCatalog.Domain.Validation.Common;
using ProductCatalog.Domain.Validation.Concrete.Rules.MobilePhones;

namespace ProductCatalog.Domain.Validation.Concrete.Policies
{
    [Documentation("products.policy.phone", "Validate aggregate presence, common description and camera/secondary descriptions. The money-rule collection is empty; hardware policy is not invoked.")]
    public sealed class MobilePhonesValidationPolicy
        : IValidationPolicy<MobilePhone>, IValidationPolicyDescriptorProvider
    {
        private readonly List<IValidationRule<MobilePhone>> _rules = [];
        private readonly List<IValidationRule<Money>> _moneyRules = [];

        public MobilePhonesValidationPolicy()
        {
            _rules.Add(new MobilePhonesCommonDescriptionValidationRule());
            _rules.Add(new MobilePhonesStringValidationRule());
            _rules.Add(new MobilePhonesIsNullValidationRule());
        }

        public async Task<ValidationResult> Validate(MobilePhone entity)
        {
            ValidationResult validationResult = new();

            foreach (var rule in _rules)
                await rule.IsValid(entity, validationResult);

            if (entity == null)
                return validationResult;

            foreach (var rule in _moneyRules)
                await rule.IsValid(entity.Price, validationResult);

            return validationResult;
        }

        public ValidationPolicyDescriptor Describe()
        {
            var mobilePhoneErrors = _rules
                .Select(rule => new ValidationRuleDescriptor()
                {
                    RuleName = rule.GetType().Name,
                    Rules = rule.Describe()
                })
                .ToList();

            var moneyErrors = _moneyRules
                .Select(rule => new ValidationRuleDescriptor()
                {
                    RuleName = rule.GetType().Name,
                    Rules = rule.Describe()
                })
                .ToList();

            return new ValidationPolicyDescriptor()
            {
                PolicyName = nameof(MobilePhonesValidationPolicy),
                Rules = mobilePhoneErrors.Concat(moneyErrors).ToList()
            };
        }
    }
}
```

[MobilePhonesCommonDescriptionValidationRule.cs](https://github.com/MichalBoczula/ProductsCatalog/blob/9730b12d10a6bbd7d59c2a634230be626969b6d3/src/ProductCatalog.Domain/Validation/Concrete/Rules/MobilePhones/MobilePhonesCommonDescriptionValidationRule.cs#L1-L68)

```csharp
using ProductCatalog.Domain.AggregatesModel.MobilePhoneAggregate;
using ProductCatalog.Domain.Validation.Abstract;
using ProductCatalog.Domain.Validation.Common;

namespace ProductCatalog.Domain.Validation.Concrete.Rules.MobilePhones
{
    [Documentation("products.rule.phone-description", "Reject a missing common description or blank name, brand or main description; do not validate photo references here.")]
    public sealed class MobilePhonesCommonDescriptionValidationRule : IValidationRule<MobilePhone>
    {
        private readonly ValidationError commonDescriptionIsNull;
        private readonly ValidationError nameIsNullOrWhitespace;
        private readonly ValidationError descriptionIsNullOrWhitespace;
        private readonly ValidationError brandIsNullOrWhitespace;

        public MobilePhonesCommonDescriptionValidationRule()
        {
            commonDescriptionIsNull = new ValidationError
            {
                Message = "Common description cannot be null.",
                Name = nameof(MobilePhonesCommonDescriptionValidationRule),
                Entity = nameof(MobilePhone)
            };
            nameIsNullOrWhitespace = new ValidationError
            {
                Message = "Name cannot be null or whitespace.",
                Name = nameof(MobilePhonesCommonDescriptionValidationRule),
                Entity = nameof(MobilePhone)
            };
            descriptionIsNullOrWhitespace = new ValidationError
            {
                Message = "Description cannot be null or whitespace.",
                Name = nameof(MobilePhonesCommonDescriptionValidationRule),
                Entity = nameof(MobilePhone)
            };
            brandIsNullOrWhitespace = new ValidationError
            {
                Message = "Brand cannot be null or whitespace.",
                Name = nameof(MobilePhonesCommonDescriptionValidationRule),
                Entity = nameof(MobilePhone)
            };
        }

        public async Task IsValid(MobilePhone entity, ValidationResult validationResults)
        {
            if (entity == null) return;

            if (entity.CommonDescription == default)
            {
                validationResults.AddValidationError(commonDescriptionIsNull);
                return;
            }

            if (string.IsNullOrWhiteSpace(entity.CommonDescription.Name))
                validationResults.AddValidationError(nameIsNullOrWhitespace);

            if (string.IsNullOrWhiteSpace(entity.CommonDescription.Description))
                validationResults.AddValidationError(descriptionIsNullOrWhitespace);

            if (string.IsNullOrWhiteSpace(entity.CommonDescription.Brand))
                validationResults.AddValidationError(brandIsNullOrWhitespace);
        }

        public List<ValidationError> Describe()
        {
            return [commonDescriptionIsNull, nameIsNullOrWhitespace, descriptionIsNullOrWhitespace, brandIsNullOrWhitespace];
        }
    }
}
```

[MobilePhonesStringValidationRule.cs (lines 36–48)](https://github.com/MichalBoczula/ProductsCatalog/blob/9730b12d10a6bbd7d59c2a634230be626969b6d3/src/ProductCatalog.Domain/Validation/Concrete/Rules/MobilePhones/MobilePhonesStringValidationRule.cs#L36-L48)

```csharp
        public async Task IsValid(MobilePhone entity, ValidationResult validationResults)
        {
            if (entity == null) return;

            if (string.IsNullOrWhiteSpace(entity.Description2))
                validationResults.AddValidationError(description2IsNullOrWhitespace);

            if (string.IsNullOrWhiteSpace(entity.Description3))
                validationResults.AddValidationError(description3IsNullOrWhitespace);

            if (string.IsNullOrWhiteSpace(entity.Camera))
                validationResults.AddValidationError(camera);
        }
```

[MobilePhonesIsNullValidationRule.cs](https://github.com/MichalBoczula/ProductsCatalog/blob/9730b12d10a6bbd7d59c2a634230be626969b6d3/src/ProductCatalog.Domain/Validation/Concrete/Rules/MobilePhones/MobilePhonesIsNullValidationRule.cs#L1-L33)

```csharp
using ProductCatalog.Domain.AggregatesModel.MobilePhoneAggregate;
using ProductCatalog.Domain.Validation.Abstract;
using ProductCatalog.Domain.Validation.Common;

namespace ProductCatalog.Domain.Validation.Concrete.Rules.MobilePhones
{
    [Documentation("products.rule.phone-exists", "Reject a missing phone aggregate; update/delete currently expose this policy rejection as 400 before saving.")]
    public sealed class MobilePhonesIsNullValidationRule : IValidationRule<MobilePhone>
    {
        private readonly ValidationError mobilePhoneIsNull;

        public MobilePhonesIsNullValidationRule()
        {
            mobilePhoneIsNull = new ValidationError
            {
                Message = "Mobile phone cannot be null.",
                Name = nameof(MobilePhonesIsNullValidationRule),
                Entity = nameof(MobilePhone),
            };
        }

        public async Task IsValid(MobilePhone entity, ValidationResult validationResults)
        {
            if (entity == null)
                validationResults.AddValidationError(mobilePhoneIsNull);
        }

        public List<ValidationError> Describe()
        {
            return [mobilePhoneIsNull];
        }
    }
}
```

[ElectronicDetailsValidationPolicy.cs (lines 9–21)](https://github.com/MichalBoczula/ProductsCatalog/blob/9730b12d10a6bbd7d59c2a634230be626969b6d3/src/ProductCatalog.Domain/Validation/Concrete/Policies/ElectronicDetailsValidationPolicy.cs#L9-L21)

```csharp
    public sealed class ElectronicDetailsValidationPolicy
        : IValidationPolicy<ElectronicDetails>, IValidationPolicyDescriptorProvider
    {
        private readonly List<IValidationRule<ElectronicDetails>> _rules = [];

        public ElectronicDetailsValidationPolicy()
        {
            _rules.Add(new ElectronicDetailsStringsValidationRule());
            _rules.Add(new ElectronicDetailsNumbersValidationRule());
        }

        public async Task<ValidationResult> Validate(ElectronicDetails entity)
        {
```

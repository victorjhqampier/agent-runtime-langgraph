from Domain.Containers.DependencyInjection.CoreServices import CoreServices as Services
from Infrastructure.Securities.RuntimeSecurity.SecuritySettings import SecuritySettings
from Infrastructure.Securities.RuntimeSecurity.Commands.MaskSensitiveDataCommand import MaskSensitiveDataCommand


class SecuritySetting:
    @classmethod
    def add_services(cls) -> None:
        Services.add_singleton_instance(MaskSensitiveDataCommand(SecuritySettings()))

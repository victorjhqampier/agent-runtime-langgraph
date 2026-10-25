import ast
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))


class ArchitectureBoundaryTests(unittest.TestCase):
    project_root = Path(__file__).resolve().parents[2]
    source_root = project_root / "src"

    def get_imports(self, directory: Path) -> dict[Path, set[str]]:
        imports: dict[Path, set[str]] = {}
        for source_file in directory.rglob("*.py"):
            tree = ast.parse(source_file.read_text(encoding="utf-8"), filename=str(source_file))
            modules: set[str] = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    modules.update(alias.name for alias in node.names)
                if isinstance(node, ast.ImportFrom) and node.module:
                    modules.add(node.module)
            imports[source_file] = modules
        return imports

    def get_forbidden_imports(self, imports: set[str], forbidden_roots: set[str]) -> set[str]:
        return {module for module in imports if module.split(".")[0] in forbidden_roots}

    def test_infrastructure_does_not_depend_on_inner_or_presentation_layers(self) -> None:
        forbidden_roots = {"Runtime", "Presentation", "Application"}

        violations = {
            str(source_file.relative_to(self.source_root)): self.get_forbidden_imports(imports, forbidden_roots)
            for source_file, imports in self.get_imports(self.source_root / "Infrastructure").items()
            if self.get_forbidden_imports(imports, forbidden_roots)
        }

        self.assertEqual({}, violations)

    def test_domain_is_independent_of_layers_and_provider_sdks(self) -> None:
        forbidden_roots = {"Application", "Infrastructure", "Presentation", "Runtime", "boto3", "botocore", "fastapi", "langchain", "langgraph", "livekit", "redis"}

        violations = {
            str(source_file.relative_to(self.source_root)): self.get_forbidden_imports(imports, forbidden_roots)
            for source_file, imports in self.get_imports(self.source_root / "Domain").items()
            if self.get_forbidden_imports(imports, forbidden_roots)
        }

        self.assertEqual({}, violations)

    def test_runtime_provider_dependencies_are_limited_to_the_composition_root(self) -> None:
        runtime_imports = self.get_imports(self.source_root / "Runtime")
        violations = {
            str(source_file.relative_to(self.source_root)): self.get_forbidden_imports(imports, {"Infrastructure"})
            for source_file, imports in runtime_imports.items()
            if source_file.name != "CoreRuntimeSetting.py" and self.get_forbidden_imports(imports, {"Infrastructure"})
        }

        self.assertEqual({}, violations)
        composition_imports = runtime_imports[self.source_root / "Runtime" / "CoreRuntimeSetting.py"]
        self.assertIn("Infrastructure.InfrastructureSetting", composition_imports)
        self.assertNotIn("langgraph.checkpoint.redis", composition_imports)

    def test_workflow_logic_does_not_import_infrastructure_providers(self) -> None:
        workflow_directories = [
            self.source_root / "Runtime" / "UseCases" / "AttendIncident" / "Nodes",
            self.source_root / "Runtime" / "UseCases" / "AttendIncident" / "Workflows",
            self.source_root / "Runtime" / "UseCases" / "AttendIncident",
        ]
        violations: dict[str, set[str]] = {}
        for directory in workflow_directories:
            for source_file, imports in self.get_imports(directory).items():
                forbidden = self.get_forbidden_imports(imports, {"Infrastructure"})
                if forbidden:
                    violations[str(source_file.relative_to(self.source_root))] = forbidden

        self.assertEqual({}, violations)

    def test_agentcore_entrypoint_does_not_depend_on_fastapi(self) -> None:
        imports = self.get_imports(self.source_root / "Presentation" / "AmazonAgentcore")
        violations = {
            str(source_file.relative_to(self.source_root)): self.get_forbidden_imports(module_imports, {"fastapi", "Presentation.FastApi"})
            for source_file, module_imports in imports.items()
            if self.get_forbidden_imports(module_imports, {"fastapi", "Presentation.FastApi"})
        }

        self.assertEqual({}, violations)

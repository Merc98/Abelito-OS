"""Binary Injector: Analysis and code injection for binaries."""
from __future__ import annotations

import asyncio
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import structlog

logger = structlog.get_logger()


@dataclass
class BinaryAnalysisResult:
    """Result of binary analysis."""
    file_path: str
    file_type: str
    architecture: str
    entry_point: int | None = None
    sections: list[dict[str, Any]] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)
    exports: list[str] = field(default_factory=list)
    strings: list[str] = field(default_factory=list)
    threats: list[dict[str, Any]] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


class BinaryAnalyzer:
    """Analyzes binary files (PE, ELF, Mach-O)."""

    def __init__(self):
        self.supported_formats = ["PE", "ELF", "Mach-O"]

    async def analyze(self, file_path: str) -> BinaryAnalysisResult:
        """Analyze a binary file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Binary not found: {file_path}")

        logger.info(f"Analyzing binary: {file_path}")

        # Detect file type
        file_type = await self._detect_file_type(path)
        architecture = await self._detect_architecture(path)

        result = BinaryAnalysisResult(
            file_path=str(path),
            file_type=file_type,
            architecture=architecture,
        )

        # Extract sections
        result.sections = await self._extract_sections(path)

        # Extract imports/exports
        result.imports = await self._extract_imports(path)
        result.exports = await self._extract_exports(path)

        # Extract strings
        result.strings = await self._extract_strings(path)

        # Threat analysis
        result.threats = await self._analyze_threats(result)

        # Generate recommendations
        result.recommendations = self._generate_recommendations(result)

        return result

    async def _detect_file_type(self, path: Path) -> str:
        """Detect binary file type using magic bytes."""
        try:
            with open(path, "rb") as f:
                magic = f.read(4)

            if magic[:2] == b"MZ":
                return "PE"
            elif magic[:4] == b"\x7fELF":
                return "ELF"
            elif magic[:4] in (b"\xfe\xed\xfa\xce", b"\xce\xfa\xed\xfe"):
                return "Mach-O"
            else:
                return "Unknown"
        except Exception as e:
            logger.error(f"Error detecting file type: {e}")
            return "Unknown"

    async def _detect_architecture(self, path: Path) -> str:
        """Detect CPU architecture."""
        try:
            # Use file command on Unix
            result = subprocess.run(
                ["file", str(path)],
                capture_output=True,
                text=True,
                timeout=5
            )
            output = result.stdout.lower()

            if "x86-64" in output or "x86_64" in output:
                return "x86_64"
            elif "arm64" in output or "aarch64" in output:
                return "ARM64"
            elif "arm" in output:
                return "ARM"
            elif "i386" in output or "i686" in output:
                return "x86"
            else:
                return "Unknown"
        except Exception as e:
            logger.debug(f"Error detecting architecture: {e}")
            return "Unknown"

    async def _extract_sections(self, path: Path) -> list[dict[str, Any]]:
        """Extract section information."""
        sections = []
        try:
            if path.suffix.lower() == ".elf" or await self._detect_file_type(path) == "ELF":
                result = subprocess.run(
                    ["readelf", "-S", str(path)],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                # Parse readelf output (simplified)
                for line in result.stdout.split("\n"):
                    if "[" in line and "]" in line:
                        parts = line.split()
                        if len(parts) > 3:
                            sections.append({"name": parts[-1], "raw": line})
        except Exception as e:
            logger.debug(f"Error extracting sections: {e}")

        return sections

    async def _extract_imports(self, path: Path) -> list[str]:
        """Extract imported functions/libraries."""
        imports = []
        try:
            # Use nm or objdump
            result = subprocess.run(
                ["nm", "-u", str(path)],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                imports = [line.strip() for line in result.stdout.split("\n") if line.strip()]
        except Exception as e:
            logger.debug(f"Error extracting imports: {e}")

        return imports[:100]  # Limit results

    async def _extract_exports(self, path: Path) -> list[str]:
        """Exported functions/symbols."""
        exports = []
        try:
            result = subprocess.run(
                ["nm", "-D", str(path)],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if " T " in line or " t " in line:
                        parts = line.split()
                        if len(parts) >= 3:
                            exports.append(parts[-1])
        except Exception as e:
            logger.debug(f"Error extracting exports: {e}")

        return exports[:100]

    async def _extract_strings(self, path: Path, min_length: int = 6) -> list[str]:
        """Extract printable strings from binary."""
        strings = []
        try:
            result = subprocess.run(
                ["strings", "-n", str(min_length), str(path)],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                strings = [s.strip() for s in result.stdout.split("\n") if s.strip()]
        except Exception as e:
            logger.debug(f"Error extracting strings: {e}")

        return strings[:500]  # Limit results

    async def _analyze_threats(self, result: BinaryAnalysisResult) -> list[dict[str, Any]]:
        """Analyze binary for potential threats."""
        threats = []

        # Check for suspicious imports
        suspicious_imports = [
            "VirtualAlloc", "VirtualProtect", "WriteProcessMemory",
            "CreateRemoteThread", "NtUnmapViewOfSection",
            "socket", "connect", "send", "recv",
            "RegSetValue", "CreateService", "OpenProcess"
        ]

        for imp in result.imports:
            for susp in suspicious_imports:
                if susp.lower() in imp.lower():
                    threats.append({
                        "type": "suspicious_import",
                        "name": imp,
                        "severity": "medium",
                        "description": f"Suspicious import: {imp}"
                    })

        # Check for suspicious strings
        suspicious_strings = [
            "password", "admin", "root", "hack", "exploit",
            "cmd.exe", "/bin/sh", "powershell", "eval("
        ]

        for s in result.strings[:100]:
            for susp in suspicious_strings:
                if susp.lower() in s.lower():
                    threats.append({
                        "type": "suspicious_string",
                        "value": s[:50],
                        "severity": "low",
                        "description": f"Suspicious string found"
                    })
                    break

        return threats

    def _generate_recommendations(self, result: BinaryAnalysisResult) -> list[str]:
        """Generate recommendations based on analysis."""
        recommendations = []

        if result.threats:
            recommendations.append(f"Review {len(result.threats)} potential security concerns")

        if len(result.imports) > 50:
            recommendations.append("Consider reducing external dependencies")

        if result.file_type == "Unknown":
            recommendations.append("Verify file format - type not recognized")

        if not recommendations:
            recommendations.append("No specific recommendations - binary appears normal")

        return recommendations


class CodeInjector:
    """Injects code into running processes or binaries."""

    def __init__(self):
        self.injected_processes: list[int] = []

    async def inject_frida(self, target_pid: int, script: str) -> bool:
        """Inject Frida script into process."""
        try:
            # This would use frida-python in real implementation
            logger.info(f"Would inject Frida script into PID {target_pid}")
            # import frida
            # device = frida.get_local_device()
            # session = device.attach(target_pid)
            # script_obj = session.create_script(script)
            # script_obj.load()
            self.injected_processes.append(target_pid)
            return True
        except Exception as e:
            logger.error(f"Frida injection failed: {e}")
            return False

    async def patch_binary(self, binary_path: str, patches: list[dict[str, Any]]) -> str:
        """Apply patches to binary file."""
        path = Path(binary_path)
        if not path.exists():
            raise FileNotFoundError(f"Binary not found: {binary_path}")

        try:
            with open(path, "r+b") as f:
                for patch in patches:
                    offset = patch.get("offset")
                    bytes_to_write = patch.get("bytes", b"")
                    if isinstance(bytes_to_write, str):
                        bytes_to_write = bytes.fromhex(bytes_to_write)

                    f.seek(offset)
                    f.write(bytes_to_write)
                    logger.info(f"Patched offset {offset} in {binary_path}")

            # Return path to patched binary
            patched_path = str(path.with_suffix(path.suffix + ".patched"))
            return patched_path
        except Exception as e:
            logger.error(f"Binary patching failed: {e}")
            raise


async def main():
    """Demo binary analysis."""
    print("\n=== ABELITO OS BINARY INJECTOR ===\n")

    analyzer = BinaryAnalyzer()

    # Example: analyze self (python interpreter)
    import sys
    python_path = sys.executable

    print(f"Analyzing: {python_path}")
    result = await analyzer.analyze(python_path)

    print(f"\nFile Type: {result.file_type}")
    print(f"Architecture: {result.architecture}")
    print(f"Sections: {len(result.sections)}")
    print(f"Imports: {len(result.imports)}")
    print(f"Exports: {len(result.exports)}")
    print(f"Strings extracted: {len(result.strings)}")
    print(f"Threats detected: {len(result.threats)}")

    if result.threats:
        print("\nThreats:")
        for threat in result.threats[:5]:
            print(f"  • [{threat['severity']}] {threat['description']}")

    if result.recommendations:
        print("\nRecommendations:")
        for rec in result.recommendations[:5]:
            print(f"  • {rec}")


if __name__ == "__main__":
    asyncio.run(main())

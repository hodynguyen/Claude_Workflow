"""Build the complete project profile — orchestrator that imports all detectors."""
import os

from detectors.utils import read_json
from detectors.node import detect_node
from detectors.go import detect_go
from detectors.python_lang import detect_python
from detectors.rust import detect_rust
from detectors.java import detect_java
from detectors.csharp import detect_csharp
from detectors.ruby import detect_ruby
from detectors.php import detect_php
from detectors.devops import detect_devops
from detectors.monorepo import detect_monorepo
from detectors.database import detect_database
from detectors.conventions import detect_conventions
from detectors.integrations import load_existing_integrations


def build_profile(cwd):
    """Build the complete project profile."""
    project_name = os.path.basename(os.path.abspath(cwd))

    # Try to get name from package.json
    pkg = read_json(os.path.join(cwd, "package.json"))
    if pkg and pkg.get("name"):
        project_name = pkg["name"]

    profile = {"project": {"name": project_name}}

    # Detect stacks
    fe = None
    be = None
    testing = None
    e2e = None
    linter = None
    formatter = None

    # Node.js detection
    node_result = detect_node(cwd)
    if node_result and isinstance(node_result, tuple) and len(node_result) == 6:
        node_fe, node_be, testing, e2e, linter, formatter = node_result
        if node_fe:
            fe = node_fe
        if node_be:
            be = node_be

    # Go detection (can override/add backend)
    go_be = detect_go(cwd)
    if go_be:
        be = go_be
        if not testing:
            testing = "go-test"

    # Python detection (can override/add backend)
    py_be, py_testing = detect_python(cwd)
    if py_be:
        be = py_be
    if py_testing and not testing:
        testing = py_testing

    # Rust detection
    rust_be, rust_testing = detect_rust(cwd)
    if rust_be:
        be = rust_be
    if rust_testing and not testing:
        testing = rust_testing

    # Java detection
    java_be, java_testing = detect_java(cwd)
    if java_be:
        be = java_be
    if java_testing and not testing:
        testing = java_testing

    # C#/.NET detection
    csharp_be, csharp_testing = detect_csharp(cwd)
    if csharp_be:
        be = csharp_be
    if csharp_testing and not testing:
        testing = csharp_testing

    # Ruby detection
    ruby_be, ruby_testing = detect_ruby(cwd)
    if ruby_be:
        be = ruby_be
    if ruby_testing and not testing:
        testing = ruby_testing

    # PHP detection
    php_be, php_testing = detect_php(cwd)
    if php_be:
        be = php_be
    if php_testing and not testing:
        testing = php_testing

    # Monorepo detection
    monorepo = detect_monorepo(cwd)
    if monorepo:
        profile["project"]["type"] = "monorepo"
        profile["monorepo"] = monorepo
    # Determine project type
    elif fe and be:
        profile["project"]["type"] = "fullstack"
    elif fe:
        profile["project"]["type"] = "frontend"
    elif be:
        profile["project"]["type"] = "backend"
    else:
        profile["project"]["type"] = "unknown"

    # Database
    db = detect_database(cwd)

    # Add sections
    if fe:
        if testing:
            fe["testing"] = testing
        if e2e:
            fe["e2e"] = e2e
        profile["frontend"] = fe

    if be:
        if db:
            be["database"] = db
        if testing:
            be["testing"] = testing
        profile["backend"] = be

    # DevOps
    devops = detect_devops(cwd)
    if devops:
        profile["devops"] = devops

    # Conventions
    conventions = detect_conventions(cwd)
    if linter:
        conventions = conventions or {}
        conventions["linter"] = linter
    if formatter:
        conventions = conventions or {}
        conventions["formatter"] = formatter
    if conventions:
        profile["conventions"] = conventions

    # Preserve user-configured integrations from existing profile
    integrations = load_existing_integrations(cwd)
    if integrations:
        profile["integrations"] = integrations

    return profile

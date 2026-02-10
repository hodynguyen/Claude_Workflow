#!/usr/bin/env python3
"""
Auto-detect project tech stack from config files.
Outputs .hody/profile.yaml with detected stack info.

Supported stacks:
  - Node.js (React, Vue, Angular, Svelte, SvelteKit, Next, Nuxt, Express, Fastify, Nest)
  - Go (Gin, Echo, Fiber)
  - Python (Django, FastAPI, Flask)
  - Rust (Actix-web, Rocket, Axum)
  - Java/Kotlin (Spring Boot, Quarkus, Micronaut)
  - C#/.NET (ASP.NET Core, Blazor, Entity Framework)
  - Ruby (Rails, Sinatra, Hanami)
  - PHP (Laravel, Symfony, Magento)
  - Docker, GitHub Actions, GitLab CI, Jenkins
  - Terraform, Pulumi
"""
import json
import os
import sys
import argparse


def read_json(path):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError, PermissionError):
        return None


def read_lines(path):
    try:
        with open(path, "r") as f:
            return f.read().lower()
    except (FileNotFoundError, PermissionError):
        return ""


def detect_node(cwd):
    """Detect Node.js project from package.json."""
    pkg = read_json(os.path.join(cwd, "package.json"))
    if not pkg:
        return None, None

    deps = {}
    deps.update(pkg.get("dependencies", {}))
    dev_deps = pkg.get("devDependencies", {})

    result = {"language": "javascript"}

    # TypeScript
    if "typescript" in dev_deps or "typescript" in deps:
        result["language"] = "typescript"

    # Frontend framework
    fe = {}
    if "react" in deps or "react-dom" in deps:
        fe["framework"] = "react"
    elif "vue" in deps:
        fe["framework"] = "vue"
    elif "svelte" in deps:
        fe["framework"] = "svelte"
    elif "@angular/core" in deps:
        fe["framework"] = "angular"

    # SSR/meta frameworks (override)
    if "next" in deps:
        fe["framework"] = "next"
    elif "nuxt" in deps:
        fe["framework"] = "nuxt"
    elif "@sveltejs/kit" in deps or "@sveltejs/kit" in dev_deps:
        fe["framework"] = "sveltekit"

    # State management
    if "zustand" in deps:
        fe["state"] = "zustand"
    elif "redux" in deps or "@reduxjs/toolkit" in deps:
        fe["state"] = "redux"
    elif "pinia" in deps:
        fe["state"] = "pinia"
    elif "mobx" in deps:
        fe["state"] = "mobx"

    # Styling
    if "tailwindcss" in deps or "tailwindcss" in dev_deps:
        fe["styling"] = "tailwind"
    elif "styled-components" in deps:
        fe["styling"] = "styled-components"
    elif "sass" in dev_deps or "node-sass" in dev_deps:
        fe["styling"] = "scss"

    # Build tool
    if "vite" in dev_deps:
        fe["build"] = "vite"
    elif "webpack" in dev_deps:
        fe["build"] = "webpack"
    elif "esbuild" in dev_deps:
        fe["build"] = "esbuild"

    if fe.get("framework"):
        fe["language"] = result["language"]

    # Backend framework
    be = {}
    if "express" in deps:
        be["framework"] = "express"
    elif "fastify" in deps:
        be["framework"] = "fastify"
    elif "@nestjs/core" in deps:
        be["framework"] = "nest"

    # ORM
    if "prisma" in dev_deps or "@prisma/client" in deps:
        be["orm"] = "prisma"
    elif "drizzle-orm" in deps:
        be["orm"] = "drizzle"
    elif "typeorm" in deps:
        be["orm"] = "typeorm"
    elif "sequelize" in deps:
        be["orm"] = "sequelize"

    if be.get("framework"):
        be["language"] = result["language"]

    # Testing
    testing = None
    if "vitest" in dev_deps:
        testing = "vitest"
    elif "jest" in dev_deps:
        testing = "jest"

    # E2E testing
    e2e = None
    if "playwright" in dev_deps or "@playwright/test" in dev_deps:
        e2e = "playwright"
    elif "cypress" in dev_deps:
        e2e = "cypress"

    # Linter / Formatter
    linter = None
    formatter = None
    if "eslint" in dev_deps:
        linter = "eslint"
    elif "@biomejs/biome" in dev_deps:
        linter = "biome"
    if "prettier" in dev_deps:
        formatter = "prettier"
    elif "@biomejs/biome" in dev_deps:
        formatter = "biome"

    return (
        fe if fe.get("framework") else None,
        be if be.get("framework") else None,
        testing,
        e2e,
        linter,
        formatter,
    )


def detect_go(cwd):
    """Detect Go project from go.mod."""
    gomod_path = os.path.join(cwd, "go.mod")
    content = read_lines(gomod_path)
    if not content:
        return None

    be = {"language": "go"}

    if "github.com/gin-gonic/gin" in content:
        be["framework"] = "gin"
    elif "github.com/labstack/echo" in content:
        be["framework"] = "echo"
    elif "github.com/gofiber/fiber" in content:
        be["framework"] = "fiber"

    if "gorm.io/gorm" in content:
        be["orm"] = "gorm"
    elif "github.com/jmoiron/sqlx" in content:
        be["orm"] = "sqlx"

    return be


def detect_python(cwd):
    """Detect Python project from requirements.txt or pyproject.toml."""
    content = ""
    for fname in ["requirements.txt", "Pipfile", "pyproject.toml", "setup.py"]:
        content += read_lines(os.path.join(cwd, fname))

    if not content:
        return None, None

    be = {"language": "python"}
    testing = None

    if "django" in content:
        be["framework"] = "django"
    elif "fastapi" in content:
        be["framework"] = "fastapi"
    elif "flask" in content:
        be["framework"] = "flask"

    if "sqlalchemy" in content:
        be["orm"] = "sqlalchemy"
    elif "django" in content:
        be["orm"] = "django-orm"

    if "pytest" in content:
        testing = "pytest"
    elif "unittest" in content:
        testing = "unittest"

    return be if be.get("framework") else None, testing


def detect_rust(cwd):
    """Detect Rust project from Cargo.toml."""
    content = read_lines(os.path.join(cwd, "Cargo.toml"))
    if not content:
        return None, None

    be = {"language": "rust"}
    testing = "cargo-test"

    if "actix-web" in content:
        be["framework"] = "actix-web"
    elif "rocket" in content:
        be["framework"] = "rocket"
    elif "axum" in content:
        be["framework"] = "axum"

    if "diesel" in content:
        be["orm"] = "diesel"
    elif "sqlx" in content:
        be["orm"] = "sqlx"
    elif "sea-orm" in content:
        be["orm"] = "sea-orm"

    return be if be.get("framework") else None, testing


def detect_java(cwd):
    """Detect Java project from pom.xml or build.gradle."""
    content = ""
    build_tool = None

    pom_content = read_lines(os.path.join(cwd, "pom.xml"))
    if pom_content:
        content = pom_content
        build_tool = "maven"

    gradle_content = read_lines(os.path.join(cwd, "build.gradle"))
    if not gradle_content:
        gradle_content = read_lines(os.path.join(cwd, "build.gradle.kts"))
    if gradle_content:
        content += gradle_content
        build_tool = "gradle"

    if not content:
        return None, None

    be = {"language": "java", "build": build_tool}

    if "spring-boot" in content or "org.springframework.boot" in content:
        be["framework"] = "spring-boot"
    elif "quarkus" in content or "io.quarkus" in content:
        be["framework"] = "quarkus"
    elif "micronaut" in content or "io.micronaut" in content:
        be["framework"] = "micronaut"

    if "kotlin" in content:
        be["language"] = "kotlin"

    return be if be.get("framework") else None, "junit"


def detect_csharp(cwd):
    """Detect C#/.NET project from .csproj, .sln, or global.json."""
    content = ""

    # Check for .sln files
    sln_files = [f for f in os.listdir(cwd) if f.endswith(".sln")] if os.path.isdir(cwd) else []
    # Check for .csproj files
    csproj_files = [f for f in os.listdir(cwd) if f.endswith(".csproj")] if os.path.isdir(cwd) else []

    for f in csproj_files:
        content += read_lines(os.path.join(cwd, f))

    global_json = read_lines(os.path.join(cwd, "global.json"))
    content += global_json

    if not content and not sln_files and not csproj_files:
        return None, None

    be = {"language": "csharp"}
    testing = None

    if "microsoft.aspnetcore" in content or "asp.net" in content or "webapplication" in content:
        be["framework"] = "aspnet-core"
    elif "microsoft.net.sdk.blazor" in content or "blazor" in content:
        be["framework"] = "blazor"

    if "microsoft.entityframeworkcore" in content or "entityframework" in content:
        be["orm"] = "entity-framework"
    elif "dapper" in content:
        be["orm"] = "dapper"

    if "xunit" in content:
        testing = "xunit"
    elif "nunit" in content:
        testing = "nunit"
    elif "mstest" in content:
        testing = "mstest"

    # If we found .csproj or .sln but no framework, still return as C# project
    if not be.get("framework") and (sln_files or csproj_files):
        be["framework"] = "dotnet"

    return be if be.get("framework") else None, testing


def detect_ruby(cwd):
    """Detect Ruby project from Gemfile."""
    content = read_lines(os.path.join(cwd, "Gemfile"))
    if not content:
        return None, None

    be = {"language": "ruby"}
    testing = None

    if "rails" in content or "railties" in content:
        be["framework"] = "rails"
    elif "sinatra" in content:
        be["framework"] = "sinatra"
    elif "hanami" in content:
        be["framework"] = "hanami"

    if "activerecord" in content or "rails" in content:
        be["orm"] = "activerecord"
    elif "sequel" in content:
        be["orm"] = "sequel"

    if "rspec" in content:
        testing = "rspec"
    elif "minitest" in content:
        testing = "minitest"

    return be if be.get("framework") else None, testing


def detect_php(cwd):
    """Detect PHP project from composer.json."""
    composer = read_json(os.path.join(cwd, "composer.json"))
    if not composer:
        return None, None

    require = {}
    require.update(composer.get("require", {}))
    require_dev = composer.get("require-dev", {})

    be = {"language": "php"}
    testing = None

    if "laravel/framework" in require:
        be["framework"] = "laravel"
    elif "symfony/framework-bundle" in require or "symfony/symfony" in require:
        be["framework"] = "symfony"
    elif "magento/product-community-edition" in require or "magento/magento2-base" in require:
        be["framework"] = "magento"
    elif "slim/slim" in require:
        be["framework"] = "slim"

    if "doctrine/orm" in require:
        be["orm"] = "doctrine"
    elif "illuminate/database" in require or "laravel/framework" in require:
        be["orm"] = "eloquent"

    if "phpunit/phpunit" in require_dev or "phpunit/phpunit" in require:
        testing = "phpunit"
    elif "pestphp/pest" in require_dev:
        testing = "pest"

    return be if be.get("framework") else None, testing


def detect_devops(cwd):
    """Detect CI/CD, containerization, and infrastructure."""
    devops = {}

    # Container
    if os.path.isfile(os.path.join(cwd, "Dockerfile")):
        devops["containerize"] = "docker"
    elif os.path.isfile(os.path.join(cwd, "docker-compose.yml")) or os.path.isfile(
        os.path.join(cwd, "docker-compose.yaml")
    ):
        devops["containerize"] = "docker"

    # CI
    if os.path.isdir(os.path.join(cwd, ".github", "workflows")):
        devops["ci"] = "github-actions"
    elif os.path.isfile(os.path.join(cwd, ".gitlab-ci.yml")):
        devops["ci"] = "gitlab-ci"
    elif os.path.isfile(os.path.join(cwd, "Jenkinsfile")):
        devops["ci"] = "jenkins"

    # Infrastructure
    tf_files = [f for f in os.listdir(cwd) if f.endswith(".tf")] if os.path.isdir(cwd) else []
    if tf_files:
        devops["infra"] = "terraform"
    elif os.path.isdir(os.path.join(cwd, "pulumi")):
        devops["infra"] = "pulumi"

    return devops if devops else None


def detect_conventions(cwd):
    """Detect project conventions."""
    conventions = {}

    if os.path.isfile(os.path.join(cwd, ".github", "PULL_REQUEST_TEMPLATE.md")):
        conventions["pr_template"] = True

    return conventions if conventions else None


def detect_database(cwd):
    """Try to detect database from common config patterns."""
    db = None
    for fname in ["docker-compose.yml", "docker-compose.yaml", ".env", ".env.example"]:
        content = read_lines(os.path.join(cwd, fname))
        if "postgres" in content or "postgresql" in content:
            db = "postgresql"
            break
        elif "mysql" in content or "mariadb" in content:
            db = "mysql"
            break
        elif "mongodb" in content or "mongo:" in content:
            db = "mongodb"
            break
        elif "redis" in content:
            if not db:
                db = "redis"
    return db


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

    # Determine project type
    if fe and be:
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

    return profile


def to_yaml(data, indent=0):
    """Convert dict to YAML string without external dependencies."""
    lines = []
    prefix = "  " * indent
    for key, value in data.items():
        if isinstance(value, dict):
            lines.append(f"{prefix}{key}:")
            lines.append(to_yaml(value, indent + 1))
        elif isinstance(value, bool):
            lines.append(f"{prefix}{key}: {'true' if value else 'false'}")
        elif value is None:
            lines.append(f"{prefix}{key}: null")
        else:
            lines.append(f"{prefix}{key}: {value}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Detect project tech stack")
    parser.add_argument("--cwd", default=".", help="Project root directory")
    parser.add_argument("--output", default=None, help="Output path (default: <cwd>/.hody/profile.yaml)")
    parser.add_argument("--json", action="store_true", help="Output as JSON instead of YAML")
    parser.add_argument("--dry-run", action="store_true", help="Print to stdout, don't write file")
    args = parser.parse_args()

    cwd = os.path.abspath(args.cwd)
    if not os.path.isdir(cwd):
        print(f"Error: {cwd} is not a directory", file=sys.stderr)
        sys.exit(1)

    profile = build_profile(cwd)

    if args.json:
        output = json.dumps(profile, indent=2)
    else:
        output = to_yaml(profile)

    if args.dry_run:
        print(output)
        sys.exit(0)

    # Write to file
    output_path = args.output or os.path.join(cwd, ".hody", "profile.yaml")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w") as f:
        f.write(output + "\n")

    print(f"Profile written to {output_path}")
    print(f"Detected: {profile['project'].get('type', 'unknown')} project")

    # Print summary
    if "frontend" in profile:
        fe = profile["frontend"]
        print(f"  Frontend: {fe.get('framework', '?')} ({fe.get('language', '?')})")
    if "backend" in profile:
        be = profile["backend"]
        print(f"  Backend: {be.get('framework', '?')} ({be.get('language', '?')})")
    if "devops" in profile:
        devops = profile["devops"]
        parts = [f"{k}: {v}" for k, v in devops.items()]
        print(f"  DevOps: {', '.join(parts)}")


if __name__ == "__main__":
    main()
